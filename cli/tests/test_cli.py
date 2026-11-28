import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).parents[1] / "flagforge_cli.py"
spec = importlib.util.spec_from_file_location("flagforge_cli", MODULE_PATH)
cli = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(cli)


class ScannerTests(unittest.TestCase):
    def test_cleanup_preview_is_explicit_and_read_only(self):
        args = cli.parser().parse_args(["cleanup", "preview"])
        self.assertEqual(args.cleanup_action, "preview")

    def test_python_ast_references_and_dynamic_marked_unknown(self):
        refs = cli.scan_python("src/a.py", 'flagsmith.has_feature("checkout")\nflagsmith.is_enabled(feature_name)\n')
        self.assertEqual(refs[0]["flag_key"], "checkout")
        self.assertEqual(refs[0]["line_number"], 1)
        self.assertEqual(refs[0]["confidence"], "high")
        self.assertIsNone(refs[1]["flag_key"])
        self.assertEqual(refs[1]["confidence"], "low")

    def test_typescript_patterns_and_dynamic_reference(self):
        refs = cli.scan_lexical("src/flags.ts", 'flagsmith.hasFeature("new_checkout"); flagsmith.getValue(name);')
        self.assertEqual([ref["flag_key"] for ref in refs], ["new_checkout", None])
        self.assertEqual(refs[0]["confidence"], "medium")

    def test_javascript_comments_do_not_create_references(self):
        source = '''
// flagsmith.hasFeature("commented_line")
/* flagsmith.getValue("commented_block") */
const enabled = flagsmith.hasFeature("real_flag");
'''
        refs = cli.scan_lexical("src/flags.ts", source)
        self.assertEqual([ref["flag_key"] for ref in refs], ["real_flag"])
        self.assertEqual(refs[0]["line_number"], 4)

    def test_walk_ignores_generated_and_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".gitignore").write_text("generated/\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "generated").mkdir()
            (root / "src" / "app.ts").write_text('flagsmith.hasFeature("on");', encoding="utf-8")
            (root / "src" / ".env").write_text('FLAGSMITH_TOKEN="secret"', encoding="utf-8")
            (root / "generated" / "gen.ts").write_text('flagsmith.hasFeature("off");', encoding="utf-8")
            result = cli.scan_tree(root)
            self.assertEqual(result["files_scanned"], 1)
            self.assertEqual([ref["flag_key"] for ref in result["references"]], ["on"])

    def test_archive_path_traversal_is_not_extracted(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("owner-repo-root/../escape.py", 'flagsmith.has_feature("bad")')
            archive.writestr("owner-repo-root/src/good.py", 'flagsmith.has_feature("safe")')
        result = cli.scan_archive(buffer.getvalue())
        self.assertEqual([ref["flag_key"] for ref in result["references"]], ["safe"])

    def test_repo_url_rejects_non_github_hosts_before_network(self):
        with self.assertRaises(cli.CliError):
            cli.fetch_public_github_zip("https://example.com/owner/repo")

    def test_github_archive_fetch_uses_zipball_endpoint(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("owner-repo-root/src/app.py", 'flagsmith.has_feature("checkout")')
        payload = buffer.getvalue()

        class FakeResponse(io.BytesIO):
            headers = {"Content-Length": str(len(payload))}

            def geturl(self):
                return "https://codeload.github.com/owner/repo/legacy.zip/refs/heads/main"

        with patch.object(cli.urllib.request, "urlopen", return_value=FakeResponse(payload)) as open_url:
            self.assertEqual(cli.fetch_public_github_zip("https://github.com/owner/repo.git"), payload)

        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.github.com/repos/owner/repo/zipball")
        result = cli.scan_archive(payload)
        self.assertEqual([ref["flag_key"] for ref in result["references"]], ["checkout"])

    def test_environment_diff_reports_only_read_only_state_changes_without_exposing_keys(self):
        source_key = "source-sdk-key-do-not-print"
        target_key = "target-sdk-key-do-not-print"
        source = [
            {"name": "checkout", "enabled": True, "feature_state_value": "v1"},
            {"feature": {"name": "unchanged"}, "enabled": False, "value": None},
            {"name": "source_only", "enabled": True},
        ]
        target = [
            {"name": "checkout", "enabled": False, "feature_state_value": "v2"},
            {"feature": {"name": "unchanged"}, "enabled": False, "value": None},
            {"key": "target_only", "enabled": True},
        ]

        with patch.dict(os.environ, {
            "FLAGSMITH_SOURCE_ENVIRONMENT_KEY": source_key,
            "FLAGSMITH_TARGET_ENVIRONMENT_KEY": target_key,
        }):
            with patch.object(cli, "run_provider", side_effect=[
                subprocess.CompletedProcess([], 0, json.dumps(source), ""),
                subprocess.CompletedProcess([], 0, json.dumps(target), ""),
            ]) as provider, patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(cli.main(["--json", "diff", "staging", "production"]), 0)

        calls = provider.call_args_list
        self.assertEqual(calls[0].kwargs["extra_env"]["FLAGSMITH_ENVIRONMENT"], source_key)
        self.assertEqual(calls[1].kwargs["extra_env"]["FLAGSMITH_ENVIRONMENT"], target_key)
        output = stdout.getvalue()
        self.assertNotIn(source_key, output)
        self.assertNotIn(target_key, output)
        result = json.loads(output)
        self.assertEqual(result["source_only"][0]["flag"], "source_only")
        self.assertEqual(result["target_only"][0]["flag"], "target_only")
        self.assertEqual(result["changed"][0]["flag"], "checkout")
        self.assertEqual(result["unchanged_count"], 1)

    def test_environment_diff_refuses_same_key(self):
        key = "same-environment-key"
        with patch.dict(os.environ, {
            "FLAGSMITH_SOURCE_ENVIRONMENT_KEY": key,
            "FLAGSMITH_TARGET_ENVIRONMENT_KEY": key,
        }), patch.object(cli, "run_provider") as provider, patch("sys.stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(cli.main(["diff", "staging", "staging-copy"]), 2)
        provider.assert_not_called()
        self.assertNotIn(key, stderr.getvalue())

    def test_environment_diff_requires_private_keys_in_noninteractive_mode(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FLAGSMITH_SOURCE_ENVIRONMENT_KEY", None)
            os.environ.pop("FLAGSMITH_TARGET_ENVIRONMENT_KEY", None)
            with patch("sys.stdin.isatty", return_value=False), patch("sys.stderr", new_callable=io.StringIO) as stderr:
                self.assertEqual(cli.main(["diff", "staging", "production", "--no-input"]), 3)
        self.assertIn("FLAGSMITH_SOURCE_ENVIRONMENT_KEY", stderr.getvalue())

    def test_provider_error_redacts_environment_key(self):
        key = "do-not-leak-environment-key"
        failed = subprocess.CompletedProcess(["flagsmith"], 1, "", f"request failed for {key}")
        with patch.object(cli, "provider_command", return_value=["flagsmith"]), patch.object(
            cli.subprocess, "run", return_value=failed
        ), patch.dict(os.environ, {}):
            with self.assertRaises(cli.CliError) as error:
                cli.run_provider(["flag", "list"], extra_env={"FLAGSMITH_ENVIRONMENT": key})
        self.assertNotIn(key, str(error.exception))


if __name__ == "__main__":
    unittest.main()
