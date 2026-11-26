$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function New-HexSecret([int]$ByteCount = 32) {
    $bytes = New-Object byte[] $ByteCount
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return (($bytes | ForEach-Object { $_.ToString("x2") }) -join "")
}

function New-FernetKey {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToBase64String($bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_") + "="
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI is not installed or is not on PATH. Install Docker Desktop from https://docs.docker.com/desktop/setup/install/windows-install/."
}
docker info --format "Docker Engine {{.ServerVersion}} ({{.OSType}})" | Write-Host
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is unavailable. Start Docker Desktop and wait until 'docker info' reports a Server section."
}

if (-not (Test-Path -LiteralPath ".env")) {
    $postgresPassword = New-HexSecret 24
    $flagsmithPostgresPassword = New-HexSecret 24
    $settings = [ordered]@{
        APP_ENV = "development"
        APP_NAME = "FlagForge API"
        APP_SECRET_KEY = New-HexSecret 32
        ENCRYPTION_KEY = New-FernetKey
        API_PORT = "8000"
        WEB_PORT = "3000"
        DEMO_APP_PORT = "8080"
        WEB_BASE_URL = "http://localhost:3000"
        API_BASE_URL = "http://localhost:8000"
        DATABASE_URL = "postgresql+asyncpg://flagforge:$postgresPassword@postgres:5432/flagforge"
        POSTGRES_DB = "flagforge"
        POSTGRES_USER = "flagforge"
        POSTGRES_PASSWORD = $postgresPassword
        POSTGRES_PORT = "5433"
        REDIS_URL = "redis://redis:6379/0"
        REDIS_PORT = "6380"
        FLAGSMITH_BASE_URL = "http://flagsmith:8000/api/v1"
        FLAGSMITH_ALLOWED_HOSTS = '["flagsmith"]'
        FLAGSMITH_PORT = "8081"
        FLAGSMITH_DOMAIN = "localhost:8081"
        FLAGSMITH_IMAGE = "docker.flagsmith.com/flagsmith/flagsmith:2.295.2@sha256:48905c664152d8ae2c843ec9cee72ff197e7caff6e91b959bb851a235915ea35"
        FLAGSMITH_POSTGRES_PASSWORD = $flagsmithPostgresPassword
        FLAGSMITH_DJANGO_SECRET_KEY = New-HexSecret 48
        FLAGSMITH_WAREHOUSE_CREDENTIALS_SECRET = New-HexSecret 48
        FLAGSMITH_ENVIRONMENT_KEY = ""
        GITHUB_APP_ID = ""
        GITHUB_APP_PRIVATE_KEY = ""
        GITHUB_WEBHOOK_SECRET = ""
        OTEL_EXPORTER_OTLP_ENDPOINT = "http://otel-collector:4318"
        OTEL_INGEST_TOKEN = New-HexSecret 32
        FLAGFORGE_TELEMETRY_ORGANIZATION_ID = ""
        FLAGFORGE_TELEMETRY_PROJECT_ID = ""
        FLAGFORGE_TELEMETRY_ENVIRONMENT = "staging"
        LLM_PROVIDER = ""
        LLM_API_KEY = ""
        LLM_MODEL = ""
        AUTO_ROLLBACK_DEFAULT = "false"
        MAX_ROLLBACK_ATTEMPTS = "2"
        ROLLBACK_COOLDOWN_SECONDS = "600"
    }
    $lines = foreach ($entry in $settings.GetEnumerator()) { "$($entry.Key)=$($entry.Value)" }
    [IO.File]::WriteAllLines((Join-Path $PSScriptRoot ".env"), [string[]]$lines, [Text.UTF8Encoding]::new($false))
    Write-Host "Created .env with generated local-only secrets. The file is gitignored."
} else {
    Write-Host "Using existing .env and preserving its configured values."
    $existingEnv = Get-Content -LiteralPath ".env"
    if (-not ($existingEnv | Where-Object { $_ -match '^OTEL_INGEST_TOKEN=' })) {
        Add-Content -LiteralPath ".env" -Value "OTEL_INGEST_TOKEN=$(New-HexSecret 32)"
        Write-Host "Added a generated local-only OTLP ingestion credential to the ignored .env file."
    }
}

$configuredEnv = @{}
foreach ($line in (Get-Content -LiteralPath ".env")) {
    if ($line -match '^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$') {
        $configuredEnv[$matches[1]] = $matches[2].Trim('"')
    }
}
function Get-ConfiguredPort([string]$Name, [int]$Default) {
    $value = $configuredEnv[$Name]
    if ($value -match '^\d+$') { return [int]$value }
    return $Default
}

$ports = @(
    (Get-ConfiguredPort "WEB_PORT" 3000),
    (Get-ConfiguredPort "API_PORT" 8000),
    (Get-ConfiguredPort "DEMO_APP_PORT" 8080),
    (Get-ConfiguredPort "FLAGSMITH_PORT" 8081),
    (Get-ConfiguredPort "POSTGRES_PORT" 5433),
    (Get-ConfiguredPort "REDIS_PORT" 6380),
    13133, 4317, 4318, 8889
)
$listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $ports -contains $_.LocalPort } |
    Select-Object -ExpandProperty LocalPort -Unique
if ($listeners) {
    throw "Required FlagForge host ports are already in use: $($listeners -join ', '). Existing listeners were left untouched. Change the corresponding port values in .env and rerun setup.ps1."
}

docker compose config --quiet
if ($LASTEXITCODE -ne 0) { throw "Docker Compose configuration is invalid. Review .env and docker-compose.yml." }

docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw "Docker Compose startup failed. Inspect 'docker compose ps -a' and service logs; existing data was not removed." }

& (Join-Path $PSScriptRoot "scripts\health-check.ps1")
if ($LASTEXITCODE -ne 0) { throw "The stack started but did not pass all health checks. See the service evidence printed above." }

Write-Host "Flagsmith: http://localhost:8081"
Write-Host "FlagForge: http://localhost:3000"
Write-Host "FlagForge API docs: http://localhost:8000/api/v1/docs"
Write-Host "Demo application: http://localhost:8080"
