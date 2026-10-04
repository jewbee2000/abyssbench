"""Deterministic synthetic fluid plant and trusted controller adapter."""
from dataclasses import dataclass
import math
import random

from .contracts import Command, Controller, InputError, Measurement, Tick, finite
from .controller import FluidController

MODEL = {'compliance': 1e-8, 'pump_conductance': 1e-10, 'max_head_Pa': 300000,
         'pump_tau_ms': 100, 'valve_tau_ms': 200, 'K_m3_s': 2e-5, 'P_ref_Pa': 100000}
FAULTS = {'freeze', 'disconnect', 'range', 'stuck', 'delay'}


@dataclass
class Plant:
    pressure: float = 0.0
    pump: float = 0.0
    valve: float = 1.0

    def step(self, outputs, dt_ms=10, stuck=False):
        if not 0 < dt_ms <= 10 or any(not finite(v) or not 0 <= v <= 1 for v in outputs.values()):
            raise InputError('invalid integration step or actuator fraction')
        self.pump += dt_ms / 100 * (outputs['pump'] - self.pump)
        self.valve = 0.0 if stuck else self.valve + dt_ms / 200 * (outputs['valve'] - self.valve)
        q_in = 1e-10 * max(300000 * self.pump - self.pressure, 0)
        q_out = 2e-5 * self.valve * math.sqrt(max(self.pressure, 0) / 100000)
        proposed = self.pressure + dt_ms / 1000 * (q_in - q_out) / 1e-8
        if not math.isfinite(proposed):
            raise InputError('nonfinite plant state')
        self.pressure = max(proposed, 0)
        return q_out, proposed < 0


def event(sequence, time_ms, kind, data):
    return {'schema_version': 1, 'clock': 'simulation', 'sequence': sequence,
            'time_ms': time_ms, 'kind': kind, 'data': data}


def run(controller: Controller | None = None, *, fault=None, seed=0, duration_ms=1500,
        requests=None, noise=0.0):
    """Invoke trusted Python controller on 10 ms ticks; return raw ordered events.

    Default arm/start at 10/20 ms, stop at 1450. Fault onset is 500 ms.
    Caller may supply a {time_ms: [Command]} schedule instead.
    """
    if fault is not None and fault not in FAULTS:
        raise InputError('unknown fault schedule')
    if type(duration_ms) is not int or not 20 <= duration_ms <= 60000 or duration_ms % 10:
        raise InputError('duration must be 20..60000 ms, multiple of 10')
    if not finite(noise) or noise < 0:
        raise InputError('noise must be finite and nonnegative')
    ctrl = controller or FluidController()
    rng = random.Random(seed)
    plant = Plant()
    outputs = {'pump': 0.0, 'valve': 1.0}
    readings = {}
    events = []
    if requests is None:
        requests = {t: [Command(f'{name}-{t}', name, {}, t, t + 100)]
                    for t, name in [(10, 'arm'), (20, 'start'), (1450, 'stop')]}

    def emit(now, kind, data):
        events.append(event(len(events), now, kind, data))

    last_connection = None
    for now in range(0, duration_ms + 1, 10):
        flow, clamped = plant.step(outputs, stuck=fault == 'stuck' and now >= 500)
        if clamped:
            emit(now, 'numerical', {'pressure_clamped': True})
        connected = not (fault == 'disconnect' and 500 <= now < 700)
        if connected != last_connection:
            emit(now, 'connection', {'connected': connected})
            last_connection = connected
        emit(now, 'heartbeat', {'received_at_ms': now})
        if now == 500 and fault:
            emit(now, 'injection', {'fault': fault, 'onset_ms': 500})
        if now % 50 == 0:
            for channel, value, unit in [('pressure1', plant.pressure, 'Pa'),
                                          ('pressure2', plant.pressure * 0.98, 'Pa'),
                                          ('flow', flow, 'm3/s')]:
                sample = now
                if fault == 'freeze' and now >= 500:
                    sample = 450
                    value = readings[channel].value
                if fault == 'delay' and now == 500:
                    sample = 100
                if fault == 'range' and now >= 500 and channel == 'pressure1':
                    value = 310000
                if getattr(ctrl, 'defect', None) == 'pressure_unit' and now >= 500 and channel == 'pressure1':
                    unit = 'kPa'
                    value /= 1000
                m = Measurement(channel, value + rng.uniform(-noise, noise), unit, sample,
                                now, 'good', sample // 50, 'synthetic-identity-v1')
                readings[channel] = m
                emit(now, 'measurement', m.to_dict())
        emit(now, 'actuator', {'valve': plant.valve})
        commands = tuple(requests.get(now, []))
        for command in commands:
            emit(now, 'request', command.to_dict())
        result = ctrl.step(Tick(now, dict(readings), connected, now, plant.valve, commands))
        for outcome in result.outcomes:
            emit(now, 'command_result', outcome)
        for cause in result.detected:
            emit(now, 'fault', {'cause': cause})
        outputs = dict(result.commands)
        if set(outputs) != {'pump', 'valve'} or any(not finite(v) or not 0 <= v <= 1 for v in outputs.values()):
            raise InputError('controller returned invalid actuator outputs')
        emit(now, 'command', outputs)
        emit(now, 'state', {'state': result.state, 'history': list(result.history)})
        emit(now, 'tick', {})
    return events
