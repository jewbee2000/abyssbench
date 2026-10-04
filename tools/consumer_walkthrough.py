"""Agent-executed cold consumer install; preserved failed input then correction."""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from abyssbench.recording import metadata, sha256


def main():
    repo = Path.cwd().resolve()
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', default='artifacts/consumer')
    args = parser.parse_args()
    consumer = (repo / args.directory).resolve()
    if not consumer.is_relative_to(repo / 'artifacts'):
        raise SystemExit('Consumer directory must be under artifacts/')
    if consumer.exists():
        raise SystemExit('Use --directory with a new consumer directory')
    consumer.mkdir(parents=True)
    started = time.perf_counter()
    commands = []
    def invoke(argv, expected=0):
        at = time.perf_counter()
        result = subprocess.run([str(arg) for arg in argv], cwd=consumer, capture_output=True, text=True, timeout=300, check=False)
        commands.append({'command': [str(a) for a in argv], 'cwd': str(consumer), 'exit_code': result.returncode,
                         'elapsed_seconds': time.perf_counter()-at, 'stdout_tail': result.stdout[-1200:], 'stderr_tail': result.stderr[-1200:]})
        assert result.returncode == expected, commands[-1]
        return result
    invoke([sys.executable, '-m', 'venv', '.venv'])
    python = consumer / '.venv/Scripts/python.exe'
    invoke([python, '-m', 'pip', 'install', '-r', repo / 'requirements-lock.txt'])
    wheel = next((repo / 'artifacts/dist').glob('abyssbench-*.whl'))
    invoke([python, '-m', 'pip', 'install', '--no-deps', wheel])
    invoke([python, '-m', 'pip', 'check'])
    rules = {'schema_version': 1, 'channels': {'temperature': 'degC'}, 'rules': [
        {'id': 'USER-AGE', 'type': 'sample_age', 'channel': 'temperature', 'max_age_ms': 125,
         'response': {'heater': 0}, 'deadline_ms': 30},
        {'id': 'USER-RANGE', 'type': 'range', 'channel': 'temperature', 'min': 10, 'max': 90}]}
    (consumer / 'rules.json').write_text(json.dumps(rules, indent=2))
    traces = {}
    for name, heater in [('failed', 1), ('corrected', 0)]:
        rows = [(0, 'measurement', {'channel': 'temperature', 'value': 55, 'unit': 'degC',
                    'sample_time_ms': 0, 'receive_time_ms': 0, 'quality': 'good', 'sequence': 0,
                    'calibration_id': 'synthetic-consumer'}),
                (0, 'command', {'heater': 1}), (125, 'tick', {}),
                (132, 'fault', {'cause': 'old-temperature'}), (162, 'command', {'heater': heater}),
                (162, 'tick', {})]
        events = [{'schema_version': 1, 'clock': 'simulation', 'sequence': i,
                   'time_ms': t, 'kind': kind, 'data': data} for i, (t, kind, data) in enumerate(rows)]
        trace = ''.join(json.dumps(e)+'\n' for e in events)
        traces[name] = sha256(trace.encode())
        (consumer / f'{name}.jsonl').write_text(trace)
        invoke([python, '-m', 'abyssbench', 'check', f'{name}.jsonl', '--rules', 'rules.json',
                '--result', f'{name}-verdict.json'], expected=1 if name == 'failed' else 0)
    shutil.copyfile(repo / 'examples/consumer/controller.py', consumer / 'controller.py')
    script = "from controller import ConsumerController\nfrom abyssbench import run, monitor\nresult = monitor(run(ConsumerController(), fault='freeze'), profile='fluid')\nprint(result['status'])\nassert result['status'] == 'pass'\n"
    (consumer / 'exercise.py').write_text(script)
    invoke([python, 'exercise.py'])
    invoke([python, '-m', 'abyssbench', 'demo', '--offline', '--output', 'demo'])
    invoke([python, '-m', 'abyssbench', 'verify', 'demo'])
    output = {'label': 'Agent-executed clean consumer walkthrough, not practitioner validation',
              'setup_elapsed_seconds': time.perf_counter()-started, 'commands': commands,
              'source': metadata(), 'wheel_hash': sha256(wheel.read_bytes()), 'trace_hashes': traces,
              'consumer_files': {p.name: {'bytes': p.stat().st_size, 'lines': len(p.read_text().splitlines())}
                                 for p in consumer.iterdir() if p.is_file()},
              'outcomes': {'failed': 'fail', 'corrected': 'pass', 'external_controller': 'pass', 'fresh_demo': 'pass'},
              'limits': 'Single clock, JSON payload column for CSV, trusted Python callback; no practitioner feedback. Raw baseline needs no wheel but requires manual provenance/window/report glue.'}
    Path('evidence/consumer-walkthrough.json').write_text(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
