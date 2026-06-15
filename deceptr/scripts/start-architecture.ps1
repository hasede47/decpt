$ErrorActionPreference = "Stop"
$FinalRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
& (Join-Path $FinalRoot "start.ps1")
