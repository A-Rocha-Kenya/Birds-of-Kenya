"""Write and verify self-contained checklist release bundles."""

import csv
import hashlib
import json
import shutil
from pathlib import Path

from taxonomy_comparison import snapshot


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def seal(directory, metadata, status, pending=()):
    """Seal files after rendering. Published seals are verified rather than regenerated."""
    rows = read_csv(directory / "checklist.csv")
    (directory / "taxonomy.json").write_text(json.dumps(snapshot(rows), ensure_ascii=False, indent=2) + "\n")
    descriptor = {"id": metadata["release_id"], "status": status, "publication": metadata,
                  "pdf": metadata["render"]["output_filename"], "pending_earc": sorted(pending),
                  "checksums": {str(p.relative_to(directory)): checksum(p) for p in sorted(directory.rglob("*"))
                                if p.is_file() and p.name != "release.json" and "comparison" not in p.parts}}
    (directory / "release.json").write_text(json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n")
    return descriptor


def verify(directory):
    descriptor = json.loads((directory / "release.json").read_text())
    for name, digest in descriptor["checksums"].items():
        if checksum(directory / name) != digest:
            raise ValueError(f"Release {descriptor['id']} has changed: {name}")
    pdfs = list(directory.glob("*.pdf"))
    if descriptor["pdf"] and [p.name for p in pdfs] != [descriptor["pdf"]]:
        raise ValueError(f"Release {descriptor['id']} must contain its one canonical PDF")
    return descriptor


def curate(source, destination, paths):
    for key, entry in paths.items():
        if "curation/" in entry["path"]:
            original = source / entry["path"]
            if checksum(original) != entry["sha256"]:
                raise ValueError(f"Curated input changed since build: {original}")
            target = destination / "curation" / Path(entry["path"]).name
            target.parent.mkdir(exist_ok=True)
            shutil.copy2(original, target)
