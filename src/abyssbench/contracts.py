"""Public immutable controller boundary and strict recipe validation."""
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


class InputError(ValueError):
    """Invalid, unsupported or resource-limited evidence (CLI exit 2)."""


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


@dataclass(frozen=True)
class Measurement:
    channel: str
    value: float
    unit: str
    sample_time_ms: int | None
    receive_time_ms: int
    quality: str
    sequence: int
    calibration_id: str

    def __post_init__(self):
        if not finite(self.value) or not self.channel or not self.calibration_id:
            raise InputError('measurement must be finite with channel and provenance')
        for v in (self.receive_time_ms, self.sequence):
            if type(v) is not int or v < 0:
                raise InputError('integer nonnegative receive time and packet sequence required')
        if self.sample_time_ms is not None and type(self.sample_time_ms) is not int:
            raise InputError('sample time must be integer milliseconds or null')

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Command:
    command_id: str
    type: str
    payload: dict[str, Any]
    issued_at_ms: int
    expires_at_ms: int

    def __post_init__(self):
        if not self.command_id or self.type not in {'arm', 'start', 'stop', 'ack'}:
            raise InputError('unsupported user command')
        if type(self.issued_at_ms) is not int or type(self.expires_at_ms) is not int:
            raise InputError('command times must be integer milliseconds')
        if self.issued_at_ms < 0 or self.expires_at_ms < self.issued_at_ms:
            raise InputError('invalid command lifetime')
        if self.payload:
            raise InputError('v1 user commands have empty payloads')

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Tick:
    time_ms: int
    measurements: dict[str, Measurement]
    connected: bool
    heartbeat_ms: int
    valve_position: float
    requests: tuple[Command, ...] = ()


@dataclass(frozen=True)
class TickResult:
    state: str
    commands: dict[str, float]
    history: tuple[str, ...] = ()
    detected: tuple[str, ...] = ()
    outcomes: tuple[dict[str, Any], ...] = ()


class Controller(Protocol):
    """Trusted caller code only; the library never executes code from log inputs."""
    def step(self, tick: Tick) -> TickResult: ...


@dataclass(frozen=True)
class Recipe:
    version: int = 1
    preconditions: dict[str, str] = field(default_factory=lambda: {
        'pressure1': 'Pa', 'pressure2': 'Pa', 'flow': 'm3/s'})
    steps: tuple[dict[str, Any], ...] = field(default_factory=lambda: (
        {'duration_ms': 60000, 'pump': 0.5, 'valve': 0.6},))
    stop_conditions: dict[str, Any] = field(default_factory=lambda: {'pressure_max_Pa': 200000})
    max_duration_ms: int = 60000

    @classmethod
    def from_dict(cls, value):
        keys = {'version', 'preconditions', 'steps', 'stop_conditions', 'max_duration_ms'}
        if set(value) != keys or value['version'] != 1:
            raise InputError('recipe v1 requires exactly its five documented fields')
        if value['preconditions'] != {'pressure1': 'Pa', 'pressure2': 'Pa', 'flow': 'm3/s'}:
            raise InputError('fluid preconditions require explicit SI units')
        if type(value['max_duration_ms']) is not int or not 0 < value['max_duration_ms'] <= 60000:
            raise InputError('recipe maximum duration must be 1..60000 ms')
        steps = value['steps']
        if not isinstance(steps, list) or not 1 <= len(steps) <= 32:
            raise InputError('recipe requires 1..32 steps')
        total = 0
        for step in steps:
            if set(step) != {'duration_ms', 'pump', 'valve'}:
                raise InputError('unknown recipe step field')
            duration = step['duration_ms']
            if type(duration) is not int or duration <= 0:
                raise InputError('positive integer duration required')
            total += duration
            for key in ('pump', 'valve'):
                if not finite(step[key]) or not 0 <= step[key] <= 1:
                    raise InputError('setpoints must be finite fractions in [0,1]')
        stop = value['stop_conditions']
        if set(stop) != {'pressure_max_Pa'} or not finite(stop['pressure_max_Pa']):
            raise InputError('explicit finite pressure stop condition required')
        if not 0 < stop['pressure_max_Pa'] <= 200000 or total > value['max_duration_ms']:
            raise InputError('recipe exceeds reference limits')
        return cls(1, value['preconditions'], tuple(steps), stop, value['max_duration_ms'])

    def to_dict(self):
        result = asdict(self)
        result['steps'] = list(result['steps'])
        return result
