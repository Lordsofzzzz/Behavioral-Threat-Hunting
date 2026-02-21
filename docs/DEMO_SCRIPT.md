# 2-Minute Demo Script (Viva Ready)

## Goal
Demonstrate end-to-end detection, explainability, incident correlation, and dashboard visibility quickly.

## Pre-Demo Setup (before presentation)
1. Open terminal at repository root.
2. Ensure Docker Desktop is running.
3. Start stack:
   - `docker compose up --build`
4. Open dashboard:
   - `http://localhost:8888`

## Live Demo Timeline (2 minutes)

### 0:00 - 0:20 (Project Positioning)
Say:
- This is an open-source behavioral threat hunting system for web logs.
- It combines signature detection with behavioral anomaly detection.
- Every alert includes explainable reason codes and a risk score.

### 0:20 - 0:50 (Live Alert Generation)
Show:
- Simulator container writes representative attacks automatically.
- Sentinel console displays alerts in real time.

Say:
- Here we can see SQLi/XSS/traversal/scanner detections.
- Alert records include severity and score.

### 0:50 - 1:20 (Dashboard Evidence)
Show on dashboard:
- Total/critical/warning cards
- Attack type distribution
- Top attacking IPs
- Live alert feed

Say:
- This gives immediate operational visibility for analysts.

### 1:20 - 1:45 (Unique Factors)
Show:
- Alert metadata containing reason traces
- Correlated incidents panel

Say:
- Instead of isolated alerts, related events are grouped into incidents.
- This reduces noise and helps triage faster.

### 1:45 - 2:00 (Academic Validation)
Say:
- The project includes a reproducible benchmark harness.
- It reports precision, recall, F1, latency, throughput, and memory.
- This makes our claims measurable and research-friendly.

## Backup Commands
- Stop stack:
  - `docker compose down`
- Re-run metrics locally:
  - `python log-sentinel/evaluation/generate_dataset.py`
  - `python log-sentinel/evaluation/evaluate.py`

## Viva Q&A One-Liners
- Why unique?
  - Hybrid signature + behavioral + explainable + incident correlation.
- Why open source?
  - Transparent rules, reproducible metrics, and community extensibility.
- How to reduce false positives?
  - Rule tuning, dedup window, and baseline thresholds in config.
