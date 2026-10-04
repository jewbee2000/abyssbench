"""Killable data-only evaluator worker. Never evaluates executable log content."""
import json
import sys

from .monitor import monitor
from .trace import load_json, read_csv, read_jsonl


def main():
    try:
        request = json.load(sys.stdin)
        rules = load_json(request['rules']) if request['rules'] else None
        if request['map']:
            events = read_csv(request['trace'], load_json(request['map']))
        else:
            events = read_jsonl(request['trace'], units=rules['channels'] if rules else None)
        result = monitor(events, rules=rules, profile=request['profile'])
    except Exception as error:
        result = {'schema_version': 1, 'status': 'inconclusive', 'window_ms': None,
                  'clock_assumptions': 'unsupported or invalid evidence',
                  'checks': [{'id': 'INPUT', 'status': 'inconclusive',
                              'details': [{'reason': f'{type(error).__name__}: {error}'}]}]}
    print(json.dumps(result, allow_nan=False))
    return {'pass': 0, 'fail': 1, 'inconclusive': 2}[result['status']]


if __name__ == '__main__':
    sys.exit(main())
