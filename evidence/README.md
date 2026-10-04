# Evidence directory

No application or live-model runs have been performed yet. This directory will contain real manifests, selected failures, and reports as implementation proceeds.

Each manifest must identify run mode (deterministic, replay, live), source commit, dirty diff hash if any, requirement IDs, input and oracle hashes, environment versions, commands, exit codes, artifacts, and limitations. Live runs additionally record actual model/provider, attempts, tokens when available, time, budget, and costs when known. Preserve unavailable values as null; never replace them with invented zeros.
