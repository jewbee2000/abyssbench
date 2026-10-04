"""Non-executable bounded trace import; ordered logs retain unordered packets."""
import csv
import json
import math
import time
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .contracts import InputError, finite

MAX_BYTES = 20 * 1024 * 1024
MAX_EVENTS = 100000
MAX_SECONDS = 60.0
SCHEMAS = Path(__file__).parent / 'schemas'
EVENT_VALIDATOR = Draft202012Validator(json.loads((SCHEMAS / 'event-v1.json').read_text()))


def has_nonfinite(value):
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, dict):
        return any(has_nonfinite(v) for v in value.values())
    if isinstance(value, list):
        return any(has_nonfinite(v) for v in value)
    return False


def load_json(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise InputError('input exceeds 20 MiB')
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'),
                          parse_constant=lambda s: (_ for _ in ()).throw(InputError('nonfinite JSON')))
    except (ValueError, OSError) as error:
        raise InputError(str(error)) from error


def validate_events(events, *, seconds=MAX_SECONDS):
    started = time.perf_counter()
    if len(events) > MAX_EVENTS:
        raise InputError('input exceeds 100000 events; incomplete')
    last = -1
    for index, item in enumerate(events):
        if time.perf_counter() - started > seconds:
            raise InputError('elapsed-time limit; incomplete')
        if has_nonfinite(item):
            raise InputError(f'event {index}: nonfinite numeric evidence')
        error = next(EVENT_VALIDATOR.iter_errors(item), None)
        if error:
            raise InputError(f'event {index}: {error.message}')
        if type(item['time_ms']) is not int or type(item['sequence']) is not int:
            raise InputError('event times and sequence must be integers')
        if item['sequence'] != index or item['time_ms'] < last:
            raise InputError('unordered event log')
        last = item['time_ms']
        if item['kind'] == 'measurement':
            d = item['data']
            if not finite(d['value']) or d['receive_time_ms'] != item['time_ms']:
                raise InputError('measurement must be finite with event time equal to receive time')
        if item['kind'] == 'command' and (not item['data'] or any(not finite(v) for v in item['data'].values())):
            raise InputError('commands require finite numeric actuator fractions')
    return events


def check_channels(events, units):
    channels = set()
    for e in events:
        if e['kind'] == 'measurement':
            m = e['data']
            channels.add(m['channel'])
            if m['channel'] in units and m['unit'] != units[m['channel']]:
                raise InputError('unit mismatch: ' + m['channel'])
    if set(units) - channels:
        raise InputError('missing required channels: ' + ','.join(sorted(set(units) - channels)))


def read_jsonl(path, *, units=None):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise InputError('input exceeds 20 MiB; incomplete')
    events: list[dict[str, Any]] = []
    started = time.perf_counter()
    try:
        with path.open(encoding='utf-8-sig') as source:
            for line in source:
                if time.perf_counter() - started > MAX_SECONDS or len(events) >= MAX_EVENTS:
                    raise InputError('input resource limit; incomplete')
                events.append(json.loads(line))
    except (ValueError, OSError) as error:
        raise InputError(str(error)) from error
    validate_events(events)
    if units:
        check_channels(events, units)
    return events


def read_csv(path, column_map):
    """Explicit envelope-column map plus channel units; data column contains JSON."""
    if set(column_map) != {'columns', 'units', 'clock', 'schema_version'}:
        raise InputError('CSV needs columns, units, clock and schema_version')
    columns = column_map['columns']
    if set(columns) != {'sequence', 'time_ms', 'kind', 'data'} or len(set(columns.values())) != 4:
        raise InputError('CSV envelope columns must be mapped unambiguously')
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise InputError('input exceeds 20 MiB; incomplete')
    events: list[dict[str, Any]] = []
    started = time.perf_counter()
    try:
        with path.open(newline='', encoding='utf-8-sig') as source:
            reader = csv.DictReader(source)
            if set(columns.values()) - set(reader.fieldnames or []):
                raise InputError('mapped CSV columns missing')
            for row in reader:
                if len(events) >= MAX_EVENTS or time.perf_counter() - started > MAX_SECONDS:
                    raise InputError('CSV resource limit; incomplete')
                events.append({'schema_version': column_map['schema_version'],
                               'clock': column_map['clock'], 'sequence': int(row[columns['sequence']]),
                               'time_ms': int(row[columns['time_ms']]), 'kind': row[columns['kind']],
                               'data': json.loads(row[columns['data']])})
    except (ValueError, KeyError, OSError) as error:
        raise InputError(str(error)) from error
    validate_events(events)
    if not column_map['units']:
        raise InputError('explicit CSV units required')
    check_channels(events, column_map['units'])
    return events


def write_jsonl(path, events):
    validate_events(events)
    with Path(path).open('w', encoding='utf-8', newline='\n') as output:
        output.writelines(json.dumps(e, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n' for e in events)
