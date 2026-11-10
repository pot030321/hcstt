"""Download the public CLAP checkpoint and ESC-50 data used by this experiment."""

import hashlib
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path


DATA = Path(__file__).parent / "data"
ASSETS = (
    (
        "630k-audioset-best.pt",
        "https://huggingface.co/lukewys/laion_clap/resolve/main/630k-audioset-best.pt",
        1_863_587_645,
        "8053c9775516af2f4902e1e8281e356cc1bf7a85e8b761908170767b77c3f037",
    ),
    (
        "ESC-50.zip",
        "https://codeload.github.com/karolpiczak/ESC-50/zip/refs/heads/master",
        645_695_005,
        "805afc618aff80eff0641d51311647871fead5807da68bb18e43a27db47a79ce",
    ),
)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(name, url, size, sha256):
    path = DATA / name
    if path.is_file() and path.stat().st_size == size and digest(path) == sha256:
        print(f"OK: {name} already present, SHA-256 verified")
        return path

    temporary = DATA / (name + ".part")
    h = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(url, timeout=90) as source, temporary.open("wb") as target:
            while block := source.read(1024 * 1024):
                target.write(block)
                h.update(block)
                total += len(block)
                if total // (100 * 1024 * 1024) != (total - len(block)) // (100 * 1024 * 1024):
                    print(f"{name}: {total // (1024 * 1024)} MiB")
        if total != size or h.hexdigest() != sha256:
            raise ValueError(f"{name}: size or SHA-256 differs from the recorded version; verify the source before replacing it")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"OK: {name} downloaded, SHA-256 verified")
    return path


def extract_esc50(archive):
    root = DATA / "ESC-50"
    audio_dir = root / "audio"
    metadata = root / "meta" / "esc50.csv"
    if metadata.is_file() and len(list(audio_dir.glob("*.wav"))) == 2000:
        print("OK: ESC-50 already extracted (2,000 WAV files)")
        return

    with zipfile.ZipFile(archive) as zipped:
        files = [name for name in zipped.namelist() if name.startswith("ESC-50-master/audio/") and name.endswith(".wav")]
        if len(files) != 2000 or "ESC-50-master/meta/esc50.csv" not in zipped.namelist():
            raise ValueError("ESC-50 ZIP does not contain 2,000 WAV files and metadata")
        audio_dir.mkdir(parents=True, exist_ok=True)
        metadata.parent.mkdir(parents=True, exist_ok=True)
        for name in files:
            with zipped.open(name) as source, (audio_dir / Path(name).name).open("wb") as target:
                shutil.copyfileobj(source, target)
        with zipped.open("ESC-50-master/meta/esc50.csv") as source, metadata.open("wb") as target:
            shutil.copyfileobj(source, target)
    print("OK: ESC-50 extracted (2,000 WAV files)")


def main():
    DATA.mkdir(exist_ok=True)
    for name, url, size, sha256 in ASSETS:
        path = download(name, url, size, sha256)
        if name == "ESC-50.zip":
            extract_esc50(path)


if __name__ == "__main__":
    main()
