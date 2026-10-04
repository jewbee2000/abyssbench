# Implementation tasks

Check off only after recording executed evidence; see evidence/progress.md.

- [x] M0 — Compare baselines and freeze temporal semantics. Gate: A small reproducible scenario establishes what the package adds; all twelve reference invariants have independent expectations.
- [x] M1 — Replay a trace and one healthy stand run. Gate: A user-supplied trace is checked without the plant; a healthy reference run is deterministic.
- [x] M2 — Test external controllers and fault behavior. Gate: All deliberate defects are caught; incomplete evidence is inconclusive and faults produce measured command latency.
- [x] M3 — Prove reuse and make timelines readable. Gate: The second example uses the same engine; reports identify cause, observation window, detection, commands, and limitations.
- [ ] M4 — Verify adoption and prepare the local release. Gate: Every applicable Must requirement has evidence; simulation and physical behavior remain explicitly separate.

- [ ] Record dispositions for every Should/Could item and verify Won't claims remain excluded.
- [ ] Complete the independent consumer walkthrough and compare its cost with the baseline.

See IMPLEMENTATION_PLAN.md and docs/REQUIREMENTS.md.
