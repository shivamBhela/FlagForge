$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$base = "http://localhost:8000/api/v1"
$workerStopped = $false

try {
    docker compose stop worker | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not stop the isolated FlagForge worker container." }
    $workerStopped = $true

    $email = "e2e-qa-$([guid]::NewGuid().ToString('N'))@flagforge.io"
    $password = "QaOnly-$([guid]::NewGuid().ToString('N'))!"
    $null = Invoke-RestMethod -Method Post -Uri "$base/auth/register" -ContentType "application/json" -Body (@{
        email = $email; password = $password; full_name = "Isolated end-to-end QA"
    } | ConvertTo-Json)
    $auth = Invoke-RestMethod -Method Post -Uri "$base/auth/login" -ContentType "application/json" -Body (@{
        email = $email; password = $password
    } | ConvertTo-Json)
    $headers = @{ Authorization = "Bearer $($auth.access_token)" }

    $org = Invoke-RestMethod -Method Post -Uri "$base/organizations" -ContentType "application/json" -Headers $headers -Body (@{
        name = "FlagForge Isolated Worker and Telemetry QA"; slug = "qa-$([guid]::NewGuid().ToString('N').Substring(0, 12))"
    } | ConvertTo-Json)
    $project = Invoke-RestMethod -Method Post -Uri "$base/organizations/$($org.id)/projects" -ContentType "application/json" -Headers $headers -Body (@{
        name = "Staging Telemetry QA"; slug = "staging-qa"; description = "Isolated local acceptance test"; create_default_environments = $true
    } | ConvertTo-Json)
    $repository = Invoke-RestMethod -Method Post -Uri "$base/organizations/$($org.id)/repositories" -ContentType "application/json" -Headers $headers -Body (@{
        name = "restart-recovery"; repo_url = "https://example.invalid/restart-recovery"; language = "typescript"
    } | ConvertTo-Json)

    $job = Invoke-RestMethod -Method Post -Uri "$base/organizations/$($org.id)/jobs/repository-scan" -ContentType "application/json" -Headers $headers -Body (@{
        repository_id = $repository.id; custom_files = @{ "src/qa.ts" = "flagsmith.hasFeature('restart_recovery_flag')" }
    } | ConvertTo-Json -Depth 6)
    $pending = Invoke-RestMethod -Uri "$base/organizations/$($org.id)/jobs/$($job.id)" -Headers $headers
    if ($pending.status -ne "PENDING") { throw "Expected job to remain pending while worker is stopped." }

    docker compose up -d --no-deps worker | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not restart the isolated worker container." }
    $workerStopped = $false
    $deadline = (Get-Date).AddSeconds(25)
    do {
        Start-Sleep -Milliseconds 500
        $state = Invoke-RestMethod -Uri "$base/organizations/$($org.id)/jobs/$($job.id)" -Headers $headers
    } while (($state.status -in @("PENDING", "RUNNING")) -and (Get-Date) -lt $deadline)
    if ($state.status -ne "COMPLETED") { throw "Restart recovery did not complete (status $($state.status))." }

    $envPath = Join-Path (Get-Location) ".env"
    $envLines = [System.Collections.Generic.List[string]]::new()
    $envLines.AddRange([string[]](Get-Content -LiteralPath $envPath))
    foreach ($pair in @(
        @{ Key = "FLAGFORGE_TELEMETRY_ORGANIZATION_ID"; Value = $org.id },
        @{ Key = "FLAGFORGE_TELEMETRY_PROJECT_ID"; Value = $project.id },
        @{ Key = "FLAGFORGE_TELEMETRY_ENVIRONMENT"; Value = "staging" }
    )) {
        $found = $false
        for ($i = 0; $i -lt $envLines.Count; $i++) {
            if ($envLines[$i] -match "^$($pair.Key)=") { $envLines[$i] = "$($pair.Key)=$($pair.Value)"; $found = $true; break }
        }
        if (-not $found) { $envLines.Add("$($pair.Key)=$($pair.Value)") }
    }
    [IO.File]::WriteAllLines($envPath, $envLines, [Text.UTF8Encoding]::new($false))

    docker compose up -d --no-deps --force-recreate demo-app | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not configure the demo app for the isolated QA project." }
    Start-Sleep -Seconds 4
    for ($i = 0; $i -lt 5; $i++) {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/checkout" -SkipHttpErrorCheck -TimeoutSec 5
        if ($response.StatusCode -ne 200) { throw "Successful demo checkout returned HTTP $($response.StatusCode)." }
    }
    $failed = Invoke-WebRequest -Uri "http://localhost:8080/checkout?fail=true" -SkipHttpErrorCheck -TimeoutSec 5
    if ($failed.StatusCode -ne 500) { throw "Controlled QA failure endpoint returned HTTP $($failed.StatusCode), expected 500." }
    for ($i = 0; $i -lt 70; $i++) {
        $null = Invoke-WebRequest -Uri "http://localhost:8080/checkout?user_id=qa-$i" -SkipHttpErrorCheck -TimeoutSec 5
    }

    Start-Sleep -Seconds 3
    $metrics = Invoke-RestMethod -Uri "$base/organizations/$($org.id)/telemetry/metrics?flag_key=checkout_v2_redesign&environment_name=staging" -Headers $headers
    if ($metrics.total_requests -lt 50 -or $metrics.error_count -lt 1 -or -not $metrics.has_latency_histogram) {
        throw "OTLP data was not fully persisted. Requests=$($metrics.total_requests), errors=$($metrics.error_count)."
    }
    $risk = Invoke-RestMethod -Method Post -Uri "$base/organizations/$($org.id)/guardian/evaluate?flag_key=checkout_v2_redesign&environment_name=staging" -Headers $headers
    if ($risk.factors.telemetry_confidence -ne "SUFFICIENT") { throw "Risk Engine did not consume sufficient real QA telemetry." }
    Write-Output "WORKER_RESTART_RECOVERY=PASSED status=$($state.status) attempts=$($state.attempts) references=$($state.result.references_found)"
    Write-Output "OTLP_END_TO_END=PASSED requests=$($metrics.total_requests) successful=$($metrics.successful_requests) errors=$($metrics.error_count) error_rate=$($metrics.avg_error_rate) p95_ms=$($metrics.avg_p95_ms)"
    Write-Output "RISK_WITH_LIVE_OTEL=PASSED confidence=$($risk.factors.telemetry_confidence) band=$($risk.risk_band) score=$($risk.calculated_score)"
    Write-Output "QA_SCOPE=Isolated organization/project; Staging telemetry only; no Flagsmith flag mutation."
}
finally {
    if ($workerStopped) { docker compose up -d --no-deps worker | Out-Null }
}
