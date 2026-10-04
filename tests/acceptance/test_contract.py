"""Independent contract expectations, written before the product modules.

No expected value is computed with a controller/plant/monitor helper.
"""
import json
from pathlib import Path

import pytest

from abyssbench import Command, FluidController, Measurement, Tick, monitor, run

ORACLE = json.loads((Path(__file__).parents[1] / 'oracle/expectations.json').read_text())


def readings(now, sample=None, pressure=1000, quality='good', unit='Pa'):
    return {c: Measurement(c, v, u, now if sample is None else sample, now,
                           quality, now, 'synthetic-test')
            for c, v, u in [('pressure1', pressure, unit), ('pressure2', pressure, unit),
                            ('flow', 0.0, 'm3/s')]}


def tick(now, requests=(), **kwargs):
    defaults = dict(measurements=readings(now), connected=True, heartbeat_ms=now,
                    valve_position=1.0, requests=tuple(requests))
    defaults.update(kwargs)
    return Tick(now, **defaults)


def request(name, now, identity=None, issued=None, payload=None):
    issue = now if issued is None else issued
    return Command(identity or f'{name}-{now}', name, payload or {}, issue, issue + 100)


@pytest.mark.requirements('AB-02', 'AB-04')
@pytest.mark.parametrize('age, expected', ORACLE['freshness'].items())
def test_sample_age_boundaries(age, expected):
    c = FluidController()
    c.step(tick(0))
    c.step(tick(10, [request('arm', 10)]))
    c.step(tick(20, [request('start', 20)]))
    result = c.step(tick(300, measurements=readings(300, 300-int(age))))
    assert result.state == ('running' if expected == 'valid' else 'fault')


@pytest.mark.requirements('AB-03')
@pytest.mark.parametrize('state', ORACLE['state_table'])
@pytest.mark.parametrize('event', ORACLE['state_events'])
def test_all_state_event_pairs(state, event):
    c = FluidController()
    c.state = state
    c.connected = state != 'disconnected'
    if event == 'connect':
        c.connected = False
    if state in ('fault', 'recovery_required'):
        c.history = ['old_fault']
        c.acknowledged = False
    c.valid_since = 0
    requests = [request(event, 1000)] if event not in ('connect', 'disconnect', 'fault') else []
    connection = event == 'connect' or state != 'disconnected'
    result = c.step(tick(1000, requests, connected=connection and event != 'disconnect',
                         measurements=readings(1000, quality='bad') if event == 'fault' else readings(1000)))
    index = ORACLE['state_events'].index(event)
    assert result.state == ORACLE['state_table'][state][index]


@pytest.mark.requirements('AB-07')
@pytest.mark.parametrize('age, outcome', ORACLE['command_age'].items())
def test_expiry_boundary(age, outcome):
    c = FluidController()
    result = c.step(tick(int(age), [request('arm', int(age), issued=0)]))
    assert result.outcomes[0]['outcome'] == outcome


@pytest.mark.requirements('AB-07')
def test_duplicate_and_conflicting_identity():
    c = FluidController()
    cmd = request('arm', 0, 'one')
    assert c.step(tick(0, [cmd])).outcomes[0]['outcome'] == 'applied'
    assert c.step(tick(10, [cmd])).outcomes[0]['outcome'] == 'duplicate'
    assert c.step(tick(20, [request('start', 0, 'one')])).outcomes[0]['outcome'] == 'conflict'


@pytest.mark.requirements('AB-01', 'AB-05', 'AB-08')
@pytest.mark.parametrize('fault, expected', ORACLE['fault_scenarios'].items())
def test_deterministic_fault_schedule(fault, expected):
    events = run(fault=fault)
    assert events == run(fault=fault)
    faults = [e for e in events if e['kind'] == 'fault']
    assert faults[0]['time_ms'] == expected['detection_ms']
    safe = [e for e in events if e['kind'] == 'command' and e['time_ms'] >= faults[0]['time_ms']]
    assert safe[0]['data']['pump'] == 0
    assert safe[0]['data']['valve'] == 1
    assert safe[0]['time_ms'] - faults[0]['time_ms'] <= 10
    result = monitor(events, profile='fluid')
    assert result['status'] == 'pass', result
    assert {v['id'] for v in result['checks']} >= set(ORACLE['invariants'])


@pytest.mark.requirements('AB-01', 'AB-12')
def test_healthy():
    events = run()
    assert not any(e['kind'] == 'fault' for e in events)
    assert monitor(events, profile='fluid')['status'] == 'pass'


@pytest.mark.requirements('AB-06')
def test_recovery_requires_all_steps():
    c = FluidController()
    for t, action in [(0, None), (10, 'arm'), (20, 'start')]:
        c.step(tick(t, [] if action is None else [request(action, t)]))
    assert c.step(tick(30, connected=False)).state == 'fault'
    assert c.step(tick(40, [request('start', 40)])).state == 'recovery_required'
    assert c.step(tick(1030, [request('ack', 1030)])).state == 'recovery_required'
    assert c.step(tick(1040, [request('ack', 1040)])).state == 'ready'
    assert c.step(tick(1050, [request('start', 1050)])).state == 'ready'
    assert c.step(tick(1060, [request('arm', 1060)])).state == 'armed'
    assert c.step(tick(1070, [request('start', 1070)])).state == 'running'
    assert c.history == ['disconnect']


@pytest.mark.requirements('AB-03')
def test_stop_wins_and_arm_start_are_separate():
    c = FluidController()
    assert c.step(tick(0, [request('arm', 0), request('start', 0)])).state == 'armed'
    assert c.step(tick(10, [request('stop', 10), request('start', 10)])).state == 'ready'


@pytest.mark.requirements('AB-08')
def test_heartbeat_and_actuator_boundaries():
    c = FluidController()
    assert c.step(tick(300, heartbeat_ms=0)).state == 'ready'
    assert c.step(tick(301, heartbeat_ms=0)).state == 'fault'
    c = FluidController()
    assert c.step(tick(0, valve_position=0.8)).state == 'ready'
    assert c.step(tick(500, valve_position=0.8)).state == 'ready'
    assert c.step(tick(510, valve_position=0.79)).state == 'ready'
    assert c.step(tick(1010, valve_position=0.79)).state == 'ready'
    assert c.step(tick(1011, valve_position=0.79)).state == 'fault'
