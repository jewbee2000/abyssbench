# Research and design references

Research reviewed October 3, 2026. These sources inform the workflow; they do not establish that these projects have achieved any particular performance. Requirements and effort estimates are original design decisions for this portfolio.

- [OpenAI — Iterating Development Workflows with Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex): keep durable plans, progress, and evidence that survive a fresh session.
- [OpenAI — Build iterative repair loops with Codex](https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex): implement a bounded propose, execute, evaluate, repair cycle with inspectable artifacts.
- [OpenAI — Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra): keep guidance concise and load task-specific context when needed. This is a workflow reference, not a requirement to use that model.
- [Anthropic — Harness design for long running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps): separate generation from evaluation and use explicit progress checkpoints.
- [Anthropic — Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): assess outcomes and repeated trials, including unsuccessful attempts.
- [GitHub Spec Kit](https://github.com/github/spec-kit/blob/main/docs/index.md): specification, plan, tasks, implementation. We use a lightweight version instead of installing a large framework.
- [Hypothesis stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html): generate sequences and check invariants after transitions.
- [build123d](https://build123d.readthedocs.io/en/latest/): CAD kernel interfaces, valid solids, and export capabilities; check stable package compatibility during the environment spike.
- [PyVISA sim](https://pyvisa.readthedocs.io/projects/pyvisa-sim/en/latest/): a possible later adapter for instrument simulation, not a dependency of the initial wire-level oracle.
- [OpenHTF](https://github.com/google/openhtf): a useful later integration target for phased test execution.
- [NIST experimental design handbook](https://www.itl.nist.gov/div898/handbook/pri/pri.htm): why physical claims need repeatable measurements and confirmation experiments.

Personal context comes from Walter's resume reviewed in the earlier research and his public [portfolio](https://walter.teitelbaum.us/), especially [bicycle components](https://walter.teitelbaum.us/2025/04/01/3D-Printed-Bicycle-Components/) and [automated pruning](https://walter.teitelbaum.us/2021/07/25/Automated-Pruning-for-Polyculture/). No employer designs, logs, protocols, measurements, or confidential materials belong in these repositories.
