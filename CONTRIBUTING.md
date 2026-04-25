# Contributing Guide

Thanks for your interest in improving Behavioral Threat Hunting.

## Development Setup
1. Create and activate a Python virtual environment.
2. Install dependencies:
   - `pip install -r log-sentinel/requirements.txt`
3. (Optional, only if running the generator outside Docker):
   - `pip install -r apps/log-generator/requirements.txt`
4. Run locally (Python):
   - `python log-sentinel/sentinel.py`
5. If running outside Docker, make sure `log-sentinel/config.yaml` points `log_file` to a valid host path.

Optional (Docker, recommended for contributors):
- `docker compose --profile full up -d --build`
- `docker compose down`

## Contribution Scope
- Detection rules in `log-sentinel/rules/`
- Detection engine in `log-sentinel/sentinel.py`
- Log generation in `apps/log-generator/`
- Demo app and Nginx config in `apps/demo-webapp/`
- Observability configuration in `infra/`
- Documentation in `README.md`, `docs/ARCHITECTURE.md`, and `PHASED_IMPROVEMENT_PLAN.md`

## Rule Contribution Requirements
- Keep regex focused and explain intended attack pattern.
- Avoid broad patterns that generate excessive false positives.
- Add at least one representative test line in PR description.

## Pull Request Checklist
- [ ] Code builds and runs locally
- [ ] No obvious regressions in detection flow
- [ ] Documentation updated for behavior/config changes
- [ ] PR includes concise rationale and expected impact

## Commit Style
Prefer small, focused commits with clear messages.

Examples:
- `feat: add behavioral spike anomaly scoring`
- `fix: prevent duplicate alert emission`
- `docs: update config options for incident correlation`
