"""Durable local artifacts; completion is a final fsync + atomic rename."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

from .contracts import InputError, Recipe
from .runner import MODEL


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def tree_hash(root, exclude=()):
    root = Path(root)
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in exclude):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes().replace(b'\r\n', b'\n'))
    return digest.hexdigest()


def metadata(root=None):
    root = Path(root or Path.cwd()).resolve()
    def git(*args):
        try:
            result = subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', *args],
                                    cwd=root, capture_output=True, timeout=5, check=False)
            return result.stdout if result.returncode == 0 else b''
        except (OSError, subprocess.SubprocessError):
            return b''
    status = git('status', '--porcelain')
    diff = git('diff', '--binary', 'HEAD', '--', '.', ':!src/abyssbench/oracle-provenance.json')
    # Include untracked input/source files in provenance, not only Git's diff.
    untracked = git('ls-files', '--others', '--exclude-standard').decode().splitlines()
    for name in sorted(untracked):
        p = root / name
        if p.is_file() and name != 'src/abyssbench/oracle-provenance.json':
            diff += name.encode() + p.read_bytes()
    oracle_path = root / 'tests'
    frozen = Path(__file__).parent / 'oracle-provenance.json'
    packaged = json.loads(frozen.read_text()) if frozen.exists() else {}
    oracle_hash = tree_hash(oracle_path) if oracle_path.is_dir() else (
        packaged.get('oracle_hash', 'unknown'))
    local = {'code_commit': git('rev-parse', 'HEAD').decode().strip() or 'unknown',
            'dirty_tree': bool(status), 'diff_hash': sha256(diff),
            'code_hash': tree_hash(Path(__file__).parent, exclude=('oracle-provenance.json',)),
            'oracle_hash': oracle_hash,
            'lock_hash': sha256((root / 'requirements-lock.txt').read_bytes())
                         if (root / 'requirements-lock.txt').exists() else 'unknown',
            'model_parameters': MODEL, 'recipe_hash': sha256(json.dumps(Recipe().to_dict(), sort_keys=True).encode()),
            'event_schema_version': 1, 'controller_version': 'fluid-v1'}
    if not (root / 'src/abyssbench').is_dir():
        for key in ('code_commit', 'dirty_tree', 'diff_hash', 'code_hash', 'oracle_hash', 'lock_hash'):
            local[key] = packaged.get(key, local[key])
    return local


def safe_output(path):
    path = Path(path)
    if '..' in path.parts:
        raise InputError('output path traversal rejected')
    return path.resolve()


class Recorder:
    def __init__(self, directory, parameters):
        self.directory = safe_output(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        if any(self.directory.iterdir()):
            raise InputError('output must be a new or empty directory')
        self.manifest = {'manifest_version': 1, 'status': 'incomplete', **metadata(),
                         **parameters, 'artifacts': {}}
        self._manifest()

    def path(self, name):
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or name in ('manifest.json', 'manifest.tmp'):
            raise InputError('artifact path traversal or reserved name')
        target = (self.directory / p).resolve()
        if not target.is_relative_to(self.directory):
            raise InputError('artifact escaped output directory')
        return target

    def _manifest(self):
        temp = self.directory / 'manifest.tmp'
        with temp.open('w', encoding='utf-8', newline='\n') as output:
            output.write(json.dumps(self.manifest, indent=2, allow_nan=False) + '\n')
            output.flush()
            os.fsync(output.fileno())
        temp.replace(self.directory / 'manifest.json')

    def write(self, name, content):
        target = self.path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode('utf-8') if isinstance(content, str) else content
        with target.open('wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        self.manifest['artifacts'][name] = sha256(data)

    def finish(self):
        self.manifest['status'] = 'complete'
        self._manifest()


def verify(directory):
    directory = Path(directory).resolve()
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest.get('manifest_version') != 1 or manifest.get('status') != 'complete':
        raise InputError('incomplete or unsupported run manifest')
    if not manifest.get('artifacts'):
        raise InputError('manifest has no artifacts')
    for name, expected in manifest['artifacts'].items():
        target = (directory / name).resolve()
        if Path(name).is_absolute() or '..' in Path(name).parts or not target.is_relative_to(directory):
            raise InputError('manifest artifact path escaped directory')
        if not target.is_file() or sha256(target.read_bytes()) != expected:
            raise InputError('artifact hash mismatch: ' + name)
    return manifest
