# FlagForge CLI (companion)

FlagForge uses the official [Flagsmith CLI](https://github.com/Flagsmith/flagsmith-cli) as its provider command layer. The upstream CLI is a standalone Go program with its own supported commands and API client; it does not document a plugin or Python library extension point. FlagForge therefore does **not** claim to be an upstream plugin or fork. It delegates provider operations (initialization, flag list/get, authentication status) to the official CLI and adds read-only code intelligence around its output.

The upstream CLI is MIT-licensed. Install it using the official instructions, then install this companion package:

```powershell
python -m pip install -e .\cli
flagforge --help
```

The package has no runtime dependencies beyond Python 3.11+. Use the official CLI's documented secure login or environment-based credentials; do not put credentials in source files. `flagforge init` stores the Flagsmith CLI config under `.flagforge/` and adds that directory to `.gitignore`.

## Commands

```text
flagforge init [--api-url URL]
flagforge doctor
flagforge flags list
flagforge flags inspect NAME
flagforge flags audit
flagforge scan [PATH]
flagforge scan-repo https://github.com/OWNER/REPOSITORY
flagforge dependencies
flagforge diff SOURCE TARGET
flagforge sync --dry-run
flagforge risk assess --flag KEY [--environment NAME]
flagforge cleanup preview
flagforge monitor
flagforge report [--path PATH] [--format json|markdown]
flagforge github pr
```

`flags list`, `flags inspect`, and provider reads are delegated to the official CLI. `scan` supports Python AST call patterns and regex-based JavaScript/TypeScript patterns. It excludes common generated/dependency directories, symlinks, `.env` files and large files. Dynamic references are surfaced without a guessed key. GitHub archive scanning accepts only `github.com` URLs, downloads a size-limited tarball to memory, extracts into a temporary directory with path traversal checks, and never executes repository code. An optional `GITHUB_TOKEN` is consumed only from the process environment for private repository access.

Commands whose safe full behavior needs additional provider or authenticated application context are explicit about their limits: named environment diff is not implemented in this companion; `sync` is dry-run only; `risk` needs `FLAGFORGE_ACCESS_TOKEN` and `FLAGFORGE_ORGANIZATION_ID`; `cleanup preview` reports no candidates unless provider comparison proves them; and `github pr` does not create a branch or PR. These operations remain available in the dashboard where implemented and tested. No flag mutation or PR is performed by the CLI.

## Tests

```powershell
python -m unittest discover -s cli/tests -v
```

The CLI tests cover Python and JS/TS references, dynamic-reference labeling, ignored files, archive traversal safety, and host validation. They do not substitute for live Flagsmith or GitHub verification.
