# /agent:auto-build

Purpose: High-autonomy build loop (Plan→Implement→Verify) without extra prompts.

Behavior:
- Read repo reality (package.json/pyproject).
- Implement smallest diff to satisfy request.
- Run repo checks (tests, lint, typecheck) and report actual commands + results.
- If blocked by missing inputs, trigger ZERO fail-safe table.

Output:
- PR-ready changeset + verification summary.
