"""Narrow GitHub REST client for repository discovery and cleanup pull requests."""
import base64
import time
from typing import Any, Optional
from urllib.parse import quote

import httpx
from jose import jwt

from app.core.config import settings
from app.core.crypto import decrypt_secret
from app.models.github import GitHubConnection

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"
MAX_SOURCE_BYTES = 1_000_000


class GitHubApiError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    def __init__(self, token: str, transport: Optional[httpx.AsyncBaseTransport] = None):
        self.token = token
        self.transport = transport

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        async with httpx.AsyncClient(
            base_url=API_URL,
            timeout=20.0,
            follow_redirects=False,
            transport=self.transport,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "FlagForge",
            },
        ) as client:
            try:
                response = await client.request(method, path, **kwargs)
            except httpx.RequestError as exc:
                raise GitHubApiError("Could not reach GitHub. Check the connection and retry.") from exc
        if not response.is_success:
            code = response.status_code
            message = {
                401: "GitHub credentials are invalid or expired.",
                403: "GitHub denied this request. Check token permissions and rate limits.",
                404: "The GitHub resource was not found or is not accessible to this connection.",
                409: "GitHub reported a repository conflict. Refresh repository state and retry.",
            }.get(code, f"GitHub API request failed ({code}).")
            raise GitHubApiError(message, code if code in (401, 403, 404, 409, 422) else 502)
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise GitHubApiError("GitHub returned an invalid response.") from exc

    async def list_repositories(self, credential_type: str) -> list[dict[str, Any]]:
        path = "/installation/repositories" if credential_type == "APP_INSTALLATION" else "/user/repos?per_page=100&sort=updated"
        result = await self.request("GET", path)
        repos = result.get("repositories", []) if credential_type == "APP_INSTALLATION" else result
        return [
            {
                "id": repo.get("id"),
                "full_name": repo.get("full_name"),
                "private": bool(repo.get("private")),
                "default_branch": repo.get("default_branch"),
                "permissions": repo.get("permissions") or {},
                "html_url": repo.get("html_url"),
            }
            for repo in repos
            if isinstance(repo, dict) and repo.get("full_name")
        ]

    async def get_repository(self, full_name: str) -> dict[str, Any]:
        owner, repo = split_repo(full_name)
        data = await self.request("GET", f"/repos/{owner}/{repo}")
        if data.get("full_name", "").lower() != full_name.lower():
            raise GitHubApiError("GitHub returned a different repository than the selected one.", 409)
        permissions = data.get("permissions") or {}
        if permissions.get("push") is not True and permissions.get("admin") is not True:
            raise GitHubApiError("The selected repository does not grant write access.", 403)
        if data.get("archived") or data.get("disabled"):
            raise GitHubApiError("The selected repository is archived or disabled.", 409)
        return data

    async def get_ref(self, full_name: str, branch: str) -> str:
        owner, repo = split_repo(full_name)
        ref = quote(branch, safe="")
        result = await self.request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{ref}")
        return str(result["object"]["sha"])

    async def get_commit(self, full_name: str, sha: str) -> dict[str, Any]:
        owner, repo = split_repo(full_name)
        return await self.request("GET", f"/repos/{owner}/{repo}/git/commits/{quote(sha, safe='')}")

    async def get_file(self, full_name: str, path: str, ref: str) -> tuple[str, str]:
        owner, repo = split_repo(full_name)
        encoded_path = "/".join(quote(part, safe="") for part in path.split("/"))
        result = await self.request("GET", f"/repos/{owner}/{repo}/contents/{encoded_path}", params={"ref": ref})
        if result.get("type") != "file" or result.get("encoding") != "base64":
            raise GitHubApiError("Only regular base64-encoded source files can be patched.", 409)
        if int(result.get("size", 0)) > MAX_SOURCE_BYTES:
            raise GitHubApiError("Source files larger than 1 MB cannot be edited through Cleanup Studio.", 413)
        try:
            content = base64.b64decode(result["content"], validate=False).decode("utf-8")
        except (KeyError, UnicodeDecodeError, ValueError) as exc:
            raise GitHubApiError("The selected source file is not valid UTF-8 text.", 409) from exc
        return content, str(result["sha"])

    async def create_branch(self, full_name: str, branch: str, base_sha: str) -> None:
        owner, repo = split_repo(full_name)
        await self.request("POST", f"/repos/{owner}/{repo}/git/refs", json={"ref": f"refs/heads/{branch}", "sha": base_sha})

    async def put_file(self, full_name: str, path: str, branch: str, content: str, old_sha: str, message: str) -> dict[str, Any]:
        owner, repo = split_repo(full_name)
        encoded_path = "/".join(quote(part, safe="") for part in path.split("/"))
        return await self.request(
            "PUT", f"/repos/{owner}/{repo}/contents/{encoded_path}",
            json={
                "message": message,
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "branch": branch,
                "sha": old_sha,
            },
        )

    async def find_pull_request(self, full_name: str, branch: str, base: str) -> Optional[dict[str, Any]]:
        owner, repo = split_repo(full_name)
        results = await self.request("GET", f"/repos/{owner}/{repo}/pulls", params={"state": "all", "head": f"{owner}:{branch}", "base": base, "per_page": 100})
        return results[0] if results else None

    async def create_pull_request(self, full_name: str, branch: str, base: str, title: str, body: str) -> dict[str, Any]:
        owner, repo = split_repo(full_name)
        return await self.request("POST", f"/repos/{owner}/{repo}/pulls", json={"head": branch, "base": base, "title": title[:200], "body": body[:60000], "draft": False})

    async def get_pull_request(self, full_name: str, number: int) -> dict[str, Any]:
        owner, repo = split_repo(full_name)
        return await self.request("GET", f"/repos/{owner}/{repo}/pulls/{number}")


def split_repo(full_name: str) -> tuple[str, str]:
    pieces = full_name.split("/")
    if len(pieces) != 2 or any(not part or part in (".", "..") for part in pieces):
        raise GitHubApiError("Repository must use owner/name format.", 422)
    return pieces[0], pieces[1]


async def get_client_for_connection(connection: GitHubConnection) -> GitHubClient:
    if connection.credential_type == "FINE_GRAINED_PAT":
        if not connection.encrypted_token:
            raise GitHubApiError("GitHub fine-grained token is not configured.", 503)
        return GitHubClient(decrypt_secret(connection.encrypted_token))
    if connection.credential_type != "APP_INSTALLATION" or not connection.installation_id:
        raise GitHubApiError("GitHub App installation is not configured.", 503)
    if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY:
        raise GitHubApiError("Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY on the server first.", 503)
    now = int(time.time())
    private_key = settings.GITHUB_APP_PRIVATE_KEY.replace("\\n", "\n")
    app_jwt = jwt.encode({"iat": now - 30, "exp": now + 8 * 60, "iss": settings.GITHUB_APP_ID}, private_key, algorithm="RS256")
    app_client = GitHubClient(app_jwt)
    token_body = None
    if connection.repository_full_name:
        token_body = {"repositories": [connection.repository_full_name.split("/", 1)[1]]}
    token_data = await app_client.request(
        "POST",
        f"/app/installations/{quote(connection.installation_id, safe='')}/access_tokens",
        json=token_body,
    )
    token = token_data.get("token")
    expires_at = token_data.get("expires_at")
    if not token or not expires_at:
        raise GitHubApiError("GitHub did not return an installation token with an expiry.")
    return GitHubClient(token)
