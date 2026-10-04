# AbyssBench

A simulated fluid test stand that makes timing and recovery failures reproducible.

**Status: planned; implementation has not started.** This repository contains the requirements, execution plan, acceptance design, and blog draft for an agent-assisted engineering project. It does not yet contain working application code or benchmark results.

Start with [START_HERE.md](START_HERE.md). The [implementation plan](IMPLEMENTATION_PLAN.md) defines the build and [specification](docs/SPEC.md) defines what must be proven.

The intended demonstration: Run the same recipe against a healthy stand, a frozen pressure reading, and a stuck valve. Compare deterministic timelines. A deliberately faulty controller treats a delayed packet as fresh, is caught by the independent monitor, and is repaired without disabling the alarm.

The final release must run offline without hardware or a model key. Live AI evaluations and physical validation, where applicable, are separate and explicitly labeled.
