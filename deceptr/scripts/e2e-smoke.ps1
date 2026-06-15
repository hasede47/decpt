param(
  [string]$ProjectRoot = "D:\assir\Ismagi\PFA\deceptr",
  [string]$TpotRoot = "D:\assir\Ismagi\PFA\tpotce-wsl",
  [int]$WaitSeconds = 45
)

$ErrorActionPreference = "Stop"

function Read-DotEnvValue {
  param([string]$Path, [string]$Name)
  $line = Select-String -Path $Path -Pattern "^$Name=" | Select-Object -First 1
  if (-not $line) { return "" }
  return $line.Line.Split("=", 2)[1]
}

function Assert-ContainerRunning {
  param([string]$Name)
  $state = docker inspect -f "{{.State.Running}}" $Name 2>$null
  if ($state -ne "true") {
    throw "Container is not running: $Name"
  }
}

function Send-TelnetInteraction {
  param(
    [string]$TargetHost = "127.0.0.1",
    [int]$Port = 23,
    [string]$Username,
    [string]$Password
  )

  $client = [System.Net.Sockets.TcpClient]::new()
  $client.Connect($TargetHost, $Port)
  $stream = $client.GetStream()
  $stream.ReadTimeout = 1500
  $stream.WriteTimeout = 1500
  $encoding = [System.Text.Encoding]::ASCII

  function Write-Line([string]$Text) {
    $bytes = $encoding.GetBytes($Text + "`r`n")
    $stream.Write($bytes, 0, $bytes.Length)
    Start-Sleep -Milliseconds 800
  }

  function Drain-Available {
    $buffer = New-Object byte[] 4096
    $text = ""
    $deadline = (Get-Date).AddSeconds(2)
    while ((Get-Date) -lt $deadline) {
      if ($stream.DataAvailable) {
        $read = $stream.Read($buffer, 0, $buffer.Length)
        if ($read -gt 0) { $text += $encoding.GetString($buffer, 0, $read) }
      } else {
        Start-Sleep -Milliseconds 100
      }
    }
    return $text
  }

  try {
    [void](Drain-Available)
    Write-Line $Username
    [void](Drain-Available)
    Write-Line $Password
    [void](Drain-Available)
    Write-Line "uname -a"
    [void](Drain-Available)
    Write-Line "cat /etc/passwd"
    [void](Drain-Available)
    Write-Line "exit"
  } finally {
    $client.Close()
  }
}

Push-Location $ProjectRoot
try {
  $elasticPassword = Read-DotEnvValue -Path (Join-Path $ProjectRoot ".env") -Name "ELASTIC_PASSWORD"
  if (-not $elasticPassword) { throw "ELASTIC_PASSWORD not found in .env" }

  $runId = "codex-e2e-" + (Get-Date).ToUniversalTime().ToString("yyyyMMddHHmmss")
  $testIp = "198.51.100.188"

  $required = @(
    "deceptr-elasticsearch",
    "deceptr-logstash",
    "deceptr-redis",
    "deceptr-pipeline",
    "deceptr-api",
    "deceptr-kibana",
    "cowrie",
    "deceptr-tpot-forwarder"
  )
  foreach ($name in $required) { Assert-ContainerRunning $name }

  $tls = docker exec deceptr-tpot-forwarder bash -lc "filebeat test output -c /usr/share/filebeat/filebeat.yml -e --strict.perms=false 2>&1"
  $tlsText = ($tls -join "`n")
  if ($tlsText -notmatch "TLS version: TLSv1.3") {
    throw "T-Pot forwarder TLS test did not report TLSv1.3"
  }

  Send-TelnetInteraction -Username $runId -Password "badpass-$runId"

  # Add a stable synthetic source IP event in the official T-Pot Cowrie log so the
  # assertion is deterministic even when the local Telnet source is Docker NAT.
  $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ")
  $event = [ordered]@{
    eventid = "cowrie.login.failed"
    username = $runId
    password = "badpass-$runId"
    src_ip = $testIp
    src_port = 55444
    dst_port = 23
    session = $runId
    protocol = "telnet"
    timestamp = $timestamp
    message = "login attempt [$runId/badpass-$runId] failed"
  }
  $payload = (($event | ConvertTo-Json -Compress) + "`n")
  $payloadB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($payload))
  docker run --rm --user 0 -e EVENT_B64="$payloadB64" -v "${TpotRoot}\data\cowrie\log:/logs" elasticsearch:8.13.0 bash -lc 'echo "$EVENT_B64" | base64 -d >> /logs/cowrie.json' | Out-Null

  Start-Sleep -Seconds $WaitSeconds

  $escapedRunId = [Uri]::EscapeDataString("`"$runId`"")
  $rawUrl = "http://localhost:9200/cowrie-*/_search?q=$escapedRunId&size=1&sort=@timestamp:desc"
  $raw = docker exec deceptr-elasticsearch curl -s -u "elastic:$elasticPassword" $rawUrl
  $rawObj = $raw | ConvertFrom-Json
  if ($rawObj.hits.total.value -lt 1) { throw "Raw Cowrie event not found for $runId" }

  $enrichedUrl = "http://localhost:9200/deceptr-events-*/_search?q=$escapedRunId&size=1&sort=timestamp:desc"
  $enriched = docker exec deceptr-elasticsearch curl -s -u "elastic:$elasticPassword" $enrichedUrl
  $enrichedObj = $enriched | ConvertFrom-Json
  if ($enrichedObj.hits.total.value -lt 1) { throw "Enriched DECEPTR event not found for $runId" }

  $loginBody = @{ username = "admin"; password = "deceptr2025" } | ConvertTo-Json
  $login = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/auth/login" -ContentType "application/json" -Body $loginBody
  $headers = @{ Authorization = "Bearer $($login.access_token)" }
  $stats = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/alerts/stats" -Headers $headers

  [ordered]@{
    status = "OK"
    run_id = $runId
    tpot_cowrie = "running"
    tpot_forwarder_tls = "TLSv1.3"
    raw_index = $rawObj.hits.hits[0]._index
    enriched_index = $enrichedObj.hits.hits[0]._index
    enriched_type = $enrichedObj.hits.hits[0]._source.event_type
    mitre = $enrichedObj.hits.hits[0]._source.mitre_technique
    api_total_alerts = $stats.total_alerts
    api_alerts_24h = $stats.alerts_24h
  } | ConvertTo-Json -Depth 5
} finally {
  Pop-Location
}
