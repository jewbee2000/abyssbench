# Frozen v1 decisions (M0)

This is a small Python/pytest recipe and replay library, not a new test framework.
Integer milliseconds on one monotonic clock (`simulation`) are required. Events
have contiguous sequence IDs starting at 0, nondecreasing event time, schema
version 1, kind, and data. Packet sequence/sample times may go backwards inside
an ordered event log. Receipt never changes sample age. Missing sample time gives
inconclusive evidence; incompatible clocks and units give invalid input.

Rule types are range, sample_age, response, and transition. Thresholds are
inclusive; stale is strictly greater than the configured maximum. Invalid signal
rules may specify a bounded safe command response instead of rejecting the
presence of a deliberately injected fault. Response endpoints are inclusive.
Future obligations stay inconclusive until satisfied or their deadline is
observed. Closed observation windows never extrapolate beyond the last event.
Empty observations and missing required channels cannot pass. A streaming prefix
uses the same finite-window semantics. No distributed clock reconstruction.

The fluid profile additionally checks the twelve SPEC invariants from raw
measurements, requests, commands, state, heartbeat and actuator observations;
it does not import controller logic. RTAMT provides numeric predicates, while
identity, provenance, latching and finite-window evidence are explicit Python.
Each applicable invariant is returned even if vacuously satisfied; details
identify triggers, deadlines, observed responses, and missing evidence.

Reference decisions: disconnect while armed commands safe and returns
disconnected; disconnect while running latches fault. Initial unconnected state
does not latch. Reconnect after a fault enters recovery_required. Ack requires
1000 ms of continuously healthy inputs and connection. Ack returns ready;
arm and start must then be separate ticks. Stop disarms to ready. Invalid or
expired user commands latch a fault; conflicting IDs are rejected without action.
Heartbeat is an independent received event. Valve feedback is synthetic fraction
in [0,1]. Recipe v1 is finite and strict; no expression execution.

Limits frozen before implementation: 20 MiB, 100000 events, 60 seconds trace
evaluation wall time, 32 demo cases, 60000 ms simulated duration. Performance
target: check a 10000-event trace in <10 seconds and <256 MiB RSS on this Windows
machine (i9-11900H, 8 cores / 16 threads, 64 GiB RAM). These are local targets,
not universal guarantees. Trusted consumer controller callbacks are caller code;
untrusted generated code is disabled. No CAD work exists in this fluid scope
(the CAD-worker sentence in AB-20 is inapplicable). Model campaigns are optional
and disabled; no sandbox is inferred from a subprocess or worktree.
