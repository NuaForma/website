"""Generate fixed public demo images from an explicitly selected image-comparison Git source."""
import argparse
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-repository', required=True, type=pathlib.Path)
    parser.add_argument('--source-ref', default='main')
    parser.add_argument('--output', required=True, type=pathlib.Path, help='Fresh candidate directory under website build/')
    args = parser.parse_args()
    output = args.output.resolve()
    build = (ROOT / 'build').resolve()
    if not output.is_relative_to(build) or output == build or output.exists():
        raise ValueError('Choose a fresh candidate directory under website build; never overwrite public examples automatically')
    revision = subprocess.check_output(['git', '-C', str(args.source_repository), 'rev-parse', '--verify', args.source_ref + '^{commit}'], text=True).strip()
    files = subprocess.check_output(['git', '-C', str(args.source_repository), 'ls-tree', '-r', '--name-only', revision,
                                     'image-comparison/src/main/java/'], text=True).splitlines()
    sources = []
    for name in files:
        if not name.endswith('.java'):
            continue
        relative = pathlib.PurePosixPath(name)
        if '..' in relative.parts or relative.is_absolute():
            raise ValueError('Invalid source path')
        target = output / 'source' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(['git', '-C', str(args.source_repository), 'show', revision + ':' + name]))
        sources.append(str(target))
    classes = output / 'classes'
    classes.mkdir()
    subprocess.run(['javac', '--release', '17', '-d', str(classes), *sources, str(ROOT / 'tools/site/ImageComparisonDemo.java')], check=True)
    images = output / 'images'
    subprocess.run(['java', '-Djava.awt.headless=true', '-cp', str(classes), 'ImageComparisonDemo', str(images)], check=True)
    record = json.loads((images / 'comparison.json').read_text())
    record['sourceCommit'] = revision
    record['sourceRepository'] = 'https://github.com/NuaForma/image-comparison'
    record['generatorSha256'] = hashlib.sha256((ROOT / 'tools/site/ImageComparisonDemo.java').read_bytes()).hexdigest()
    record['images'] = {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in sorted(images.glob('*.png'))}
    (images / 'comparison.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
