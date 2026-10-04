# AbyssBench specification

Status: refined proposal; M0 baseline comparison is pending. No implementation or benchmark results are claimed. Read [REQUIREMENTS.md](REQUIREMENTS.md) first for priorities, rationale, external-user interfaces, and release gates.


## Scope and physical model

Model one pump feeding a compliant chamber through one controllable outlet valve, with two pressure channels and an outlet flow channel. This is an educational lumped model, not validated hydraulic analysis, a digital twin, subsea qualification, or a functional safety system.

Use milliseconds for integer simulation time and SI units inside the model. Proposed reference defaults: dt = 10 ms, chamber compliance C = 1e-8 m³/Pa, pump conductance Gp = 1e-10 m³/(s Pa), maximum pump head Pmax = 300000 Pa, pump time constant 100 ms, and valve time constant 200 ms. Inputs u_pump and u_valve are in [0,1]. Update actuator states with an explicit first-order lag. Define Q_in = Gp × max(Pmax × pump_state - P, 0), Q_out = K × valve_state × sqrt(max(P,0)/P_ref), and dP/dt = (Q_in - Q_out)/C, with K = 2e-5 m³/s and P_ref = 100000 Pa. This is an illustrative orifice-like approximation with explicit units, not a calibrated valve coefficient. Use the updated actuator states and current pressure to compute flows, then a forward Euler pressure update with dt expressed in seconds. Clamp pressure at zero and record any clamp as a numerical event; reject nonfinite state.

Pressure channel 1 measures chamber P; pressure channel 2 measures 0.98P in the reference model; flow measures Q_out. Default measurement noise is zero. Any optional noise uses a recorded seed. No external measured data are implied. Validate dimensional consistency, zero-input equilibrium, and dt-convergence behavior before freezing the reference traces.

The plant integrates at 10 ms and publishes sensor samples every 50 ms. The reference controller ticks every 10 ms. Use sample timestamps from the simulator's monotonic clock; receive time is separate. A pressure or flow sample is stale when age is greater than 200 ms, invalid when quality is not good, and rejected if its timestamp is in the future. A controller cannot refresh an old measurement simply by receiving it again.

## State and command contract

States are disconnected, ready, armed, running, fault, and recovery_required. Startup commands pump off and outlet valve open. Ready requires connection and all required fresh, valid sensors. Arming requires an explicit command. Running requires a valid recipe, fresh measurements, and no latched fault. Fault transitions command pump off and outlet open within one controller tick of detection. These are simulation requirements only; a stuck actuator may prevent the commanded state from being physically reached.

Overpressure threshold is 200000 Pa. Missing heartbeat for more than 300 ms, stale input, invalid quality, out-of-range pressure, command expiry, disconnect, and actuator mismatch all latch fault. Actuator mismatch means absolute measured versus commanded valve fraction greater than 0.2 for more than 500 ms; initial transition grace is exactly 500 ms. A delayed command expires 100 ms after its issue timestamp. Duplicate command IDs return the previous outcome without reapplying an action; conflicting duplicate payloads are rejected.

Reconnect moves to recovery_required, never directly to running. Recovery requires valid inputs and no active fault cause continuously for 1000 ms, explicit acknowledgment of the old fault, then a separate arm and start. Fault history survives reconnect. A stop request always has priority over a start request at the same tick. A watchdog can command safe outputs but cannot claim to fix a mechanically stuck valve.

## Independent monitor invariants

The monitor must implement these twelve control assertions in addition to the broader acceptance requirements below. Evaluate them from event records without controller helper functions.

1. Running is entered only from armed after an explicit valid start.
2. Running cannot persist beyond one controller tick after any required input becomes invalid, pressure exceeds 200000 Pa, or a pressure reading falls outside 0–300000 Pa.
3. Freshness uses sample time; age exactly 200 ms is valid, age greater than 200 ms is stale, and future timestamps are invalid.
4. Every detected fault is followed by a pump-off command within 10 ms.
5. Every detected fault is followed by an outlet-open command within 10 ms, regardless of whether the valve actually moves.
6. Reconnection never transitions directly to running.
7. The previous fault remains in the event history; recovery requires 1000 ms of valid inputs, acknowledgment, rearm, and a separate start.
8. Heartbeat age greater than 300 ms latches a fault by the next controller tick.
9. Exact duplicate command IDs are applied at most once; a changed payload under an existing ID is rejected.
10. A command is valid through its expiry timestamp and rejected when the controller time is greater than expires_at_ms. Test issue+99, +100, and +101 ms for the standard 100 ms lifetime.
11. Stop wins over start when both occur at the same tick.
12. A valve position error greater than 0.2 lasting more than 500 ms latches a fault; equality at either boundary does not trigger that rule.

## Typed inputs and durable outputs

Measurement fields: channel, value, unit, sample_time_ms, receive_time_ms, quality, sequence, calibration_id (synthetic identity). Command fields: command_id, type, payload, issued_at_ms, expires_at_ms. Recipe: version, preconditions, ordered steps, durations, setpoints, stop conditions, and maximum duration. Reject incompatible units and unknown recipe fields.

Proposed modules: plant/, clock/, controller/, recipes/, fault_injection/, monitor/, recording/, api/, report/. Separate the monitor from controller logic. The monitor consumes the raw event stream and applies the frozen requirements. Do not import controller helpers into expected-value calculations.

Run manifests contain code commit, dirty-tree flag and diff hash, model parameters, recipe hash, seed, event schema version, controller version, oracle hash, and artifact hashes. Write event records durably using a temp-and-rename manifest at completion; mark interrupted runs incomplete. Do not silently report success after an interrupted writer. Optional Parquet rows keep integer timestamps and SI units; a human report may show kPa and L/min explicitly.

## Demonstration contract

Target command: `python -m abyssbench demo --offline --output artifacts/demo`. It runs healthy, stale-sensor, and stuck-valve scenarios, exports JSONL event records (Parquet is a Should feature), verdicts.json, manifest.json, and report.html. Exit 0 means expected healthy behavior and expected fault detection both occurred; an unexpected invariant breach exits nonzero. `python -m abyssbench serve artifacts/demo` later serves read-only charts and event details on localhost.

The report plots pressure, flow, commands, and controller state against simulation time, with marked detection and safe-command times. Show the distinction between issuing a safe command and an actuator actually responding. Compare controller versions on identical fault schedules.

## Fault set and boundaries

Inject sensor freeze, disconnect, out-of-range reading, valve stuck, and delayed/out-of-order delivery. Test boundary timestamps, simultaneous stop/start, and recovery sequences. Stress one thousand short randomized event sequences, then retain minimal failing examples. Optional C++ reuses the protocol contract and is tested against the same independent monitor. Full industrial PLC support, autonomous tuning, hardware control, and live fault injection on a real machine are out of scope.

## Public interface applicability

The 10 ms response deadline, 200 ms freshness threshold, and recovery rules in SPEC.md belong to the fluid reference case. The public monitor takes explicitly configured bounded rules: signal range, sample age, trigger-to-command deadline, and prohibited state transition. M0 freezes their JSON schema. The second example sets its own thresholds. Receiving an out-of-order sample in a valid ordered event log is allowed and evaluated as data; a structurally unordered event log is rejected. This distinction is required for fault replay.

## Acceptance requirements

The authoritative rationale, applicability, and independent acceptance evidence for these requirements are in [REQUIREMENTS.md](REQUIREMENTS.md). Reference-case behavior above does not replace the public-interface requirements.

| ID | Priority | Milestone | Requirement |
| --- | --- | --- | --- |
| AB-01 | must | M1 | The plant and clock reproduce the same event sequence for a fixed configuration, seed, and fault schedule. |
| AB-02 | must | M0 | Sensors carry unit, sample time, receive time, quality, and provenance separately. |
| AB-03 | must | M0 | Arming, starting, stopping, and recovery follow the specified state graph. |
| AB-04 | must | M2 | Stale age >200 ms and future timestamps are detected using sample time. |
| AB-05 | must | M2 | A detected fault commands pump off and valve open within 10 ms. |
| AB-06 | must | M2 | Reconnect cannot restart the stand and fault history remains latched. |
| AB-07 | must | M1 | Expired and conflicting duplicate commands are rejected; exact duplicates are not reapplied. |
| AB-08 | must | M2 | All five fault types are injected deterministically and detected under their specified conditions. |
| AB-09 | must | M2 | The monitor catches six seeded controller defects without using controller implementation logic. |
| AB-10 | must | M3 | Run artifacts preserve hashes and identify interrupted runs as incomplete. |
| AB-11 | must | M2 | Recipe validation and randomized event sequences preserve the invariant set. |
| AB-12 | must | M4 | Offline demo and report work without hardware or credentials and disclose the simulation boundary. |
| AB-13 | must | M0 | Compare pytest plus RTAMT and OpenHTF against the required replay and timing workflow before introducing a new framework. |
| AB-14 | must | M1 | Import versioned JSONL traces and CSV through an explicit column/unit map without running the bundled plant. |
| AB-15 | must | M2 | A public Python controller adapter accepts measurements and a virtual tick and returns commands; pytest can invoke the runner without a web server. |
| AB-16 | must | M2 | Temporal verdicts are pass, fail, or inconclusive and state their observation window and clock assumptions. |
| AB-17 | must | M3 | Reuse the same monitor and trace interface in a second, simple thermal-controller example with stale-temperature and heater-off requirements. |
| AB-18 | should | M3 | Provide an OpenHTF integration example and optional Parquet export after the JSONL/pytest workflow works. |
| AB-19 | must | M2 | Publish a versioned input and result schema, stable requirement IDs, public Python API, and a scriptable CLI with clear failure semantics. |
| AB-20 | must | M4 | Declare resource limits and measure repeatable performance for the supported workload in the pinned environment. |
| AB-21 | must | M4 | Keep offline workflows local by default and document dependency, fixture, manual, and example licensing. |
| AB-22 | must | M4 | Demonstrate adoption from a separate clean consumer directory using only the documented public interface. |
