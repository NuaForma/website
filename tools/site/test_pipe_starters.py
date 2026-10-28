"""Downloadable pipe starters must match their retained sources and contain only intended files."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile
import tempfile
import build_pipe_starters

ROOT = Path(__file__).resolve().parents[2]


class PipeStartersTest(unittest.TestCase):
    def test_packaging_normalizes_text_but_preserves_wrapper_binary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            product, output = root / 'product', root / 'downloads'
            for name in ['examples/pipe-starters/README.md', 'examples/pipe-starters/LICENSE',
                         'examples/pipe-starters/pom.xml', 'examples/pipe-starters/build.gradle.kts',
                         'examples/pipe-starters/settings.gradle.kts', 'examples/pipe-starters/src/Example.java',
                         'gradlew', 'gradlew.bat', 'gradle/wrapper/gradle-wrapper.properties', 'gradle/wrapper/gradle-wrapper.jar']:
                target = product / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'example\r\n')
            build_pipe_starters.package(product, output)
            with zipfile.ZipFile(output / 'pipe-starter-gradle.zip') as archive:
                self.assertEqual(archive.read('gradlew.bat'), b'example\n')
                self.assertEqual(archive.read('gradle/wrapper/gradle-wrapper.jar'), b'example\r\n')
                self.assertNotIn(b'\r\n', archive.read('manifest.json'))

    def test_downloads_match_hash_manifest_and_have_packaged_service_tests(self):
        for variant in ('maven', 'gradle'):
            folder = ROOT / 'site/downloads' / ('pipe-starter-' + variant)
            manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['nuaformaVersion'], '0.3.0-alpha.2')
            self.assertEqual(manifest['javaRelease'], 17)
            with zipfile.ZipFile(folder.with_suffix('.zip')) as archive:
                self.assertEqual(set(archive.namelist()), set(manifest['sha256']) | {'manifest.json'})
                for name in archive.namelist():
                    self.assertEqual(archive.read(name), (folder / name).read_bytes(), name)
                    self.assertNotIn('..', Path(name).parts)
                for name, digest in manifest['sha256'].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest, name)
                service = archive.read('src/main/resources/META-INF/services/dev.nuaforma.contracts.TemplatePipe').decode().splitlines()
                self.assertEqual(service, ['example.PrefixPipe', 'example.UppercasePipe', 'example.SelectPipe'])
                for implementation in service:
                    self.assertIn('src/main/resources/META-INF/nuaforma/pipes/' + implementation + '.properties', archive.namelist())
                self.assertIn('src/test/java/example/StarterTest.java', archive.namelist())
                self.assertNotIn('target/', ''.join(archive.namelist()))
                self.assertNotIn('build/', ''.join(archive.namelist()))
                if variant == 'gradle':
                    self.assertTrue(archive.getinfo('gradlew').external_attr >> 16 & 0o111)
                    self.assertIn('distributionSha256Sum=', archive.read('gradle/wrapper/gradle-wrapper.properties').decode())
                else:
                    self.assertIn('<scope>provided</scope>', archive.read('pom.xml').decode())
            self.assertTrue('Maven' in (folder / 'README.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
