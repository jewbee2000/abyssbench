"""Scriptable local workflow; check uses a bounded, killable data evaluator."""
import argparse
import json
import subprocess
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .contracts import InputError
from .controller import FluidController
from .monitor import monitor
from .recording import Recorder, safe_output, sha256, verify
from .report import render_report
from .runner import run


def demo(output):
    recorder = Recorder(output, {'seed': 0, 'mode': 'OFFLINE SYNTHETIC REPLAY', 'cases': []})
    cases = {}
    expected = {'healthy': (None, None), 'stale-sensor': ('freeze', 660),
                'stuck-valve': ('stuck', 1010), 'disconnect': ('disconnect', 500),
                'out-of-range': ('range', 500), 'delayed-packet': ('delay', 500),
                'freshness_receive': ('freeze', None), 'repaired': ('freeze', 660)}
    injection_parameters = {
        None: {},
        'freeze': {'channels': ['pressure1', 'pressure2', 'flow'], 'sample_time_ms': 450},
        'stuck': {'actuator': 'valve', 'position': 0},
        'disconnect': {'connected': False, 'reconnect_ms': 700},
        'range': {'channel': 'pressure1', 'value': 310000, 'unit': 'Pa'},
        'delay': {'channels': ['pressure1', 'pressure2', 'flow'], 'sample_time_ms': 100,
                  'receive_time_ms': 500},
    }
    all_expected = True
    for name, (fault, detection) in expected.items():
        defect = 'freshness_receive' if name == 'freshness_receive' else None
        events = run(FluidController(defect=defect), fault=fault)
        result = monitor(events, profile='fluid')
        cases[name] = (events, result)
        filename = f'{name}/events.jsonl'
        recorder.write(filename, ''.join(json.dumps(e, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n' for e in events))
        detected = [e['time_ms'] for e in events if e['kind'] == 'fault']
        expected_status = 'fail' if defect else 'pass'
        correct = result['status'] == expected_status and (
            detection is None or (bool(detected) and detected[0] == detection))
        if name == 'healthy':
            correct = correct and not detected
        all_expected &= correct
        recorder.manifest['cases'].append({'name': name, 'fault': fault, 'onset_ms': 500 if fault else None,
            'injection_parameters': injection_parameters[fault],
            'expected_detection_ms': detection, 'observed_detection_ms': detected[0] if detected else None,
            'controller_version': defect or 'fluid-v1', 'events': filename,
            'required_safe_response': {'pump': 0, 'valve': 1}, 'deadline_ms': 10,
            'duration_ms': 1500, 'expected_status': expected_status, 'expectations_met': correct})
    recorder.write('verdicts.json', json.dumps({name: result for name, (_, result) in cases.items()}, indent=2))
    recorder.write('report.html', render_report(cases))
    recorder.manifest['expected_checks_passed'] = all_expected
    recorder.finish()
    return 0 if all_expected else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description='Local offline controller replay evidence')
    commands = parser.add_subparsers(dest='command', required=True)
    demo_parser = commands.add_parser('demo')
    demo_parser.add_argument('--offline', action='store_true', required=True)
    demo_parser.add_argument('--output', type=Path, default=Path('artifacts/demo'))
    check = commands.add_parser('check')
    check.add_argument('trace')
    check.add_argument('--rules')
    check.add_argument('--profile', choices=['fluid'])
    check.add_argument('--map', dest='column_map')
    check.add_argument('--result', type=Path)
    check.add_argument('--timeout', type=float, default=60.0)
    verify_parser = commands.add_parser('verify')
    verify_parser.add_argument('directory', type=Path)
    serve_parser = commands.add_parser('serve')
    serve_parser.add_argument('directory', type=Path)
    serve_parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            return demo(args.output)
        if args.command == 'verify':
            print(json.dumps(verify(args.directory), indent=2))
            return 0
        if args.command == 'serve':
            verify(args.directory)
            root = args.directory.resolve()
            class ReadOnly(SimpleHTTPRequestHandler):
                def translate_path(self, path):
                    resolved = Path(super().translate_path(path)).resolve()
                    return str(resolved) if resolved.is_relative_to(root) else str(root / '__denied__')
            with ThreadingHTTPServer(('127.0.0.1', args.port), partial(ReadOnly, directory=str(root))) as server:
                print(f'Local read-only report: http://127.0.0.1:{args.port}/report.html', flush=True)
                server.serve_forever()
            return 0
        if args.command == 'check':
            if not 0 < args.timeout <= 60:
                raise InputError('timeout must be >0 and <=60 seconds')
            request = {'trace': args.trace, 'rules': args.rules, 'profile': args.profile, 'map': args.column_map}
            try:
                child = subprocess.run([sys.executable, '-m', 'abyssbench._check_worker'],
                    input=json.dumps(request), capture_output=True, text=True, timeout=args.timeout, check=False)
                result = json.loads(child.stdout)
                if child.returncode not in (0, 1, 2):
                    raise InputError('evaluator crashed')
            except (subprocess.TimeoutExpired, ValueError, InputError) as error:
                result = {'schema_version': 1, 'status': 'inconclusive', 'window_ms': None,
                          'clock_assumptions': 'evaluation incomplete',
                          'checks': [{'id': 'EXECUTION', 'status': 'inconclusive',
                                      'details': [{'reason': str(error)}]}]}
            trace = Path(args.trace)
            result['input_hash'] = sha256(trace.read_bytes()) if trace.is_file() and trace.stat().st_size <= 20*1024*1024 else 'unavailable'
            if args.result:
                target = safe_output(args.result)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(json.dumps(result, allow_nan=False))
            return {'pass': 0, 'fail': 1, 'inconclusive': 2}[result['status']]
    except (InputError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'incomplete: {error}', file=sys.stderr)
        return 2
    return 2
