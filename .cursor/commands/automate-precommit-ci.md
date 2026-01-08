# /automate pre-commit+ci

Purpose: Apply pre-commit + CI scaffolding in one go.

Steps:
1) Ensure Python 3.13 environment is available.
2) Run:
   - `python tools/init_settings.py --apply-precommit --apply-ci --apply-workspace`
3) Validate:
   - `pre-commit run --all-files`
   - `pytest -q` (if Python present)

Outputs:
- `.pre-commit-config.yaml`
- `.github/workflows/ci.yml`
- `.cursor/config/workspace.json`
