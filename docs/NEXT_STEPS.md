# Next steps after the deterministic release

The next milestone is one useful external trace and one independent engineer's trial. The existing 116-test suite and clean consumer walkthrough establish software behavior, not practitioner adoption or physical validation.

## Walter's actions, in order

1. Inspect the demonstration. From this project folder, run:

   ```powershell
   .\.venv\Scripts\python.exe -m abyssbench demo --offline --output artifacts/walter-review
   .\.venv\Scripts\python.exe -m abyssbench verify artifacts/walter-review
   .\.venv\Scripts\python.exe -m abyssbench serve artifacts/walter-review --port 8770
   ```

   Use a new output directory. Open the printed report URL. Confirm that `freshness_receive` fails and `repaired` passes on the same frozen-sensor input. Inspect the stuck-valve case: safe commands occur, while the simulated valve remains stuck. Write down anything unclear or misleading.

2. Choose one timing failure you actually want to investigate. Supply a small personal/public log you can share, or define a new synthetic case from that problem. Include the channel names, units, sample and receive timestamps, command/state events, desired response and deadline. State the expected answer before evaluating it. A temperature/heater log is a simple first candidate. No hardware session is required for replay.

3. Ask one engineer to try the README from a fresh checkout without coaching. Suggested request:

   > Could you try AbyssBench on one controller log or timing scenario? Please record installation friction, time to the first useful verdict, anything confusing in the timeline, and whether you would use it again. An unsuccessful trial is useful feedback too.

   Give them the GitHub URL. Record their actual environment, steps, failures and feedback with permission to retain it. This is the missing practitioner evidence; an agent repeating the walkthrough does not replace it.

4. Review the unpublished article in your own voice after the trial. Confirm the account of the failure, correction and limitations; add the verified repository/evidence links and any real feedback. Give a separate explicit instruction when you want the website published. Keep its publication date unset until then.

## Follow-up implementation work

First add GitHub Actions on Windows/Python 3.12 for the already-working lint, type, test, wheel and offline-demo commands. Preserve failures as workflow artifacts. CI has not run yet. [GitHub's Python workflow guide](https://docs.github.com/en/actions/tutorials/build-and-test-code/python) explains the supported setup and test steps.

Then implement only the import/report changes exposed by the external trace and trial. Preserve the original failed trace and freeze its expected verdict independently before repairing code. Flat CSV conversion is a likely need; the current mapped CSV interface requires a JSON payload column.

A Linux compatibility check and a tagged wheel release can follow a successful trial. Parquet, PLC adapters, physical calibration and isolated model experiments remain separate choices justified by a demonstrated need. The core tool is already usable without those additions.

Exit evidence for this milestone: one non-fixture trace with a predeclared expected verdict, one preserved failure/correction, and an independent engineer's recorded trial. Report unsuccessful or inconclusive outcomes honestly.
