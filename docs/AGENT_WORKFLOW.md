# Agent development and evaluation workflow

The central portfolio claim is that Walter can direct an agent through an engineering problem and judge the result against requirements. A chatbot interface is not required. Each project first needs useful deterministic software; optional model-driven generation or repair comes afterward.

## Development loop

1. Read START_HERE.md, the specification, and the next incomplete task. Record assumptions and map the task to requirement IDs before coding.
2. Build the acceptance oracle first from the written contract. Include a hand-calculated example. Commit it separately. The oracle must not call the production implementation to obtain its expected answers.
3. Implement one vertical slice, run its relevant checks, inspect the resulting artifact, and repair failures. Use at most three consecutive attempts at the same approach; after that, diagnose and change the approach rather than repeating a prompt.
4. Review the diff against the specification in a separate pass with implementation context cleared when practical. Different prompts from the same model are additional checks, not proof of reviewer independence.
5. Commit a coherent change. Update TASKS.md and evidence/progress.md with actual commands, results, limitations, and the next task. Retain failures that explain design changes. Do not invent elapsed human time or reconstruct a fictional development history.

Use one primary coding agent by default. Parallel agents are optional only if Walter explicitly requests them; give them disjoint modules and separate worktrees. Worktrees prevent file collisions, not hostile code execution. Keep AGENTS.md short and put detailed domain knowledge in docs. Only add a skill after a repeated failure reveals a useful reusable procedure.

## Independent evaluation boundaries

Maintain development cases and evaluation cases in different directories. Freeze the evaluation manifest and its SHA256 before an experiment. The product's code-generation or repair process must receive only allowed input files and development feedback, never the evaluator implementation or expected evaluation answers.

For untrusted generated Python/CAD, use an actual isolated execution environment with no credentials, no network, read-only inputs, a narrow output mount, CPU/memory/process limits, and a timeout. Never execute generated code in the host process. If isolation is unavailable, the deterministic application can still run, but generated-code execution and the live evaluation remain blocked; do not silently downgrade to a host subprocess and call it a sandbox.

When all fixtures are public, describe results as an open evaluation suite. A restricted runtime view reduces direct leakage but does not prove the underlying model has never seen a public fixture. A genuinely held-out claim requires fresh evaluation cases that were not exposed during development. Record which condition applies.

## Bounded product agent

Expose narrow operations such as inspect specification, propose candidate, run development checks, inspect failure, and submit patch. Typed inputs and outputs must include IDs, source references, and explicit error states. Separate the language model from the test runner. A model's explanation never overrides an executable failure.

Use a provider adapter and a recorded-response adapter. The default demonstration uses recorded candidates or deliberate mutations and is labeled REPLAY. It proves harness behavior, not live model competence. LIVE mode is explicit and uses an available configured coding agent or API adapter; no hardcoded latest model name. Capture provider, actual model/version when returned, tool versions, timestamp, seed, input hash, oracle hash, source commit, elapsed time, token usage when available, and pricing source/date for any cost estimate. Unknown cost remains unknown.

Default live bounds: three attempts per case, 120 seconds per attempt, 15 tool calls per attempt, and 30,000 output tokens per case. A separately authorized spending ceiling overrides these upper bounds. Timeouts, malformed output, abstentions, and exhausted budgets are recorded outcomes. Stop on any critical violation, evaluator modification, or attempt to escape the permitted artifact paths.

## Evidence and attribution

Each run produces a machine-readable manifest, candidate patch or generated artifact, test report, and concise narrative explaining what failed and why. Commit small representative evidence; store large generated outputs as release assets later. Keep raw and redacted logs separate; never commit keys, account identifiers unrelated to the project, or employer data.

For a live campaign, repeat every evaluation task three times from a fresh workspace. Compare the same cases under deterministic baseline, one-shot generation, and bounded repair. Publish all outcomes and denominators, not the best trial. Report success, critical violations, attempts, latency, and costs separately. Do not claim a speedup over a human unless a real comparable human baseline was measured.

The coding agent must treat requirement changes as explicit design changes. It may resolve routine details itself and document its choice. It may not weaken a requirement, change an oracle, or omit a failing case to improve a score without recording the change and invalidating comparisons to the old suite. An oracle bug can be fixed with a reproduction and a new evaluation version.

## Completion gates

- A fresh clone can install from a lockfile, run all required checks, and produce the offline demonstration without a paid API or physical hardware.
- Every requirement maps to passing tests or an explicitly unresolved limitation. A checked task list is not evidence.
- The independent suite detects every deliberately seeded critical defect.
- The README gives a two-minute path to the result, limitations, architecture, and evidence.
- Blog conclusions cite artifacts actually generated by the project. Proposed benchmarks and physical claims remain prospective until measured.
- Code and blog can be committed locally. Do not push, publish releases, create remote code commits, or deploy the website under the current authorization.
