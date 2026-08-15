#!/usr/bin/env python3
"""Rebuild the checklist and produce the identical local and deployable website."""

import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLICATION = ROOT / "publication" / "publication.toml"


def run(*arguments):
    subprocess.run([sys.executable, *map(str, arguments)], cwd=ROOT, check=True)


def main():
    metadata = tomllib.loads(PUBLICATION.read_text(encoding="utf-8"))
    release_id = metadata["release_id"]
    dist = ROOT / "dist" / release_id
    public_release = ROOT / "release-assets" / release_id

    run(ROOT / "scripts" / "build_release.py", ROOT / "config" / "release.toml")
    run(ROOT / "tests" / "validate_release.py", dist)
    run(ROOT / "scripts" / "stage_release_assets.py", "--source", dist)
    run(ROOT / "scripts" / "build_site.py", "--release-dir", public_release, "--output", ROOT / "_site", "--allow-draft")
    run(ROOT / "tests" / "validate_site.py", ROOT / "_site")
    print(f"Website refreshed from one release output: {public_release.relative_to(ROOT)} -> _site")


if __name__ == "__main__":
    main()
