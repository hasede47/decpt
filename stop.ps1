$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$DeceptrRoot = Join-Path $Root "deceptr"
$TpotRoot = Join-Path $Root "tpot-runtime"

Push-Location $TpotRoot
cmd.exe /c "docker compose stop deceptr-tpot-forwarder cowrie"
Pop-Location

Push-Location $DeceptrRoot
cmd.exe /c "docker compose -f docker-compose.yml -f docker-compose.tpot.yml stop"
Pop-Location

Write-Host "[OK] Stopped final DECEPTR architecture. Data volumes kept."
