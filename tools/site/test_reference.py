"""Pinned public runtime profiles cannot silently drift during website packaging."""
import json
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
            profile = root / 'seccomp.json'
            profile.write_bytes(profile.read_bytes() + b' ')
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
