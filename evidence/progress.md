# Progress

2026-10-03 — Preparation only. Requirements, acceptance designs, milestones, agent guidance, and unpublished article draft created. Application code, executable acceptance tests, model campaigns, and physical validation have not been implemented or run. Next task: M0 in IMPLEMENTATION_PLAN.md.

## 2026-10-04 requirements audit

Added explicit Must/Should/Could/Won't priorities, per-requirement rationale and acceptance, existing-tool evidence, M0 differentiation gate, and external consumer release criteria. No application implementation or tests were run. All application requirements remain not implemented.

Planning verification: work/verify_project_packages.py checked unique IDs, priorities, nonempty rationale and acceptance, valid dependency references, milestone/spec mapping, local document links, unchanged unpublished website draft status, and absent project remotes. git diff --check passed. Space plan readback verified all 22 requirement IDs and five exclusions under the correct parent. These checks validate documentation consistency, not application behavior.

## M0 (2026-10-04)
Environment: repo-local .venv, Python 3.12.14; pip install selected dependencies, pip freeze --all to requirements-lock.txt; pip check exit 0. Hardware and lock hash: environment.json. No global installs. Git ownership differs from current user; every git command uses a scoped safe.directory override. Docker daemon unavailable, generated-code/model execution disabled.
Executed tools/baseline.py: first exit 1 from zero-robustness Boolean encoding (retained baseline-first-failure.json); corrected encoding exit 0, both bad cases fail and both corrected pass; OpenHTF PASS with attachment. Gap/decisions/limits in docs/BASELINE.md and SEMANTICS.md. Independent twelve-invariant expectations and full state matrix frozen in tests/oracle/expectations.json. First pytest collection correctly failed (package absent); raw output oracle-first-run.txt. This is an open agent-authored oracle, not blind practitioner evaluation.
Next: implement the minimal replay and deterministic controller slice against these expectations.

## M1 and deterministic M2 slice
Implemented strict events, immutable controller boundary, recipes, deterministic Euler plant, raw recording, JSONL/CSV import and pytest/RTAMT monitor integration. Tests run: pytest -q -k "not 1000", 94 passed (m2-first-tests.txt). Includes full state matrix, exact timestamps, independent hand calculation (first pump step 3 Pa), convergence, thermal fixtures, all six controller defects and twelve negative monitor controls. Failed controller traces retained in failed-candidates/.
First implementation failed recipe tuple-to-JSON-list conversion; fixed serialization (m1-first-tests.txt). State fixture setup initially implied a connect for disconnected+arm and omitted the unacknowledged latch; corrected setup without changing the frozen expected state table. Old-packet fixture initially inserted receipt 40 ms before remaining 0 ms records; moved insertion after those records, retaining the same expected failure. This is oracle version 2 setup, open suite, no live comparison has run. m1-second-tests.txt and m1-tests.txt retain failures. Next: property result, durable manifest/report/CLI, clean consumer and release evidence. Lint/type first runs exposed formatting and missing annotations; not yet passing.
