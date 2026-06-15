# Run as Administrator on the DECEPTR analysis host.
# Replace the placeholder IPs before executing.

param(
  [Parameter(Mandatory = $true)]
  [string]$TpotSensorIp,

  [Parameter(Mandatory = $true)]
  [string]$SocAdminIp
)

$ErrorActionPreference = "Stop"

New-NetFirewallRule -DisplayName "DECEPTR Logstash TLS from T-Pot" `
  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5044 `
  -RemoteAddress $TpotSensorIp

New-NetFirewallRule -DisplayName "DECEPTR API from SOC" `
  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 `
  -RemoteAddress $SocAdminIp

New-NetFirewallRule -DisplayName "DECEPTR Kibana from SOC" `
  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5601 `
  -RemoteAddress $SocAdminIp

New-NetFirewallRule -DisplayName "DECEPTR Elasticsearch from SOC" `
  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 9200 `
  -RemoteAddress $SocAdminIp

Write-Host "DECEPTR firewall allow rules created."

