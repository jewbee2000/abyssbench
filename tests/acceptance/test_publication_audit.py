"""Literal regression traces found during the separate publication audit."""
import pytest

from abyssbench import monitor


def trace(rows):
    return [{'schema_version': 1, 'clock': 'simulation', 'sequence': i,
             'time_ms': at, 'kind': kind, 'data': data}
            for i, (at, kind, data) in enumerate(rows)]


def measurement(at, value, sampled=None):
    return {'channel': 'temperature', 'value': value, 'unit': 'degC',
            'sample_time_ms': at if sampled is None else sampled, 'receive_time_ms': at,
            'quality': 'good', 'sequence': at, 'calibration_id': 'synthetic-audit'}


def rules(rule):
    return {'schema_version': 1, 'channels': {'temperature': 'degC'}, 'rules': [rule]}


@pytest.mark.requirements('AB-16', 'AB-19')
@pytest.mark.parametrize('value, expected', [(0, 'pass'), (120, 'pass'), (121, 'fail')])
def test_single_observation_range_keeps_its_actual_window(value, expected):
    result = monitor(trace([(100, 'measurement', measurement(100, value))]),
                     rules=rules({'id': 'RANGE', 'type': 'range', 'channel': 'temperature',
                                  'min': 0, 'max': 120}))
    assert result['status'] == expected
    assert result['window_ms'] == [100, 100]


@pytest.mark.requirements('AB-02', 'AB-16')
@pytest.mark.parametrize('kind', ['range', 'sample_age'])
@pytest.mark.parametrize('command_after, expected', [(False, 'fail'), (True, 'pass')])
def test_response_cannot_precede_its_measurement_at_the_same_timestamp(kind, command_after,
                                                                     expected):
    # End with a good measurement so only the 100 ms observation creates an
    # obligation. The literal deadline is zero: timestamp and sequence matter.
    bad = (100, 'measurement', measurement(100, 121 if kind == 'range' else 20, 0))
    safe = (100, 'command', {'heater': 0})
    rows = [bad, safe] if command_after else [safe, bad]
    rows.append((101, 'measurement', measurement(101, 20)))
    rule = {'id': 'SAFE', 'type': kind, 'channel': 'temperature',
            'response': {'heater': 0}, 'deadline_ms': 0}
    rule.update({'min': 0, 'max': 120} if kind == 'range' else {'max_age_ms': 75})
    result = monitor(trace(rows), rules=rules(rule))
    assert result['status'] == expected


@pytest.mark.requirements('AB-16')
def test_single_observation_does_not_complete_a_future_response_window():
    rule = {'id': 'SAFE', 'type': 'range', 'channel': 'temperature', 'min': 0, 'max': 120,
            'response': {'heater': 0}, 'deadline_ms': 10}
    result = monitor(trace([(100, 'measurement', measurement(100, 121))]), rules=rules(rule))
    assert result['status'] == 'inconclusive'
    assert result['window_ms'] == [100, 100]
