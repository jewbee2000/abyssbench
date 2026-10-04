"""Record installed package metadata, retain upstream license files in wheels."""
import json
from importlib import metadata
from pathlib import Path

inventory = []
for distribution in sorted(metadata.distributions(), key=lambda d: d.metadata['Name'].lower()):
    data = distribution.metadata
    name = data['Name']
    license_text = data.get('License-Expression') or data.get('License')
    classifiers = [c for c in data.get_all('Classifier', []) if c.startswith('License ::')]
    inventory.append({'name': name, 'version': distribution.version,
                      'license': license_text.splitlines()[0][:160] if license_text else None,
                      'license_classifiers': classifiers,
                      'license_files': data.get_all('License-File', []),
                      'source': data.get('Home-page') or data.get_all('Project-URL', [])})
Path('evidence/dependency-licenses.json').write_text(json.dumps(inventory, indent=2))
