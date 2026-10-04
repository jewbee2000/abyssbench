# Acceptance and evidence plan

Status: test design only; no application tests have run. Read [REQUIREMENTS.md](REQUIREMENTS.md) for the full prioritized register, rationale, applicability, and acceptance criteria, and [SPEC.md](SPEC.md) for the reference-case contracts. [requirements.json](../requirements.json) provides planned test paths. Avoid a second independently edited requirements table.

## Required layers

1. M0 baseline comparison establishes the useful contribution and selects existing libraries.
2. Independent contract checks cover units, boundary equality, missing/invalid data, and lifecycle behavior.
3. Integration checks exercise externally supplied inputs or a consumer package through public interfaces.
4. Known defects and negative cases verify that the oracle catches the intended errors.
5. End-to-end checks verify CLI outcomes, reports, export integrity, installation, resource bounds, and local data handling.

Do not compute expected values with implementation helpers. Keep a separate oracle commit before optional generation or repair experiments. Test counts are coverage inventories, not quality scores.

## Release evidence

Every applicable Must requirement needs executed evidence, not a planned test path. Record command, environment/lockfile hash, input hash, source commit and dirty state, oracle hash, requirement ID, exit code, artifact hash, and outcome. A required failure or inconclusive result blocks a successful release check. Conditional requirements may be not applicable only with the disabled feature and reason documented. Explicitly record deferred Should/Could items and all exclusions.

Run meaningful lint, type, property, integration, mutation, and fresh-install checks appropriate to the implementation. Add CI only after its commands work locally. Separate implementation verification, simulation evidence, physical measurement, practitioner feedback, and live model evaluation. A bundled demo or an agent walkthrough is not proof of industry adoption.
