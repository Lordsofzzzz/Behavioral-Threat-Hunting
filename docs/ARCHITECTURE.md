# Log Sentinel Architecture

## System Overview
Log Sentinel is a real-time web threat hunting pipeline built around the following stages:
1. Traffic generation and log creation
2. Log ingestion and parsing
3. Signature and behavioral detection
4. Alert persistence and observability export
5. Visualization in Grafana

## Architecture Diagram
```mermaid
flowchart LR
  U[Log Generator / Real Traffic] --> W[Demo Webapp Nginx]
  W --> V[nginx_logs volume\n/var/log/nginx/access.log]

  V --> S[Sentinel Engine\nparse + normalize + detect]
  S --> D1[Signature Detection\nSQLi/XSS/Traversal/CMDi/Scanner]
  S --> D2[Behavioral Detection\nrate spike/new endpoint/new UA]
  D1 --> E[Alert Enrichment\nscore + reasons + severity]
  D2 --> E

  E --> A[data/alerts.log\nappend-only evidence]
  S --> M[/metrics\nport 8000]

  M --> P[Prometheus]
  V --> PT[Promtail]
  PT --> L[Loki]

  P --> G[Grafana]
  L --> G
```

## Core Components

### Sentinel Engine
- File: `log-sentinel/sentinel.py`
- Responsibilities:
  - Parse Nginx-style lines (combined + fallback format)
  - Normalize and decode paths for robust matching
  - Run signature rules from `rules/*.txt`
  - Run behavioral anomaly checks per IP
  - Compute risk score and severity
  - Emit explainable alerts with reason codes
  - Suppress duplicate alerts in a configurable window
  - Expose Prometheus metrics on `:8000/metrics`

### Rule Pack
- Files: `log-sentinel/rules/*.txt`
- Attack categories:
  - SQL Injection
  - Cross-Site Scripting
  - Path Traversal
  - Command Injection
  - Scanner User-Agents

### Alert Store
- File: `log-sentinel/data/alerts.log`
- Role:
  - Durable, chronological security evidence
  - Source-of-truth for local alert history and debugging

### Container Orchestration
- File: `docker-compose.yml`
- Services:
  - `demo-webapp` (Nginx target)
  - `log-generator` (traffic simulator)
  - `sentinel` (detection engine)
  - `prometheus`, `grafana`, `loki`, `promtail` (observability stack)
- Profiles:
  - `demo`, `engine`, `core`, `observability`, `full`

### Observability Stack
- Prometheus scrapes Sentinel metrics from `http://sentinel:8000/metrics`
- Promtail forwards Nginx logs to Loki
- Grafana visualizes both metrics (Prometheus) and logs (Loki)

## Differentiators (Final-Year Unique Factors)
- Behavioral + signature hybrid detection
- Explainable alerts (human-readable reason trail)
- Open-source rule ecosystem and governance
- End-to-end containerized demo environment with monitoring

## Data Flow Summary
1. New log line arrives.
2. Sentinel tails `access.log`, parses, and normalizes request data.
3. Signature and behavioral detectors evaluate each request.
4. Alerts are scored, reasoned, deduplicated, and persisted to `data/alerts.log`.
5. Sentinel updates Prometheus counters for processed lines and categorized alerts.
6. Prometheus scrapes metrics while Promtail ships logs to Loki.
7. Grafana displays threat trends and log context for analysis.
