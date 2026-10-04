"""Measured local scope; raw library timing is narrower than full validation."""
import gc
import json
import threading
import time
from pathlib import Path

import openhtf as htf
import psutil
import rtamt

from abyssbench import monitor, run
from abyssbench.recording import metadata, sha256


def measure(call):
    gc.collect()
    stop = threading.Event()
    process = psutil.Process()
    rss = [process.memory_info().rss]
    def sample():
        while not stop.wait(0.005):
            rss.append(process.memory_info().rss)
    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    started = time.perf_counter()
    try:
        result = call()
        elapsed = time.perf_counter()-started
    finally:
        stop.set()
        thread.join()
    rss.append(process.memory_info().rss)
    return {'elapsed_seconds': elapsed, 'peak_rss_bytes': max(rss), 'result': result}


def main():
    events = run(duration_ms=18000)[:10000]
    values = [e['data']['value'] for e in events if e['kind'] == 'measurement' and e['data']['channel'] == 'pressure1']
    def baseline():
        spec = rtamt.StlDiscreteTimeSpecification()
        spec.declare_var('pressure', 'float')
        spec.spec = '(pressure >= 0) and (pressure <= 200000)'
        spec.parse()
        robust = spec.evaluate({'time': list(range(len(values))), 'pressure': values})
        return 'pass' if all(r >= 0 for _, r in robust) else 'fail'
    def openhtf():
        results = []
        @htf.measures(htf.Measurement('within_range').equals(True))
        def phase(test):
            test.measurements.within_range = baseline() == 'pass'
        test = htf.Test(phase, test_name='Offline baseline resource measurement')
        test.add_output_callbacks(lambda record: results.append(record.outcome.name))
        test.execute(test_start=lambda: 'synthetic')
        return results[0]
    results = {'full_event_validation_and_12_invariants': [measure(lambda: monitor(events, profile='fluid')['status']) for _ in range(3)],
               'rtamt_pressure_predicate_only': [measure(baseline) for _ in range(3)],
               'openhtf_phase_plus_pressure_predicate': [measure(openhtf) for _ in range(3)]}
    output = {'event_count': len(events), 'input_hash': sha256(json.dumps(events, sort_keys=True).encode()),
              'source': metadata(), 'method': 'perf_counter; RSS sampled every 5 ms in same warmed process; 3 sequential repetitions; includes live Python heap, excludes child processes',
              'comparison_limit': 'RTAMT/OpenHTF pressure-only baselines do less work than full replay evaluator; no speedup claim',
              'results': results}
    Path('evidence/performance.json').write_text(json.dumps(output, indent=2))
    assert all(r['result'] == 'pass' and r['elapsed_seconds'] < 10 and r['peak_rss_bytes'] < 256*1024*1024
               for r in results['full_event_validation_and_12_invariants'])


if __name__ == '__main__':
    main()
