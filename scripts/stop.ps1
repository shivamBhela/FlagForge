$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
docker compose stop
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "FlagForge and its included Flagsmith services are stopped. Named volumes and existing unrelated Docker projects were left untouched."
