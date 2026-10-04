# Executed software evidence

Start with [REQUIREMENT_EVIDENCE.md](REQUIREMENT_EVIDENCE.md) for the 21 applicable Must requirements and [progress.md](progress.md) for the local milestone history and retained failures.

- [acceptance-run.json](acceptance-run.json) and [pytest-final.txt](pytest-final.txt): full independent open suite, including the 1000-example property check.
- [fresh-install-run.json](fresh-install-run.json): checks against a wheel installed in a new virtual environment.
- [baseline.json](baseline.json) and [consumer-walkthrough.json](consumer-walkthrough.json): installed-library comparison and agent-executed non-default consumer failure/correction.
- [performance.json](performance.json): three measured 10000-event repetitions, with method and comparison limits.
- [environment.json](environment.json), [dependency-licenses.json](dependency-licenses.json), [release.json](release.json): versions, licenses, source/input/oracle/lock/artifact hashes and command outcomes.
- failed-candidates/: six actual seeded controller failures. Files containing first-failure, before, or first-tests retain earlier unsuccessful checks; they are history, not current passing evidence.
- [stuck-valve-report.png](stuck-valve-report.png) and blog preview images: inspected output, with command and actuator behavior distinct.

All signals are synthetic. No physical validation, live model campaign or practitioner adoption occurred. The article remains unpublished. Command issuance and simulation timing do not prove physical response. Unknown campaign cost/token values are not represented as fabricated measurements.
