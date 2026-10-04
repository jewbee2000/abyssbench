import copy
import json
from pathlib import Path

from hypothesis import given, settings, strategies as st
from hypothesis.database import DirectoryBasedExampleDatabase
import pytest

from abyssbench import Command, FluidController, InputError, Recipe, monitor, run, write_jsonl
from abyssbench.runner import Plant


@pytest.mark.requirements('AB-09')
@pytest.mark.parametrize('defect, fault, target', [
    ('freshness_receive', 'freeze', 'I03'), ('inverted_valve', 'range', 'I05'),
    ('pressure_unit', None, 'I03'), ('unsafe_reconnect', 'disconnect', 'I06'),
    ('unbounded_retry', 'range', 'I04'), ('lost_latch', 'disconnect', 'I07')])
def test_six_real_controller_mutations(defect, fault, target):
    events = run(FluidController(defect=defect), fault=fault)
    result = monitor(events, profile='fluid')
    assert result['status'] == 'fail'
    assert next(c for c in result['checks'] if c['id'] == target)['status'] == 'fail'
    destination = Path('evidence/failed-candidates')
    destination.mkdir(exist_ok=True)
    write_jsonl(destination / f'{defect}.jsonl', events)
    (destination / f'{defect}.json').write_text(json.dumps(result, indent=2))
    assert monitor(run(FluidController(), fault=fault), profile='fluid')['status'] == 'pass'


@pytest.mark.requirements('AB-09', 'AB-12')
@pytest.mark.parametrize('identity', [f'I{i:02}' for i in range(1, 13)])
def test_each_monitor_invariant_has_a_negative_control(identity):
    # These are event edits, independent of the controller's defect switches.
    # Time/sequence are retained and literal expected invariant IDs are fixed.
    scenario = 'range' if identity in ('I04', 'I05', 'I07') else None
    events = copy.deepcopy(run(fault=scenario))
    for e in events:
        now, kind, d = e['time_ms'], e['kind'], e['data']
        if identity == 'I01' and kind == 'state' and now == 10:
            d['state'] = 'running'
        if identity in ('I02', 'I03'):
            if kind == 'measurement' and now >= 500:
                d['sample_time_ms'] = 100
        if identity == 'I04' and kind == 'command' and now >= 500:
            d['pump'] = 1
        if identity == 'I05' and kind == 'command' and now >= 500:
            d['valve'] = 0
        if identity == 'I06' and kind == 'connection' and now == 0:
            d['connected'] = False
        if identity == 'I07' and kind == 'state' and now >= 500:
            d['history'] = []
        if identity == 'I08' and kind == 'heartbeat':
            d['received_at_ms'] = 0
        if identity == 'I09' and kind == 'command_result' and now == 20:
            d['command']['command_id'] = 'arm-10'
        if identity == 'I10' and kind == 'command_result' and now == 20:
            d['command']['expires_at_ms'] = 19
        if identity == 'I11' and kind == 'command_result' and now == 1450:
            d['command']['type'] = 'start'
        if identity == 'I12' and kind == 'actuator' and now >= 500:
            d['valve'] = 0
    if identity == 'I06':
        events.insert(0, {'schema_version': 1, 'clock': 'simulation', 'sequence': 0,
                          'time_ms': 0, 'kind': 'connection', 'data': {'connected': False}})
        # Explicit disconnect observation at a prior tick and reconnect while running.
        for e in events:
            if e['kind'] == 'connection':
                e['data']['connected'] = False
        index = next(i for i, e in enumerate(events) if e['time_ms'] == 30)
        events.insert(index, {'schema_version': 1, 'clock': 'simulation', 'sequence': 0,
                              'time_ms': 30, 'kind': 'connection', 'data': {'connected': True}})
    if identity == 'I11':
        # Same-tick accepted stop + start with running retained.
        index = next(i for i, e in enumerate(events) if e['kind'] == 'command_result' and e['time_ms'] == 1450)
        extra = copy.deepcopy(events[index])
        extra['data']['command']['type'] = 'stop'
        extra['data']['command']['command_id'] = 'stop-parallel'
        events.insert(index, extra)
        for e in events:
            if e['kind'] == 'state' and e['time_ms'] >= 1450:
                e['data']['state'] = 'running'
    for index, e in enumerate(events):
        e['sequence'] = index
    checks = monitor(events, profile='fluid')['checks']
    assert next(c for c in checks if c['id'] == identity)['status'] == 'fail'


@pytest.mark.requirements('AB-11')
@given(st.lists(st.sampled_from(['arm', 'start', 'stop', 'ack']), min_size=1, max_size=25),
       st.sampled_from([None, 'freeze', 'disconnect', 'range', 'delay']),
       st.integers(min_value=0, max_value=100000))
@settings(max_examples=1000, deadline=None,
          database=DirectoryBasedExampleDatabase('evidence/hypothesis-counterexamples'))
def test_1000_bounded_sequences(actions, fault, seed):
    schedule = {}
    for index, name in enumerate(actions):
        now = index * 10
        schedule[now] = [Command(f'c{index}', name, {}, now, now+100)]
        if index % 7 == 0:
            schedule[now].append(Command(f'c{index}', name, {}, now, now+100))
    result = monitor(run(requests=schedule, fault=fault, seed=seed, duration_ms=700), profile='fluid')
    assert result['status'] == 'pass', result


@pytest.mark.requirements('AB-11')
@pytest.mark.parametrize('mutation', ['nan', 'inf', 'unit', 'unknown', 'duration'])
def test_recipe_invalid_input(mutation):
    recipe = {'version': 1, 'preconditions': {'pressure1': 'Pa', 'pressure2': 'Pa', 'flow': 'm3/s'},
              'steps': [{'duration_ms': 100, 'pump': 0.5, 'valve': 1}],
              'stop_conditions': {'pressure_max_Pa': 200000}, 'max_duration_ms': 100}
    if mutation in ('nan', 'inf'):
        recipe['steps'][0]['pump'] = float(mutation)
    elif mutation == 'unit':
        recipe['preconditions']['pressure1'] = 'kPa'
    elif mutation == 'unknown':
        recipe['expression'] = '__import__'
    else:
        recipe['steps'][0]['duration_ms'] = 101
    with pytest.raises(InputError):
        Recipe.from_dict(recipe)


@pytest.mark.requirements('AB-01')
def test_hand_calculated_plant_and_convergence():
    # First 10 ms pump update = 0.1, inlet 3e-6 m3/s, outlet 0,
    # pressure increment 0.01 * 3e-6 / 1e-8 = 3 Pa.
    p = Plant()
    flow, clamp = p.step({'pump': 1, 'valve': 0})
    assert p.pressure == pytest.approx(3)
    assert flow == 0 and clamp is False
    p = Plant()
    p.step({'pump': 0, 'valve': 1})
    assert p.pressure == 0
    finals = []
    for dt in (10, 5, 1):
        p = Plant()
        for _ in range(1000//dt):
            p.step({'pump': 0.5, 'valve': 0.6}, dt_ms=dt)
        finals.append(p.pressure)
    assert abs(finals[1]-finals[2]) < abs(finals[0]-finals[2])
    assert abs(finals[0]-finals[2]) / finals[2] < 0.03
