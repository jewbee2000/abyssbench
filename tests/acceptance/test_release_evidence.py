import json
from pathlib import Path

import openhtf as htf
import pytest
from jsonschema import Draft202012Validator

from abyssbench import InputError, monitor, read_jsonl, run
from abyssbench.integrations import attach_verdict
from abyssbench.trace import MAX_EVENTS, SCHEMAS, validate_events


@pytest.mark.requirements('AB-18')
def test_openhtf_requirement_attachment():
    records = []
    result = monitor(run(), profile='fluid')
    def phase(api):
        return attach_verdict(api, result)
    test = htf.Test(phase)
    test.add_output_callbacks(lambda record: records.append(record))
    test.execute(test_start=lambda: 'synthetic')
    assert records[0].outcome.name == 'PASS'
    assert any('abyssbench-verdict.json' in phase.attachments for phase in records[0].phases)


@pytest.mark.requirements('AB-19')
def test_result_schema_and_unsupported_trigger():
    schema = json.loads((SCHEMAS / 'result-v1.json').read_text())
    for candidate in ('valid', 'violating', 'incomplete'):
        result = monitor(read_jsonl(f'tests/oracle/thermal-{candidate}.jsonl'),
                         rules=json.loads(Path('tests/oracle/thermal-rules.json').read_text()))
        Draft202012Validator(schema).validate(result)
    bad = {'schema_version': 1, 'channels': {'temperature': 'degC'},
           'rules': [{'id': 'BAD', 'type': 'response', 'trigger_kind': 'unknown',
                      'response': {'heater': 0}, 'deadline_ms': 1}]}
    with pytest.raises(InputError):
        monitor(read_jsonl('tests/oracle/thermal-valid.jsonl'), rules=bad)


@pytest.mark.requirements('AB-20')
def test_case_event_limits_and_executed_performance():
    with pytest.raises(InputError):
        validate_events([{}] * (MAX_EVENTS+1))
    output = json.loads(Path('evidence/performance.json').read_text())
    assert output['event_count'] == 10000
    measured = output['results']['full_event_validation_and_12_invariants']
    assert len(measured) == 3
    assert all(r['result'] == 'pass' and r['elapsed_seconds'] < 10 and r['peak_rss_bytes'] < 256*1024*1024 for r in measured)


@pytest.mark.requirements('AB-12', 'AB-22')
def test_executed_clean_consumer_walkthrough():
    output = json.loads(Path('evidence/consumer-walkthrough.json').read_text())
    assert output['outcomes'] == {'failed': 'fail', 'corrected': 'pass', 'external_controller': 'pass', 'fresh_demo': 'pass'}
    assert [c['exit_code'] for c in output['commands']].count(1) == 1
    assert all(c['exit_code'] in (0, 1) for c in output['commands'])
    assert output['setup_elapsed_seconds'] > 0


@pytest.mark.requirements('AB-21')
def test_license_and_fixture_provenance():
    inventory = json.loads(Path('evidence/dependency-licenses.json').read_text())
    packages = {r['name'].lower(): r for r in inventory}
    for name in ('rtamt', 'jsonschema', 'openhtf'):
        assert packages[name]['license'] or packages[name]['license_classifiers']
    assert Path('LICENSE').read_text().startswith('MIT License')
    assert 'independently authored' in Path('docs/LICENSING.md').read_text()
    assert 'synthetic' in Path('tests/oracle/thermal-valid.jsonl').read_text()
