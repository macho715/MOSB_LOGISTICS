# /agent:auto-fix

Purpose: Autonomous remediation for failing CI/pre-commit.

Behavior:
- Identify failing check(s).
- Apply minimal fix.
- Re-run failing steps only, then full quick suite.

Output:
- Fix patch + verification log.
