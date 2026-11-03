#!/usr/bin/env python3
"""One-time import of accepted historical files, without rerunning old EBD evidence."""

import json
import csv
import io
from collections import Counter
import shutil
import subprocess
import tomllib
from pathlib import Path

from release_archive import checksum, read_csv, seal

ROOT = Path(__file__).resolve().parents[1]


def main():
    old = ROOT / "release-assets/v2025.0"
    if not (old / "release.json").exists():
        metadata = tomllib.loads(subprocess.check_output(["git", "show", "4476eb7cd6d754c8df1f37906f984db5ee065c58:publication/publication.toml"], cwd=ROOT, text=True))
        metadata = json.loads(json.dumps(metadata).replace("2026.0", "2025.0"))
        manifest = json.loads((old / "manifest.json").read_text())
        for entry in manifest["sources"].values():
            if "curation/" in entry["path"]:
                target = old / "curation" / Path(entry["path"]).name
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(subprocess.check_output(["git", "show", f"4476eb7cd6d754c8df1f37906f984db5ee065c58:{entry['path']}"], cwd=ROOT))
                if checksum(target) != entry["sha256"]:
                    raise ValueError(f"Historical input checksum differs: {target}")
        mapping = old / "curation/taxonomy_2019.1_to_2025.0.csv"
        mapping.write_bytes(subprocess.check_output(["git", "show", "4476eb7cd6d754c8df1f37906f984db5ee065c58:data/curation/taxonomy_2019.1_to_2026.0.csv"], cwd=ROOT))
        links = [{"old_id": r["old_avibase_id"], "new_id": identifier} for r in read_csv(mapping) for identifier in r["new_avibase_ids"].split(";") if identifier]
        (old / "transition.json").write_text(json.dumps({"from_release": "v2019.1", "to_release": "v2025.0", "links": links}, indent=2) + "\n")
        for source, name in [(metadata["sources"]["policy"], "policy.md"), (metadata["sources"]["category_definitions"], "category_definitions.csv")]:
            (old / name).write_bytes(subprocess.check_output(["git", "show", f"4476eb7cd6d754c8df1f37906f984db5ee065c58:{source}"], cwd=ROOT))
        comparison = json.loads((old / "comparison/taxonomy-changes.json").read_text())
        pending = {r["id"] for g in comparison["groups"] if g.get("pending_earc") for r in g["new"]}
        seal(old, metadata, "released", pending)
    legacy = ROOT / "release-assets/v2019.1"
    if not legacy.exists():
        legacy.mkdir()
        shutil.copy2(ROOT / "data/legacy/2019.1/checklist.csv", legacy / "checklist.csv")
        name = "Birds-of-Kenya-2019-original-printed-edition.pdf"
        shutil.copy2(next((ROOT / "data/legacy/2019.1").glob("*.pdf")), legacy / name)
        descriptor = seal(legacy, {"release_id": "v2019.1", "render": {"output_filename": name}}, "released")
        descriptor["pdf_label"] = "Original printed 2019 edition (CSV is the corrected 2019.1 transcription)"
        (legacy / "release.json").write_text(json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n")
    original = ROOT / "release-assets/v2019.0"
    if not original.exists():
        original.mkdir()
        data = subprocess.check_output(["git", "show", "v2019.0:data/main.csv"], cwd=ROOT)
        (original / "checklist.csv").write_bytes(data)
        name = "Birds-of-Kenya-2019-original-printed-edition.pdf"
        shutil.copy2(legacy / name, original / name)
        rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
        counts = Counter(r["avibaseid"] for r in rows)
        excluded = [r for r in rows if not r["avibaseid"].startswith("avibase-") or counts[r["avibaseid"]] != 1]
        (original / "taxonomy-exclusions.json").write_text(json.dumps(excluded, ensure_ascii=False, indent=2) + "\n")
        descriptor = seal(original, {"release_id": "v2019.0", "render": {"output_filename": name}}, "released")
        descriptor.update(pdf_label="Original printed 2019 edition", taxonomy_excluded_rows=len(excluded))
        (original / "release.json").write_text(json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
