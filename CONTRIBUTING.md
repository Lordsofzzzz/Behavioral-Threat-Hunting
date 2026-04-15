# Contributing Guide

Thanks for your interest in improving Behavioral Threat Hunting.

## Development Setup
1. Create and activate a Python virtual environment.
2. Install dependencies:
   - `pip install -r log-sentinel/requirements.txt`
   - `pip install -r apps/portal-api/requirements.txt`
3. (Optional for Portal UI local dev) install Node dependencies:
   - `cd apps/portal-ui && npm install`
   - `cd ../..`
4. Run locally (Python):
   - `python log-sentinel/sentinel.py`
   - `python log-sentinel/Dashboard-server.py`

Optional (Docker one-command):
- Windows PowerShell: `./run-stack.ps1 -Profile full -Action up`
- Windows CMD: `run-stack.bat full up`
- Linux/macOS: `./run-stack.sh full up`

## Contribution Scope
- Detection rules in `log-sentinel/rules/`
- Detection engine in `log-sentinel/sentinel.py`
- Dashboard API and UI in `log-sentinel/Dashboard-server.py` and `log-sentinel/dashboard.html`
- Portal API in `apps/portal-api/`
- Portal UI in `apps/portal-ui/`
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
