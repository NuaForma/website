"""Pinned public runtime profiles cannot silently drift during website packaging."""
import json
import hashlib
import pathlib
import shutil
import tempfile
import unittest
from check_reference import PROFILES, verify


class ReferenceTest(unittest.TestCase):
    def test_immutable_source_and_exact_inputs_are_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / 'runtime'
            shutil.copytree(PROFILES, root)
            record = verify(root)
            self.assertEqual('NuaForma/NuaForma', record['repository'])
            profile = root / 'NOTICE'
            profile.write_bytes(profile.read_bytes() + b' ')
            with self.assertRaises(ValueError):
                verify(root)

    def test_default_boundary_requires_all_immutable_runtime_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            files = {}
            for name in ('compose.yaml', 'validate-pdf.sh', 'helm-deployment.yaml', 'NOTICE', 'licenses/APACHE-2.0.txt'):
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(name, encoding='utf-8')
                files[name] = hashlib.sha256(file.read_bytes()).hexdigest()
            record = dict(repository='NuaForma/NuaForma', sourceCommit='a' * 40,
                          release='0.3.0-alpha.1', validationBoundary='container', files=files)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps(record))
            self.assertEqual('container', verify(root)['validationBoundary'])
            del record['files']['validate-pdf.sh']
            manifest.write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                verify(root)
            record['validationBoundary'] = 'unconfined'
            manifest.write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                verify(root)

    def test_missing_or_external_manifest_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / 'runtime'
            shutil.copytree(PROFILES, root)
            manifest = root / 'manifest.json'
            record = json.loads(manifest.read_text())
            record['files']['../outside'] = 'a' * 64
            manifest.write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                verify(root)


if __name__ == '__main__':
    unittest.main()
