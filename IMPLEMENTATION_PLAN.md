# AbyssBench implementation plan

Revised 2026-10-04. Begin with [requirements and rationale](docs/REQUIREMENTS.md). The previous all-features-at-once plan is superseded by this useful-core-first sequence. Application implementation has not started.

## Purpose and feasibility

A reusable controller fault-replay and timing-contract test tool, demonstrated with a simulated fluid test stand. Many controller bugs concern ordering and elapsed time rather than steady-state values. A reproducible trace with an independent monitor can turn an intermittent failure into a regression test. It fits Walter's automation, motion-control, and fault-handling experience.

The proposed contribution is a small integration layer for engineering signal provenance, replay, fault schedules, and requirement-linked failure timelines that works on logs and external controllers. Generic temporal verification is not new. Confidence: medium; reusable interfaces and a second example are necessary to avoid producing only a pump simulator.

75–115 engineering hours as a planning range, to revise after M0. Python and static reports are the first release; external traces and a second example take priority over C++ or live AI experiments.

Core software can be built with minimal owner guidance, but novelty and adoption are not established. Use existing libraries and routine design judgment. Do not require physical measurements to finish a software release; do not claim those measurements occurred.

## Build sequence

### M0 Compare baselines and freeze temporal semantics

Work: Evaluate the existing-tool baseline; define trace schema, rule semantics, threshold equality, observation windows, and clock policy. Check fluid equation units and reference traces.

Exit evidence: A small reproducible scenario establishes what the package adds; all twelve reference invariants have independent expectations.

Primary requirements: AB-02 AB-03 AB-13. All earlier contracts remain regression requirements.

### M1 Replay a trace and one healthy stand run

Work: Build a virtual clock, JSONL/CSV import, plant example, and raw event recorder before UI work.

Exit evidence: A user-supplied trace is checked without the plant; a healthy reference run is deterministic.

Primary requirements: AB-01 AB-07 AB-14. All earlier contracts remain regression requirements.

### M2 Test external controllers and fault behavior

Work: Add public Python/pytest adapters, fault scheduling, independent monitor, six defects, and stateful sequences.

Exit evidence: All deliberate defects are caught; incomplete evidence is inconclusive and faults produce measured command latency.

Primary requirements: AB-04 AB-05 AB-06 AB-08 AB-09 AB-11 AB-15 AB-16 AB-19. All earlier contracts remain regression requirements.

### M3 Prove reuse and make timelines readable

Work: Build the independent thermal example and HTML timelines. Add OpenHTF/Parquet only after core behavior passes.

Exit evidence: The second example uses the same engine; reports identify cause, observation window, detection, commands, and limitations.

Primary requirements: AB-10 AB-17 AB-18. All earlier contracts remain regression requirements.

### M4 Verify adoption and prepare the local release

Work: Run fresh-install checks, deterministic replay, interrupted-log recovery, resource tests, lint/types/tests, and the consumer walkthrough. Update the blog from actual results.

Exit evidence: Every applicable Must requirement has evidence; simulation and physical behavior remain explicitly separate.

Primary requirements: AB-12 AB-20 AB-21 AB-22. All earlier contracts remain regression requirements.

## Method and dependencies

Use Python with a repository-local pinned environment; select compatible versions during M0. Read SPEC.md for existing reference-case constants. Requirements proceed M0 → M1 → M2 → M3 → M4; the machine-readable register identifies primary milestones and baseline dependencies. Tests and documentation evolve with each slice rather than accumulating at the end.

For every nontrivial feature: state the requirement, write an independent failing check, implement the smallest slice, inspect actual output, record evidence, and commit locally. Preserve known failures and explain repairs. A product model, elaborate UI, web service, or paid API is not needed for the useful first release. Reuse primary-source libraries after verifying current installation and capabilities.

## Model evaluation after the deterministic release


Use six seeded defects × three fresh trials for one-shot repair and six × three for bounded repair: 36 live trials in total, with a deterministic scripted-patch baseline reported separately. Require the independent monitor to catch all six defects. A target such as repairing four of six defect classes is an experiment goal, not a release requirement or observed result. Record any repair that changes the oracle as invalid. The core project remains useful if no live model campaign is run.

The evaluator's inputs are frozen before the campaign. One-shot and repair runs use the same budgets except for the explicitly reported repair allowance. Capture all attempts; do not discard unsuccessful trials. Separate a replay demonstration from a live model evaluation. These comparisons are project-local experiments, not claims about every AI model or engineering task.

## Risks and decision rules

The largest product risk is duplicating existing software or building a demonstration that accepts only its own fixtures. The M0 comparison and M4 independent consumer walkthrough are release gates. Prefer a narrow library/plugin when it satisfies the same needs. Do not silently drop external integration in order to finish a more impressive-looking demo.

If a technical dependency or required semantic cannot be implemented, record it as blocked or unsupported and do not label the release complete. If the entire useful contribution disappears after the baseline comparison, stop broad implementation and report the concrete result; do not invent novelty or ask for routine design approvals.

## Owner involvement and publication

No owner guidance is needed for routine architecture, naming, examples, or tests within these requirements. Physical tests, paid live model campaigns, and remote publication require separate resources or authorization. Do not contact maintainers or prospective users automatically. No pushes, deployment, or remote commits. Local commits are authorized.

## Definition of finished

All applicable Must requirements have independent executed evidence. Should/Could omissions and Won't scope are explicit. A clean consumer walkthrough works on a non-default input, and reports show a real detected failure and repair. The first-person article is updated only from observed work, remains unpublished, and has no invented anecdotes, physical measurements, or live-model scores. Hosted repositories and website publication remain pending a later instruction.
