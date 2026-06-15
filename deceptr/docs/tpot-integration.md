# DECEPTR + Official T-Pot Integration

This repository does not embed the official T-Pot stack inside the DECEPTR
Compose file. T-Pot is a full honeypot distribution/stack and should run on a
dedicated Linux VM or server in the DMZ.

## Target Logical Architecture

```text
Internet / attackers
        |
        v
Firewall NAT / DMZ
        |
        v
Official T-Pot sensor
  - Cowrie SSH/Telnet
  - Suricata and other T-Pot sensors
  - Cowrie log: /data/cowrie/log/cowrie.json
        |
        | Filebeat TLS 1.3, TCP/5044
        v
DECEPTR analysis server
  - Logstash TLS input
  - Redis queue
  - Python pipeline
  - Elasticsearch / MySQL / MinIO
  - FastAPI / Dashboard / Kibana / ElastAlert
```

## Install Official T-Pot

Run on a clean Linux VM/server:

```bash
cd /opt
git clone https://github.com/telekom-security/tpotce
cd tpotce
./install.sh
```

The helper script `tpot/scripts/install-official-tpot.sh` performs the same
clone-and-run flow. Use a clean VM because the T-Pot installer can change host
services, ports and Docker configuration.

## Local Windows/WSL Lab Install

For the local lab machine, T-Pot was installed with WSL + Docker Desktop in:

```text
D:\assir\Ismagi\PFA\tpotce-wsl
```

Because Docker Desktop did not expose the new `Ubuntu-24.04` WSL integration
socket, the official T-Pot repository was prepared from WSL and then copied to
the Windows filesystem. This follows the official Windows mode:

```text
compose/mac_win.yml -> docker-compose.yml
TPOT_OSTYPE=win
```

The local override is:

```text
D:\assir\Ismagi\PFA\tpotce-wsl\docker-compose.deceptr-local.yml
```

It does two things:
- remaps T-Pot `elasticpot` from host `9200` to `19200`, because DECEPTR uses `9200`
- remaps T-Pot `redishoneypot` from host `6379` to `16379`, because DECEPTR uses `6379`
- adds `deceptr-tpot-forwarder`, which sends official T-Pot Cowrie logs to DECEPTR Logstash over TLS

Start the validated local Cowrie path:

```powershell
cd D:\assir\Ismagi\PFA\tpotce-wsl
docker compose -f docker-compose.yml -f docker-compose.deceptr-local.yml up -d tpotinit cowrie deceptr-tpot-forwarder
```

Check it:

```powershell
docker compose -f docker-compose.yml -f docker-compose.deceptr-local.yml ps
docker exec deceptr-tpot-forwarder filebeat test output -c /usr/share/filebeat/filebeat.yml -e --strict.perms=false
```

The validated flow is:

```text
official T-Pot Cowrie -> deceptr-tpot-forwarder -> TLS 1.3 -> DECEPTR Logstash -> Redis -> Pipeline -> Elasticsearch
```

## Forward Cowrie From T-Pot To DECEPTR

On the T-Pot host:

```bash
mkdir -p /opt/deceptr-tpot
cp -r tpot/* /opt/deceptr-tpot/
mkdir -p /opt/deceptr-tpot/certs
```

Copy this file from the DECEPTR server to the T-Pot host:

```text
elk/certs/ca.crt -> /opt/deceptr-tpot/certs/ca.crt
```

Edit `/opt/deceptr-tpot/.env`:

```env
DECEPTR_LOGSTASH_HOST=<DECEPTR_IP>
DECEPTR_LOGSTASH_PORT=5044
TPOT_COWRIE_LOG_PATH=/data/cowrie/log
```

Start the forwarder:

```bash
cd /opt/deceptr-tpot
./scripts/start-deceptr-forwarder.sh
```

## DECEPTR Production/T-Pot Mode

When the real T-Pot sensor is used, start DECEPTR without the local Cowrie
container:

```bash
docker compose -f docker-compose.yml -f docker-compose.tpot.yml up -d
```

To start the local Cowrie again for lab testing:

```bash
docker compose -f docker-compose.yml -f docker-compose.tpot.yml --profile local-cowrie up -d
```

## Firewall Rules

Allow:

```text
T-Pot sensor IP -> DECEPTR TCP/5044
SOC/Admin IP    -> DECEPTR TCP/8000, TCP/5601, TCP/9200
Internet        -> T-Pot honeypot ports only
```

Templates:

```text
config/firewall/windows-deceptr-rules.ps1
config/firewall/ufw-deceptr-rules.sh
```
