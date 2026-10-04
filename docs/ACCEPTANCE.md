# Acceptance and evidence plan

This is a test design, not a report of passing tests. The concrete contracts and thresholds are in [SPEC.md](SPEC.md). Machine-readable traceability is in [requirements.json](../requirements.json). Every listed test path is planned and must be created during implementation.

| ID | Required behavior | Independent acceptance evidence |
| --- | --- | --- |
| AB-01 | The plant and clock reproduce the same event sequence for a fixed configuration, seed, and fault schedule. | Compare canonical JSON event hashes across two runs; exclude wall-clock metadata. |
| AB-02 | Sensors carry unit, sample time, receive time, quality, and provenance separately. | Delay and replay packets; verify sample age is unchanged and unit mismatch is rejected. |
| AB-03 | Arming, starting, stopping, and recovery follow the specified state graph. | Table-test every state/event pair, including illegal starts and simultaneous stop/start. |
| AB-04 | Stale age >200 ms and future timestamps are detected using sample time. | Test 199, 200, 201 ms ages and future timestamps; receiving an old packet cannot reset freshness. |
| AB-05 | A detected fault commands pump off and valve open within 10 ms. | Independent event monitor measures detection-to-command latency under all fault schedules. |
| AB-06 | Reconnect cannot restart the stand and fault history remains latched. | Disconnect during a run, reconnect, acknowledge, rearm; missing any recovery step blocks start. |
| AB-07 | Expired and conflicting duplicate commands are rejected; exact duplicates are not reapplied. | Vary expiry around 100 ms and repeat IDs with identical and changed payloads. |
| AB-08 | All five fault types are injected deterministically and detected under their specified conditions. | Scenario manifest includes onset, values, expected earliest detection, and exact required response. |
| AB-09 | The monitor catches six seeded controller defects without using controller implementation logic. | Freshness from receive time, inverted valve command, pressure unit mismatch, unsafe reconnect, unbounded retry, and lost latch each fail. |
| AB-10 | Run artifacts preserve hashes and identify interrupted runs as incomplete. | Interrupt recording, corrupt an artifact, and reproduce a completed run from its manifest. |
| AB-11 | Recipe validation and randomized event sequences preserve the invariant set. | Reject nonfinite values and unknown units; run 1000 bounded Hypothesis sequences and store counterexamples. |
| AB-12 | Offline demo and report work without hardware or credentials and disclose the simulation boundary. | Fresh-install run verifies charts, fault times, and labels; all twelve invariants have assertions. |

## Test layers

Use schema tests for input constraints; deterministic unit and contract tests for semantics; property/stateful tests for combinations; mutation tests for whether the oracle catches wrong implementations; and one end-to-end offline demonstration for packaging and artifact integrity. Avoid test counts as a proxy for engineering quality. Every seeded critical defect must be caught for an identified behavioral reason.

Expected values must come from the written contract, hand arithmetic, independent geometry inspection, or explicit state tables. Do not compute expected output by invoking the implementation under test. Freeze the oracle and case inventory in a distinct commit before the product-agent experiment.

## Required release evidence

Provide a manifest with commit and dirty-tree hash, environment lock hash, requirement IDs, input hashes, oracle hash, actual commands, exit codes, artifact hashes, and known limitations. Record cases as pass, fail, blocked, or not run. Supply a readable report and a representative negative example. Do not ship a prewritten passing result in place of running tests.

Target validation after implementation: formatter/linter, strict type check on core modules, pytest with relevant property tests, and the documented offline demo. Add a CI workflow only when its commands work locally; do not add decorative green badges before a real run.
