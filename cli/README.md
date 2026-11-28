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
flagforge diff SOURCE TARGET [--no-input]
flagforge sync --dry-run
flagforge risk assess --flag KEY [--environment NAME]
flagforge cleanup preview
flagforge monitor
flagforge report [--path PATH] [--format json|markdown]
flagforge github pr
```

`flags list`, `flags inspect`, environment comparison, and provider reads are delegated to the official CLI. `diff SOURCE TARGET` compares enabled/value state read from each Flagsmith environment; if `FLAGSMITH_SOURCE_ENVIRONMENT_KEY` and `FLAGSMITH_TARGET_ENVIRONMENT_KEY` are absent, the CLI prompts for each key with input hidden. Add `--no-input` for automation to fail cleanly instead of prompting. Keys are passed to the official CLI through its documented `FLAGSMITH_ENVIRONMENT` variable and are not written to config or output. The comparison is read-only and reports source-only, target-only, and changed flags; it does not synchronize or mutate provider state. `scan` uses Python AST call patterns and comment-stripped, line-based JavaScript/TypeScript patterns; JS/TS literal matches are medium confidence, and dynamic references are surfaced without a guessed key. The scanner excludes common generated/dependency directories, symlinks, `.env` files and large files. GitHub archive scanning accepts only `github.com` URLs, downloads a size-limited ZIP archive to memory, extracts regular files into a temporary directory with path traversal checks, and never executes repository code. An optional `GITHUB_TOKEN` is consumed only from the process environment for private repository access.

Commands whose safe full behavior needs additional provider or authenticated application context are explicit about their limits: `sync` is dry-run only; `risk` needs `FLAGFORGE_ACCESS_TOKEN` and `FLAGFORGE_ORGANIZATION_ID`; `cleanup preview` reports no candidates unless provider comparison proves them; and `github pr` does not create a branch or PR. These operations remain available in the dashboard where implemented and tested. No flag mutation or PR is performed by the CLI.

## Tests

```powershell
python -m unittest discover -s cli/tests -v
```

The CLI tests cover Python and JS/TS references, dynamic-reference labeling, comment exclusion, ignored files, archive traversal safety, the GitHub ZIP endpoint and host validation, and environment-diff classification/key redaction. A public GitHub archive scan was verified separately; private-repository authorization and live Flagsmith management reads remain unverified in this pass.
