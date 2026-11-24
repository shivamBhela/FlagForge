# FlagForge Setup & Health Verification Script for Windows PowerShell
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " FlagForge Setup & Health Verification" -ForegroundColor Cyan
Write-Host "============================================================"

# Pre-flight check
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH."
    exit 1
}

if (-not (Test-Path .env)) {
    Write-Host "📋 Copying .env.example to .env..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

Write-Host "🚀 Starting FlagForge multi-service stack with Docker Compose..." -ForegroundColor Green
docker compose up -d --build

Write-Host "⏳ Polling FlagForge API health at http://localhost:8000/health..." -ForegroundColor Yellow
$maxRetries = 30
$count = 0
$healthy = $false

while ($count -lt $maxRetries) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.status -eq "healthy") {
            $healthy = $true
            break
        }
    } catch {
        # Retry
    }
    $count++
    Write-Host "Waiting for API... ($count/$maxRetries)"
    Start-Sleep -Seconds 2
}

if ($healthy) {
    Write-Host "✅ FlagForge API is healthy and operational!" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " FlagForge Stack Running Successfully" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Web UI:         http://localhost:3000" -ForegroundColor White
    Write-Host "  API Docs:       http://localhost:8000/api/v1/docs" -ForegroundColor White
    Write-Host "  API Health:     http://localhost:8000/health" -ForegroundColor White
    Write-Host "  OTel Collector: http://localhost:4318" -ForegroundColor White
    Write-Host "============================================================" -ForegroundColor Cyan
} else {
    Write-Warning "Health check timed out. Check 'docker compose logs api'."
}
