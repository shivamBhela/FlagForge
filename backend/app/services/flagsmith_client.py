import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlsplit
import httpx
from app.core.ssrf import validate_target_url

logger = logging.getLogger("flagsmith-client")


class FlagsmithApiError(Exception):
    """Flagsmith API call failed."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FlagsmithClient:
    """Asynchronous HTTP client for Flagsmith Management API."""

    def __init__(self, base_url: str, token: str, timeout: float = 15.0):
        # Normalize base URL (strip trailing slash)
        clean_url = base_url.strip().rstrip("/")
        if clean_url.endswith("/api"):
            clean_url = f"{clean_url}/v1"
        elif not clean_url.endswith("/api/v1"):
            clean_url = f"{clean_url}/api/v1"
        self.base_url = clean_url
        self.token = token.strip()
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            # Flagsmith Management API organisation tokens use the Api-Key scheme.
            "Authorization": f"Api-Key {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "FlagForge/1.0",
        }

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        visited_urls = set()
        results = []
        # follow_redirects=False strictly prevents redirect-based SSRF attacks
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
            for page_number in range(1, 101):
                if url in visited_urls:
                    raise FlagsmithApiError("Flagsmith returned a repeated pagination URL.")
                visited_urls.add(url)

                try:
                    response = await client.request(
                        method,
                        url,
                        headers=self._headers(),
                        **(kwargs if page_number == 1 else {}),
                    )
                except httpx.TimeoutException:
                    raise FlagsmithApiError(f"Connection to Flagsmith at {self.base_url} timed out.", status_code=504)
                except httpx.RequestError as e:
                    raise FlagsmithApiError(f"Network error connecting to Flagsmith: {str(e)}", status_code=502)

                if response.status_code in (401, 403):
                    raise FlagsmithApiError("Flagsmith authentication failed. Please check your Management API token.", status_code=response.status_code)
                elif response.status_code == 404:
                    raise FlagsmithApiError(f"Flagsmith resource not found at {path}", status_code=404)
                elif response.status_code == 429:
                    raise FlagsmithApiError("Flagsmith rate limit exceeded.", status_code=429)
                elif response.status_code >= 500:
                    raise FlagsmithApiError(f"Flagsmith server error ({response.status_code}): {response.text[:200]}", status_code=response.status_code)
                elif not response.is_success:
                    raise FlagsmithApiError(f"Flagsmith API request failed ({response.status_code}): {response.text[:200]}", status_code=response.status_code)

                try:
                    data = response.json()
                except Exception:
                    return response.text

                if isinstance(data, dict) and isinstance(data.get("results"), list):
                    results.extend(data["results"])
                    next_page = data.get("next")
                    if not next_page:
                        return results
                    next_url = urljoin(url, next_page)
                    self._validate_pagination_url(next_url)
                    url = next_url
                    continue
                return data

            raise FlagsmithApiError("Flagsmith pagination exceeded the 100-page safety limit.")

    def _validate_pagination_url(self, next_url: str) -> None:
        """Keep API-provided pagination links on the configured origin and API path."""
        base = urlsplit(self.base_url)
        target = urlsplit(next_url)
        same_origin = (
            target.scheme == base.scheme
            and target.hostname == base.hostname
            and target.port == base.port
        )
        api_path = base.path.rstrip("/")
        within_api = target.path == api_path or target.path.startswith(f"{api_path}/")
        if not same_origin or not within_api:
            raise FlagsmithApiError("Flagsmith returned a pagination URL outside the configured API origin.")

    async def test_connection(self) -> Dict[str, Any]:
        """Tests API reachability and credentials against /projects/."""
        projects = await self.get_projects()
        return {
            "ok": True,
            "projects_count": len(projects) if isinstance(projects, list) else 0,
            "message": "Successfully connected to Flagsmith instance.",
        }

    async def get_projects(self) -> List[Dict[str, Any]]:
        """Retrieves list of projects accessible via token."""
        data = await self._request("GET", "/projects/")
        return data if isinstance(data, list) else []

    async def get_project_environments(self, project_id: str | int) -> List[Dict[str, Any]]:
        """Retrieves environments configured for a project."""
        data = await self._request("GET", f"/projects/{project_id}/environments/")
        return data if isinstance(data, list) else []

    async def get_project_features(self, project_id: str | int) -> List[Dict[str, Any]]:
        """Retrieves feature flags configured for a project."""
        data = await self._request("GET", f"/projects/{project_id}/features/")
        return data if isinstance(data, list) else []

    async def get_environment_feature_states(self, environment_api_key: str) -> List[Dict[str, Any]]:
        """Retrieves current feature states for an environment."""
        data = await self._request("GET", f"/environments/{environment_api_key}/featurestates/")
        return data if isinstance(data, list) else []
