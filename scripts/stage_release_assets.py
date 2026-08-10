#!/usr/bin/env python3
"""Stage the public website assets from a local release build."""

import argparse
import json
import shutil
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLICATION = ROOT / "publication" / "publication.toml"


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def require(path):
    if not path.exists():
        raise ValueError(f"required release asset is missing: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication", type=Path, default=PUBLICATION)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-root", type=Path, default=ROOT / "release-assets")
    args = parser.parse_args()

    metadata = tomllib.loads(args.publication.resolve().read_text(encoding="utf-8"))
    release_id = metadata["release_id"]
    source = (args.source or ROOT / metadata["sources"]["release_directory"]).resolve()
    output = args.output_root.resolve() / release_id

    manifest = json.loads(require(source / "manifest.json").read_text(encoding="utf-8"))
    if manifest["release_id"] != release_id:
        raise ValueError("publication metadata and release manifest identifiers do not match")

    comparison_pdfs = list((source / "comparison").glob("Taxonomy-changes-*.pdf"))
    if len(comparison_pdfs) > 1:
        raise ValueError("release has more than one taxonomy comparison PDF")

    assets = [
        (source / "manifest.json", output / "manifest.json"),
        (source / "checklist.csv", output / "checklist.csv"),
        (source / metadata["render"]["output_filename"], output / metadata["render"]["output_filename"]),
        (source / "comparison" / "taxonomy-changes.json", output / "comparison" / "taxonomy-changes.json"),
        (source / "comparison" / "taxonomy-changes.csv", output / "comparison" / "taxonomy-changes.csv"),
    ]
    if comparison_pdfs:
        comparison_pdf = comparison_pdfs[0]
        assets.append((comparison_pdf, output / "comparison" / comparison_pdf.name))
    for source_path, output_path in assets:
        copy(require(source_path), output_path)

    print(f"Staged {len(assets)} public assets in {output}")


if __name__ == "__main__":
    main()
