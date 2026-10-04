import importlib.util
from pathlib import Path

import pytest

from abyssbench import monitor, run


@pytest.mark.requirements('AB-15')
def test_external_controller_only_public_interface():
    path = Path('examples/consumer/controller.py')
    spec = importlib.util.spec_from_file_location('consumer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = monitor(run(module.ConsumerController(), fault='freeze'), profile='fluid')
    assert result['status'] == 'pass'
    assert 'FluidController' not in path.read_text()
