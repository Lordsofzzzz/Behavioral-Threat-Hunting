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
- Integrated teammate-style Portal stack (FastAPI + Next.js + Postgres) for customizable dashboard workflows.
- Added automated GitHub Release workflow triggered by version tags (`vX.Y.Z`) to publish core and full downloadable bundles.
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
- apps/
  - portal-api/: FastAPI service for dashboard registry, layout persistence, and summary APIs
  - portal-ui/: Next.js analyst UI with embedded dashboard workspace
- infra/
  - grafana/, prometheus/, loki/, promtail/: observability stack configs (compose optional profiles)
- build-release.bat: Windows helper to create and push release tags safely
- PHASED_IMPROVEMENT_PLAN.md: Final-year implementation roadmap

## Requirements
- Python 3.8+ (core engine and dashboard)
- Node.js 20+ and npm (Portal UI local development)
- Docker Desktop (recommended for full integrated stack)
- Python dependency files:
  - `log-sentinel/requirements.txt` (currently `PyYAML>=6.0,<7.0`)
  - `apps/portal-api/requirements.txt`

## Setup
1) Create a virtual environment (optional) and install dependencies:

```bash
pip install -r log-sentinel/requirements.txt
pip install -r apps/portal-api/requirements.txt
```

2) (Optional, for local Portal UI development) install UI dependencies:

```bash
cd apps/portal-ui
npm install
cd ../..
```

3) Update the log path and settings in log-sentinel/config.yaml if needed.

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

## Run Portal UI/API (Recommended)
From repository root (Docker):

```bash
docker compose --profile portal up --build
```

Then open:
- Portal UI: `http://localhost:3001`
- Portal API: `http://localhost:8080`

Portal API is already integrated with Log Sentinel dashboard APIs.

## Download the Right Release Bundle
Current release automation in this repository focuses on the Log Sentinel core bundle.
For the new Portal-based customization workflow, use source checkout from this repository and run with Docker Compose profiles (`portal`, `observability`, or `full`).

## Create a New Release (Maintainers)
From repository root on a clean branch:

```bat
build-release.bat 1.2.3
```

What this does:
- Normalizes the version to `v1.2.3`
- Warns if there are uncommitted changes
- Prevents duplicate local or remote tags
- Pushes the tag so GitHub Actions builds and publishes release bundles

## One-Command Docker Demo
Quick Start Matrix:

| OS / Shell | Start Full Stack | Logs | Stop |
|---|---|---|---|
| Windows PowerShell | `./run-stack.ps1 -Profile full -Action up` | `./run-stack.ps1 -Profile full -Action logs` | `./run-stack.ps1 -Profile full -Action down` |
| Windows CMD | `run-stack.bat full up` | `run-stack.bat full logs` | `run-stack.bat full down` |
| Linux/macOS | `./run-stack.sh full up` | `./run-stack.sh full logs` | `./run-stack.sh full down` |

Demo-only profile (web target + traffic generator):

| OS / Shell | Start Demo | Logs | Stop |
|---|---|---|---|
| Windows PowerShell | `./run-stack.ps1 -Profile demo -Action up` | `./run-stack.ps1 -Profile demo -Action logs` | `./run-stack.ps1 -Profile demo -Action down` |
| Windows CMD | `run-stack.bat demo up` | `run-stack.bat demo logs` | `run-stack.bat demo down` |
| Linux/macOS | `./run-stack.sh demo up` | `./run-stack.sh demo logs` | `./run-stack.sh demo down` |

From the repository root:

```bash
docker compose --profile full up --build
```

Or use one command launcher scripts:

PowerShell:

```powershell
./run-stack.ps1 -Profile full -Action up
```

CMD:

```bat
run-stack.bat full up
```

Linux/macOS:

```bash
chmod +x ./run-stack.sh
./run-stack.sh full up
```

Run components separately (isolated profiles):

```powershell
./run-stack.ps1 -Profile core -Action up       # sentinel + dashboard
./run-stack.ps1 -Profile engine -Action up     # sentinel only
./run-stack.ps1 -Profile dashboard -Action up  # dashboard only
./run-stack.ps1 -Profile simulator -Action up  # simulator only
./run-stack.ps1 -Profile demo -Action up       # demo-webapp + log-generator
./run-stack.ps1 -Profile portal -Action up     # postgres + redis + portal-api + portal-ui
./run-stack.ps1 -Profile observability -Action up  # prometheus + grafana
./run-stack.ps1 -Profile homarr -Action up     # Homarr launcher dashboard
```

Linux/macOS profile examples:

```bash
./run-stack.sh core up
./run-stack.sh engine up
./run-stack.sh dashboard up
./run-stack.sh simulator up
./run-stack.sh demo up
./run-stack.sh portal up
./run-stack.sh observability up
./run-stack.sh homarr up
```

Show launcher help:

```powershell
./run-stack.ps1 -Help
```

```bat
run-stack.bat help
```

```bash
./run-stack.sh --help
```

This allows one component group to fail without stopping other independently-run groups.

This starts:
- `demo-webapp` (Nginx target app on `http://localhost:8088`)
- `log-generator` (continuous mixed benign/attack traffic for demos)
- `sentinel` (detection engine)
- `dashboard` (UI/API on `http://localhost:8888`)
- `simulator` (scripted attack traffic generator for demo)
- `postgres`, `redis`, `portal-api`, `portal-ui` (customizable dashboard workflow)
- `prometheus`, `grafana` (observability profile)
- `homarr` (service launcher and quick navigation at `http://localhost:7575`)

Stop with:

```bash
docker compose down
```

or with launchers:

```powershell
./run-stack.ps1 -Profile full -Action down
```

```bash
./run-stack.sh full down
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

Portal API consumes these endpoints and normalizes them for Portal UI summaries and dashboard workflows.

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
