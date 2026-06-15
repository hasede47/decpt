$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$DeceptrRoot = Join-Path $Root "deceptr"
$TpotRoot = Join-Path $Root "tpot-runtime"

function Run {
  param([string]$Command, [string]$Cwd)
  Write-Host "[RUN] $Command"
  Push-Location $Cwd
  try {
    cmd.exe /c $Command
    if ($LASTEXITCODE -ne 0) {
      throw "Command failed with exit code $LASTEXITCODE`: $Command"
    }
  } finally {
    Pop-Location
  }
}

docker version *> $null
if ($LASTEXITCODE -ne 0) {
  throw "Docker Desktop is not ready."
}

New-Item -ItemType Directory -Force -Path (Join-Path $TpotRoot "deceptr\filebeat") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $TpotRoot "deceptr\certs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $TpotRoot "data\nginx\conf") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $TpotRoot "data\nginx\cert") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $TpotRoot "data\cowrie\log") | Out-Null
Copy-Item -Force (Join-Path $DeceptrRoot "tpot\filebeat\tpot-cowrie-to-deceptr.yml") (Join-Path $TpotRoot "deceptr\filebeat\tpot-cowrie-to-deceptr.yml")
Copy-Item -Force (Join-Path $DeceptrRoot "elk\certs\ca.crt") (Join-Path $TpotRoot "deceptr\certs\ca.crt")

Run "docker compose -f docker-compose.yml -f docker-compose.tpot.yml up -d --build" $DeceptrRoot
Run "docker compose up -d cowrie deceptr-tpot-forwarder" $TpotRoot

Write-Host ""
Write-Host "[OK] DECEPTR final architecture is running."
Write-Host "Dashboard : http://127.0.0.1:8088/index.html?v=3"
Write-Host "Kibana    : http://127.0.0.1:5601"
Write-Host "API Docs  : http://127.0.0.1:8000/docs"
