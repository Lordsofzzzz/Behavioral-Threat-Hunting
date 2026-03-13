# Behavioral Threat Hunting - Log Sentinel

Log Sentinel is a lightweight, real-time log monitor for Nginx-style access logs. It detects common web attacks using pattern rules, rate limiting, and 404 spam heuristics, and can optionally serve a live dashboard for alerts and stats.

## Features
- Detects SQL injection, XSS, path traversal, and command injection
- Flags known scanner User-Agents
- Rate limit and 404 spam detection per IP
- Console alerts and file-based alert logging
- Optional dashboard with API endpoints
- Robust parsing for common Nginx log variants
- Duplicate alert suppression to reduce noisy repeated alerts
- Dynamic risk scoring (0-100) with score-based severity
- Behavioral anomaly detection (new endpoint, new user-agent, request spike)
- Explainable alerts with machine-readable reason codes
- Incident correlation (group related alerts into campaign-like incidents)

## Release Highlights (Feb 2026)
- Hardened detection pipeline with config validation, path normalization, deduplication, and score-based severity.
- Added behavioral anomaly intelligence with explainable reason codes in every enriched alert.
- Added incident correlation (`/api/incidents`) and dashboard incident panel for faster analyst triage.
- Added reproducible evaluation harness for academic metrics (precision, recall, F1, latency, throughput, memory).
- Added Dockerized one-command demo stack (`sentinel`, `dashboard`, `simulator`).
- Added open-source maturity assets: CI workflow, LICENSE, contribution templates, code of conduct, and security policy.

## Release Highlights (Mar 2026)
- Improved dashboard reliability under concurrent requests by moving to a threaded HTTP server.
- Added thread-safe alert parsing cache in dashboard API to avoid race conditions and stale reads.
- Improved Sentinel Canvas API client with in-flight request deduplication, timeout handling, and transient retry logic.
- Added automated GitHub Release workflow triggered by version tags (`vX.Y.Z`) to publish downloadable zip bundles.
- Added Windows release helper script (`build-release.bat`) with safeguards (version validation, dirty-tree warning, duplicate tag checks).

## Project Structure
- .github/: CI and contribution templates
  - workflows/release.yml: Tag-triggered build and release pipeline
- docs/: architecture and demo docs
- log-sentinel/
  - sentinel.py: Log monitor and detection engine
  - config.yaml: Runtime settings
  - Dashboard-server.py: Dashboard HTTP server
  - dashboard.html: Dashboard UI
  - demo_simulator.py: Docker demo traffic generator
  - rules/: Pattern files for detection
  - evaluation/: Benchmark dataset and metrics scripts
  - data/: Runtime log files (git-ignored)
  - test.sh: Log attack simulator (bash)
- sentinel-canvas/
  - canvas-server.py: Lightweight static server for Canvas UI
  - index.html: Canvas main page
  - css/: Styling modules
  - js/: Canvas builder, widget, and API client modules
- build-release.bat: Windows helper to create and push release tags safely
- PHASED_IMPROVEMENT_PLAN.md: Final-year implementation roadmap

## Requirements
- Python 3.8+
- Dependencies listed in `log-sentinel/requirements.txt`

## Setup
1) Create a virtual environment (optional) and install dependencies:

```bash
pip install -r log-sentinel/requirements.txt
```

2) Update the log path and settings in log-sentinel/config.yaml if needed.

## Run the Sentinel
From the log-sentinel directory:

```bash
python sentinel.py
```

The sentinel tails the configured log file and writes alerts to `log-sentinel/data/alerts.log`.

## Run the Dashboard
In a separate terminal, from log-sentinel:

```bash
python Dashboard-server.py
```

Then open http://localhost:8888 in a browser.

## Run Sentinel Canvas (Optional)
In another terminal, from sentinel-canvas:

```bash
python canvas-server.py
```

Then open http://localhost:8889 in a browser.
Canvas can consume the dashboard API from `http://localhost:8888`.

## Download the Right Release Bundle
Each tagged release publishes 3 zip packages. Choose based on your use case:

- `sentinel-core-only-vX.Y.Z.zip`
  - Includes only `log-sentinel/`
  - Use this if you only need the detection engine + classic dashboard API/UI
- `sentinel-canvas-only-vX.Y.Z.zip`
  - Includes only `sentinel-canvas/`
  - Use this if you already run the core backend and only want the drag-and-drop Canvas frontend
- `sentinel-full-bundle-vX.Y.Z.zip`
  - Includes both `log-sentinel/` and `sentinel-canvas/`
  - Best choice for first-time setup and demos

Practical recommendation:
- New users: download full bundle
- Security lab / backend-only deployment: download core-only
- UI-only upgrade for existing core install: download canvas-only

## Create a New Release (Maintainers)
From repository root on a clean branch:

```bat
build-release.bat 1.2.3
```

What this does:
- Normalizes the version to `v1.2.3`
- Warns if there are uncommitted changes
- Prevents duplicate local or remote tags
- Pushes the tag so GitHub Actions builds and publishes the 3 zip bundles

## One-Command Docker Demo
From the repository root:

```bash
docker compose up --build
```

This starts:
- `sentinel` (detection engine)
- `dashboard` (UI/API on `http://localhost:8888`)
- `simulator` (scripted attack traffic generator for demo)

Stop with:

```bash
docker compose down
```

## Simulate Attacks
The test script appends sample attack lines to the configured log.

```bash
bash test.sh
```

Note: On Windows, run this in Git Bash or WSL.

## Configuration
Key settings in log-sentinel/config.yaml:
- log_file: Path to access log to monitor
- alert_log: Output file for alerts
- enable_*_detection: Toggle detectors
- rate_limit_*: Rate limit settings
- enable_404_detection / max_404_per_minute
- whitelist_ips: Comma-separated IPs to skip
- dedup_enabled / dedup_window_seconds: Suppress duplicate alerts in a time window
- max_path_length: Limit very long path output in console
- enable_behavioral_detection: Enable anomaly detection on request behavior
- behavior_*: Tune baseline history thresholds and spike multiplier

## Rules
Detection patterns live in log-sentinel/rules/:
- sqli_patterns.txt
- xss_patterns.txt
- traversal_patterns.txt
- cmdi_patterns.txt
- scanner_patterns.txt

Patterns are treated as case-insensitive regular expressions.

## Output
Alerts are written to `log-sentinel/data/alerts.log` and optionally printed to the console. The dashboard reads that file and exposes:
- GET /api/alerts (last 100 alerts)
- GET /api/stats (summary stats)
- GET /api/incidents (correlated incidents by IP and time window)

Sentinel Canvas reads these same API endpoints and renders them as configurable widgets.

## Notes
- The Nginx log regex expects the default combined log format.
- alert levels are labeled INFO/WARNING/CRITICAL but the minimum level filter is not enforced in code yet.

## Final-Year Track
- The project now includes Phase 0 and Phase 1 hardening improvements in code.
- See PHASED_IMPROVEMENT_PLAN.md for the full multi-phase roadmap through behavioral analytics, OSS maturity, and evaluation.

## Evaluation (Final-Year Metrics)
Run the built-in benchmark harness to generate measurable results:

```bash
python log-sentinel/evaluation/generate_dataset.py
python log-sentinel/evaluation/evaluate.py
```

Outputs:
- `log-sentinel/evaluation/dataset.jsonl`
- `log-sentinel/evaluation/report.json`

Reported metrics include precision, recall, F1, latency, throughput, memory usage, and per-attack-type recall.

## Open Source Readiness
- License: MIT (`LICENSE`)
- Contribution guide: `CONTRIBUTING.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
- Security policy: `SECURITY.md`
- Community templates: `.github/ISSUE_TEMPLATE/` and `.github/pull_request_template.md`
- CI checks: `.github/workflows/ci.yml`

## Presentation Docs
- Architecture overview: `docs/ARCHITECTURE.md`
- 2-minute demo flow: `docs/DEMO_SCRIPT.md`
