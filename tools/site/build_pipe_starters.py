"""Package the reviewed product starter sources; never include build output or runtime dependencies."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def package(product, output):
    product, output = Path(product), Path(output)
    source = product / 'examples/pipe-starters'
    common = [source / 'README.md', source / 'LICENSE', *sorted((source / 'src').rglob('*'))]
    for variant in ('maven', 'gradle'):
        folder = output / ('pipe-starter-' + variant)
        files = {path.relative_to(source).as_posix(): path for path in common if path.is_file()}
        if variant == 'maven':
            files['pom.xml'] = source / 'pom.xml'
        else:
            for name in ('build.gradle.kts', 'settings.gradle.kts'):
                files[name] = source / name
            for name in ('gradlew', 'gradlew.bat', 'gradle/wrapper/gradle-wrapper.jar', 'gradle/wrapper/gradle-wrapper.properties'):
                files[name] = product / name
        for name, path in files.items():
            if path.is_symlink():
                raise ValueError('Starter sources must not be symbolic links')
            target = folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            data = path.read_bytes()
            target.write_bytes(data if path.suffix == '.jar' else data.replace(b'\r\n', b'\n'))
        hashes = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in sorted(files)}
        manifest = {'nuaformaVersion': '0.3.0-alpha.2', 'javaRelease': 17, 'variant': variant, 'sha256': hashes}
        (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
        with zipfile.ZipFile(output / ('pipe-starter-' + variant + '.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in [*sorted(files), 'manifest.json']:
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (0o100755 if name == 'gradlew' else 0o100644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, (folder / name).read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--product-repository', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'site/downloads')
    args = parser.parse_args()
    package(args.product_repository, args.output)
    print('Packaged Maven and Gradle Java 17 pipe starters with source checksums')
