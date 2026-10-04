import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from abyssbench import monitor, read_jsonl, run
from abyssbench.cli import demo
from abyssbench.contracts import InputError
from abyssbench.recording import Recorder, verify
from abyssbench.report import render_report


@pytest.mark.requirements('AB-10')
def test_incomplete_writer_and_corruption(tmp_path):
    directory = tmp_path / 'interrupted'
    recorder = Recorder(directory, {'seed': 0})
    recorder.write('partial.json', '{}')
    assert json.loads((directory / 'manifest.json').read_text())['status'] == 'incomplete'
    with pytest.raises(InputError):
        verify(directory)
    recorder.finish()
    assert verify(directory)['status'] == 'complete'
    (directory / 'partial.json').write_text('corrupted')
    with pytest.raises(InputError):
        verify(directory)


@pytest.mark.requirements('AB-10')
def test_abrupt_recorder_process_exit_is_incomplete(tmp_path):
    directory = tmp_path / 'killed-writer'
    program = ("from abyssbench.recording import Recorder\nimport sys\n"
               f"r=Recorder({str(directory)!r}, {{'seed':0}})\n"
               "r.write('partial.json','{}')\nprint('ready',flush=True)\nsys.stdin.read()\n")
    child = subprocess.Popen([sys.executable, '-c', program], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == 'ready'
        child.terminate()
        child.wait(timeout=5)
        with pytest.raises(InputError):
            verify(directory)
        assert json.loads((directory / 'manifest.json').read_text())['status'] == 'incomplete'
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=5)


@pytest.mark.requirements('AB-08', 'AB-10', 'AB-12')
def test_demo_manifest_and_replay(tmp_path):
    output = tmp_path / 'demo'
    assert demo(output) == 0
    manifest = verify(output)
    assert manifest['seed'] == 0
    assert manifest['oracle_hash']
    injection_parameters = {
        None: {},
        'freeze': {'channels': ['pressure1', 'pressure2', 'flow'], 'sample_time_ms': 450},
        'stuck': {'actuator': 'valve', 'position': 0},
        'disconnect': {'connected': False, 'reconnect_ms': 700},
        'range': {'channel': 'pressure1', 'value': 310000, 'unit': 'Pa'},
        'delay': {'channels': ['pressure1', 'pressure2', 'flow'], 'sample_time_ms': 100,
                  'receive_time_ms': 500},
    }
    for case in manifest['cases']:
        assert case['injection_parameters'] == injection_parameters[case['fault']]
        if case['controller_version'] == 'fluid-v1':
            assert read_jsonl(output / case['events']) == run(fault=case['fault'], seed=manifest['seed'])
    report = (output / 'report.html').read_text()
    for required in ('Simulation only', 'Pressure (kPa)', 'Flow (L/min)', 'Controller state',
                     'Safe command', 'stuck', 'freshness_receive', 'Observation window'):
        assert required in report
    assert '<svg' in report and 'https://' not in report
    verdicts = json.loads((output / 'verdicts.json').read_text())
    assert verdicts['freshness_receive']['status'] == 'fail'
    assert verdicts['repaired']['status'] == 'pass'


@pytest.mark.requirements('AB-21')
def test_offline_egress_and_html_escape(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('egress disabled')
    monkeypatch.setattr(socket, 'socket', denied)
    monkeypatch.setattr(socket, 'create_connection', denied)
    assert demo(tmp_path / 'offline') == 0
    html = render_report({'<script>alert(1)</script>': (run(), monitor(run(), profile='fluid'))})
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
    writer = Recorder(tmp_path / 'paths', {})
    for path in ('../outside', '/absolute', 'nested/../../escape'):
        with pytest.raises(InputError):
            writer.write(path, 'x')
    for path in (Path('..') / 'escape',):
        with pytest.raises(InputError):
            demo(path)


@pytest.mark.requirements('AB-19')
@pytest.mark.parametrize('candidate, expected', [('valid', 0), ('violating', 1), ('incomplete', 2)])
def test_cli_statuses(candidate, expected, tmp_path):
    result_file = tmp_path / 'result.json'
    result = subprocess.run([sys.executable, '-m', 'abyssbench', 'check',
        f'tests/oracle/thermal-{candidate}.jsonl', '--rules', 'tests/oracle/thermal-rules.json',
        '--result', str(result_file)], capture_output=True, text=True, check=False)
    assert result.returncode == expected, result.stderr
    assert json.loads(result_file.read_text())['status'] == {0: 'pass', 1: 'fail', 2: 'inconclusive'}[expected]


@pytest.mark.requirements('AB-20')
def test_oversize_and_timeout(tmp_path):
    oversize = tmp_path / 'oversize.jsonl'
    with oversize.open('wb') as output:
        output.truncate(20 * 1024 * 1024 + 1)
    result_file = tmp_path / 'bounded.json'
    for args in ([str(oversize)], ['tests/oracle/thermal-valid.jsonl', '--timeout', '0.001']):
        result = subprocess.run([sys.executable, '-m', 'abyssbench', 'check', *args,
            '--rules', 'tests/oracle/thermal-rules.json', '--result', str(result_file)],
            capture_output=True, text=True, timeout=10, check=False)
        assert result.returncode == 2
        assert json.loads(result_file.read_text())['status'] == 'inconclusive'
    with pytest.raises(InputError):
        monitor(run(), profile='fluid', seconds=0)
