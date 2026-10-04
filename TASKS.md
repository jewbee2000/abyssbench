# Implementation tasks

All tasks below are unstarted. The preparation commit contains specifications and editorial drafts, not application code.

- [ ] M0 — Freeze the simulator assumptions. Evidence: Hand calculations and a zero-input equilibrium check agree; example traces define boundary behavior.
- [ ] M1 — Build one healthy test run. Evidence: Healthy run reproduces exactly and responds to an explicit stop.
- [ ] M2 — Build the independent monitor and fault suite. Evidence: Every critical mutation is caught and fault command latency is measured.
- [ ] M3 — Add report and bounded repair experiment. Evidence: Same schedule compares bad and repaired controller; a patch that disables checks is rejected.
- [ ] M4 — Prepare a reproducible portfolio release. Evidence: Every requirement has evidence; public claims explicitly cover only simulated behavior.

Update this file only after checking the milestone evidence. See IMPLEMENTATION_PLAN.md for dependencies and estimates.
