# Implementation tasks

Check off only after recording executed evidence; see evidence/progress.md.

- [x] M0 — Compare baselines and freeze temporal semantics. Gate: A small reproducible scenario establishes what the package adds; all twelve reference invariants have independent expectations.
- [x] M1 — Replay a trace and one healthy stand run. Gate: A user-supplied trace is checked without the plant; a healthy reference run is deterministic.
- [x] M2 — Test external controllers and fault behavior. Gate: All deliberate defects are caught; incomplete evidence is inconclusive and faults produce measured command latency.
- [x] M3 — Prove reuse and make timelines readable. Gate: The second example uses the same engine; reports identify cause, observation window, detection, commands, and limitations.
- [x] M4 — Verify adoption and prepare the local release. Gate: Every applicable Must requirement has evidence; simulation and physical behavior remain explicitly separate. Consumer workflow is agent-executed; practitioner adoption is unverified.

- [x] Record dispositions for every Should/Could item and verify Won't claims remain excluded. AB-18 OpenHTF attachment passes; Parquet deferred because JSONL preserves required data. No Could item is selected. AB-W01–W05 remain excluded, as do conditional live-model/CAD features.
- [x] Complete the independent consumer walkthrough and compare its cost with the baseline. Fresh wheel, non-default thermal rules and public Python controller pass; 48.80 s measured setup/workflow with warmed package cache. Baseline comparison establishes integration effort without a human-effort or speedup claim.

Final checks: 116 full-suite passes (including 1000 configured Hypothesis examples), 115 installed-wheel passes with that property test deselected, Ruff, mypy and pip check. Commands, hashes, preserved failures and limitations are linked in evidence/REQUIREMENT_EVIDENCE.md.

See IMPLEMENTATION_PLAN.md and docs/REQUIREMENTS.md.

## Follow-up after source publication

- [x] Push the project source with Walter's explicit authorization; verified public origin/main, website draft unchanged. See evidence/github-publication.json.
- [ ] Add Windows/Python 3.12 GitHub Actions for the verified local checks and wheel/demo artifacts.
- [ ] Replay one useful external trace with an independently specified expected verdict.
- [ ] Record one independent engineer's fresh-checkout trial and actual feedback.
- [ ] Fix friction demonstrated by that trial, then assess Linux support and a tagged wheel release.
- [ ] Complete Walter's article review and verified-link update; publish only on a later explicit instruction.

Walter's exact actions and suggested trial request are in docs/NEXT_STEPS.md.

## Separate publication audit

Two uncovered generic-monitor cases were fixed after the initial release: singleton numerical input and response ordering within one timestamp. Eight new literal regressions preserve their pre-fix failures. Current suite: 124 passes; fresh wheel: 123 passes with one property test deselected. See evidence/publication-audit/README.md; initial evidence is retained unchanged.
