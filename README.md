# AbyssBench

A reusable controller fault-replay and timing-contract test tool, demonstrated with a simulated fluid test stand.

**Status: refined planning repository; implementation has not started.** Start with [requirements and rationale](docs/REQUIREMENTS.md), then [START_HERE.md](START_HERE.md) and the [implementation plan](IMPLEMENTATION_PLAN.md).

Many controller bugs concern ordering and elapsed time rather than steady-state values. A reproducible trace with an independent monitor can turn an intermittent failure into a regression test. It fits Walter's automation, motion-control, and fault-handling experience.

Existing tools already cover parts of this problem. M0 must compare them and establish a useful addition or integration. The plan makes no claim of unique invention or practitioner adoption. All software and engineering validation remain pending.

The first release must work without hardware or model credentials. Live AI experiments and physical tests are separate. Commits stay local; publication is not authorized.
