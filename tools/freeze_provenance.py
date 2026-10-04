"""Run before building a release wheel; captures actual current dirty state."""
import json
from pathlib import Path

from abyssbench.recording import metadata

output = metadata()
output['label'] = 'Open agent-authored independent acceptance suite; no live campaign'
Path('src/abyssbench/oracle-provenance.json').write_text(json.dumps(output, indent=2))
