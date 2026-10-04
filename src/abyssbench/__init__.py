"""Public v1 API for local, trusted Python controller replay."""
from typing import TYPE_CHECKING

from .contracts import Command, Controller, InputError, Measurement, Recipe, Tick, TickResult
from .monitor import monitor
from .trace import read_csv, read_jsonl, write_jsonl

if TYPE_CHECKING:
    from .controller import FluidController
    from .runner import run


def __getattr__(name):
    # A generic trace consumer does not import the fluid example.
    if name == 'FluidController':
        from .controller import FluidController
        return FluidController
    if name == 'run':
        from .runner import run
        return run
    raise AttributeError(name)

__all__ = [
           'Command',
           'Controller',
           'FluidController',
           'InputError',
           'Measurement',
           'Recipe',
           'Tick',
           'TickResult',
           'monitor',
           'read_csv',
           'read_jsonl',
           'run',
           'write_jsonl',
]
