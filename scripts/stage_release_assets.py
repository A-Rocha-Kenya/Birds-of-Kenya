#!/usr/bin/env python3
"""Stage the public website assets from a local release build."""

import argparse
import json
import shutil
import tempfile
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
    if manifest["release_id"] != release_id or source.name != release_id:
        raise ValueError("publication metadata and release manifest identifiers do not match")

    comparison_pdfs = list((source / "comparison").glob("Taxonomy-changes-*.pdf"))
    if len(comparison_pdfs) > 1:
        raise ValueError("release has more than one taxonomy comparison PDF")

    assets = [
        (source / "manifest.json", Path("manifest.json")),
        (source / "checklist.csv", Path("checklist.csv")),
        (source / metadata["render"]["output_filename"], Path(metadata["render"]["output_filename"])),
        (source / "comparison" / "taxonomy-changes.json", Path("comparison/taxonomy-changes.json")),
        (source / "comparison" / "taxonomy-changes.csv", Path("comparison/taxonomy-changes.csv")),
    ]
    if comparison_pdfs:
        comparison_pdf = comparison_pdfs[0]
        assets.append((comparison_pdf, Path("comparison") / comparison_pdf.name))
    assets = [(require(source_path), relative_path) for source_path, relative_path in assets]

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{release_id}-", dir=output.parent) as temporary:
        temporary = Path(temporary)
        staging = temporary / release_id
        for source_path, relative_path in assets:
            copy(source_path, staging / relative_path)
        previous = temporary / "previous"
        if output.exists():
            output.rename(previous)
        try:
            staging.rename(output)
        except OSError:
            if previous.exists():
                previous.rename(output)
            raise

    print(f"Staged {len(assets)} public assets in {output}")


if __name__ == "__main__":
    main()
