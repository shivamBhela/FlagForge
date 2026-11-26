$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)

$longRunning = @(
    "web", "api", "worker", "postgres", "redis", "otel-collector", "demo-app",
    "flagsmith-postgres", "flagsmith", "flagsmith-task-processor"
)
$oneShot = @("migrate", "flagsmith-migrate-db")
$maxAttempts = 60
$ready = $false

for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    $allReady = $true
    foreach ($service in $longRunning) {
        $id = docker compose ps --all --quiet $service
        if (-not $id) { $allReady = $false; break }
        $parts = (docker inspect --format '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}|{{.State.ExitCode}}' $id) -split '\|'
        if ($parts[0] -ne "running" -or ($parts[1] -ne "none" -and $parts[1] -ne "healthy")) {
            $allReady = $false
            break
        }
    }

    if ($allReady) {
        foreach ($service in $oneShot) {
            $id = docker compose ps --all --quiet $service
            if (-not $id) { $allReady = $false; break }
            $parts = (docker inspect --format '{{.State.Status}}|{{.State.ExitCode}}' $id) -split '\|'
            if ($parts[0] -ne "exited" -or $parts[1] -ne "0") { $allReady = $false; break }
        }
    }

    if ($allReady) {
        try {
            $api = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthz" -TimeoutSec 4
            $null = Invoke-WebRequest -Uri "http://localhost:3000/" -UseBasicParsing -TimeoutSec 4
            $null = Invoke-WebRequest -Uri "http://localhost:8081/health/liveness/" -UseBasicParsing -TimeoutSec 4
            $null = Invoke-WebRequest -Uri "http://localhost:13133/" -UseBasicParsing -TimeoutSec 4
            $null = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 4
            if ($api.status -eq "healthy") { $ready = $true; break }
        } catch {
            $allReady = $false
        }
    }

    if ($attempt -lt $maxAttempts) { Start-Sleep -Seconds 5 }
}

docker compose ps --all
foreach ($service in $longRunning + $oneShot) {
    $id = docker compose ps --all --quiet $service
    if ($id) {
        $detail = if ($service -in $oneShot) {
            docker inspect --format '{{.State.Status}} exit={{.State.ExitCode}}' $id
        } else {
            docker inspect --format '{{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}not-configured{{end}}' $id
        }
        Write-Host "$service : $detail"
    } else {
        Write-Host "$service : MISSING"
    }
}

if (-not $ready) { exit 1 }
Write-Host "HTTP checks passed: FlagForge API, web UI, demo app, Flagsmith liveness, and OTel health endpoint."
exit 0
