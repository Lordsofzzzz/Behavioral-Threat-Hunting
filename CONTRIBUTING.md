# Contributing Guide

Thanks for your interest in improving Behavioral Threat Hunting.

## Development Setup
1. Create and activate a Python virtual environment.
2. Install dependencies:
   - `pip install -r log-sentinel/requirements.txt`
3. Run locally:
   - `python log-sentinel/sentinel.py`
   - `python log-sentinel/Dashboard-server.py`

## Contribution Scope
- Detection rules in `log-sentinel/rules/`
- Detection engine in `log-sentinel/sentinel.py`
- Dashboard API and UI in `log-sentinel/Dashboard-server.py` and `log-sentinel/dashboard.html`
- Documentation in `README.md` and `PHASED_IMPROVEMENT_PLAN.md`

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
