#!/usr/bin/env python3
"""Freeze a draft release, including one PDF and its version-specific curation."""

import argparse
import json
import shutil
import tempfile
import tomllib
from pathlib import Path

from publication_metadata import pending_earc_ids, render_provenance
from release_archive import curate, seal, verify

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication", type=Path, default=ROOT / "publication/publication.toml")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-root", type=Path, default=ROOT / "release-assets")
    args = parser.parse_args()
    metadata = tomllib.loads(args.publication.read_text())
    source = args.source or ROOT / metadata["sources"]["release_directory"]
    output = args.output_root / metadata["release_id"]
    manifest = json.loads((source / "manifest.json").read_text())
    if manifest["release_id"] != metadata["release_id"] or source.name != metadata["release_id"]:
        raise ValueError("publication and release identifiers differ")
    if (output / "release.json").exists() and verify(output)["status"] == "released":
        raise ValueError("Published release is immutable; choose a new release ID")
    provenance = json.loads((source / metadata["render"]["output_filename"]).with_suffix(".inputs.json").read_text())
    expected = render_provenance(metadata, ROOT, source, source / metadata["render"]["output_filename"])
    if provenance != expected:
        raise ValueError("PDF is stale; render it again from the current checklist and metadata")
    args.output_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.output_root) as tmp:
        staging = Path(tmp) / source.name
        staging.mkdir()
        for name in ["manifest.json", "checklist.csv", metadata["render"]["output_filename"]]:
            shutil.copy2(source / name, staging / name)
        curate(ROOT, staging, manifest["sources"])
        shutil.copy2(ROOT / metadata["sources"]["policy"], staging / "policy.md")
        shutil.copy2(ROOT / metadata["sources"]["category_definitions"], staging / "category_definitions.csv")
        if metadata["sources"].get("taxonomy_transition"):
            shutil.copy2(ROOT / metadata["sources"]["taxonomy_transition"], staging / "transition.json")
        pending = pending_earc_ids(metadata, ROOT, source)
        seal(staging, metadata, metadata["status"], pending)
        verify(staging)
        previous = Path(tmp) / "previous"
        if output.exists():
            output.rename(previous)
        try:
            staging.rename(output)
        except OSError:
            if previous.exists():
                previous.rename(output)
            raise
    print(f"Staged frozen release {output}")


if __name__ == "__main__":
    main()
