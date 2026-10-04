"""Independent raw-event evaluator; no controller or plant imports.

RTAMT supplies numeric range robustness. A finite event ledger supplies
bounded response, identity and history evidence without inventing a DSL.
"""
import json
import time
from bisect import bisect_left
from collections import defaultdict
from itertools import groupby
from typing import Any

import rtamt
from jsonschema import Draft202012Validator

from .contracts import InputError, finite
from .trace import MAX_SECONDS, SCHEMAS, check_channels, validate_events


def range_robustness(values, low, high):
    spec = rtamt.StlDiscreteTimeSpecification()
    spec.declare_var('value', 'float')
    spec.spec = f'(value >= {float(low)}) and (value <= {float(high)})'
    spec.parse()
    return [r for _, r in spec.evaluate({'time': list(range(len(values))), 'value': values})]


class Ledger:
    def __init__(self, events):
        self.events = events
        self.end = events[-1]['time_ms'] if events else -1
        self.by_kind = defaultdict(list)
        for e in events:
            self.by_kind[e['kind']].append(e)
        self.times = {k: [e['time_ms'] for e in v] for k, v in self.by_kind.items()}
        self.checks = {}

    def init(self, identity):
        self.checks.setdefault(identity, {'id': identity, 'status': 'pass', 'details': []})

    def mark(self, identity, status, detail):
        self.init(identity)
        check = self.checks[identity]
        rank = {'not_applicable': 0, 'pass': 1, 'inconclusive': 2, 'fail': 3}
        if rank[status] > rank[check['status']]:
            check['status'] = status
        check['details'].append(detail)

    def obligation(self, identity, at, deadline_ms, kind, predicate, sequence=-1):
        deadline = at + deadline_ms
        found = None
        candidates = self.by_kind[kind]
        index = bisect_left(self.times.get(kind, []), at)
        for e in candidates[index:]:
            if e['time_ms'] > deadline:
                break
            if e['sequence'] >= sequence and predicate(e['data']):
                found = e['time_ms']
                break
        status = 'pass' if found is not None else ('inconclusive' if self.end < deadline else 'fail')
        self.mark(identity, status, {'trigger_ms': at, 'deadline_ms': deadline,
                                    'observed_ms': found, 'latency_ms': None if found is None else found-at,
                                    'evidence_kind': kind})

    def commands(self, identity, at, deadline, targets, sequence=-1):
        # Each output must actually be issued after the trigger. A held prior
        # value cannot prove that a controller handled the fault.
        for channel, value in targets.items():
            self.obligation(identity, at, deadline, 'command',
                            lambda d, c=channel, v=value: d.get(c) == v, sequence)


def frames(events):
    measurements = {}
    state: dict[str, Any] = {'state': None, 'history': []}
    connection = None
    heartbeat = None
    valve = None
    previous_command = {'pump': 0.0, 'valve': 1.0}
    for now, grouped in groupby(events, key=lambda e: e['time_ms']):
        group = list(grouped)
        old_state = state['state']
        prior = dict(previous_command)
        for e in group:
            data = e['data']
            if e['kind'] == 'measurement':
                measurements[data['channel']] = data
            elif e['kind'] == 'state':
                state = data
            elif e['kind'] == 'connection':
                connection = data['connected']
            elif e['kind'] == 'heartbeat':
                heartbeat = data['received_at_ms']
            elif e['kind'] == 'actuator':
                valve = data['valve']
            elif e['kind'] == 'command':
                previous_command.update(data)
        yield {'time': now, 'measurements': dict(measurements), 'state': state,
               'old_state': old_state, 'connected': connection, 'heartbeat': heartbeat,
               'valve': valve, 'prior_command': prior, 'events': group}


def generic(ledger, rows, config):
    validator = Draft202012Validator(json.loads((SCHEMAS / 'rules-v1.json').read_text()))
    error = next(validator.iter_errors(config), None)
    if error:
        raise InputError('rule schema: ' + error.message)
    rules = config['rules']
    if len({r['id'] for r in rules}) != len(rules):
        raise InputError('duplicate requirement IDs')
    check_channels(ledger.events, config['channels'])
    for rule in rules:
        identity = rule['id']
        ledger.init(identity)
        kind = rule['type']
        if any(not finite(v) for k, v in rule.items() if k in ('min', 'max', 'max_age_ms', 'deadline_ms')):
            raise InputError('rule thresholds must be finite')
        if 'response' in rule and any(not finite(v) for v in rule['response'].values()):
            raise InputError('rule responses must be finite')
        if kind == 'response' and rule['trigger_kind'] not in {
                'measurement', 'command', 'state', 'tick', 'fault', 'request', 'command_result',
                'connection', 'heartbeat', 'actuator', 'injection', 'numerical'}:
            raise InputError('unsupported trigger kind')
        if 'response' in rule and 'deadline_ms' not in rule:
            raise InputError('response needs explicit deadline')
        if kind in ('range', 'sample_age'):
            channel = rule['channel']
            if channel not in config['channels']:
                raise InputError('rule references undeclared channel')
            applicable = [row for row in rows if 'when_state' not in rule or
                          row['state']['state'] == rule['when_state']]
            if not applicable:
                ledger.mark(identity, 'inconclusive', {'reason': 'no applicable observations'})
                continue
            numeric = []
            observed = []
            for row in applicable:
                m = row['measurements'].get(channel)
                if m is None or (kind == 'sample_age' and m['sample_time_ms'] is None):
                    ledger.mark(identity, 'inconclusive', {'time_ms': row['time'], 'reason': 'missing sample evidence'})
                    continue
                numeric.append(m['value'] if kind == 'range' else row['time'] - m['sample_time_ms'])
                observed.append(row)
            low, high = (rule['min'], rule['max']) if kind == 'range' else (0, rule['max_age_ms'])
            if low > high:
                raise InputError('inverted range')
            robust = range_robustness(numeric, low, high) if numeric else []
            for row, margin in zip(observed, robust, strict=True):
                m = row['measurements'][channel]
                if margin < 0 or m['quality'] != 'good':
                    if 'response' in rule:
                        ledger.commands(identity, row['time'], rule['deadline_ms'], rule['response'])
                    else:
                        ledger.mark(identity, 'fail', {'time_ms': row['time'], 'channel': channel,
                                                       'robustness': margin})
        elif kind == 'response':
            triggers = ledger.by_kind[rule['trigger_kind']]
            for e in triggers:
                ledger.commands(identity, e['time_ms'], rule['deadline_ms'], rule['response'], e['sequence'])
        elif kind == 'transition':
            prior = None
            for e in ledger.by_kind['state']:
                new = e['data']['state']
                if prior == rule['from'] and new == rule['to']:
                    ledger.mark(identity, 'fail', {'time_ms': e['time_ms'], 'from': prior, 'to': new})
                prior = new


def fluid(ledger, rows):
    for i in range(1, 13):
        ledger.init(f'I{i:02}')
    required = {'pressure1': 'Pa', 'pressure2': 'Pa', 'flow': 'm3/s'}
    pressure_margins = {}
    for channel in ('pressure1', 'pressure2'):
        values = [row['measurements'].get(channel, {}).get('value', 0) for row in rows]
        pressure_margins[channel] = range_robustness(values, 0, 200000) if values else []
    history: set[str] = set()
    acknowledged = True
    valid_since = None
    mismatch_since = None
    identities: dict[str, str] = {}
    prior_connected = None
    any_tick = False
    for index, row in enumerate(rows):
        if not any(e['kind'] == 'tick' for e in row['events']):
            continue
        any_tick = True
        now = row['time']
        state = row['state']['state']
        invalid = []
        missing = False
        for channel, unit in required.items():
            m = row['measurements'].get(channel)
            if m is None or m['sample_time_ms'] is None:
                missing = True
                ledger.mark('I03', 'inconclusive', {'time_ms': now, 'channel': channel, 'reason': 'sample time/channel absent'})
                continue
            if now - m['sample_time_ms'] > 200 or m['sample_time_ms'] > now:
                invalid.append('stale_input')
            if m['unit'] != unit:
                invalid.append('unit')
            if m['quality'] != 'good':
                invalid.append('quality')
            if channel.startswith('pressure') and pressure_margins[channel][index] < 0:
                invalid.append('range' if m['value'] < 0 or m['value'] > 300000 else 'overpressure')
        heartbeat_bad = row['heartbeat'] is not None and (now-row['heartbeat'] > 300 or row['heartbeat'] > now)
        if row['heartbeat'] is None:
            ledger.mark('I08', 'inconclusive', {'time_ms': now, 'reason': 'heartbeat absent'})
        if row['valve'] is None:
            ledger.mark('I12', 'inconclusive', {'time_ms': now, 'reason': 'actuator feedback absent'})
        elif abs(row['valve'] - row['prior_command']['valve']) > 0.2:
            if mismatch_since is None:
                mismatch_since = now
        else:
            mismatch_since = None
        mismatch_bad = mismatch_since is not None and now-mismatch_since > 500
        connected = row['connected']
        if connected is None:
            ledger.mark('I06', 'inconclusive', {'time_ms': now, 'reason': 'connection absent'})
        disconnect_bad = connected is False and (row['old_state'] == 'running' or (bool(history) and not acknowledged))
        active = bool(invalid) or heartbeat_bad or mismatch_bad or disconnect_bad
        if active or missing or not connected:
            valid_since = None
        elif valid_since is None:
            valid_since = now
        if invalid:
            ledger.obligation('I02', now, 10, 'state', lambda d: d['state'] != 'running')
            for cause in set(invalid) - history:
                ledger.obligation('I03', now, 10, 'fault', lambda d, c=cause: d['cause'] == c)
        if heartbeat_bad and 'heartbeat' not in history:
            ledger.obligation('I08', now, 10, 'fault', lambda d: d['cause'] == 'heartbeat')
        if mismatch_bad and 'valve_mismatch' not in history:
            ledger.obligation('I12', now, 10, 'fault', lambda d: d['cause'] == 'valve_mismatch')
        applied = [e['data']['command']['type'] for e in row['events']
                   if e['kind'] == 'command_result' and e['data']['outcome'] == 'applied']
        requests = {json.dumps(e['data'], sort_keys=True) for e in row['events'] if e['kind'] == 'request'}
        for e in row['events']:
            if e['kind'] == 'command_result' and json.dumps(e['data']['command'], sort_keys=True) not in requests:
                ledger.mark('I09', 'fail', {'time_ms': now, 'reason': 'outcome has no matching raw request'})
                if e['data']['command']['type'] == 'start':
                    ledger.mark('I01', 'fail', {'time_ms': now, 'reason': 'start has no explicit request'})
        if state == 'running' and row['old_state'] != 'running' and (
                row['old_state'] != 'armed' or 'start' not in applied or active or not acknowledged):
            ledger.mark('I01', 'fail', {'time_ms': now, 'reason': 'illegal running entry'})
        if 'stop' in applied and 'start' in applied and state == 'running':
            ledger.mark('I11', 'fail', {'time_ms': now})
        if prior_connected is False and connected is True and state == 'running':
            ledger.mark('I06', 'fail', {'time_ms': now, 'reason': 'reconnect restarted'})
        prior_connected = connected
        for e in row['events']:
            if e['kind'] == 'fault':
                history.add(e['data']['cause'])
                acknowledged = False
                ledger.commands('I04', now, 10, {'pump': 0}, e['sequence'])
                ledger.commands('I05', now, 10, {'valve': 1}, e['sequence'])
            if e['kind'] == 'command_result':
                d = e['data']
                cmd = d['command']
                payload = json.dumps(cmd, sort_keys=True)
                if cmd['command_id'] in identities:
                    old = identities[cmd['command_id']]
                    expected = 'duplicate' if old == payload else 'conflict'
                    if d['outcome'] != expected:
                        ledger.mark('I09', 'fail', {'time_ms': now, 'reason': 'duplicate outcome'})
                else:
                    identities[cmd['command_id']] = payload
                    expired = now > cmd['expires_at_ms'] or now < cmd['issued_at_ms']
                    if (d['outcome'] == 'expired') != expired:
                        ledger.mark('I10', 'fail', {'time_ms': now})
                    if expired:
                        ledger.obligation('I10', now, 10, 'fault', lambda x: x['cause'] == 'command_expiry')
        if not history.issubset(set(row['state']['history'])):
            ledger.mark('I07', 'fail', {'time_ms': now, 'reason': 'fault history lost'})
        if not acknowledged and state in ('ready', 'armed', 'running'):
            if state == 'ready' and 'ack' in applied and valid_since is not None and now-valid_since >= 1000:
                acknowledged = True
            else:
                ledger.mark('I07', 'fail', {'time_ms': now, 'reason': 'recovery evidence missing'})
        if 'ack' in applied and state == 'ready' and history and (valid_since is None or now-valid_since < 1000):
            ledger.mark('I07', 'fail', {'time_ms': now, 'reason': 'recovery window too short'})
    if not any_tick:
        for identity in ledger.checks:
            ledger.mark(identity, 'inconclusive', {'reason': 'no controller ticks'})


def monitor(events, *, rules=None, profile=None, seconds=MAX_SECONDS):
    started = time.perf_counter()
    validate_events(events, seconds=seconds)
    ledger = Ledger(events)
    rows = list(frames(events))
    if profile == 'fluid':
        fluid(ledger, rows)
    elif profile is not None:
        raise InputError('unknown monitor profile')
    if rules is not None:
        generic(ledger, rows, rules)
    if profile is None and rules is None:
        raise InputError('explicit rules or fluid profile required')
    if time.perf_counter() - started > seconds:
        raise InputError('elapsed-time limit; incomplete')
    checks = list(ledger.checks.values())
    status = 'fail' if any(c['status'] == 'fail' for c in checks) else (
        'inconclusive' if not events or not checks or any(c['status'] == 'inconclusive' for c in checks) else 'pass')
    return {'schema_version': 1, 'status': status,
            'window_ms': [events[0]['time_ms'], ledger.end] if events else None,
            'clock_assumptions': 'single monotonic simulation clock; integer ms; no extrapolation',
            'checks': checks}
