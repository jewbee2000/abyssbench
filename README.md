# AbyssBench

[Source repository](https://github.com/jewbee2000/abyssbench). The deterministic
offline release is verified; the article remains unpublished. Follow
[the next-step checklist](docs/NEXT_STEPS.md) for a real trace, an independent
engineer's trial, and the next implementation work.

A small offline controller replay and timing-contract integration for
**pytest + RTAMT**, with optional OpenHTF record attachments. Import your event
log or plug in a trusted Python controller; inspect requirement failures on a
repeatable timeline. The pump/valve simulation is one synthetic example. A
thermal log and clean consumer demonstrate a second domain.

## Try it locally (PowerShell, Python 3.12)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-lock.txt
.venv\Scripts\python -m pip install --no-deps --no-build-isolation -e .
.venv\Scripts\python -m abyssbench demo --offline --output artifacts/my-demo
.venv\Scripts\python -m abyssbench verify artifacts/my-demo
.venv\Scripts\python -m abyssbench serve artifacts/my-demo
```

Open the printed localhost report URL. Choose a new/empty output directory for
each run. Demo exit 0 means healthy/control cases passed and its deliberately
broken freshness controller failed as expected. It exports eight JSONL traces,
verdicts.json, hashed manifest.json and static report.html. Pressure, flow,
command issue times, measured valve position and controller state stay separate.
No keys or hardware are required after installation.

```powershell
.venv\Scripts\python -m abyssbench check tests/oracle/thermal-violating.jsonl --rules tests/oracle/thermal-rules.json
# expected exit 1; use thermal-valid.jsonl for exit 0, thermal-incomplete.jsonl for exit 2
```

Normal check exits: **0 pass**, **1 violation**, **2 invalid/incomplete/unsupported**.
CLI evaluation runs in a killable data-only worker with a 60-second maximum.

## Evidence and reproduction

- [M0 comparison and usefulness decision](docs/BASELINE.md): installed pytest,
  RTAMT and OpenHTF reproduce stale/reconnect failures. The contribution is
  provenance, bounded finite-window results and engineering evidence glue.
- [Requirement-to-test evidence](evidence/REQUIREMENT_EVIDENCE.md) and
  [progress](evidence/progress.md): commands, failures and local milestones.
- [Public API and schemas](docs/API.md), [frozen semantics](docs/SEMANTICS.md),
  [thermal example](docs/THERMAL_EXAMPLE.md),
  [consumer walkthrough](evidence/consumer-walkthrough.json).
- [Local performance measurements](evidence/performance.json) and
  [licensing/data handling](docs/LICENSING.md).

Run the complete local evidence workflow:

```powershell
.venv\Scripts\python tools/baseline.py
.venv\Scripts\python tools/benchmark.py
.venv\Scripts\python tools/license_inventory.py
.venv\Scripts\python tools/freeze_provenance.py
.venv\Scripts\python -m build --wheel --no-isolation --outdir artifacts/dist
.venv\Scripts\python tools/consumer_walkthrough.py --directory artifacts/new-consumer
.venv\Scripts\python -m ruff check src tests tools examples
.venv\Scripts\python -m mypy src/abyssbench
.venv\Scripts\python -m pytest -q
.venv\Scripts\python tools/release_evidence.py
```

The walkthrough creates another clean venv, installs the pinned dependencies
and wheel, checks a non-default failed thermal input, corrects it, tests a
separate controller, and runs/verifies the offline demo. This is an
agent-executed walkthrough; practitioner adoption remains unverified.

## Supported scope and limits

Single monotonic integer-millisecond clock; versioned JSONL and explicitly
mapped CSV with a JSON payload column. Pa, m3/s, degC and unitless fraction
channels. Four configured rule types plus the twelve fluid reference
invariants. Unknown versions, ambiguous units, unordered logs, incomplete
windows and corrupted artifacts cannot justify a successful check.

20 MiB input, 100000 events, 32 rules/cases, 60000 ms simulated run. Local
resource target: 10000 events in <10 seconds and <256 MiB RSS. Measured results
apply to the recorded Windows/Python environment, not universal hardware.
Trusted controller callbacks are ordinary caller code; **untrusted generated
code is disabled**. The data worker is a resource boundary, not a sandbox.

The fluid equations are illustrative and uncalibrated. Software command
issuance does not establish real actuator motion, functional safety, hard
real-time behavior or lab qualification. Multi-clock reconstruction, PLC/C++
adapters, hardware control, CAD and live-model campaigns are excluded. OpenHTF
attachments work; optional Parquet is deferred. The source repository was
pushed with Walter's authorization on 2026-10-04. The [blog draft](docs/BLOG_DRAFT.md) remains
unpublished. Code, fixtures and original docs are MIT licensed.
