"""Download the DDXPlus knowledge-base files and official test split."""

import hashlib
import json
from pathlib import Path
from urllib.request import ProxyHandler, build_opener


ARTICLE = "https://api.figshare.com/v2/articles/22687585/versions/2"
FILES = {"release_conditions.json", "release_evidences.json", "release_test_patients.zip"}
DEST = Path(__file__).parent / "data" / "raw"


def main() -> None:
    opener = build_opener(ProxyHandler({}))
    with opener.open(ARTICLE, timeout=30) as response:
        metadata = json.load(response)
    selected = {file["name"]: file for file in metadata["files"] if file["name"] in FILES}
    if selected.keys() != FILES:
        raise RuntimeError(f"Missing DDXPlus files: {FILES - selected.keys()}")

    DEST.mkdir(parents=True, exist_ok=True)
    for name, file in selected.items():
        with opener.open(file["download_url"], timeout=60) as response:
            content = response.read()
        if len(content) != file["size"] or hashlib.md5(content).hexdigest() != file["supplied_md5"]:
            raise RuntimeError(f"Checksum or size mismatch: {name}")
        if name.endswith(".json"):
            json.loads(content)
        (DEST / name).write_bytes(content)
        print(f"Saved {DEST / name} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
