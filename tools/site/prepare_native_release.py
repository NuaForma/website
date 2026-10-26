"""Prepare the selected native-engine release offline; never modify or publish site/."""
import argparse
import hashlib
import html
import json
import pathlib
import re
import shutil
import subprocess

import build_client_collections as clients
import build_example_kit as examples
import package_complete_kit as complete
import package_deployment_kits as deployments
from check_reference import verify

ROOT = pathlib.Path(__file__).resolve().parents[2]
VERSION = '0.3.0-alpha.1'
RETIRED = ('seccomp.json', 'nuaforma.apparmor', 'compose.apparmor.yaml')


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def prepare(product, commit, destination):
    destination = destination.resolve()
    if destination.exists() or not destination.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh ignored build directory')
    if not re.fullmatch('[a-f0-9]{40}', commit):
        raise ValueError('Require the full reviewed immutable product commit')
    subprocess.run(['git', '-C', str(product), 'verify-commit', commit], check=True)
    destination.mkdir(parents=True)
    site = destination / 'site'
    shutil.copytree(ROOT / 'site', site)
    reference = destination / 'reference'
    inputs = {'compose.yaml': 'deployment/pdf-runtime/compose.yaml',
              'validate-pdf.sh': 'deployment/pdf-runtime/validate-pdf.sh',
              'helm-deployment.yaml': 'deployment/helm/nuaforma/templates/deployment.yaml',
              'NOTICE': 'deployment/pdf-runtime/NOTICE',
              'licenses/APACHE-2.0.txt': 'deployment/pdf-runtime/licenses/APACHE-2.0.txt'}
    hashes = {}
    for name, source in inputs.items():
        content = subprocess.check_output(['git', '-C', str(product), 'show', commit + ':' + source])
        file = reference / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
        hashes[name] = hashlib.sha256(content).hexdigest()
    record = dict(repository='NuaForma/NuaForma', sourceCommit=commit, release=VERSION,
                  validationBoundary='container', files=hashes)
    write(reference / 'manifest.json', json.dumps(record, indent=2) + '\n')
    for file in site.rglob('*'):
        if file.is_file() and (file.suffix in ('.md', '.html', '.json', '.yaml', '.js', '.bru') or file.name == 'Dockerfile'):
            text = re.sub(r'0\.2\.0-alpha\.[12]', VERSION, file.read_text(encoding='utf-8'))
            text = text.replace('Compose requires the included `seccomp.json`; extract the entire folder.', 'Compose uses runtime default security policies; extract the complete kit.')
            text = text.replace('The evaluation alpha retains documented native-runtime security risk accepted for this release; remediation remains open', 'Runtime component security follow-up remains open')
            text = re.sub(r'4\. `04-opaque-pdfa1b.json`:.*', '4. `04-opaque-pdfa1b.json`: PDF/A-1b without a requested watermark. All requested watermarks, including opaque text, are refused for this profile. The download filename is retained for compatibility.', text)
            text = re.sub(r'The seven-scenario template authoring procedure is.*', 'Prepare the native-release candidate using `tools/site/prepare_native_release.py` with an explicit reviewed product commit. The existing authored template requires real qualification against that candidate; packaging alone does not qualify documents.', text)
            write(file, text)
    write(site / 'README.md', f'# NuaForma website\n\nCandidate {VERSION}. Website maintenance belongs to the repository root README. This directory is the static publication tree. Product generation and real client qualification remain in NuaForma/NuaForma, under tools/site-qualification. Preparation alone does not authorize publication.\n')
    downloads = site / 'downloads'
    names = ('docker', 'docker-arm64', 'docker-playground', 'docker-playground-arm64', 'helm')
    for name in names:
        folder = downloads / name
        for retired in RETIRED:
            file = folder / retired
            if file.exists():
                file.unlink()  # Only files in this fresh disposable candidate copy.
        if name.startswith('docker'):
            compose = (folder / 'compose.yaml').read_text(encoding='utf-8')
            compose = '\n'.join(line for line in compose.splitlines() if 'seccomp=' not in line) + '\n'
            write(folder / 'compose.yaml', compose)
            development = 'playground' in name
            architecture = 'arm64' if name.endswith('arm64') else 'amd64'
            write(folder / 'README.md', f'''# {'DEVELOPMENT ONLY Playground' if development else 'Production service'} — {architecture}

Candidate `{VERSION}` uses the native PDF engine. No LibreOffice, Bubblewrap, custom seccomp file or installed AppArmor profile is required. Keep the runtime's default security policies, non-root user, read-only root, dropped capabilities, no-new-privileges and supplied limits.

Create `custom-fonts` and `extensions`, then run `docker compose up -d`. The service binds to loopback port 8080. Inspect `/api/v1/capabilities` and `/health/ready`. Mount only appropriately licensed readable standalone TTF/OTF files and trusted extension JARs. Restart after changing fonts. Native Linux/{architecture} is required; use the other kit for the other architecture.

{'DEVELOPMENT ONLY: synthetic data; development logging can contain document values. Open /playground/. ' if development else ''}There is no built-in authentication or TLS. Add your own authenticated TLS gateway before remote access. Do not use privileged or unconfined execution. With Podman, use VM-visible absolute font/extension paths and the native architecture; host policy remains enabled.

Standard PDF, PDF/A-2b and PDF/A-3b accept requested text watermarks. PDF/A-1b refuses every requested watermark, including opaque text. The native conversion profile rejects unsupported source constructs explicitly; it does not promise complete Word compatibility. See the [PDF guide](https://github.com/NuaForma/NuaForma/blob/main/nuaforma-docx-pdf/README.md).

Preserve NOTICE and LICENSE. Java, veraPDF and OS components retain their own terms; matching component sources/notices accompany the [release](https://github.com/NuaForma/NuaForma/releases/tag/v{VERSION}). Stop with `docker compose down`.
''')
    helm = downloads / 'helm/nuaforma'
    write(helm / 'templates/deployment.yaml', (reference / 'helm-deployment.yaml').read_text(encoding='utf-8'))
    values = (helm / 'values.yaml').read_text(encoding='utf-8')
    values = re.sub(r'sha256:[a-f0-9]{64}', 'REQUIRED_APPROVED_RELEASE_DIGEST', values)
    values = values.replace('seccomp:\n  localhostProfile: nuaforma/seccomp.json\n', '')
    write(helm / 'values.yaml', values)
    write(downloads / 'helm/README.md', f'''# Native-engine Helm evaluation example

Candidate `{VERSION}` uses RuntimeDefault seccomp with non-root execution, a read-only root, dropped capabilities and no privilege escalation. No custom host profiles or unprivileged-user-namespace setup is required. Preserve memory/CPU limits, bounded temporary storage and probes; configure pod PID bounds through your platform. This example does not qualify every Kubernetes cluster. Keep the service private and add authenticated TLS before remote access.

Before publication replace REQUIRED_APPROVED_RELEASE_DIGEST in values.yaml with the reviewed published multi-platform production index digest. Development Playground instructions require REQUIRED_APPROVED_PLAYGROUND_DIGEST. Never reuse a previous release digest. After binding, use `helm lint ./nuaforma`, `helm template nuaforma ./nuaforma` and `helm upgrade --install nuaforma ./nuaforma`. The default node selector is native Linux/amd64; choose arm64 on ARM64 nodes. Fonts and trusted extensions use existing read-only PVCs. Preserve NOTICE/LICENSE and the matching release's component notices/sources. No product artifact has been published by this preparation tool.
''')
    scenario_file = downloads / '04-opaque-pdfa1b.json'
    envelope = json.loads(scenario_file.read_text(encoding='utf-8'))
    envelope.get('options', {}).pop('watermark', None)
    write(scenario_file, json.dumps(envelope, indent=2) + '\n')
    scenarios = json.loads((downloads / 'scenarios.json').read_text(encoding='utf-8'))
    scenarios[3].update(title='PDF/A-1b without a watermark', profile='PDF/A-1b · no watermark',
                        description='Opaque images and no requested watermark. Every requested watermark is rejected for PDF/A-1b.',
                        expected='Independently validated PDF/A-1b; no watermark or transparency flattening. The historical download filename is retained.')
    write(downloads / 'scenarios.json', json.dumps(scenarios, indent=2) + '\n')
    source = (site / 'index.html').read_text(encoding='utf-8')
    source = source.replace('DOCX-only applications do not need Docker or LibreOffice. PDF requires the separately configured isolated runtime.',
                            'DOCX and native PDF libraries run in your JVM without LibreOffice. Archival PDF validation uses the configured validator.')
    source = source.replace('Both container isolation layers remain enabled.', 'The default container policies and resource limits remain enabled.')
    source = source.replace('0.2 &amp; ROADMAP', '0.3 &amp; ROADMAP')
    # Replace full obsolete operational paragraphs rather than leave contradictory fragments.
    source = re.sub(r'<p>Version 0\.3\.0-alpha\.1 adds.*?</p>', '<p>Version 0.3.0-alpha.1 replaces LibreOffice with the native PDF engine. Embedded libraries remain Java 17 compatible; the service uses Java 25. Standard PDF and validated PDF/A-1b, 2b and 3b embed supplied fonts. Requested watermarks work in standard PDF, 2b and 3b; 1b explicitly refuses them. The qualified native profile rejects unsupported document constructs. Value/content pipes, health checks, SBOM and the separate development Playground remain available.</p>', source)
    source = re.sub(r'<p>Choose AMD64 for Intel/AMD hosts.*?</p>', '<p>Choose AMD64 for Intel/AMD hosts or ARM64 for Apple Silicon and other ARM64 hosts. No custom image build, seccomp.json or AppArmor profile installation is required. Keep runtime default policies and supplied limits.</p>', source)
    source = re.sub(r'<a class="button secondary" href="downloads/docker/seccomp.json".*?</a>', '', source)
    source = re.sub(r'<p>The ARM64 kit includes.*?</p>', '<p>The ARM64 kit uses the native engine and the same default container safeguards, fonts and extension mounts.</p>', source)
    source = re.sub(r'<p>The service binds to your computer.*?</p>', '<p>The service binds to loopback port 8080. Add an authenticated TLS gateway before remote access. Keep the runtime default host security policies; no custom host profile is required.</p>', source)
    source = re.sub(r'<p id="docker-kit-status".*?</p>', '<p id="docker-kit-status" class="plain-note" role="status" aria-live="polite">Each kit includes compose.yaml, README.md, Dockerfile, NOTICE and LICENSE. Extract before starting Compose.</p>', source)
    source = re.sub(r'<p>Check your browser.*?Alternatively, download the complete kit with curl:</p>', '<p>Check your browser downloads or download the complete kit with curl:</p>', source)
    source = source.replace('Do not remove the seccomp setting or replace it with an unconfined profile.', 'Preserve the supplied limits and runtime default security policies.')
    source = re.sub(r'<p>The chart is a deployment starting point.*?</p>', '<p>The chart uses RuntimeDefault seccomp and requires no custom host profile installation. Qualify it on your own native Linux/amd64 or Linux/arm64 cluster and retain all supplied safeguards.</p>', source)
    source = source.replace('the reviewed seccomp profile', 'runtime default security policies')
    source = source.replace('Documented native-runtime risks are accepted for this evaluation alpha; remediation remains open.', 'Runtime component security follow-up is tracked in issue #51; inspect candidate-specific findings before deployment.')
    for code, name in (('compose-code', 'docker'), ('compose-arm64-code', 'docker-arm64')):
        replacement = html.escape((downloads / name / 'compose.yaml').read_text(encoding='utf-8').strip(), quote=False)
        source = re.sub(r'(<code id="' + code + r'">).*?(</code>)', lambda match: match[1] + replacement + match[2], source, flags=re.S)
    write(site / 'index.html', source)
    operations = site / 'operations.html'
    write(operations, operations.read_text(encoding='utf-8').replace('reviewed seccomp/AppArmor settings', 'runtime default security policies').replace('Earlier alpha.1 images do not gain these settings automatically;', 'Earlier releases do not gain the native engine automatically;'))
    # Existing document bytes are deliberately retained for a real native qualification trial.
    clients.OUT = examples.OUT = complete.OUT = downloads
    clients.build(version=VERSION)
    deployments.PROFILES = reference
    deployments.verify = lambda: verify(reference)
    deployments.package(downloads)
    examples.package()
    complete.package()
    write(site / 'RELEASE-PREPARATION.txt', 'NOT FOR PUBLICATION: qualify all seven authored examples on the exact candidate; review source/notice inputs; bind published production and Playground digests; verify public Maven/image/source artifacts and final source commit.\n')
    print('Prepared offline native candidate:', destination)
    print('Publication remains blocked; site/ and live downloads are unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--product-repository', required=True, type=pathlib.Path)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    prepare(args.product_repository, args.source_commit, args.output)
