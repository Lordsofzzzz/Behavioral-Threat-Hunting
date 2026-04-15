# Log Sentinel Architecture

## System Overview
Log Sentinel is a real-time web threat hunting pipeline with four major stages:
1. Log ingestion and parsing
2. Signature and behavioral detection
3. Alert persistence and API serving
4. Visual analytics and incident correlation

## Architecture Diagram
```mermaid
flowchart LR
  T[Demo Simulator / Real Traffic] --> A[Access Log Source\nNginx-style log lines]
  A --> B[Sentinel Engine\nparsing + normalization]
  B --> C[Signature Detection\nSQLi/XSS/Traversal/CMDi/Scanner]
  B --> D[Behavioral Detection\nbaseline + anomalies]
  C --> E[Alert Enrichment\nscore + reasons + severity]
  D --> E
  E --> F[data/alerts.log\nappend-only evidence]

  F --> G[Dashboard API Server\nthreaded parse + cache + incidents]
  G --> H[/api/alerts]
  G --> I[/api/stats]
  G --> J[/api/incidents]
  G --> K[/api/prometheus/query-range]
  G --> L[/api/grafana/embed-preview]

  subgraph Portal Workflow
    M[Portal API\nFastAPI + Postgres + Redis]
    N[Portal UI\nNext.js analyst workspace]
  end

  H --> M
  I --> M
  J --> M
  K --> M
  L --> M
  M --> N

  subgraph Observability Workflow
    O[Prometheus]
    P[Grafana]
  end

  G --> O
  O --> P
  P --> N
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
  - Source-of-truth for dashboard API

### Dashboard API
- File: `log-sentinel/Dashboard-server.py`
- Endpoints:
  - `/api/alerts` recent enriched alerts
  - `/api/stats` aggregate counts, score metrics, anomaly totals
  - `/api/incidents` correlated incident groups by IP and time window
  - `/api/prometheus/metrics` discover Prometheus metric names for custom charting
  - `/api/prometheus/query-range` query time-series by metric + dimension + range + step
  - `/api/grafana/embed-preview` build safe Grafana embed URLs for dashboard/panel previews

### Dashboard UI
- File: `log-sentinel/dashboard.html`
- Views:
  - Live feed
  - Type breakdown
  - Top attacking IPs
  - Timeline
  - Correlated incidents

### Evaluation Harness
- Folder: `log-sentinel/evaluation/`
- Purpose:
  - Reproducible benchmark dataset
  - Precision/recall/F1 and performance metrics

## Differentiators (Final-Year Unique Factors)
- Behavioral + signature hybrid detection
- Explainable alerts (human-readable reason trail)
- Incident correlation from low-level alerts
- Open-source rule ecosystem and governance
- Reproducible evaluation artifacts for academic validation

## Data Flow Summary
1. New log line arrives.
2. Sentinel parses and normalizes it.
3. Signature and behavioral detectors run.
4. Alert is scored, reasoned, deduplicated, and logged.
5. Dashboard server parses alert log, computes stats/incidents, and exposes Grafana helper APIs.
6. Portal API consumes dashboard endpoints and persists workspace/dashboard metadata in Postgres/Redis.
7. Portal UI renders customizable analyst views with embedded Sentinel and Grafana context.
8. Prometheus scrapes metrics, Grafana visualizes trends, and embeds are surfaced inside Portal UI.
