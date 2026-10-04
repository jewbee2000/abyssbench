"""Reference controller. Monitor deliberately has no imports from this module."""
import json

from .contracts import Recipe, Tick, TickResult


class FluidController:
    version = 'fluid-v1'

    def __init__(self, recipe=None, defect=None):
        self.recipe = Recipe.from_dict((recipe or Recipe()).to_dict())
        self.defect = defect
        self.state = 'disconnected'
        self.connected = False
        self.history: list[str] = []
        self.acknowledged = True
        self.valid_since: int | None = None
        self.mismatch_since: int | None = None
        self.outputs = {'pump': 0.0, 'valve': 1.0}
        self.identities: dict[str, tuple[str, str]] = {}
        self.started_at: int | None = None

    def step(self, tick: Tick) -> TickResult:
        now = tick.time_ms
        previous = self.state
        active = []
        for channel, unit in self.recipe.preconditions.items():
            m = tick.measurements.get(channel)
            if m is None:
                active.append('missing_input')
                continue
            sample = m.receive_time_ms if self.defect == 'freshness_receive' else m.sample_time_ms
            if sample is None or now - sample > 200 or sample > now:
                active.append('stale_input')
            if m.quality != 'good':
                active.append('quality')
            if m.unit != unit and self.defect != 'pressure_unit':
                active.append('unit')
            if channel.startswith('pressure'):
                if m.value < 0 or m.value > 300000:
                    active.append('range')
                elif m.value > self.recipe.stop_conditions['pressure_max_Pa']:
                    active.append('overpressure')
        if now - tick.heartbeat_ms > 300 or tick.heartbeat_ms > now:
            active.append('heartbeat')
        if abs(tick.valve_position - self.outputs['valve']) > 0.2:
            if self.mismatch_since is None:
                self.mismatch_since = now
            if now - self.mismatch_since > 500:
                active.append('valve_mismatch')
        else:
            self.mismatch_since = None
        if not tick.connected:
            if self.state in ('running', 'fault'):
                active.append('disconnect')
            else:
                self.state = 'disconnected'
        elif not self.connected:
            if self.history and not self.acknowledged:
                self.state = 'recovery_required'
                if self.defect == 'unsafe_reconnect':
                    self.state = 'running'
                elif self.defect == 'lost_latch':
                    self.history = []
                    self.acknowledged = True
                    self.state = 'ready'
            elif self.state == 'disconnected':
                self.state = 'ready'
        self.connected = tick.connected
        accepted = []
        outcomes = []
        for cmd in tick.requests:
            signature = json.dumps(cmd.to_dict(), sort_keys=True)
            if cmd.command_id in self.identities:
                old, outcome = self.identities[cmd.command_id]
                outcome = 'duplicate' if old == signature else 'conflict'
            elif now > cmd.expires_at_ms or now < cmd.issued_at_ms:
                outcome = 'expired'
                active.append('command_expiry')
                self.identities[cmd.command_id] = (signature, outcome)
            else:
                outcome = 'applied'
                accepted.append(cmd.type)
                self.identities[cmd.command_id] = (signature, outcome)
            outcomes.append({'command': cmd.to_dict(), 'outcome': outcome,
                             'previous_outcome': self.identities.get(cmd.command_id, ('', 'conflict'))[1]})
        detected = []
        if active and (tick.connected or previous != 'disconnected' or bool(tick.measurements)):
            self.state = 'fault'
            self.acknowledged = False
            for cause in dict.fromkeys(active):
                if cause not in self.history:
                    self.history.append(cause)
                    detected.append(cause)
            self.valid_since = None
        elif tick.connected:
            if self.valid_since is None:
                self.valid_since = now
            if 'stop' in accepted:
                if self.state in ('running', 'armed'):
                    self.state = 'ready'
            elif 'ack' in accepted and self.state in ('fault', 'recovery_required'):
                if now - self.valid_since >= 1000:
                    self.state = 'ready'
                    self.acknowledged = True
            elif 'arm' in accepted and self.state == 'ready':
                self.state = 'armed'
            elif 'start' in accepted and self.state == 'armed' and previous == 'armed':
                self.state = 'running'
                self.started_at = now
        else:
            self.valid_since = None
        outputs = {'pump': 0.0, 'valve': 1.0}
        if self.state == 'running':
            elapsed = now - (self.started_at if self.started_at is not None else now)
            for step in self.recipe.steps:
                if elapsed < step['duration_ms']:
                    outputs = {'pump': step['pump'], 'valve': step['valve']}
                    break
                elapsed -= step['duration_ms']
            else:
                self.state = 'ready'
        if self.state == 'fault':
            if self.defect == 'inverted_valve':
                outputs['valve'] = 0.0
            if self.defect == 'unbounded_retry':
                outputs = self.outputs.copy()
        self.outputs = outputs
        return TickResult(self.state, outputs, tuple(self.history), tuple(detected), tuple(outcomes))
