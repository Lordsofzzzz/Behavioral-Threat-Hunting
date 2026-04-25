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
- Expand Grafana dashboard coverage (attack categories, top sources, rate trends)
- Add clearer alert triage views from persisted alert evidence
- Add operator-focused troubleshooting and tuning guidance

## Phase 4 — Open Source Maturity
- Add OSS governance docs (`LICENSE`, `CONTRIBUTING`, `SECURITY`, templates)
- Add CI for lint/tests/rule validation
- Add community rule-pack structure and contribution checks

## Phase 5 — Academic Validation
- Build reproducible benchmark dataset and replay tooling
- Measure precision, recall, F1, detection latency, and resource usage
- Compare against baseline tools and document trade-offs

## Phase 6 — Packaging and Operations
- Add Docker packaging for reproducible environment setup
- Isolate component startup using compose profiles for resilient demos
- Document quick-start and troubleshooting commands for viva/demo readiness

## Current Status
- Implemented in code: **Phase 0 + Phase 1 core engine improvements**.
- Implemented in code: **Phase 2 baseline behavioral anomaly detection + explainable reason codes**.
- Partially implemented: **Phase 3 analyst experience via Grafana dashboards and Prometheus metrics exposure**.
- In progress / future work: **Phase 5 formal benchmark harness and published validation report**.
- Implemented in code: **Phase 6 Docker packaging + compose profiles for demo, engine, observability, and full stack runs**.
