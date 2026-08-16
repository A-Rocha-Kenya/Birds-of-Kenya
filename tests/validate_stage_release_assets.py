#!/usr/bin/env python3
"""Validate deterministic replacement of the staged public release subset."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "stage_release_assets.py"


def main():
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        release_id = "2099-01.0"
        source = directory / release_id
        comparison = source / "comparison"
        comparison.mkdir(parents=True)
        (source / "manifest.json").write_text(json.dumps({"release_id": release_id}), encoding="utf-8")
        (source / "checklist.csv").write_text("avibase_id\navibase-example\n", encoding="utf-8")
        (source / "checklist.pdf").write_bytes(b"pdf")
        (comparison / "taxonomy-changes.json").write_text("{}\n", encoding="utf-8")
        (comparison / "taxonomy-changes.csv").write_text("change\n", encoding="utf-8")

        publication = directory / "publication.toml"
        publication.write_text(
            f'release_id = "{release_id}"\n[render]\noutput_filename = "checklist.pdf"\n',
            encoding="utf-8",
        )
        output_root = directory / "release-assets"
        previous = output_root / release_id
        previous.mkdir(parents=True)
        (previous / "obsolete.txt").write_text("stale", encoding="utf-8")

        subprocess.run([
            sys.executable, str(SCRIPT), "--publication", str(publication),
            "--source", str(source), "--output-root", str(output_root),
        ], check=True)

        staged = output_root / release_id
        expected = {
            "manifest.json", "checklist.csv", "checklist.pdf",
            "comparison/taxonomy-changes.json", "comparison/taxonomy-changes.csv",
        }
        actual = {str(path.relative_to(staged)) for path in staged.rglob("*") if path.is_file()}
        if actual != expected:
            raise ValueError(f"staged public assets differ from the required subset: {sorted(actual)}")

    print("Validated deterministic public asset staging")


if __name__ == "__main__":
    main()
