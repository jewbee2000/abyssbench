# Version 1 public workflow

Supported Python: 3.12. Offline trace data and trusted controller callbacks.
`abyssbench` exports `Measurement`, `Command`, `Recipe`, `Tick`, `TickResult`,
`Controller` (Protocol), `FluidController`, `run`, `monitor`, `read_jsonl`,
`read_csv`, `write_jsonl`, and `InputError`. The generic API imports no fluid
controller/plant; those example exports load lazily.

```python
from abyssbench import read_jsonl, monitor
import json
rules = json.load(open("tests/oracle/thermal-rules.json"))
events = read_jsonl("tests/oracle/thermal-valid.jsonl", units=rules["channels"])
result = monitor(events, rules=rules)
assert result["status"] == "pass"
```

The event envelope has `schema_version:1`, `clock:"simulation"`, contiguous
`sequence` starting at zero, integer `time_ms`, `kind`, and `data`. Events with
the same timestamp retain sequence ordering. A measurement event's time equals
its receive time. Packet sample time and packet sequence may go backwards.
Missing sample time is represented by null; it cannot prove freshness. Future
sample time is invalid signal data. Measurement data also includes channel,
value, unit, quality, sequence, and calibration_id. Calibration identities in
these examples are synthetic provenance, not real calibrations.

Schemas are packaged in `src/abyssbench/schemas/`. Unknown versions, log-order
errors, incompatible clocks, nonfinite values, ambiguous CSV unit maps, and
missing required channels are rejected. Only Pa, m3/s, degC and unitless `1`
are supported by the generic rule declaration. No automatic conversion.

Rules use stable user-selected IDs. Four rule types:

| Type | Required fields besides id/type | Meaning |
| --- | --- | --- |
| range | channel, min, max | Inclusive numeric limits and good quality |
| sample_age | channel, max_age_ms | Age from sample time, inclusive maximum, no future sample |
| response | trigger_kind, response, deadline_ms | Each trigger event requires each named actuator command in inclusive future window |
| transition | from, to | Prohibit a recorded state transition |

Range and age rules can have `when_state`, plus `response` and `deadline_ms`.
Without a response they test signal validity directly. With a response they
test fault handling: each invalid observation needs an issued safe command by
its deadline. They do not fail merely because a fault was deliberately injected.
Raw range/age numeric robustness comes from RTAMT; event response/identity/
history and finite-window evidence use the bounded Python ledger. A response
cannot be inferred from a held prior value. No triggers means a response rule
passes vacuously inside a nonempty valid window; no eligible signal observation
is inconclusive. Generic state labels are user-defined.

`monitor(events, profile="fluid")` additionally returns all twelve reference
invariants I01–I12. It independently reconstructs measurements, heartbeat,
connection, valve mismatch, command acceptance, history and recovery. It never
imports controller helper functions. Fault detections can be emitted once:
subsequent ticks must preserve their history. SPEC.md thresholds belong to this
profile; thermal rules use different explicit thresholds.
Missing or irregular 10 ms fluid ticks make timing evidence inconclusive;
they cannot prove that an unobserved interval met the response contract.

Results declare observation window, clock assumptions, and per-rule
pass/fail/inconclusive/not_applicable. Pending future obligations stay
inconclusive until observed or expired. Check exit codes: 0 all checks pass,
1 any violation, 2 invalid/incomplete/unsupported execution. A failed and a
pending required rule together remain nonzero. The demo separately expects its
deliberate bad controller to fail and all correct controllers to pass.

CSV v1 uses an explicit mapping for envelope sequence/time/kind and a JSON
payload column, plus explicit units and schema/clock. See csv-map.json and the
thermal CSV fixtures. Arbitrary flattened station logs need a small conversion
script; autodetection is intentionally unsupported.

```powershell
.venv\Scripts\python -m abyssbench check tests/oracle/thermal-violating.jsonl --rules tests/oracle/thermal-rules.json --result artifacts/negative.json
# exit 1
.venv\Scripts\python -m abyssbench check tests/oracle/thermal-valid.csv --map tests/oracle/csv-map.json --rules tests/oracle/thermal-rules.json
# exit 0
```

`run(controller, fault=..., seed=..., duration_ms=...)` calls `.step(Tick)` every
10 ms and records raw events. See examples/consumer/controller.py: it imports
only the public API and uses different setpoints. `TickResult` must return state,
pump/valve fractions, retained fault history, new detections, and command
outcomes. Callbacks are trusted Python code; they may not be untrusted generated
code. Default fluid sample interval is 50 ms, duration 1500 ms, fault onset 500
ms. Optional requests map timestamp to commands. Exact duplicate IDs return
`duplicate` with `previous_outcome` and do not reapply; changed payload is
`conflict`; valid delivery is inclusive through expiry. `applied` means the
request was handled, not proof of an actuator's physical action. State guards
still control arm/start/ack behavior. Recipes have five strict fields and finite
fraction setpoints; no expression evaluation.

Output directories must be new/empty, with no `..` segments. Recorder manifests
begin incomplete and become complete only after all artifact writes and fsync.
`verify` rejects incomplete or mismatched hashes. Provenance includes source
commit/dirty state/diff hash, exact source content hash, lock/oracle/recipe hashes,
model parameters, seed and each artifact hash. The generated provenance stamp
is excluded from its own diff/content hash to avoid self-reference. Installed
wheels carry build provenance; a consumer need not have Git or oracle source.

Limits: 20 MiB file input, 100000 events, 32 rules/cases, 60000 ms fluid duration,
60 seconds evaluation. CLI check uses a killable data-only subprocess; timeout
and oversize return incomplete exit 2. Python API checks elapsed time between
bounded operations; it is not a hard callback deadline. `serve` is read-only on
127.0.0.1 (default port 8765). Reports have static SVG, escaped text, no egress.
