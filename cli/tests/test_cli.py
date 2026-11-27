import importlib.util
import io
import json
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


if __name__ == "__main__":
    unittest.main()
