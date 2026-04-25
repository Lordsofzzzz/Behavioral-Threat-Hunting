# Behavioral Threat Hunting - Log Sentinel

Log Sentinel is a lightweight, real-time threat hunting engine for Nginx-style access logs. It combines pattern-based detection and behavioral checks, then exports metrics to Prometheus for Grafana dashboards.

## Features
- Detects SQL injection, XSS, path traversal, command injection, and scanner traffic
- Adds behavioral anomaly signals (rate spikes, new endpoint usage, new User-Agent)
- Scores alerts from 0-100 and maps to severity levels
- Emits explainable reason codes for each alert
- Suppresses duplicate alerts within a configurable window
- Exposes Prometheus metrics on port 8000

## Project Structure
- `.github/`: CI and contribution templates
- `apps/`
  - `demo-webapp/`: Nginx demo target application
  - `log-generator/`: traffic and attack simulation client
- `docs/`
  - `ARCHITECTURE.md`: architecture and data-flow reference
- `infra/`
  - `grafana/`: dashboards and provisioning
  - `loki/`: Loki configuration
  - `prometheus/`: Prometheus scrape configuration
  - `promtail/`: log shipping configuration
- `log-sentinel/`
  - `sentinel.py`: core detection engine and Prometheus exporter
  - `config.yaml`: runtime settings
  - `rules/`: detection patterns
  - `data/`: alert output files

## Requirements
- Docker Desktop (recommended)
- Python 3.13+ (only for host/manual run)
- Python packages for host/manual run: `pip install -r log-sentinel/requirements.txt`
- Optional package for host/manual traffic generation: `pip install -r apps/log-generator/requirements.txt`

## Setup and Running

### 1. Docker (recommended)
Run the full stack:

```bash
docker compose --profile full up -d --build
```

Useful profile variants:
- Engine only: `docker compose --profile engine up -d --build`
- Observability only: `docker compose --profile observability up -d`
- Demo traffic only: `docker compose --profile demo up -d --build`

Stop and remove containers:

```bash
docker compose down
```

### 2. Manual Sentinel Run (host)
From `log-sentinel/`:

```bash
pip install -r requirements.txt
python sentinel.py
```

Note: if running outside Docker, set `log_file` in `log-sentinel/config.yaml` to a real host path.

## Access URLs
- Demo web app: `http://localhost:8088`
- Sentinel metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (default admin/admin)
- Loki API: `http://localhost:3100`

## Open Source Readiness
- License: `LICENSE`
- Contribution guide: `CONTRIBUTING.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
- Security policy: `SECURITY.md`
- CI checks: `.github/workflows/ci.yml`

## Documentation
- Architecture overview: `docs/ARCHITECTURE.md`
