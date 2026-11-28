# FlagForge feature-flag scanner sample

This small source-only example gives the local scanner reproducible evidence in both TypeScript and Python. It contains no credentials and has no install or execution requirements.

From the FlagForge repository root, run:

```powershell
python cli/flagforge_cli.py scan examples/flagforge-feature-flag-sample
python cli/flagforge_cli.py dependencies
```

Expected references include `checkout_v2_redesign` and `instant_refunds`, plus one dynamic reference reported without guessing a key. The scanner reads source files and does not execute this example.
