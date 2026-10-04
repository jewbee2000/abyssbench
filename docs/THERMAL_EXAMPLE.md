# Independent second-domain reference (frozen separately)

An illustrative heater controller has one `temperature` measurement in degC.
This is a synthetic timing example with no thermal physics or hardware driver.
The packet sampled at 0 ms is still valid at age 75 ms. At the observation at
80 ms it is stale; heater=0 must be issued by 95 ms (inclusive 15 ms deadline).
The permitted signal range is 0..120 degC. Fault-to-heating is prohibited.

The independently authored oracle JSONL and CSV traces contain:

- `thermal-valid`: heater off at 95 ms, pass.
- `thermal-violating`: heater still on at 95 ms, fail.
- `thermal-incomplete`: trace ends at 80 ms, inconclusive.

`tests/oracle/thermal-rules.json` configures all four generic rule types.
No monitor code or fluid module is changed to support this domain. The authoring
script does not import the application. Its CSV format explicitly maps an event
envelope and a JSON payload column; sample/receive times stay separate. This is
a deliberate v1 format restriction, not an arbitrary CSV autodetector.

The clean consumer walkthrough independently uses 55 degC, a 125 ms freshness
bound, a 30 ms response bound, and 10..90 degC range. It preserves a failed trace
and changes only the commanded heater value to reproduce success.
