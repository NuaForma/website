"""Package explicit deployment files with unchanged reviewed profiles and their notices."""
import pathlib
import shutil
import zipfile
from check_reference import PROFILES, verify

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOWNLOADS = ROOT / "site/downloads"

def package(downloads=DOWNLOADS):
    record = verify()
    legacy = record.get("validationBoundary", "legacy") == "legacy"
    names = ["docker", "docker-arm64", "helm"]
    names.extend(name for name in ("docker-playground", "docker-playground-arm64") if (downloads / name).is_dir())
    for name in names:
        folder = downloads / name
        materials = [("NOTICE", "NOTICE"), ("licenses/APACHE-2.0.txt", "LICENSE")]
        if legacy:
            materials.extend([("seccomp.json", "seccomp.json"), ("nuaforma.apparmor", "nuaforma.apparmor")])
        else:
            for retired in ("seccomp.json", "nuaforma.apparmor", "compose.apparmor.yaml"):
                if (folder / retired).exists():
                    raise ValueError("Remove retired custom-profile input before packaging: " + str(folder / retired))
        for source, target in materials:
            shutil.copyfile(PROFILES / source, folder / target)
        if legacy and name.startswith("docker"):
            shutil.copyfile(PROFILES / "compose.apparmor.yaml", folder / "compose.apparmor.yaml")
        with zipfile.ZipFile(downloads / (name + "-kit.zip"), "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(folder.rglob("*")):
                if file.is_file():
                    assert not file.is_symlink()
                    info = zipfile.ZipInfo(file.relative_to(folder).as_posix(), (1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, file.read_bytes())
        print("Packaged", name, "deployment kit")


if __name__ == '__main__':
    package()
