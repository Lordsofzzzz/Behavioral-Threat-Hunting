# Behavioral Threat Hunting - Log Sentinel

Log Sentinel is a lightweight, real-time log monitor for Nginx-style access logs. It detects common web attacks using pattern rules, rate limiting, and 404 spam heuristics, exporting metrics directly to Prometheus for visualization in Grafana.

## Features
- Detects SQL injection, XSS, path traversal, and command injection
- Flags known scanner User-Agents
- Rate limit and 404 spam detection per IP
- Console alerts and file-based alert logging
- **Prometheus Metrics:** Native exporter for real-time monitoring
- **Grafana Dashboard:** Pre-configured security overview dashboard
- Dynamic risk scoring (0-100) with score-based severity
- Behavioral anomaly detection (new endpoint, new user-agent, request spike)
- Explainable alerts with machine-readable reason codes

## Release Highlights (Apr 2026)
- **Architecture Optimization:** Consolidated the stack by removing redundant portal services and legacy dashboard servers.
- **Docker Automation:** Implemented Docker healthchecks and service dependencies to ensure a reliable startup sequence.
- **Prometheus Integration:** Fully transitioned to Prometheus/Grafana as the primary observability stack.
- **Strict Configuration:** Unified configuration management via `config.yaml` for all environments.
- **Robustness:** Added "wait-for-file" logic in the core engine to handle container synchronization gracefully.

## Project Structure
- .github/: CI and contribution templates
- docs/: architecture and demo docs
- log-sentinel/
  - sentinel.py: Log monitor and detection engine (Prometheus exporter on port 8000)
  - config.yaml: Unified runtime settings
  - rules/: Pattern files for detection
  - data/: Alert logs and persistent data
- apps/
  - demo-webapp/: Target Nginx application
  - log-generator/: Traffic and attack simulator
- infra/
  - grafana/: Dashboards and provisioning
  - prometheus/: Scrape configurations

## Requirements
- Python 3.13+ (core engine)
- Docker Desktop (recommended for full integrated stack)
- Python dependencies: `PyYAML`, `prometheus_client`

## Setup & Running

### 1. Manual Execution (Host)
From the `log-sentinel` directory:
```bash
pip install -r requirements.txt
python sentinel.py
```
*Note: Ensure the `log_file` path in `config.yaml` exists on your host.*

### 2. Docker Execution (Recommended)
Launch the entire optimized stack with a single command:
```bash
docker compose --profile full up -d
```

Docker automatically orchestrates the sequence:
1. Starts the **Target Webapp**.
2. Waits for the Webapp to be **Healthy** (confirming logs are active).
3. Starts the **Sentinel**, **Traffic Generator**, **Prometheus**, and **Grafana**.

## Accessing the Stack
- **Target Webapp:** `http://localhost:8088`
- **Security Dashboard (Grafana):** `http://localhost:3000` (User: `admin`, Pass: `admin`)
- **Prometheus Metrics:** `http://localhost:9090`
- **Sentinel Metrics (Raw):** `http://localhost:8000/metrics`

## Open Source Readiness
- License: MIT (`LICENSE`)
- Contribution guide: `CONTRIBUTING.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
- Security policy: `SECURITY.md`
- CI checks: `.github/workflows/ci.yml`

## Presentation Docs
- Architecture overview: `docs/ARCHITECTURE.md`
- 2-minute demo flow: `docs/DEMO_SCRIPT.md`
