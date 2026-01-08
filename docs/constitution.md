# Project Constitution (v1.0)

## 1) Non‑Negotiables
- SoT = `plan.md`. When user says **go**, pick the **next unchecked test** only and execute **RED→GREEN→REFACTOR**.
- Output discipline: **ExecSummary → Visual → Options → Roadmap → Automation → QA** (KR concise + EN‑inline).
- Numerics fixed to **2 decimals**; dates use **ISO (YYYY-MM-DD)**; timezone **Asia/Dubai**.
- Scope guard: **edit only `src/**` by default**. If non‑src change is required, justify and record in changelog.
- No secrets in git. Never print tokens/keys in logs.

## 2) Quality Gates (merge conditions)
- Tests: `pytest -q` (or repo-equivalent) must pass.
- Coverage: **≥ 85.00%** for Python code paths (if Python present).
- Lint/format: **0 warnings** (`ruff`/`ruff format`/`black`/`isort`, or repo-equivalent).
- Security: `bandit` High=0 and `pip-audit --strict` pass (if Python deps present).
- CODEOWNERS approvals: **≥ 2** with branch protection.

## 3) Agent Autonomy Policy (High)
- Default mode is **Agent Mode**: implement end-to-end without asking follow-ups unless:
  - required inputs are missing and block execution, or
  - legal/compliance constraints are unclear.
- Always run the smallest validation suite before claiming readiness.
- Prefer minimal diffs; never refactor unrelated code “for cleanliness”.

## 4) Fail‑Safe (ZERO)
If core inputs are missing, or the request risks policy/secret exposure, stop and output only:

| 단계 | 이유 | 위험 | 요청데이터 | 다음조치 |
|---|---|---|---|---|
| 중단 | (fill) | (fill) | (fill) | (fill) |

## 5) Changelog
- 2026-01-08: Initial constitution template generated.
