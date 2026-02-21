# Phased Improvement Plan (Final Year)

This plan is structured to make the project academically strong, implementation-friendly, and differentiable from basic signature-only IDS tools.

## Phase 0 — Foundation Hardening
- Add configuration validation and safe defaults
- Improve startup checks and graceful error handling
- Add robust regex loading with invalid-pattern warnings
- Document runtime configuration and expected log formats

## Phase 1 — Detection Quality
- Support multiple Nginx-style formats (combined + common fallback)
- Normalize request paths before matching (double decode + canonical separators)
- Add duplicate alert suppression window to reduce noise
- Add dynamic risk scoring and score-based severity labels

## Phase 2 — Behavioral Intelligence (Unique Factor)
- Build baseline behavior per IP/endpoint/User-Agent
- Detect deviations (request spikes, unusual access patterns)
- Add explainable alerts with reason codes and context values

## Phase 3 — Analyst Experience
- Add dashboard filters (time, type, severity, IP)
- Add incident grouping/correlation instead of isolated alerts
- Add acknowledgement workflow and exportable incident summaries

## Phase 4 — Open Source Maturity
- Add OSS governance docs (`LICENSE`, `CONTRIBUTING`, `SECURITY`, templates)
- Add CI for lint/tests/rule validation
- Add community rule-pack structure and contribution checks

## Phase 5 — Academic Validation
- Create benchmark dataset and replay harness
- Measure precision, recall, F1, detection latency, and resource usage
- Compare against baseline tools and discuss trade-offs

## Current Status
- Implemented in code: **Phase 0 + Phase 1 core engine improvements**.
- Implemented in code: **Phase 2 baseline behavioral anomaly detection + explainable reason codes**.
- Implemented in code: **Phase 3 incident correlation API + dashboard panel**.
- Implemented in code: **Phase 5 evaluation harness (dataset generation + benchmark metrics report)**.
- Implemented in code: **Phase 6 Docker packaging + one-command scripted demo**.
