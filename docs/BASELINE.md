# M0 existing-tool comparison

Executed locally with Python 3.12.14, pytest 9.1.1, RTAMT 0.4.10,
OpenHTF 1.6.1. Full transitive pins: requirements-lock.txt. Command:
`.venv/Scripts/python.exe tools/baseline.py`; exit 0. Results:
[baseline.json](../evidence/baseline.json). No hardware or API calls.

Two independently authored 0–500 ms, 10 ms sampling recipes:
stale sample taken at 0 becomes invalid at 210 ms, despite recent receipt;
reconnect at 300 ms must not restart. Broken versions never issue the safe
response; corrected versions issue it at 210/300 ms. RTAMT formula is
`(trigger > 0) implies eventually[0:10] (safe > 0)`, unit ms, period 10 ms,
zero timing tolerance. Only the completed prefix through 490 ms is judged.
pytest can assert the result without providing a custom test runner. OpenHTF
executes a phase with two validated measurements and attaches the verdict JSON
to a PASS record. This is an actual installed-library spike, not a feature
comparison inferred only from documentation.

The first experiment incorrectly encoded a true trigger as equality at the
predicate boundary. Robustness zero then masked a violation. The original
output is retained in baseline-first-failure.json; using +1/-1 with >0 corrected
the encoding. This does not weaken any controller expectation. It illustrates
why raw numerical robustness needs an explicit application-level contract.

| Existing component | Solves | Work still needed for this workflow |
| --- | --- | --- |
| pytest + RTAMT | Repeatable assertions, quantitative temporal predicates | Map event logs into signals, retain packet provenance, distinguish incomplete windows, requirement-linked explanations |
| OpenHTF | Phases, measurement validation, attachments and station records | Virtual fault schedule, sample versus receipt time policy, replay input and trace report |
| labgrid | Board resources/drivers and pytest hardware fixtures | Hardware-free replay has no board resources to manage |
| Toxiproxy | TCP transport fault injection | A transport proxy cannot specify synthetic sampling age or mechanical valve mismatch |

Decision: continue with a small importable recipe/adapter package. Reuse pytest
as execution framework, RTAMT for numerical predicate robustness, jsonschema for
versioned input validation, and OpenHTF attachment integration. Python keeps a
bounded event-obligation ledger for finite windows, identity and recovery
evidence. Do not introduce a temporal DSL, model platform or station framework.
Parquet is deferred: JSONL already retains all raw timestamps, and a second
storage dependency is not needed to demonstrate reuse.

Timestamp policy: explicit integer monotonic milliseconds, one clock. No
automatic wall-clock conversion. Out-of-order packets are data; unordered log
sequence is an input error. Resource limits and clock/window decisions are
frozen in SEMANTICS.md. CAD and generated-code execution are outside this scope.

Usefulness assessment: the spike demonstrates a concrete packaging gap for
this workflow, not unique invention. These recipes could also live in an
existing engineer's test repository. A reusable package is justified only if
external log and clean consumer cases work; M4 checks that. No interviews,
practitioner adoption, physical validation, or industry novelty are established.

Primary documentation inspected 2026-10-04:
[RTAMT](https://github.com/nickovic/rtamt),
[OpenHTF](https://github.com/google/openhtf),
[labgrid](https://labgrid.readthedocs.io/en/latest/),
[Toxiproxy](https://github.com/Shopify/toxiproxy).
