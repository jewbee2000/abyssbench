# A test stand I can break on purpose

Unpublished editorial draft; canonical copy is website-drafts/_drafts/abyssbench.md. Hosted links and editorial review remain pending; local Jekyll previews verified.

2026-10-04 handoff update: the [project source](https://github.com/jewbee2000/abyssbench) is now public. The article body below records the earlier implementation handoff; its repository-publication wording and final links need editorial updating. The canonical website draft was not changed or pushed by the source-publication task.

A machine that works once is satisfying. A machine that can explain why it stopped working is considerably more useful.

For AbyssBench, I asked Codex to implement a controller replay tool from written requirements. The demonstration has a pump, an outlet valve, two pressure channels and a flow reading. All of them are simulated. That is enough machinery to create some fairly annoying timing problems without introducing plumbing into the development process.

The useful question is what happens when a reasonable-looking input stops being trustworthy. A pressure packet can arrive right now while carrying an old measurement. A connection can return without making it sensible to restart a pump. Software can correctly ask a valve to open while the valve continues to pursue other interests.

Before building the application, the agent compared existing tools on stale-input and reconnect examples. RTAMT already evaluates temporal predicates; pytest already runs tests; OpenHTF already handles test phases, measurements and record attachments. AbyssBench became a small integration around those capabilities: explicit measurement provenance, repeatable fault schedules, finite observation windows and requirement-linked timelines. Calling it an invention of temporal verification would be getting rather carried away.

The first baseline attempt also failed. A Boolean trigger encoded exactly on a numerical predicate boundary produced zero robustness and masked an intended violation. Changing the encoding to positive and negative values made the broken examples fail and corrected examples pass. The original result is still in the evidence folder. It was a useful reminder that a library's mathematical answer needs a precise application contract.

The more interesting failed candidate used receipt time to decide whether a sensor was fresh. In the frozen-sensor scenario, the last actual sample was taken at 450 ms. Packets continued arriving every 50 ms, so this controller kept treating the reading as new. The independent monitor used sample time. With a 200 ms freshness limit and a 10 ms controller tick, the first stale observation occurred at 660 ms.

The corrected controller used the sample timestamp and issued pump-off and valve-open commands at that same simulation tick. The report preserves both command streams on the identical fault schedule. This is a deliberately seeded defect and a deterministic correction, not evidence that a live model independently discovered or repaired it.

![The synthetic stuck-valve run, with commanded and observed valve positions shown separately.](/assets/images/abyssbench-stuck-valve.png)

*A command can be correct even when the simulated valve does not move. The stuck-valve case is detected at 1010 ms; the raw trace and requirement verdicts preserve the distinction.*

The implementation checks all twelve reference invariants and catches six seeded controller defects. Its full acceptance run passed 116 tests, including a property test configured for 1,000 bounded event sequences. Those numbers describe this open test suite. They are not a quality score, a model benchmark or a claim that every controller bug is covered.

I also wanted the package to accept something besides its own pump simulation. A separate thermal example uses different freshness and heater-off deadlines. The agent then installed a built wheel in a clean consumer directory, supplied a non-default temperature trace, observed the expected failure, changed the heater command and reproduced a pass. A separate Python controller used only the public interface. That demonstrates a usable path through the package; feedback from another engineer would still be stronger evidence.

The local resource check evaluated 10,000 events in about 1.2 seconds, with roughly 49 MiB of process memory across three repetitions. The raw RTAMT and OpenHTF comparisons do less work, so this is a resource measurement rather than a speedup claim. The environment, pins, commands, hashes and individual outcomes are recorded alongside the results.

The verified demonstration command is:

```text
python -m abyssbench demo --offline --output artifacts/my-demo
```

It needs an installed Python environment and a new output directory, but no hardware or model credentials. The local README explains installation and the report viewer. The requirement evidence is in `evidence/REQUIREMENT_EVIDENCE.md`; failed candidates remain available instead of disappearing from the story.

There are deliberate limits. The fluid model is illustrative and uncalibrated. Simulation deadlines do not prove physical response or hard real-time behavior. Distributed clocks, live machine control and untrusted generated-code execution are excluded. Docker was unavailable, and no live model campaign ran. Optional Parquet export is deferred; JSONL already preserves the timestamps and units needed here.

What exists is a reproducible software workflow for breaking an imaginary controller and examining why it stopped. The local draft rendered at desktop and mobile widths. The repository and this article remain unpublished. Before publication, I still need to review the editorial copy, add the actual hosted repository and evidence links, and check those final links. The imaginary pump can wait.
