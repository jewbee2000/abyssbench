# AbyssBench requirements and rationale

Revision 2026-10-04. Status: planned, not implemented. This audit supersedes the earlier unprioritized feature list. [requirements.json](../requirements.json) is the machine-readable register; [SPEC.md](SPEC.md) supplies detailed reference-case constants and contracts. Keep them synchronized.

## Purpose and practical value

A reusable controller fault-replay and timing-contract test tool, demonstrated with a simulated fluid test stand.

**Intended user:** An engineer maintaining a test-stand controller who needs to reproduce stale sensor, timeout, interlock, and recovery failures before accessing a lab.

**Job to be done:** Import an event log or plug in a Python controller, declare bounded response requirements, run a repeatable fault scenario, and inspect exactly when a requirement failed.

**Why it matters:** Many controller bugs concern ordering and elapsed time rather than steady-state values. A reproducible trace with an independent monitor can turn an intermittent failure into a regression test. It fits Walter's automation, motion-control, and fault-handling experience.

## Existing tools and the proposed contribution

OpenHTF already provides hardware test phases, measurements, plugs, and records. labgrid provides board control and pytest integration; Toxiproxy injects network faults; RTAMT already monitors temporal logic. These capabilities must be reused where appropriate, not described as inventions.

The proposed contribution is a small integration layer for engineering signal provenance, replay, fault schedules, and requirement-linked failure timelines that works on logs and external controllers. Generic temporal verification is not new. Confidence: medium; reusable interfaces and a second example are necessary to avoid producing only a pump simulator.

Research checked on 2026-10-04. This is a bounded comparison of public documentation and selected source code, not proof that no competing tool exists. No interviews, field deployments, or independent user adoption have been conducted. Do not claim industry validation or unique invention. A useful integration or plugin is an acceptable outcome.

- [OpenHTF](https://github.com/google/openhtf)
- [labgrid](https://labgrid.readthedocs.io/en/latest/)
- [Toxiproxy](https://github.com/Shopify/toxiproxy)
- [RTAMT temporal monitoring](https://github.com/nickovic/rtamt)

## Priorities and release policy

Must means release blocking for its stated applicability. Should is valuable but can be deferred with a written reason. Could is optional and must not delay a useful core. Won't means excluded from v1. Conditional Must requirements do not force an optional feature into the release; if that feature is enabled, its checks are mandatory.

M0 must establish a concrete gap or a useful integration before broad implementation. If the baseline already solves the chosen workflow, deliver the smallest reusable extension/examples package and document that choice. Do not pad scope to preserve the project name. Keep all required evidence and explain any revised requirement before implementing it.

Requirements are proposed engineering decisions, not discovered industry standards. The sample thresholds in SPEC.md are explicit reference-case choices. Users must be able to state their own contracts where the public interface supports them.

## Reference profiles and external inputs

The 10 ms response deadline, 200 ms freshness threshold, and recovery rules in SPEC.md belong to the fluid reference case. The public monitor takes explicitly configured bounded rules: signal range, sample age, trigger-to-command deadline, and prohibited state transition. M0 freezes their JSON schema. The second example sets its own thresholds. Receiving an out-of-order sample in a valid ordered event log is allowed and evaluated as data; a structurally unordered event log is rejected. This distinction is required for fault replay.

## Requirement register
### AB-01 — Must — M1

The plant and clock reproduce the same event sequence for a fixed configuration, seed, and fault schedule.

**Rationale:** An intermittent failure is actionable only if the inputs and event order can be reproduced.

**Acceptance:** Compare canonical JSON event hashes across two runs; exclude wall-clock metadata.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_deterministic_time.py`. **Status:** not implemented.

### AB-02 — Must — M0

Sensors carry unit, sample time, receive time, quality, and provenance separately.

**Rationale:** Unit errors and confused sampling/receipt timestamps can invalidate otherwise correct control decisions.

**Acceptance:** Delay and replay packets; verify sample age is unchanged and unit mismatch is rejected.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_measurement_contract.py`. **Status:** not implemented.

### AB-03 — Must — M0

Arming, starting, stopping, and recovery follow the specified state graph.

**Rationale:** An explicit transition table makes illegal starts and recovery paths reviewable.

**Acceptance:** Table-test every state/event pair, including illegal starts and simultaneous stop/start.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_state_transitions.py`. **Status:** not implemented.

### AB-04 — Must — M2

Stale age >200 ms and future timestamps are detected using sample time.

**Rationale:** A delayed packet must not make stale sensor data appear fresh.

**Acceptance:** Test 199, 200, 201 ms ages and future timestamps; receiving an old packet cannot reset freshness.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_freshness.py`. **Status:** not implemented.

### AB-05 — Must — M2

A detected fault commands pump off and valve open within 10 ms.

**Rationale:** A fault response needs a measurable deadline; issuing a command is distinct from reaching a physical state.

**Acceptance:** Independent event monitor measures detection-to-command latency under all fault schedules.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_safe_command_latency.py`. **Status:** not implemented.

### AB-06 — Must — M2

Reconnect cannot restart the stand and fault history remains latched.

**Rationale:** Reconnect is transport recovery, not authorization to resume a potentially hazardous process.

**Acceptance:** Disconnect during a run, reconnect, acknowledge, rearm; missing any recovery step blocks start.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_recovery_latch.py`. **Status:** not implemented.

### AB-07 — Must — M1

Expired and conflicting duplicate commands are rejected; exact duplicates are not reapplied.

**Rationale:** Delayed or repeated messages must not produce duplicate or outdated actions.

**Acceptance:** Vary expiry around 100 ms and repeat IDs with identical and changed payloads.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_command_identity.py`. **Status:** not implemented.

### AB-08 — Must — M2

All five fault types are injected deterministically and detected under their specified conditions.

**Rationale:** Each failure mode needs an independently specified onset and response.

**Acceptance:** Scenario manifest includes onset, values, expected earliest detection, and exact required response.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_fault_coverage.py`. **Status:** not implemented.

### AB-09 — Must — M2

The monitor catches six seeded controller defects without using controller implementation logic.

**Rationale:** Deliberate controller defects test the monitor rather than merely the happy-path controller.

**Acceptance:** Freshness from receive time, inverted valve command, pressure unit mismatch, unsafe reconnect, unbounded retry, and lost latch each fail.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_mutation_detection.py`. **Status:** not implemented.

### AB-10 — Must — M3

Run artifacts preserve hashes and identify interrupted runs as incomplete.

**Rationale:** A partial or corrupted trace cannot justify a successful run.

**Acceptance:** Interrupt recording, corrupt an artifact, and reproduce a completed run from its manifest.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_recording_integrity.py`. **Status:** not implemented.

### AB-11 — Must — M2

Recipe validation and randomized event sequences preserve the invariant set.

**Rationale:** Sequences expose ordering bugs that isolated state tests miss.

**Acceptance:** Reject nonfinite values and unknown units; run 1000 bounded Hypothesis sequences and store counterexamples.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_stateful_invariants.py`. **Status:** not implemented.

### AB-12 — Must — M4

Offline demo and report work without hardware or credentials and disclose the simulation boundary.

**Rationale:** An engineer should be able to inspect the timeline without building a physical stand.

**Acceptance:** Fresh-install run verifies charts, fault times, and labels; all twelve invariants have assertions.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_reproducibility.py`. **Status:** not implemented.

### AB-13 — Must — M0

Compare pytest plus RTAMT and OpenHTF against the required replay and timing workflow before introducing a new framework.

**Rationale:** The useful contribution must be integration or clearer engineering evidence, not reimplementing test execution or temporal logic.

**Acceptance:** Use one stale-input and one reconnect scenario; document installed versions, configuration, timestamp semantics, reporting gaps, and reuse choices in docs/BASELINE.md. Prefer a small adapter/recipe library if existing tools satisfy the requirements.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_baseline_artifacts.py`. **Status:** not implemented.

### AB-14 — Must — M1

Import versioned JSONL traces and CSV through an explicit column/unit map without running the bundled plant.

**Rationale:** Real engineers already have logs; requiring the pump simulator would make the tool a demonstration only.

**Acceptance:** A separately authored trace produces the same verdict through both formats. Preserve raw sample and receive times; reject ambiguous units, missing required channels, and unsupported clock relationships.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_external_trace.py`. **Status:** not implemented.

### AB-15 — Must — M2

A public Python controller adapter accepts measurements and a virtual tick and returns commands; pytest can invoke the runner without a web server.

**Rationale:** An engineer needs to test their controller, not only the bundled implementation.

**Acceptance:** A controller in a separate consumer directory runs without editing abyssbench source. Its command stream is judged by the independent monitor; no controller helper is imported into expected-value calculations.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_external_controller.py`. **Status:** not implemented.

### AB-16 — Must — M2

Temporal verdicts are pass, fail, or inconclusive and state their observation window and clock assumptions.

**Rationale:** Incomplete traces and incompatible clocks are common sources of false assurance.

**Acceptance:** A trace ending before a response deadline is inconclusive, never pass. Missing sample time cannot prove freshness. Reject unordered sequence IDs and unsupported cross-clock timestamps; check exact threshold boundaries. Streaming future-window rules remain pending until their deadlines.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_monitor_semantics.py`. **Status:** not implemented.

### AB-17 — Must — M3

Reuse the same monitor and trace interface in a second, simple thermal-controller example with stale-temperature and heater-off requirements.

**Rationale:** A second domain is a concrete test that the public abstraction is reusable rather than hard-coded to a pump.

**Acceptance:** Freeze a separate example specification with valid, violating, and incomplete traces. Configure channels and rules without changing the monitor engine or importing fluid-model code.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_second_example.py`. **Status:** not implemented.

### AB-18 — Should — M3

Provide an OpenHTF integration example and optional Parquet export after the JSONL/pytest workflow works.

**Rationale:** This helps adoption in an existing station workflow but is not needed to prove the core tool.

**Acceptance:** The integration attaches requirement verdicts and artifacts to a test record; Parquet and JSONL retain identical timestamps and units.

**Applies:** If selected after Must requirements pass **Planned evidence:** `tests/acceptance/test_openhtf_export.py`. **Status:** not implemented.

### AB-19 — Must — M2

Publish a versioned input and result schema, stable requirement IDs, public Python API, and a scriptable CLI with clear failure semantics.

**Rationale:** CI must not confuse an unsupported check or crashed evaluator with a valid result.

**Acceptance:** For normal check commands: exit 0 only when every applicable required check passes; exit 1 for violations; exit 2 for invalid, incomplete, unsupported, or failed execution. Results preserve individual pass/fail/inconclusive/not_applicable states. The demo command separately verifies its expected negative cases. Unknown schema versions are rejected.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_public_contract.py`. **Status:** not implemented.

### AB-20 — Must — M4

Declare resource limits and measure repeatable performance for the supported workload in the pinned environment.

**Rationale:** A tool that hangs or silently drops large input cannot be trusted in an engineering workflow.

**Acceptance:** During M0 freeze input-size/case limits and a target runtime with machine details. M4 records actual elapsed time and peak memory; an oversized input or elapsed-time limit produces a bounded error and incomplete result. CAD work runs in a killable worker. Compare against the baseline; do not claim universal performance.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_resource_limits.py`. **Status:** not implemented.

### AB-21 — Must — M4

Keep offline workflows local by default and document dependency, fixture, manual, and example licensing.

**Rationale:** Engineers must be able to inspect data handling and legally reuse the code and examples.

**Acceptance:** No credentials or telemetry are needed; the offline demo completes with egress disabled after installation. Source examples have provenance and redistributable licenses, or use a download recipe and lawful independently authored fixtures. Escape user text in HTML; reject output path traversal and avoid executing input data.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_data_and_license_boundaries.py`. **Status:** not implemented.

### AB-22 — Must — M4

Demonstrate adoption from a separate clean consumer directory using only the documented public interface.

**Rationale:** A successful bundled demo alone is not evidence that another engineer can use the tool.

**Acceptance:** Record a complete cold-start walkthrough: install, configure one non-default input, get an expected failure, correct it, and reproduce success without editing package source. Include actual commands, setup time, code/config size, and limitations versus the baseline. Label agent-executed walkthroughs as such; practitioner validation remains unverified until real feedback exists.

**Applies:** Core v1 release **Planned evidence:** `tests/acceptance/test_consumer_walkthrough.py`. **Status:** not implemented.

## Explicit scope exclusions

### AB-W01 — Won't have in v1

**A replacement for OpenHTF, labgrid, RTAMT, or a production SCADA system.** Existing projects solve those broader problems; scope is replay and engineering contracts.

Verification: Absent from the v1 supported-features list; README and reports do not claim this capability.

### AB-W02 — Won't have in v1

**A calibrated hydraulic model, digital twin, or prediction of real process performance.** The reference equations are deliberately illustrative and unvalidated.

Verification: Absent from the v1 supported-features list; README and reports do not claim this capability.

### AB-W03 — Won't have in v1

**Functional safety certification, hard real-time guarantees, or automatic control of a live stand.** Software simulation evidence does not qualify a deployed control system.

Verification: Absent from the v1 supported-features list; README and reports do not claim this capability.

### AB-W04 — Won't have in v1

**A custom temporal-logic language or theorem prover.** Start with a small explicit rule schema; evaluate existing monitoring libraries.

Verification: Absent from the v1 supported-features list; README and reports do not claim this capability.

### AB-W05 — Won't have in v1

**Distributed multi-clock reconstruction, arbitrary PLC adapters, and C++ in the first release.** These introduce separate synchronization/toolchain problems; the first external controller interface is Python.

Verification: Absent from the v1 supported-features list; README and reports do not claim this capability.

## Completion and actual usefulness

Technical readiness requires passing evidence for every applicable Must requirement, explicit dispositions for Should items, a negative-case demonstration, a clean installation, and an external consumer example. A failing or inconclusive required check blocks a successful result. All planned test paths above are future work.

Practical usefulness is a separate hypothesis. Record the baseline comparison and the consumer walkthrough, including friction and limitations. A later independent engineer using the tool on their own driver, trace, or CAD assembly would be stronger evidence. Do not contact anyone or fabricate that validation. The first release may honestly be described as a useful candidate tool with demonstrated workflows, not a field-proven industry standard.

Retain the agentic workflow: commit the contract and independent oracle before candidate repair; make small reviewable changes; inject known defects; preserve failed attempts and environment hashes. Product AI features are optional. Development history and reproducible engineering checks are the primary portfolio evidence. No pushes, deployment, paid APIs, or hardware purchases are authorized by this plan.
