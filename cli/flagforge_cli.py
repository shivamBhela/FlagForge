"""FlagForge companion CLI.

Provider operations are delegated to Flagsmith's official CLI; FlagForge adds
local static analysis and read-only intelligence commands around that workflow.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import getpass
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

VERSION = "0.1.0"
DEFAULT_IGNORES = {
    ".git", ".hg", ".svn", "node_modules", ".next", "dist", "build",
    "coverage", "vendor", "venv", ".venv", "__pycache__", "target",
}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
MAX_SOURCE_FILE_BYTES = 1_000_000
MAX_REPOSITORY_BYTES = 50_000_000
FLAG_CALL = re.compile(
    r"(?:flagsmith|flags)\.(?:hasFeature|isFeatureEnabled|isEnabled|getValue|"
    r"getFeatureValue|has_feature|is_feature_enabled|is_enabled|get_feature_value)\s*\("
)
JS_STRING = re.compile(r"(?:flagsmith|flags)\.(?:hasFeature|isFeatureEnabled|isEnabled|getValue|getFeatureValue)\s*\(\s*(['\"])([^'\"]+)\1")
JS_DYNAMIC = re.compile(r"(?:flagsmith|flags)\.(?:hasFeature|isFeatureEnabled|isEnabled|getValue|getFeatureValue)\s*\(\s*([^'\"\s][^)]*)\)")
JS_BRACKET = re.compile(r"(?:featureFlags|flags)\[\s*(['\"])([^'\"]+)\1\s*\]")
USE_FLAGS = re.compile(r"useFlags\(\s*\[([^\]]*)\]\s*\)")
STRINGS = re.compile(r"(['\"])([^'\"]+)\1")
ARCHIVE_REDIRECT_HOSTS = {"api.github.com", "codeload.github.com", "github.com"}


class CliError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def config_path() -> Path:
    return Path(os.environ.get("FLAGFORGE_CONFIG", ".flagforge/config.json"))


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CliError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CliError(f"Configuration at {path} must be a JSON object.")
    return value


def provider_command() -> list[str]:
    configured = os.environ.get("FLAGFORGE_FLAGSMITH_COMMAND")
    if configured:
        try:
            command = json.loads(configured)
        except json.JSONDecodeError as exc:
            raise CliError("FLAGFORGE_FLAGSMITH_COMMAND must be a JSON array of command parts.") from exc
        if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
            raise CliError("FLAGFORGE_FLAGSMITH_COMMAND must be a non-empty JSON array of strings.")
        return command
    path = shutil.which("flagsmith") or shutil.which("flagsmith.exe")
    if not path:
        raise CliError("Official Flagsmith CLI was not found. Install @flagsmith/cli or set FLAGFORGE_FLAGSMITH_COMMAND.", 127)
    return [path]


def run_provider(args: list[str], *, json_output: bool = False, check: bool = True,
                 extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = provider_command() + args
    env = os.environ.copy()
    config = load_config()
    env["FLAGSMITH_CONFIG_PATH"] = str(Path(config.get("flagsmith_config", ".flagforge/flagsmith.json")))
    if config.get("api_url"):
        env.setdefault("FLAGSMITH_API_URL", str(config["api_url"]))
    if json_output:
        env["FLAGSMITH_JSON_OUTPUT"] = "1"
    if extra_env:
        env.update(extra_env)
    try:
        result = subprocess.run(command, text=True, capture_output=True, env=env, timeout=90, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CliError(f"Could not run the official Flagsmith CLI: {exc}", 1) from exc
    if check and result.returncode:
        detail = (result.stderr or result.stdout).strip()
        # Provider output can contain API response data. Never echo credentials.
        detail = re.sub(r"(?i)(api[_ -]?key|token|authorization)\s*[:=]\s*\S+", r"\1=[redacted]", detail)
        if extra_env:
            for secret in sorted((value for value in extra_env.values() if value), key=len, reverse=True):
                detail = detail.replace(secret, "[redacted]")
        raise CliError(f"Flagsmith CLI command failed ({result.returncode}): {detail[:500] or 'no details'}", result.returncode)
    return result


def parse_json_output(result: subprocess.CompletedProcess[str], label: str) -> Any:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CliError(f"Official Flagsmith CLI did not return valid JSON for {label}; rerun with its documented --json output.", 1) from exc


def environment_sdk_key(label: str, variable: str, *, no_input: bool = False) -> str:
    key = os.environ.get(variable, "").strip()
    if not key and sys.stdin.isatty() and not no_input:
        key = getpass.getpass(f"{label} Flagsmith environment key (input hidden): ").strip()
    if not key:
        raise CliError(f"Set {variable} or run this command in a terminal to enter the key privately. Key values are never displayed.", 3)
    return key


def normalize_flag_list(value: Any, label: str) -> dict[str, dict[str, Any]]:
    """Normalize the documented official CLI flag-list JSON to enabled/value states."""
    if isinstance(value, dict):
        value = value.get("results", value.get("flags"))
    if not isinstance(value, list):
        raise CliError(f"Flagsmith returned an unsupported flag-list shape for {label}.", 1)

    flags: dict[str, dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, dict):
            raise CliError(f"Flagsmith returned an unsupported flag entry for {label}.", 1)
        feature = item.get("feature")
        name = item.get("name") or item.get("key")
        if not name and isinstance(feature, dict):
            name = feature.get("name") or feature.get("key")
        if not name and isinstance(feature, str):
            name = feature
        if not isinstance(name, str) or not name:
            raise CliError(f"Flagsmith returned a flag without a stable name for {label}.", 1)
        if name in flags:
            raise CliError(f"Flagsmith returned duplicate flag name {name!r} for {label}; refusing an ambiguous diff.", 1)
        state = {"enabled": item.get("enabled")}
        if "value" in item:
            state["value"] = item["value"]
        elif "feature_state_value" in item:
            state["value"] = item["feature_state_value"]
        flags[name] = state
    return flags


def diff_environments(source: str, target: str, *, no_input: bool = False) -> dict[str, Any]:
    source_key = environment_sdk_key("Source", "FLAGSMITH_SOURCE_ENVIRONMENT_KEY", no_input=no_input)
    target_key = environment_sdk_key("Target", "FLAGSMITH_TARGET_ENVIRONMENT_KEY", no_input=no_input)
    if source_key == target_key:
        raise CliError("Source and target environment keys must differ; no comparison was made.", 2)

    def load(label: str, key: str) -> dict[str, dict[str, Any]]:
        result = run_provider(
            ["flag", "list", "--json"], json_output=True,
            extra_env={"FLAGSMITH_ENVIRONMENT": key},
        )
        return normalize_flag_list(parse_json_output(result, f"{label} environment flag list"), label)

    source_flags = load(source, source_key)
    target_flags = load(target, target_key)
    source_names, target_names = set(source_flags), set(target_flags)
    return {
        "source_environment": source,
        "target_environment": target,
        "source_only": [{"flag": name, **source_flags[name]} for name in sorted(source_names - target_names)],
        "target_only": [{"flag": name, **target_flags[name]} for name in sorted(target_names - source_names)],
        "changed": [
            {"flag": name, "source": source_flags[name], "target": target_flags[name]}
            for name in sorted(source_names & target_names) if source_flags[name] != target_flags[name]
        ],
        "unchanged_count": sum(source_flags[name] == target_flags[name] for name in source_names & target_names),
        "comparison": "read-only enabled/value state via the official Flagsmith CLI",
    }


def gitignore_patterns(root: Path) -> list[str]:
    file = root / ".gitignore"
    if not file.is_file():
        return []
    return [line.strip().lstrip("/") for line in file.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip() and not line.lstrip().startswith("#") and not line.startswith("!")]


def ignored(relative: str, patterns: list[str]) -> bool:
    parts = PurePosixPath(relative).parts
    if any(part in DEFAULT_IGNORES for part in parts):
        return True
    name = parts[-1] if parts else ""
    if name in {".env", ".env.local", "secrets.json", "credentials.json"} or name.endswith((".min.js", ".map")):
        return True
    return any(fnmatch.fnmatch(relative, pattern) or fnmatch.fnmatch(name, pattern.rstrip("/"))
               or (pattern.endswith("/") and pattern.rstrip("/") in parts) for pattern in patterns)


def scan_python(path: str, content: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(content, filename=path)
    except SyntaxError:
        return scan_lexical(path, content)
    results: list[dict[str, Any]] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else (func.id if isinstance(func, ast.Name) else "")
            if name in {"has_feature", "is_feature_enabled", "is_enabled", "get_feature_value", "feature_state"} and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    results.append({"flag_key": first.value, "file_path": path, "line_number": node.lineno,
                                    "confidence": "high", "evidence": content.splitlines()[node.lineno - 1].strip()})
                else:
                    results.append({"flag_key": None, "file_path": path, "line_number": node.lineno,
                                    "confidence": "low", "evidence": "dynamic feature-flag reference"})
            self.generic_visit(node)

    Visitor().visit(tree)
    return results


def strip_javascript_comments(content: str) -> str:
    """Remove JS/TS comments while preserving quoted text and line numbers."""
    output: list[str] = []
    in_block = False
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(content):
        char = content[index]
        following = content[index:index + 2]
        if in_block:
            if following == "*/":
                output.append(" ")
                in_block = False
                index += 2
            else:
                if char == "\n":
                    output.append("\n")
                index += 1
            continue
        if quote:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if following == "/*":
            output.append(" ")
            in_block = True
            index += 2
            continue
        if following == "//":
            newline = content.find("\n", index)
            if newline == -1:
                break
            output.append("\n")
            index = newline + 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
        output.append(char)
        index += 1
    return "".join(output)


def scan_lexical(path: str, content: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    code_without_comments = strip_javascript_comments(content)
    original_lines = content.splitlines()
    for line_number, line in enumerate(code_without_comments.splitlines(), 1):
        evidence = original_lines[line_number - 1].strip() if line_number <= len(original_lines) else line.strip()
        values: list[tuple[str, str]] = []
        values.extend((match.group(2), "medium") for match in JS_STRING.finditer(line))
        values.extend((match.group(2), "medium") for match in JS_BRACKET.finditer(line))
        for match in USE_FLAGS.finditer(line):
            values.extend((item, "medium") for _, item in STRINGS.findall(match.group(1)))
        for match in JS_DYNAMIC.finditer(line):
            values.append(("", "low"))
        for key, confidence in values:
            results.append({"flag_key": key or None, "file_path": path, "line_number": line_number,
                            "confidence": confidence,
                            "evidence": evidence if key else "dynamic feature-flag reference"})
    return results


def scan_tree(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise CliError(f"Scan path is not a directory: {root}")
    patterns = gitignore_patterns(root)
    references: list[dict[str, Any]] = []
    files_scanned = 0
    bytes_scanned = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        rel_dir = Path(current).relative_to(root).as_posix()
        dirs[:] = [name for name in dirs if not ignored(f"{rel_dir}/{name}".lstrip("./"), patterns)
                   and not (Path(current) / name).is_symlink()]
        for name in names:
            file_path = Path(current) / name
            relative = file_path.relative_to(root).as_posix()
            if file_path.suffix.lower() not in SOURCE_SUFFIXES or ignored(relative, patterns) or file_path.is_symlink():
                continue
            try:
                size = file_path.stat().st_size
                if size > MAX_SOURCE_FILE_BYTES:
                    continue
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            files_scanned += 1
            bytes_scanned += size
            if bytes_scanned > MAX_REPOSITORY_BYTES:
                raise CliError("Scan exceeded the 50 MB source limit; narrow the path or add exclusions.")
            if file_path.suffix.lower() == ".py":
                references.extend(scan_python(relative, content))
            else:
                references.extend(scan_lexical(relative, content))
    return {"root": str(root), "files_scanned": files_scanned, "references": references,
            "coverage": {"python": "AST calls with literal keys; lexical fallback for invalid syntax",
                         "javascript_typescript": "supported Flagsmith call and bracket patterns; regex-based",
                         "dynamic_references": "reported without a guessed key", "other_languages": "not scanned"}}


def fetch_public_github_zip(repository_url: str) -> bytes:
    parsed = urllib.parse.urlsplit(repository_url)
    if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password:
        raise CliError("Repository URL must be an https://github.com/OWNER/REPOSITORY URL.")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) not in (2, 3) or (len(parts) == 3 and parts[2] != ""):
        raise CliError("Use a GitHub repository URL without a branch, file path, or query string.")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        raise CliError("Repository URL contains an invalid owner or repository name.")
    # The scanner validates and safely extracts ZIP files. GitHub's tarball
    # endpoint returns gzip-compressed TAR data, so request the matching zipball.
    url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": f"FlagForge/{VERSION}"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname not in ARCHIVE_REDIRECT_HOSTS:
                raise CliError("GitHub archive redirected to an unapproved host.")
            length = int(response.headers.get("Content-Length", "0") or "0")
            if length > MAX_REPOSITORY_BYTES:
                raise CliError("GitHub archive exceeds the 50 MB download limit.")
            data = response.read(MAX_REPOSITORY_BYTES + 1)
            if len(data) > MAX_REPOSITORY_BYTES:
                raise CliError("GitHub archive exceeds the 50 MB download limit.")
            return data
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise CliError("GitHub denied repository access; private repositories need a valid GITHUB_TOKEN.", 1) from exc
        if exc.code == 404:
            raise CliError("GitHub repository was not found or is not accessible.", 1) from exc
        raise CliError(f"GitHub archive request failed with HTTP {exc.code}.", 1) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise CliError(f"Could not download the GitHub archive: {exc}", 1) from exc


def scan_archive(data: bytes) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="flagforge-scan-") as temp:
        root = Path(temp).resolve()
        try:
            with zipfile.ZipFile(__import__("io").BytesIO(data)) as archive:
                total = sum(info.file_size for info in archive.infolist())
                if total > MAX_REPOSITORY_BYTES:
                    raise CliError("Expanded GitHub archive exceeds the 50 MB scan limit.")
                for info in archive.infolist():
                    member = PurePosixPath(info.filename)
                    if member.is_absolute() or ".." in member.parts or info.is_dir():
                        continue
                    if len(member.parts) < 2:
                        continue
                    destination = root.joinpath(*member.parts[1:]).resolve()
                    if root not in destination.parents:
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as source, destination.open("wb") as target:
                        shutil.copyfileobj(source, target, length=64 * 1024)
        except (zipfile.BadZipFile, OSError) as exc:
            raise CliError("GitHub returned an invalid source archive.", 1) from exc
        result = scan_tree(root)
        result.pop("root", None)
        result["source"] = "github-archive-read-only"
        return result


def emit(value: Any, *, json_output: bool, markdown: bool = False) -> None:
    if json_output:
        print(json.dumps(value, indent=2, sort_keys=True))
    elif markdown and isinstance(value, dict):
        print("# FlagForge Report\n")
        print(f"Files scanned: {value.get('files_scanned', 0)}\n")
        print("| Flag | File | Line | Confidence |\n| --- | --- | ---: | --- |")
        for ref in value.get("references", []):
            print(f"| {ref.get('flag_key') or 'dynamic'} | {ref['file_path']} | {ref['line_number']} | {ref['confidence']} |")
    else:
        print(json.dumps(value, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="flagforge", description="Feature-flag intelligence companion to the official Flagsmith CLI.")
    p.add_argument("--version", action="version", version=f"flagforge {VERSION}")
    p.add_argument("--json", action="store_true", help="Emit JSON where supported")
    commands = p.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Initialize secure local Flagsmith CLI project configuration")
    init.add_argument("--api-url", help="Self-hosted Flagsmith API base URL")
    init.add_argument("--no-input", action="store_true", help="Do not prompt in the official CLI")
    commands.add_parser("doctor", help="Check the official Flagsmith CLI and its configured authentication")
    flags = commands.add_parser("flags", help="Inspect real Flagsmith flags using the official CLI")
    flag_commands = flags.add_subparsers(dest="flags_command", required=True)
    flag_commands.add_parser("list", help="List flags in the current Flagsmith environment")
    inspect = flag_commands.add_parser("inspect", help="Inspect one flag in the current environment")
    inspect.add_argument("name")
    flag_commands.add_parser("audit", help="Compare local source references with current environment flags")
    scan = commands.add_parser("scan", help="Scan a local source directory (read-only)")
    scan.add_argument("path", nargs="?", default=".")
    scan.add_argument("--markdown", action="store_true")
    repo = commands.add_parser("scan-repo", help="Read-only scan of a public GitHub source archive")
    repo.add_argument("repository_url")
    commands.add_parser("dependencies", help="Build an evidence-only graph from local source references")
    diff = commands.add_parser("diff", help="Compare Flagsmith environments")
    diff.add_argument("source")
    diff.add_argument("target")
    diff.add_argument("--no-input", action="store_true", help="Do not prompt for missing environment keys")
    sync = commands.add_parser("sync", help="Preview configuration synchronization")
    sync.add_argument("--dry-run", action="store_true", help="Required: this CLI never mutates provider flags")
    risk = commands.add_parser("risk", help="Release risk tools")
    risk.add_argument("action", choices=["assess"])
    risk.add_argument("--flag", required=True)
    risk.add_argument("--environment", default="production")
    cleanup = commands.add_parser("cleanup", help="Review cleanup candidates")
    cleanup_sub = cleanup.add_subparsers(dest="cleanup_action", required=True)
    cleanup_sub.add_parser("preview", help="Preview candidates without changing source or provider state")
    monitor = commands.add_parser("monitor", help="Inspect available FlagForge telemetry")
    monitor.add_argument("--api-url", default=os.environ.get("FLAGFORGE_API_URL", "http://localhost:8000"))
    report = commands.add_parser("report", help="Export the latest local source audit")
    report.add_argument("--path", default=".")
    report.add_argument("--format", choices=["json", "markdown"], default="json")
    github = commands.add_parser("github", help="GitHub workflow tools")
    github_sub = github.add_subparsers(dest="github_action", required=True)
    github_sub.add_parser("pr", help="Explain the reviewed-PR workflow; creation requires authenticated approval")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            path = config_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            config = load_config()
            api_url = args.api_url or config.get("api_url")
            if api_url:
                parsed = urllib.parse.urlsplit(api_url)
                if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                    raise CliError("--api-url must be a valid http(s) URL.")
                config["api_url"] = api_url.rstrip("/")
            flagsmith_config = path.parent / "flagsmith.json"
            config["flagsmith_config"] = str(flagsmith_config)
            path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
            gitignore = Path(".gitignore")
            current = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
            if ".flagforge/" not in current.splitlines():
                gitignore.write_text(current.rstrip() + "\n\n# Local FlagForge and Flagsmith CLI credentials\n.flagforge/\n", encoding="utf-8")
            env = {"FLAGSMITH_CONFIG_PATH": str(flagsmith_config)}
            if api_url:
                env["FLAGSMITH_API_URL"] = api_url.rstrip("/")
            provider_args = ["init"] + (["--no-input"] if args.no_input else [])
            result = run_provider(provider_args, check=False, extra_env=env)
            if result.returncode:
                raise CliError((result.stderr or result.stdout).strip()[:500] or "Flagsmith CLI initialization failed.", result.returncode)
            print(f"Initialized local configuration in {path}; credential-bearing Flagsmith config stays under .flagforge/.")
            return 0

        if args.command == "doctor":
            result = run_provider(["--version"], check=False)
            if result.returncode:
                raise CliError("Official Flagsmith CLI is installed but could not report its version.", 1)
            print(f"Official Flagsmith CLI: {result.stdout.strip() or result.stderr.strip()}")
            status = run_provider(["auth", "status", "--json"], json_output=True, check=False)
            if status.returncode:
                print("Flagsmith authentication: not configured or unavailable")
                return 1
            print("Flagsmith authentication: configured (credential values not displayed)")
            return 0

        if args.command == "flags":
            if args.flags_command == "list":
                result = run_provider(["flag", "list", "--json"], json_output=True)
            elif args.flags_command == "inspect":
                result = run_provider(["flag", "get", args.name, "--json"], json_output=True)
            else:
                scan = scan_tree(Path("."))
                flags_value = parse_json_output(run_provider(["flag", "list", "--json"], json_output=True), "flag list")
                values = flags_value if isinstance(flags_value, list) else flags_value.get("results", []) if isinstance(flags_value, dict) else []
                names = {str(v.get("name") or v.get("feature") or v.get("key")) for v in values if isinstance(v, dict)}
                refs = scan["references"]
                emit({**scan, "unknown_references": [r for r in refs if r["flag_key"] and r["flag_key"] not in names],
                      "potentially_unused_flags": sorted(names - {r["flag_key"] for r in refs if r["flag_key"]}),
                      "matching_source": "official Flagsmith CLI flag list"}, json_output=args.json)
                return 0
            if args.json:
                sys.stdout.write(result.stdout)
                if result.stdout and not result.stdout.endswith("\n"):
                    print()
            else:
                print(result.stdout.strip())
            return 0

        if args.command in {"scan", "report", "dependencies", "cleanup"}:
            path = Path(args.path if args.command in {"scan", "report"} else ".")
            result = scan_tree(path)
            if args.command == "dependencies":
                edges = [{"source": f"flag:{r['flag_key']}", "target": f"file:{r['file_path']}",
                          "line": r["line_number"], "confidence": r["confidence"]}
                         for r in result["references"] if r["flag_key"]]
                result = {"nodes": sorted({edge[x] for edge in edges for x in ("source", "target")}), "edges": edges,
                          "evidence_policy": "Only source references create edges; no inferred runtime dependencies."}
            elif args.command == "cleanup":
                result = {"candidates": [], "status": "PREVIEW_ONLY",
                          "reason": "A local scan cannot prove a flag is unused without comparing accessible provider flags and scan scope."}
            elif args.command == "report":
                emit(result, json_output=args.json or args.format == "json", markdown=args.format == "markdown")
                return 0
            emit(result, json_output=args.json)
            return 0

        if args.command == "scan-repo":
            result = scan_archive(fetch_public_github_zip(args.repository_url))
            emit(result, json_output=args.json)
            return 0

        if args.command == "sync":
            if not args.dry_run:
                raise CliError("Only `flagforge sync --dry-run` is supported. Provider mutations are not implemented in this CLI.", 2)
            result = run_provider(["flag", "list", "--json"], json_output=True)
            flags_data = parse_json_output(result, "flag list")
            emit({"dry_run": True, "mutations": [], "provider_flags_read": len(flags_data) if isinstance(flags_data, list) else None}, json_output=args.json)
            return 0

        if args.command == "diff":
            emit(diff_environments(args.source, args.target, no_input=args.no_input), json_output=args.json)
            return 0

        if args.command == "risk":
            base = args.api_url if hasattr(args, "api_url") else os.environ.get("FLAGFORGE_API_URL", "http://localhost:8000")
            token = os.environ.get("FLAGFORGE_ACCESS_TOKEN")
            org = os.environ.get("FLAGFORGE_ORGANIZATION_ID")
            if not token or not org:
                raise CliError("Set FLAGFORGE_ACCESS_TOKEN and FLAGFORGE_ORGANIZATION_ID to query the authenticated FlagForge API. Values are read from the process environment and never displayed.", 3)
            query = urllib.parse.urlencode({"flag_key": args.flag, "environment_name": args.environment})
            request = urllib.request.Request(f"{base.rstrip('/')}/api/v1/organizations/{urllib.parse.quote(org)}/guardian/evaluate?{query}",
                                             headers={"Authorization": f"Bearer {token}"})
            with urllib.request.urlopen(request, timeout=15) as response:
                value = json.loads(response.read())
            emit(value, json_output=args.json)
            return 0

        if args.command == "monitor":
            url = args.api_url.rstrip("/") + "/healthz"
            with urllib.request.urlopen(url, timeout=5) as response:
                value = json.loads(response.read())
            emit({"api_health": value, "telemetry": "requires an authenticated project/org context in the dashboard"}, json_output=args.json)
            return 0

        if args.command == "github":
            raise CliError("Use the dashboard's reviewed cleanup patch flow for GitHub PRs. Live GitHub auth/PR creation is not configured in the companion CLI; it will not create a branch or PR.", 3)

    except (CliError, urllib.error.URLError, TimeoutError, OSError) as exc:
        if isinstance(exc, CliError):
            print(f"flagforge: {exc}", file=sys.stderr)
            return exc.code
        print(f"flagforge: network or filesystem error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
