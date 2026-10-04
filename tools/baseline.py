"""Independently authored public-library spike. No AbyssBench imports."""
import importlib.metadata as md
import json
import time
from pathlib import Path

import openhtf as htf
import rtamt


def evaluate(signal, response):
    spec = rtamt.StlDiscreteTimeSpecification()
    spec.unit = 'ms'
    spec.set_sampling_period(10, 'ms', 0)
    spec.declare_var('trigger', 'float')
    spec.declare_var('safe', 'float')
    spec.spec = '(trigger > 0) implies eventually[0:10] (safe > 0)'
    spec.parse()
    return spec.evaluate({'time': list(range(0, 501, 10)),
                          'trigger': [1 if x else -1 for x in signal],
                          'safe': [1 if x else -1 for x in response]})


def main():
    started = time.perf_counter()
    times = list(range(0, 501, 10))
    cases = {}
    for name in ('stale', 'reconnect'):
        trigger = [int(t > 200) if name == 'stale' else int(t == 300) for t in times]
        for candidate in ('broken', 'corrected'):
            safe = [int(t >= (210 if name == 'stale' else 300))
                    if candidate == 'corrected' else 0 for t in times]
            robustness = evaluate(trigger, safe)
            # Last point lacks a complete future window; inspect completed prefix only.
            failed = any(r < 0 for t, r in robustness if t <= 490)
            cases[f'{name}-{candidate}'] = {'failed': failed, 'robustness': robustness,
                                           'window_ms': [0, 490]}
    records = []

    @htf.measures(htf.Measurement('stale_corrected').equals(True),
                  htf.Measurement('reconnect_corrected').equals(True))
    def replay(test):
        test.measurements.stale_corrected = not cases['stale-corrected']['failed']
        test.measurements.reconnect_corrected = not cases['reconnect-corrected']['failed']
        test.attach('requirement-verdicts.json', json.dumps(cases), mimetype='application/json')

    test = htf.Test(replay, test_name='AbyssBench M0 public-library comparison')
    test.add_output_callbacks(lambda record: records.append({
        'outcome': record.outcome.name,
        'attachments': [name for phase in record.phases for name in phase.attachments],
        'phase_outcomes': [phase.outcome.name for phase in record.phases]}))
    test.execute(test_start=lambda: 'synthetic-offline')
    output = {'versions': {name: md.version(name) for name in ('pytest', 'rtamt', 'openhtf')},
              'cases': cases, 'openhtf': records,
              'elapsed_seconds': time.perf_counter() - started}
    Path('evidence/baseline.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    assert cases['stale-broken']['failed'] and cases['reconnect-broken']['failed']
    assert not cases['stale-corrected']['failed'] and not cases['reconnect-corrected']['failed']
    assert records[0]['outcome'] == 'PASS'


if __name__ == '__main__':
    main()
