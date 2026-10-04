import pytest

from abyssbench import InputError, monitor, run


@pytest.mark.requirements('AB-16', 'AB-19')
@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_nonfinite_actuator_evidence_is_rejected(value):
    events = run()
    for e in events:
        if e['kind'] == 'actuator':
            e['data']['valve'] = value
    with pytest.raises(InputError):
        monitor(events, profile='fluid')
