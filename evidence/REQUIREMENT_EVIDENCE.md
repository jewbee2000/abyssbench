# Executed requirement evidence

All 21 applicable Must requirements have executed passing software checks. AB-18 is partially implemented: OpenHTF attachment passed; Parquet is explicitly deferred. No conditional live-model/CAD feature is enabled.

The complete suite ran 116 passing tests, including one Hypothesis test configured for 1000 bounded examples. Six deliberately broken controllers and twelve independent negative event controls are detected. Counts are a coverage inventory, not a quality or model-success score.

Full raw results: [acceptance-run.json](acceptance-run.json). Subsequent report-layout checks: [report-run.json](report-run.json). Fresh installed-wheel checks: [fresh-install-run.json](fresh-install-run.json). Each run records command, exit code, commit/dirty state, diff/content/lock/oracle/input hashes and test-to-requirement mappings. [release.json](release.json) retains run provenance and artifact hashes.

| ID | Priority | Outcome | Executed test modules |
| --- | --- | --- | --- |
| AB-01 | must | verified | [test_contract.py](../tests/acceptance/test_contract.py), [test_monitor_independence.py](../tests/acceptance/test_monitor_independence.py) |
| AB-02 | must | verified | [test_contract.py](../tests/acceptance/test_contract.py), [test_replay.py](../tests/acceptance/test_replay.py) |
| AB-03 | must | verified | [test_contract.py](../tests/acceptance/test_contract.py) |
| AB-04 | must | verified | [test_contract.py](../tests/acceptance/test_contract.py) |
| AB-05 | must | verified | [test_contract.py](../tests/acceptance/test_contract.py) |
| AB-06 | must | verified | [test_contract.py](../tests/acceptance/test_contract.py) |
| AB-07 | must | verified | [test_contract.py](../tests/acceptance/test_contract.py) |
| AB-08 | must | verified | [test_artifacts.py](../tests/acceptance/test_artifacts.py), [test_contract.py](../tests/acceptance/test_contract.py) |
| AB-09 | must | verified | [test_monitor_independence.py](../tests/acceptance/test_monitor_independence.py) |
| AB-10 | must | verified | [test_artifacts.py](../tests/acceptance/test_artifacts.py) |
| AB-11 | must | verified | [test_monitor_independence.py](../tests/acceptance/test_monitor_independence.py) |
| AB-12 | must | verified | [test_artifacts.py](../tests/acceptance/test_artifacts.py), [test_contract.py](../tests/acceptance/test_contract.py), [test_monitor_independence.py](../tests/acceptance/test_monitor_independence.py), [test_release_evidence.py](../tests/acceptance/test_release_evidence.py) |
| AB-13 | must | verified | [test_replay.py](../tests/acceptance/test_replay.py) |
| AB-14 | must | verified | [test_replay.py](../tests/acceptance/test_replay.py) |
| AB-15 | must | verified | [test_external_controller.py](../tests/acceptance/test_external_controller.py) |
| AB-16 | must | verified | [test_nonfinite_trace.py](../tests/acceptance/test_nonfinite_trace.py), [test_replay.py](../tests/acceptance/test_replay.py) |
| AB-17 | must | verified | [test_replay.py](../tests/acceptance/test_replay.py) |
| AB-18 | should | partial_deferred | [test_release_evidence.py](../tests/acceptance/test_release_evidence.py) |
| AB-19 | must | verified | [test_artifacts.py](../tests/acceptance/test_artifacts.py), [test_nonfinite_trace.py](../tests/acceptance/test_nonfinite_trace.py), [test_release_evidence.py](../tests/acceptance/test_release_evidence.py), [test_replay.py](../tests/acceptance/test_replay.py) |
| AB-20 | must | verified | [test_artifacts.py](../tests/acceptance/test_artifacts.py), [test_release_evidence.py](../tests/acceptance/test_release_evidence.py) |
| AB-21 | must | verified | [test_artifacts.py](../tests/acceptance/test_artifacts.py), [test_release_evidence.py](../tests/acceptance/test_release_evidence.py) |
| AB-22 | must | verified | [test_release_evidence.py](../tests/acceptance/test_release_evidence.py) |

## Known limits and evidence boundaries

- Python 3.12 on the recorded Windows environment; ANTLR emits upstream deprecation warnings. Other operating systems are not verified.
- Single monotonic clock and explicit SI/degC units. CSV requires a JSON payload column; arbitrary flattened logs need conversion.
- Plant is synthetic and uncalibrated. Command deadlines are simulation evidence, not physical actuator or hard real-time guarantees.
- Trusted Python callbacks only. CLI data evaluation is timeout-killable; Python callbacks have no hostile-code sandbox. Docker unavailable.
- Finite input limits: 20 MiB, 100000 events, 32 rules/cases, 60000 ms simulation, 60 s evaluation. Local 10000-event target passed; raw-library comparison does less work and is not a speedup baseline.
- Clean consumer setup uses a fresh venv with the existing package cache. Agent-executed failure/correction is not independent practitioner adoption.
- Failed traces, first baseline failure and implementation failures remain in evidence/. No failing randomized sequence was found; the retained six seeded defects are deterministic negative controls.
- Parquet deferred. C++, PLC, CAD, distributed clocks, hardware qualification and model campaigns excluded. Source repository is public at https://github.com/jewbee2000/abyssbench; article remains unpublished.
- Missing or irregular fluid controller ticks are inconclusive for timing claims. Abrupt recorder process termination leaves an incomplete durable manifest. Each run preserves its own source hashes.

Local normal and explicit draft Jekyll builds passed, with desktop/mobile previews inspected. Article publication still needs Walter's editorial review, the verified repository/evidence links and final link checks. Website publication is not authorized.
