# AbyssBench specification

Status: implementation-ready proposal. No implementation or benchmark results are claimed.


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

Run manifests contain code commit, dirty-tree flag and diff hash, model parameters, recipe hash, seed, event schema version, controller version, oracle hash, and artifact hashes. Write event records durably using a temp-and-rename manifest at completion; mark interrupted runs incomplete. Do not silently report success after an interrupted writer. Parquet rows keep integer timestamps and SI units; a human report may show kPa and L/min explicitly.

## Demonstration contract

Target command: `python -m abyssbench demo --offline --output artifacts/demo`. It runs healthy, stale-sensor, and stuck-valve scenarios, exports events.parquet plus JSON event records, verdicts.json, manifest.json, and report.html. Exit 0 means expected healthy behavior and expected fault detection both occurred; an unexpected invariant breach exits nonzero. `python -m abyssbench serve artifacts/demo` later serves read-only charts and event details on localhost.

The report plots pressure, flow, commands, and controller state against simulation time, with marked detection and safe-command times. Show the distinction between issuing a safe command and an actuator actually responding. Compare controller versions on identical fault schedules.

## Fault set and boundaries

Inject sensor freeze, disconnect, out-of-range reading, valve stuck, and delayed/out-of-order delivery. Test boundary timestamps, simultaneous stop/start, and recovery sequences. Stress one thousand short randomized event sequences, then retain minimal failing examples. Optional C++ reuses the protocol contract and is tested against the same independent monitor. Full industrial PLC support, autonomous tuning, hardware control, and live fault injection on a real machine are out of scope.

## Acceptance requirements

| ID | Required behavior | Independent acceptance evidence |
| --- | --- | --- |
| AB-01 | The plant and clock reproduce the same event sequence for a fixed configuration, seed, and fault schedule. | Compare canonical JSON event hashes across two runs; exclude wall-clock metadata. |
| AB-02 | Sensors carry unit, sample time, receive time, quality, and provenance separately. | Delay and replay packets; verify sample age is unchanged and unit mismatch is rejected. |
| AB-03 | Arming, starting, stopping, and recovery follow the specified state graph. | Table-test every state/event pair, including illegal starts and simultaneous stop/start. |
| AB-04 | Stale age >200 ms and future timestamps are detected using sample time. | Test 199, 200, 201 ms ages and future timestamps; receiving an old packet cannot reset freshness. |
| AB-05 | A detected fault commands pump off and valve open within 10 ms. | Independent event monitor measures detection-to-command latency under all fault schedules. |
| AB-06 | Reconnect cannot restart the stand and fault history remains latched. | Disconnect during a run, reconnect, acknowledge, rearm; missing any recovery step blocks start. |
| AB-07 | Expired and conflicting duplicate commands are rejected; exact duplicates are not reapplied. | Vary expiry around 100 ms and repeat IDs with identical and changed payloads. |
| AB-08 | All five fault types are injected deterministically and detected under their specified conditions. | Scenario manifest includes onset, values, expected earliest detection, and exact required response. |
| AB-09 | The monitor catches six seeded controller defects without using controller implementation logic. | Freshness from receive time, inverted valve command, pressure unit mismatch, unsafe reconnect, unbounded retry, and lost latch each fail. |
| AB-10 | Run artifacts preserve hashes and identify interrupted runs as incomplete. | Interrupt recording, corrupt an artifact, and reproduce a completed run from its manifest. |
| AB-11 | Recipe validation and randomized event sequences preserve the invariant set. | Reject nonfinite values and unknown units; run 1000 bounded Hypothesis sequences and store counterexamples. |
| AB-12 | Offline demo and report work without hardware or credentials and disclose the simulation boundary. | Fresh-install run verifies charts, fault times, and labels; all twelve invariants have assertions. |
