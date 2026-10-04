"""Independent minimal trusted controller using only the documented public API.

Synthetic fluid recipe, different setpoints. No reference controller helpers.
"""
from abyssbench import Tick, TickResult


class ConsumerController:
    def __init__(self):
        self.state = 'disconnected'
        self.history = []

    def step(self, tick: Tick) -> TickResult:
        detected = []
        for measurement in tick.measurements.values():
            if (measurement.sample_time_ms is None or tick.time_ms-measurement.sample_time_ms > 200) and 'stale_input' not in self.history:
                self.history.append('stale_input')
                detected.append('stale_input')
        if self.history:
            self.state = 'fault'
        elif self.state == 'disconnected' and tick.connected:
            self.state = 'ready'
        before = self.state
        outcomes = []
        for command in tick.requests:
            if command.type == 'arm' and self.state == 'ready':
                self.state = 'armed'
            if command.type == 'start' and before == 'armed':
                self.state = 'running'
            if command.type == 'stop' and not self.history:
                self.state = 'ready'
            outcomes.append({'command': command.to_dict(), 'outcome': 'applied'})
        outputs = {'pump': 0.35, 'valve': 0.8} if self.state == 'running' else {'pump': 0, 'valve': 1}
        return TickResult(self.state, outputs, tuple(self.history), tuple(detected), tuple(outcomes))
