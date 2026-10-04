# Local data and licensing boundary

Original application code, recipes, fixtures, consumer example and documents
use the repository MIT license (Walter Teitelbaum, 2026). Every input supplied
here is labeled synthetic and independently authored. No employer files,
measured lab data, external manuals, personal account identifiers or model
responses were imported. Public-library examples are original uses of their
documented APIs; this repository does not redistribute upstream source examples
or manuals. Primary URLs and research dates are in BASELINE.md/SOURCES.md.

The runtime reuses jsonschema (MIT), RTAMT (BSD-3-Clause), and their pinned
dependencies. The optional OpenHTF integration uses Apache-2.0 OpenHTF; it is
loaded only by the integration helper. The full development/baseline environment
also includes pytest, Hypothesis, ruff, mypy, psutil and build. Installed metadata
and license file names for every distribution are retained in
[dependency-licenses.json](../evidence/dependency-licenses.json). Wheels installed
from the package registry preserve their own notices. The inventory reports
metadata; it is not a legal opinion or a claim that missing metadata is a license.

Offline operations do not use keys, provider SDKs, requests, telemetry or
external fonts/scripts. Downloads are required for initial installation; after
installation, the demo succeeds with socket egress denied by the acceptance
test. This is an application egress test, not a hostile-code sandbox or a
machine-wide firewall claim. The optional localhost server binds 127.0.0.1,
serves read-only files, and denies resolved paths outside its artifact directory.
Reports escape user-visible text. Logs/recipes are parsed as data, never executed.

The Python adapter invokes trusted caller-supplied controller code. Do not use
it to run model-generated or otherwise untrusted code. Docker is unavailable
in this environment; generated-code isolation and all live-model campaigns
remain disabled. A killable data evaluator is a resource boundary, not a sandbox.
