$ErrorActionPreference = "Stop"

$baseUrl = "http://localhost:8000/api/v1"
$nonce = [guid]::NewGuid().ToString("N")
$email = "worker-qa-$nonce@flagforge.io"
$password = $nonce + "Aa1!"
$headers = $null
$workerRestartRequested = $false

function Invoke-FlagForgePost($url, $body, $requestHeaders = @{}) {
    Invoke-RestMethod -Method Post -Uri $url -ContentType "application/json" `
        -Headers $requestHeaders -Body ($body | ConvertTo-Json -Depth 8)
}

try {
    $null = Invoke-FlagForgePost "$baseUrl/auth/register" @{
        email = $email
        password = $password
        full_name = "Worker Recovery QA"
    }
    $login = Invoke-FlagForgePost "$baseUrl/auth/login" @{
        email = $email
        password = $password
    }
    $headers = @{ Authorization = "Bearer $($login.access_token)" }
    $organization = Invoke-FlagForgePost "$baseUrl/organizations" @{
        name = "Worker Recovery QA $nonce"
        slug = "worker-qa-$nonce"
    } $headers
    $repository = Invoke-FlagForgePost "$baseUrl/organizations/$($organization.id)/repositories" @{
        name = "worker-recovery-qa"
        repo_url = "https://example.invalid/worker-recovery-qa"
        language = "typescript"
    } $headers

    docker compose stop worker | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not pause the worker for the isolated QA job." }
    $workerRestartRequested = $true

    $job = Invoke-FlagForgePost "$baseUrl/organizations/$($organization.id)/jobs/repository-scan" @{
        repository_id = $repository.id
        custom_files = @{ "src/flag.ts" = 'if (flagsmith.hasFeature("qa_flag")) { return true; }' }
    } $headers
    if ($job.status -ne "PENDING") { throw "Job was not durably queued while the worker was stopped." }

    docker compose start worker | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not restart the worker for recovery verification." }
    $state = $job
    for ($attempt = 0; $attempt -lt 30 -and $state.status -notin @("COMPLETED", "FAILED"); $attempt++) {
        Start-Sleep -Seconds 2
        $state = Invoke-RestMethod -Method Get `
            -Uri "$baseUrl/organizations/$($organization.id)/jobs/$($job.id)" -Headers $headers
    }
    if ($state.status -ne "COMPLETED") { throw "The queued isolated repository scan did not complete after worker restart." }

    docker compose stop --timeout 15 worker | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Graceful worker stop command failed." }
    $workerLog = docker compose logs --tail 40 worker
    $heartbeatExists = docker compose exec -T redis redis-cli EXISTS flagforge:worker:heartbeat
    if (($workerLog -join "") -notmatch "Worker stopped cleanly" -or (($heartbeatExists -join "").Trim() -ne "0")) {
        throw "Graceful shutdown did not log cleanly and remove its Redis heartbeat."
    }

    docker compose start worker | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Worker did not restart after graceful-shutdown verification." }
    $health = "starting"
    for ($attempt = 0; $attempt -lt 20 -and $health -ne "healthy"; $attempt++) {
        Start-Sleep -Seconds 2
        $health = docker inspect -f "{{.State.Health.Status}}" flagforge-worker-1
    }
    if ($health -ne "healthy") { throw "Worker health did not recover after restart." }

    "queued_status=$($job.status) recovered_status=$($state.status) attempts=$($state.attempts) graceful_stop=verified heartbeat_removed=verified restart_health=$health"
}
finally {
    if ($workerRestartRequested) {
        $workerStatus = docker inspect -f "{{.State.Status}}" flagforge-worker-1 2>$null
        if ($workerStatus -and $workerStatus -ne "running") {
            docker compose start worker | Out-Null
        }
    }
}
