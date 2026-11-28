import ast
import io
import os
import re
import uuid
import logging
import urllib.parse
import urllib.request
import urllib.error
import zipfile
from pathlib import PurePosixPath
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.code_intelligence import (
    Repository,
    Scan,
    ScanStatus,
    FlagReference,
    ReferenceStatus,
)
from app.models.feature_flag import FeatureFlag

logger = logging.getLogger("code-scanner")

ARCHIVE_REDIRECT_HOSTS = {"github.com", "codeload.github.com", "api.github.com"}
MAX_REPOSITORY_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_FILE_BYTES = 1024 * 1024  # 1 MB
MAX_FILE_COUNT = 1000
SCANNABLE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
IGNORED_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".cache",
    ".pytest_cache",
}

# Common JS/TS flag pattern expressions
JS_FLAG_PATTERNS = [
    # flagsmith.hasFeature("flag_key") or flags.isFeatureEnabled("flag_key")
    (r"""(?:flagsmith|flags)\.(?:hasFeature|isFeatureEnabled|isEnabled)\(\s*['"]([^'"]+)['"]\s*\)""", 0.95),
    # flagsmith.getValue("flag_key") or flagsmith.getFeatureValue("flag_key")
    (r"""(?:flagsmith|flags)\.(?:getValue|getFeatureValue)\(\s*['"]([^'"]+)['"]\s*\)""", 0.95),
    # useFlags(["flag_1", "flag_2"])
    (r"""useFlags\(\s*\[([^\]]+)\]\s*\)""", 0.95),
    # isFeatureEnabled("flag_key")
    (r"""isFeatureEnabled\(\s*['"]([^'"]+)['"]\s*\)""", 0.95),
    # featureFlags['flag_key'] or flags['flag_key']
    (r"""(?:featureFlags|flags)\[\s*['"]([^'"]+)['"]\s*\]""", 0.90),
]

JS_DYNAMIC_PATTERNS = [
    r"""(?:flagsmith|flags)\.(?:hasFeature|isFeatureEnabled|isEnabled|getValue|getFeatureValue)\(\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\)""",
]


def strip_comments_preserving_lines(content: str) -> str:
    """Strips single-line and multi-line comments from JS/TS source code

    Preserves line count and character positions so line numbers match the original file.
    """
    def block_comment_replacer(match):
        text = match.group(0)
        newlines = text.count("\n")
        return "\n" * newlines + " " * (len(text) - text.rfind("\n") - 1 if newlines > 0 else len(text))

    def line_comment_replacer(match):
        return " " * len(match.group(0))

    # Strip multi-line comments
    stripped = re.sub(r"/\*.*?\*/", block_comment_replacer, content, flags=re.DOTALL)
    # Strip single-line comments
    stripped = re.sub(r"//[^\n]*", line_comment_replacer, stripped)
    return stripped


class CodeScanner:
    """Language-aware AST and lexical static scanner for Python and TypeScript/JavaScript."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    @staticmethod
    def fetch_public_github_zip(repository_url: str, ref: Optional[str] = None) -> bytes:
        """Securely downloads a GitHub repository source zipball.

        Enforces:
        - Strict https scheme and github.com host validation
        - Safe redirect host whitelist
        - Download size limit (50 MB)
        - Least-privilege GITHUB_TOKEN support
        """
        parsed = urllib.parse.urlsplit(repository_url)
        if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password:
            raise ValueError("Repository URL must be an https://github.com/OWNER/REPOSITORY URL.")

        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(parts) not in (2, 3) or (len(parts) == 3 and parts[2] != ""):
            raise ValueError("Repository URL must not contain extra path components or query parameters.")

        owner = parts[0]
        repo = parts[1].removesuffix(".git")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
            raise ValueError("Repository URL contains an invalid owner or repository name.")

        target_ref = ref.strip() if ref and ref.strip() and ref.strip() != "HEAD" else "main"
        url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{target_ref}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "FlagForge/0.1.0",
        }
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                final = urllib.parse.urlsplit(resp.geturl())
                if final.scheme != "https" or final.hostname not in ARCHIVE_REDIRECT_HOSTS:
                    raise ValueError("GitHub archive redirected to an unapproved host.")

                length = int(resp.headers.get("Content-Length", "0") or "0")
                if length > MAX_REPOSITORY_BYTES:
                    raise ValueError(f"GitHub archive exceeds {MAX_REPOSITORY_BYTES // (1024 * 1024)} MB download limit.")

                data = resp.read(MAX_REPOSITORY_BYTES + 1)
                if len(data) > MAX_REPOSITORY_BYTES:
                    raise ValueError(f"GitHub archive exceeds {MAX_REPOSITORY_BYTES // (1024 * 1024)} MB download limit.")
                return data

        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise ValueError("GitHub denied repository access. Private repositories require a valid GITHUB_TOKEN.") from exc
            if exc.code == 404:
                raise ValueError(f"GitHub repository {owner}/{repo} (ref: {target_ref}) was not found or is inaccessible.") from exc
            raise ValueError(f"GitHub archive request failed with HTTP {exc.code}.") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ValueError(f"Could not download GitHub repository archive: {exc}") from exc

    @staticmethod
    def extract_source_files_from_zip(data: bytes) -> Dict[str, str]:
        """Safely extracts scannable source code files from a zipball archive in-memory.

        Protects against:
        - Zip traversal (Zip Slip) attacks
        - Archive zip bombs (max total uncompressed size)
        - Binary files, symlinks, and ignored folders (.git, node_modules, etc.)
        - Individual file size limits
        """
        source_files: Dict[str, str] = {}
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                total_uncompressed = sum(info.file_size for info in archive.infolist())
                if total_uncompressed > MAX_REPOSITORY_BYTES:
                    raise ValueError(f"Expanded archive exceeds {MAX_REPOSITORY_BYTES // (1024 * 1024)} MB limit.")

                file_count = 0
                for info in archive.infolist():
                    # Reject symlinks (mode attribute check)
                    mode = info.external_attr >> 16
                    if (mode & 0o120000) == 0o120000:
                        continue

                    member = PurePosixPath(info.filename)
                    if member.is_absolute() or ".." in member.parts or info.is_dir():
                        continue

                    # GitHub zipball archives have a top-level directory: owner-repo-sha/...
                    if len(member.parts) < 2:
                        continue

                    rel_parts = member.parts[1:]
                    # Check ignored directories
                    if any(part in IGNORED_DIR_NAMES for part in rel_parts):
                        continue

                    rel_path = "/".join(rel_parts)
                    ext = PurePosixPath(rel_path).suffix.lower()
                    if ext not in SCANNABLE_EXTENSIONS:
                        continue

                    if info.file_size > MAX_FILE_BYTES:
                        continue

                    file_count += 1
                    if file_count > MAX_FILE_COUNT:
                        logger.warning("Reached maximum file count limit (%d); halting archive extraction.", MAX_FILE_COUNT)
                        break

                    raw = archive.read(info)
                    try:
                        content = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            content = raw.decode("latin-1")
                        except Exception:
                            continue

                    source_files[rel_path] = content

        except zipfile.BadZipFile as exc:
            raise ValueError("The downloaded repository archive was not a valid ZIP file.") from exc

        return source_files

    def scan_python_content(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parses Python source using the native AST engine and extracts feature flag references.

        Does NOT fall back to JavaScript regex if Python syntax is invalid.
        """
        findings = []
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            logger.warning("Python syntax error in %s: %s; skipping unparseable file.", file_path, e)
            return findings

        lines = content.splitlines()

        class FlagVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_scope = None

            def visit_FunctionDef(self, node):
                prev = self.current_scope
                self.current_scope = node.name
                self.generic_visit(node)
                self.current_scope = prev

            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)

            def visit_ClassDef(self, node):
                prev = self.current_scope
                self.current_scope = node.name
                self.generic_visit(node)
                self.current_scope = prev

            def visit_Call(self, node):
                flag_key = None
                confidence = 1.0

                # 1. flagsmith.has_feature("flag_key") or flags.is_enabled("flag_key")
                if isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name in ("has_feature", "is_feature_enabled", "is_enabled", "get_feature_value", "feature_state"):
                        if node.args:
                            arg0 = node.args[0]
                            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                                flag_key = arg0.value
                            elif isinstance(arg0, ast.Name):
                                flag_key = None
                                confidence = 0.5
                # 2. is_feature_enabled("flag_key")
                elif isinstance(node.func, ast.Name):
                    if node.func.id in ("is_feature_enabled", "has_feature", "is_enabled"):
                        if node.args:
                            arg0 = node.args[0]
                            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                                flag_key = arg0.value
                            elif isinstance(arg0, ast.Name):
                                flag_key = None
                                confidence = 0.5

                if flag_key is not None or confidence < 1.0:
                    line_no = getattr(node, "lineno", 1)
                    snippet = lines[line_no - 1].strip() if 0 <= line_no - 1 < len(lines) else ""
                    findings.append({
                        "flag_key": flag_key or "[dynamic_reference]",
                        "file_path": file_path,
                        "line_number": line_no,
                        "symbol_name": self.current_scope or "module_scope",
                        "parser_confidence": confidence,
                        "evidence_snippet": snippet,
                    })

                self.generic_visit(node)

        visitor = FlagVisitor()
        visitor.visit(tree)
        return findings

    def scan_regex_content(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Lexical and pattern-based flag reference detection for TypeScript and JavaScript.

        Strips comments first to prevent false positives in commented-out blocks.
        """
        findings = []
        clean_content = strip_comments_preserving_lines(content)
        lines = clean_content.splitlines()

        for line_idx, line in enumerate(lines, start=1):
            if not line.strip():
                continue

            # Check known JS/TS flag call patterns
            for pat, conf in JS_FLAG_PATTERNS:
                matches = re.finditer(pat, line)
                for m in matches:
                    raw_flags = m.group(1)
                    # Handle multiple flags inside array (e.g. useFlags(["a", "b"]))
                    if "," in raw_flags:
                        for part in raw_flags.split(","):
                            clean_part = part.strip().strip("'\"")
                            if clean_part:
                                findings.append({
                                    "flag_key": clean_part,
                                    "file_path": file_path,
                                    "line_number": line_idx,
                                    "symbol_name": "component_scope",
                                    "parser_confidence": conf,
                                    "evidence_snippet": line.strip(),
                                })
                    else:
                        clean_flag = raw_flags.strip().strip("'\"")
                        if clean_flag:
                            findings.append({
                                "flag_key": clean_flag,
                                "file_path": file_path,
                                "line_number": line_idx,
                                "symbol_name": "component_scope",
                                "parser_confidence": conf,
                                "evidence_snippet": line.strip(),
                            })

            # Check dynamic references
            for pat in JS_DYNAMIC_PATTERNS:
                matches = re.finditer(pat, line)
                for m in matches:
                    arg_name = m.group(1)
                    if arg_name not in ("true", "false", "null", "undefined") and not re.search(r"""['"]""", line[m.start():m.end()]):
                        # Only record if not already captured by static pattern on same line
                        if not any(f["line_number"] == line_idx and f["flag_key"] != "[dynamic_reference]" for f in findings):
                            findings.append({
                                "flag_key": "[dynamic_reference]",
                                "file_path": file_path,
                                "line_number": line_idx,
                                "symbol_name": "component_scope",
                                "parser_confidence": 0.50,
                                "evidence_snippet": line.strip(),
                            })

        return findings

    async def execute_scan(
        self,
        repository_id: uuid.UUID,
        commit_sha: str = "HEAD",
        branch: str = "main",
        custom_files: Optional[Dict[str, str]] = None,
        background_job_id: Optional[uuid.UUID] = None,
    ) -> Scan:
        """Executes a code scan across supplied or live repository source files and records references."""
        if background_job_id is not None:
            prior = (await self.db.execute(select(Scan).where(
                Scan.organization_id == self.organization_id,
                Scan.background_job_id == background_job_id,
            ))).scalar_one_or_none()
            if prior is not None:
                return prior

        # Verify repository exists and belongs to this organization
        stmt_repo = select(Repository).where(
            Repository.id == repository_id,
            Repository.organization_id == self.organization_id,
        )
        repo = (await self.db.execute(stmt_repo)).scalar_one_or_none()
        if not repo:
            raise ValueError(f"Repository {repository_id} not found in this organization.")

        scan = Scan(
            organization_id=self.organization_id,
            repository_id=repository_id,
            commit_sha=commit_sha,
            branch=branch,
            background_job_id=background_job_id,
            status=ScanStatus.RUNNING,
        )
        self.db.add(scan)
        await self.db.commit()
        await self.db.refresh(scan)

        try:
            # Query existing registered Flagsmith flags for this organization to match against
            stmt_flags = select(FeatureFlag.key).join(FeatureFlag.project).where(
                FeatureFlag.project.has(organization_id=self.organization_id)
            )
            known_flags = set((await self.db.execute(stmt_flags)).scalars().all())

            # Determine files to scan
            if custom_files:
                files_to_scan = custom_files
            else:
                # Real repository archive download
                target_ref = commit_sha if commit_sha and commit_sha != "HEAD" else (branch or repo.default_branch or "main")
                zip_data = self.fetch_public_github_zip(repo.repo_url, ref=target_ref)
                files_to_scan = self.extract_source_files_from_zip(zip_data)
                if not files_to_scan:
                    raise ValueError(f"No scannable source code files (.py, .ts, .tsx, .js) found in repository {repo.name}.")

            all_findings = []
            for file_path, content in files_to_scan.items():
                if file_path.endswith(".py"):
                    findings = self.scan_python_content(content, file_path)
                else:
                    findings = self.scan_regex_content(content, file_path)
                all_findings.extend(findings)

            # Persist findings into flag_references
            for f in all_findings:
                flag_key = f["flag_key"]
                is_known = flag_key in known_flags
                ref_status = ReferenceStatus.CONFIRMED if is_known else ReferenceStatus.UNRESOLVED

                ref = FlagReference(
                    organization_id=self.organization_id,
                    scan_id=scan.id,
                    repository_id=repository_id,
                    flag_key=flag_key,
                    file_path=f["file_path"],
                    line_number=f["line_number"],
                    symbol_name=f.get("symbol_name"),
                    parser_confidence=f.get("parser_confidence", 1.0),
                    evidence_snippet=f.get("evidence_snippet"),
                    status=ref_status,
                )
                self.db.add(ref)

            scan.files_scanned = len(files_to_scan)
            scan.findings_count = len(all_findings)
            scan.status = ScanStatus.COMPLETED
            await self.db.commit()
            await self.db.refresh(scan)
            return scan

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Scan failed for repo {repository_id}: {e}", exc_info=True)
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)
            self.db.add(scan)
            await self.db.commit()
            await self.db.refresh(scan)
            return scan
