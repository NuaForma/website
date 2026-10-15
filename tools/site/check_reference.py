"""Validate the offline checksum snapshot of reviewed immutable product profile inputs."""
import hashlib
import json
import pathlib
import re

PROFILES = pathlib.Path(__file__).resolve().parents[2] / 'reference/runtime'
FILES = {'seccomp.json', 'nuaforma.apparmor', 'compose.apparmor.yaml', 'NOTICE', 'licenses/APACHE-2.0.txt'}


def verify(root=PROFILES):
    manifest = root / 'manifest.json'
    if manifest.is_symlink() or manifest.stat().st_size > 16 * 1024:
        raise ValueError('Invalid profile manifest')
    record = json.loads(manifest.read_text(encoding='utf-8'))
    if record.get('repository') != 'NuaForma/NuaForma' or not re.fullmatch('[a-f0-9]{40}', record.get('sourceCommit', '')):
        raise ValueError('Require an immutable product source identity')
    if set(record.get('files', {})) != FILES:
        raise ValueError('Require exactly the reviewed profile/notice inputs')
    for relative, expected in record['files'].items():
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Product profile snapshot differs from review: ' + relative)
    return record


if __name__ == '__main__':
    record = verify()
    print('Pinned product profile/notice inputs:', record['release'], record['sourceCommit'], 'PASS')
