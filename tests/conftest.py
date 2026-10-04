"""Executed evidence, not a generated expected-value oracle."""
import json
import sys
from pathlib import Path

from abyssbench.recording import metadata, sha256, tree_hash

reports = []


def pytest_runtest_logreport(report):
    if report.when == 'call' or report.failed:
        reports.append({'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome})


def pytest_collection_modifyitems(items):
    for item in items:
        marker = item.get_closest_marker('requirements')
        item.user_properties.append(('requirement_ids', list(marker.args) if marker else []))


def pytest_sessionfinish(session, exitstatus):
    items = {item.nodeid: dict(item.user_properties).get('requirement_ids', []) for item in session.items}
    output = {'command': [sys.executable, '-m', 'pytest', *sys.argv[1:]], 'exit_code': int(exitstatus),
              'source': metadata(), 'input_hash': tree_hash('tests/oracle'),
              'oracle_hash': tree_hash('tests'), 'results': [dict(r, requirement_ids=items.get(r['nodeid'], [])) for r in reports]}
    output['result_hash'] = sha256(json.dumps(output['results'], sort_keys=True).encode())
    Path('evidence/acceptance-run.json').write_text(json.dumps(output, indent=2))
