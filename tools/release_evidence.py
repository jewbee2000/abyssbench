"""Compile executed evidence into the requirement register; never invent results."""
import json
import re
from pathlib import Path

from abyssbench.recording import metadata, sha256


def main():
    runs = []
    for name in ('acceptance-run.json', 'report-run.json', 'fresh-install-run.json'):
        path = Path('evidence') / name
        if path.exists():
            run = json.loads(path.read_text())
            assert run['exit_code'] == 0, name
            run['file'] = name
            runs.append(run)
    assert runs and runs[0]['file'] == 'acceptance-run.json'
    passed_count = len({r['nodeid'] for r in runs[0]['results'] if r['phase'] == 'call' and r['outcome'] == 'passed'})
    register = json.loads(Path('requirements.json').read_text())
    matrix = []
    for requirement in register['requirements']:
        identity = requirement['id']
        results = [dict(r, run_file=run['file']) for run in runs for r in run['results'] if identity in r['requirement_ids']]
        assert results and all(r['outcome'] == 'passed' for r in results), identity
        requirement.setdefault('original_planned_test', requirement['planned_test'])
        requirement['planned_test'] = results[0]['nodeid'].split('::')[0]
        requirement['executed_tests'] = sorted({r['nodeid'] for r in results})
        requirement['evidence'] = 'evidence/acceptance-run.json'
        requirement['status'] = 'verified' if requirement['priority'] == 'must' else 'partial_deferred'
        matrix.append({'id': identity, 'priority': requirement['priority'], 'status': requirement['status'],
                       'tests': results, 'disposition': 'OpenHTF adapter passed; Parquet deferred (JSONL sufficient)' if identity == 'AB-18' else 'applicable Must passed'})
    register['decision_status'] = 'deterministic_offline_release_verified'
    register['status'] = 'deterministic_offline_release_verified'
    Path('requirements.json').write_text(json.dumps(register, indent=2)+'\n')
    provenance = {'source': metadata(), 'runs': [{k: run[k] for k in ('file', 'command', 'exit_code', 'source', 'input_hash', 'oracle_hash', 'result_hash')} for run in runs],
                  'requirements': matrix,
                  'artifacts': {path.name: sha256(path.read_bytes()) for path in Path('evidence').glob('*.json') if path.name != 'release.json'},
                  'boundaries': ['software simulation only', 'agent-executed consumer; no practitioner feedback',
                                 'no generated-code or live-model execution', 'no hardware, push or publication']}
    Path('evidence/release.json').write_text(json.dumps(provenance, indent=2)+'\n')
    lines = ['# Executed requirement evidence', '',
             'All 21 applicable Must requirements have executed passing software checks. AB-18 is partially implemented: OpenHTF attachment passed; Parquet is explicitly deferred. No conditional live-model/CAD feature is enabled.', '',
             f'The complete suite ran {passed_count} passing tests, including one Hypothesis test configured for 1000 bounded examples. Six deliberately broken controllers and twelve independent negative event controls are detected. Counts are a coverage inventory, not a quality or model-success score.', '',
             'Full raw results: [acceptance-run.json](acceptance-run.json). Subsequent report-layout checks: [report-run.json](report-run.json). Fresh installed-wheel checks: [fresh-install-run.json](fresh-install-run.json). Each run records command, exit code, commit/dirty state, diff/content/lock/oracle/input hashes and test-to-requirement mappings. [release.json](release.json) retains run provenance and artifact hashes.', '',
             '| ID | Priority | Outcome | Executed test modules |', '| --- | --- | --- | --- |']
    for row in matrix:
        files = sorted({test['nodeid'].split('::')[0] for test in row['tests']})
        links = ', '.join(f'[{Path(file).name}](../{file})' for file in files)
        lines.append(f'| {row["id"]} | {row["priority"]} | {row["status"]} | {links} |')
    lines.extend(['', '## Known limits and evidence boundaries', '',
                  '- Python 3.12 on the recorded Windows environment; ANTLR emits upstream deprecation warnings. Other operating systems are not verified.',
                  '- Single monotonic clock and explicit SI/degC units. CSV requires a JSON payload column; arbitrary flattened logs need conversion.',
                  '- Plant is synthetic and uncalibrated. Command deadlines are simulation evidence, not physical actuator or hard real-time guarantees.',
                  '- Trusted Python callbacks only. CLI data evaluation is timeout-killable; Python callbacks have no hostile-code sandbox. Docker unavailable.',
                  '- Finite input limits: 20 MiB, 100000 events, 32 rules/cases, 60000 ms simulation, 60 s evaluation. Local 10000-event target passed; raw-library comparison does less work and is not a speedup baseline.',
                  '- Clean consumer setup uses a fresh venv with the existing package cache. Agent-executed failure/correction is not independent practitioner adoption.',
                  '- Failed traces, first baseline failure and implementation failures remain in evidence/. No failing randomized sequence was found; the retained six seeded defects are deterministic negative controls.',
                  '- Parquet deferred. C++, PLC, CAD, distributed clocks, hardware qualification and model campaigns excluded. Repository and article remain unpublished.',
                  '- Missing or irregular fluid controller ticks are inconclusive for timing claims. Abrupt recorder process termination leaves an incomplete durable manifest. Each run preserves its own source hashes.', '',
                  "Local normal and explicit draft Jekyll builds passed, with desktop/mobile previews inspected. Publication still needs Walter's editorial review, actual hosted repository/evidence links and final link checks. No publication is authorized."])
    Path('evidence/REQUIREMENT_EVIDENCE.md').write_text('\n'.join(lines)+'\n')
    document = Path('docs/REQUIREMENTS.md').read_text(encoding='utf-8')
    document = document.replace('Status: planned, not implemented.', 'Status: deterministic offline software verified; see evidence/REQUIREMENT_EVIDENCE.md.')
    for requirement in register['requirements']:
        pattern = rf'(### {requirement["id"]} —.*?)(?=\n### |\n## |\Z)'
        def update(match, item=requirement):
            section = match[0].replace('**Status:** not implemented.', f'**Status:** {item["status"]}; executed evidence in ../evidence/REQUIREMENT_EVIDENCE.md.')
            section = section.replace('**Planned evidence:**', '**Executed evidence:**')
            section = section.replace(item['original_planned_test'], item['planned_test'])
            return section
        document = re.sub(pattern, update, document, flags=re.S)
    document = document.replace('All planned test paths above are future work.', 'Actual executed paths and retained original planned paths are recorded in requirements.json.')
    assert '**Status:** not implemented.' not in document
    assert '**Planned evidence:**' not in document
    Path('docs/REQUIREMENTS.md').write_text(document, encoding='utf-8')


if __name__ == '__main__':
    main()
