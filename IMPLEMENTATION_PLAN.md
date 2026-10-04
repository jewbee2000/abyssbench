# AbyssBench implementation plan

## Purpose and feasibility

A simulated fluid test stand that makes timing and recovery failures reproducible.

Walter has commissioned test automation, worked with motion-control fault handling, and built mechatronic systems. A simulated fluid stand extends those interests into an inspectable systems project. The public story is about testing machines, not about a particular employer or energy company.

High for a software-in-the-loop test stand; medium for the optional C++ controller and low without owner involvement for real hardware commissioning. Start with a Python reference controller and virtual clock. Add C++ only after the simulator and invariant suite work.

75–110 engineering hours for the original cross-language scope. A Python-only first release reduces environment risk but is still a substantial systems project. Optional owner review: 45–90 minutes across behavior and final demo; no hardware or domain calibration is required for synthetic tests.

## The result a visitor should see

Run the same recipe against a healthy stand, a frozen pressure reading, and a stuck valve. Compare deterministic timelines. A deliberately faulty controller treats a delayed packet as fresh, is caught by the independent monitor, and is repaired without disabling the alarm.

## Technical approach

Python 3.12, Pydantic, NumPy, pytest, Hypothesis, Typer, FastAPI, simple browser charts, Parquet via PyArrow. Use an in-process virtual clock. Optional C++20 controller over newline-delimited JSON with CMake after a compiler spike. No PLC, cloud service, real networked plant, or physical pump is required.

The public repository must be useful without live AI. The strongest evidence is a requirement that becomes an independent check, a candidate that fails it, and a justified repair. Do not turn the project into a generic chat interface. Retain the original research's specification, verification, and bounded repair approach while narrowing the first release to something one coding agent can complete.

## M0 Freeze the simulator assumptions

Work: Validate equation units, reference defaults, state/event matrix, timing boundaries, schemas, and requirements. Lock a minimal Python environment.

Exit evidence: Hand calculations and a zero-input equilibrium check agree; example traces define boundary behavior.

Requirements: AB-01 AB-02 AB-03. Planning estimate: 10–15 h.


## M1 Build one healthy test run

Work: Implement virtual clock, plant, Python controller, one recipe, and raw event export before any UI.

Exit evidence: Healthy run reproduces exactly and responds to an explicit stop.

Requirements: AB-01 AB-02 AB-03 AB-07. Planning estimate: 18–25 h.


## M2 Build the independent monitor and fault suite

Work: Author invariants, five injectors, six deliberate defects, randomized sequences, and recovery boundary cases.

Exit evidence: Every critical mutation is caught and fault command latency is measured.

Requirements: AB-04 AB-05 AB-06 AB-08 AB-09 AB-11. Planning estimate: 18–25 h.


## M3 Add report and bounded repair experiment

Work: Create comparison charts and evidence browser. Build replay-based repair tasks; optionally add C++ after compiler availability is confirmed.

Exit evidence: Same schedule compares bad and repaired controller; a patch that disables checks is rejected.

Requirements: AB-09 AB-10 AB-12. Planning estimate: 15–25 h.


## M4 Prepare a reproducible portfolio release

Work: Finish provenance, interruption tests, one-command demo, fresh-install checks, README, and blog.

Exit evidence: Every requirement has evidence; public claims explicitly cover only simulated behavior.

Requirements: AB-01 AB-10 AB-12. Planning estimate: 14–20 h.


## Model evaluation after the deterministic release

Use six seeded defects × three fresh trials for one-shot repair and six × three for bounded repair: 36 live trials in total, with a deterministic scripted-patch baseline reported separately. Require the independent monitor to catch all six defects. A target such as repairing four of six defect classes is an experiment goal, not a release requirement or observed result. Record any repair that changes the oracle as invalid. The core project remains useful if no live model campaign is run.

The evaluator's inputs are frozen before the campaign. One-shot and repair runs use the same budgets except for the explicitly reported repair allowance. Capture all attempts; do not discard unsuccessful trials. Separate a replay demonstration from a live model evaluation. These comparisons are project-local experiments, not claims about every AI model or engineering task.

## Risks and fallback decisions

Simulation can create impressive-looking graphs without engineering substance. The antidote is explicit equations, dimensional checks, clock-boundary cases, a separate monitor, and claims limited to specified behavior. A passing simulation does not qualify real hardware. If the C++ toolchain or UI consumes disproportionate effort, ship the tested Python controller and static report first; record that scope decision.

## Owner involvement

No response from Walter is needed for routine naming, data models, fixtures, UI choices, or test implementation within this specification. The agent can define missing synthetic examples and document assumptions. Ask only when a decision would materially change the project's claim or exceed the authorized environment. An optional final review of the first-person article would improve the voice; no invented memory or measured result should be used to avoid that review.

Before any live API campaign, a model adapter, credential, and spending ceiling are needed. None is required for the deterministic product or replay. Physical validation requires Walter to perform or arrange the measurement. Remote publication requires a later instruction because the present instruction forbids pushes.

## Definition of finished

All required behaviors in docs/SPEC.md have independent evidence. The README gives a working fresh-clone setup and offline demo. Artifacts are real, versioned, and labeled by scope. The code, tests, environment lockfile, architecture, evidence, and article are locally committed. A future publication step creates or selects the GitHub repository, pushes the reviewed commits, verifies public links, then publishes the matching website article. Until that later step, remote GitHub and live-site completion remain pending.
