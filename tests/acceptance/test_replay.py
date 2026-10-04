import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from abyssbench import InputError, monitor, read_csv, read_jsonl, run

FIXTURES = Path(__file__).parents[1] / 'oracle'


@pytest.mark.requirements('AB-17')
def test_generic_import_has_no_fluid_model_dependency():
    result = subprocess.run([sys.executable, '-c', "import sys; from abyssbench import monitor, read_jsonl; assert 'abyssbench.runner' not in sys.modules; assert 'abyssbench.controller' not in sys.modules"], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


@pytest.mark.requirements('AB-16')
def test_sparse_fluid_ticks_cannot_prove_deadlines():
    events = [e for e in run() if not (e['kind'] == 'tick' and e['time_ms'] == 100)]
    for sequence, e in enumerate(events):
        e['sequence'] = sequence
    assert monitor(events, profile='fluid')['status'] == 'inconclusive'


@pytest.mark.requirements('AB-13')
def test_installed_baseline_evidence():
    output = json.loads(Path('evidence/baseline.json').read_text())
    assert output['cases']['stale-broken']['failed'] is True
    assert output['cases']['reconnect-broken']['failed'] is True
    assert output['cases']['stale-corrected']['failed'] is False
    assert output['cases']['reconnect-corrected']['failed'] is False
    assert output['openhtf'][0]['outcome'] == 'PASS'
    assert 'requirement-verdicts.json' in output['openhtf'][0]['attachments']


@pytest.mark.requirements('AB-14', 'AB-17')
@pytest.mark.parametrize('candidate, expected', [('valid', 'pass'), ('violating', 'fail'), ('incomplete', 'inconclusive')])
def test_external_thermal_trace(candidate, expected):
    config = json.loads((FIXTURES / 'thermal-rules.json').read_text())
    mapping = json.loads((FIXTURES / 'csv-map.json').read_text())
    json_events = read_jsonl(FIXTURES / f'thermal-{candidate}.jsonl', units=config['channels'])
    csv_events = read_csv(FIXTURES / f'thermal-{candidate}.csv', mapping)
    assert json_events == csv_events
    result = monitor(json_events, rules=config)
    assert result == monitor(csv_events, rules=config)
    assert result['status'] == expected
    assert result['window_ms'][0] == 0


@pytest.mark.requirements('AB-16')
@pytest.mark.parametrize('end, response, expected', [(5, None, 'inconclusive'), (10, None, 'fail'), (10, 10, 'pass'), (11, 11, 'fail')])
def test_deadline_and_pending_window(end, response, expected):
    events = [{'schema_version': 1, 'clock': 'simulation', 'sequence': 0, 'time_ms': 0,
               'kind': 'measurement', 'data': {'channel': 'temperature', 'value': 20, 'unit': 'degC',
               'sample_time_ms': 0, 'receive_time_ms': 0, 'quality': 'good', 'sequence': 0,
               'calibration_id': 'independent-synthetic'}}]
    def emit(at, kind, data):
        events.append({'schema_version': 1, 'clock': 'simulation', 'sequence': len(events),
                       'time_ms': at, 'kind': kind, 'data': data})
    emit(0, 'fault', {'cause': 'test'})
    if response is not None:
        emit(response, 'command', {'heater': 0})
    emit(end, 'tick', {})
    config = {'schema_version': 1, 'channels': {'temperature': 'degC'},
              'rules': [{'id': 'T-off', 'type': 'response', 'trigger_kind': 'fault',
                         'response': {'heater': 0}, 'deadline_ms': 10}]}
    assert monitor(events, rules=config)['status'] == expected


@pytest.mark.requirements('AB-02', 'AB-14', 'AB-16')
def test_missing_sample_and_log_errors():
    config = json.loads((FIXTURES / 'thermal-rules.json').read_text())
    events = read_jsonl(FIXTURES / 'thermal-valid.jsonl')
    missing = copy.deepcopy(events)
    missing[0]['data']['sample_time_ms'] = None
    assert monitor(missing, rules=config)['status'] == 'inconclusive'
    for alteration in ('unit', 'clock', 'sequence', 'version', 'missing_channel'):
        bad = copy.deepcopy(events)
        if alteration == 'unit':
            bad[0]['data']['unit'] = 'ambiguous'
        elif alteration == 'clock':
            bad[0]['clock'] = 'wallclock'
        elif alteration == 'sequence':
            bad[-1]['sequence'] = 0
        elif alteration == 'version':
            bad[0]['schema_version'] = 999
        else:
            bad[0]['data']['channel'] = 'other'
        with pytest.raises(InputError):
            monitor(bad, rules=config)


@pytest.mark.requirements('AB-16', 'AB-19')
def test_unknown_and_malformed_rules_rejected():
    events = read_jsonl(FIXTURES / 'thermal-valid.jsonl')
    config = json.loads((FIXTURES / 'thermal-rules.json').read_text())
    bad = copy.deepcopy(config)
    bad['schema_version'] = 2
    with pytest.raises(InputError):
        monitor(events, rules=bad)
    bad = copy.deepcopy(config)
    bad['rules'][0]['max_age_ms'] = -1
    with pytest.raises(InputError):
        monitor(events, rules=bad)


@pytest.mark.requirements('AB-02')
def test_old_packet_is_data_not_structural_disorder():
    config = json.loads((FIXTURES / 'thermal-rules.json').read_text())
    events = read_jsonl(FIXTURES / 'thermal-valid.jsonl')
    packet = copy.deepcopy(events[0])
    packet['time_ms'] = 40
    packet['data']['receive_time_ms'] = 40
    packet['data']['sample_time_ms'] = -100
    packet['data']['sequence'] = 0
    events.insert(3, packet)
    for i, e in enumerate(events):
        e['sequence'] = i
    assert monitor(events, rules=config)['status'] == 'fail'
