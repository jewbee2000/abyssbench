"""Freeze separately authored thermal events; never imports product code."""
import csv
import json
from pathlib import Path

destination = Path('tests/oracle')
rules = {'schema_version': 1, 'channels': {'temperature': 'degC'}, 'rules': [
    {'id': 'TH-01', 'type': 'sample_age', 'channel': 'temperature', 'max_age_ms': 75,
     'response': {'heater': 0}, 'deadline_ms': 15},
    {'id': 'TH-02', 'type': 'response', 'trigger_kind': 'fault', 'response': {'heater': 0}, 'deadline_ms': 15},
    {'id': 'TH-03', 'type': 'range', 'channel': 'temperature', 'min': 0, 'max': 120},
    {'id': 'TH-04', 'type': 'transition', 'from': 'fault', 'to': 'heating'}]}
mapping = {'schema_version': 1, 'clock': 'simulation', 'units': {'temperature': 'degC'},
           'columns': {'sequence': 'row', 'time_ms': 'ms', 'kind': 'event', 'data': 'payload'}}
(destination / 'thermal-rules.json').write_text(json.dumps(rules, indent=2))
(destination / 'csv-map.json').write_text(json.dumps(mapping, indent=2))
for name in ('valid', 'violating', 'incomplete'):
    events = []
    def emit(at, kind, data):
        events.append({'schema_version': 1, 'clock': 'simulation', 'sequence': len(events),
                       'time_ms': at, 'kind': kind, 'data': data})
    emit(0, 'measurement', {'channel': 'temperature', 'value': 25, 'unit': 'degC',
                          'sample_time_ms': 0, 'receive_time_ms': 0, 'quality': 'good',
                          'sequence': 0, 'calibration_id': 'synthetic-thermal'})
    emit(0, 'state', {'state': 'heating', 'history': []})
    emit(0, 'command', {'heater': 1})
    emit(75, 'tick', {})  # equality is fresh, heater still on
    emit(80, 'fault', {'cause': 'stale-temperature'})
    emit(80, 'state', {'state': 'fault', 'history': ['stale-temperature']})
    if name != 'incomplete':
        emit(95, 'command', {'heater': 0 if name == 'valid' else 1})
    emit(80 if name == 'incomplete' else 95, 'tick', {})
    with (destination / f'thermal-{name}.jsonl').open('w', newline='\n') as output:
        for e in events:
            output.write(json.dumps(e) + '\n')
    with (destination / f'thermal-{name}.csv').open('w', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(['row', 'ms', 'event', 'payload'])
        for e in events:
            writer.writerow([e['sequence'], e['time_ms'], e['kind'], json.dumps(e['data'])])
