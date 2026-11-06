"""Export archived checklists and all directed taxonomy comparison pairs."""

import csv
import hashlib
import json
import shutil
import tomllib
from pathlib import Path

from release_archive import verify
from taxonomy_comparison import compare_versions


def load_archive(root, preview=None):
    registry = tomllib.loads((root / "publication/releases.toml").read_text())
    active = preview or registry["active_release"]
    bundles = {}
    for entry in registry["releases"]:
        if entry.get("status") == "draft" and entry["id"] != preview:
            continue
        path = root / entry["path"]
        if not (path / "release.json").exists() and entry.get("status") == "draft":
            continue
        descriptor = verify(path)
        if descriptor["id"] != entry["id"]:
            raise ValueError(f"Registry ID differs from sealed release: {entry['id']}")
        if descriptor["status"] == "released" or preview and entry["id"] == preview:
            bundles[entry["id"]] = (path, descriptor)
    if active not in bundles:
        raise ValueError(f"Active release {active} must be an archived published release or explicit preview")
    return active, bundles


def load_transitions(bundles):
    transitions = []
    for path, _ in bundles.values():
        if (path / "transition.json").exists():
            transitions.append(json.loads((path / "transition.json").read_text()))
        if (path / "transitions.json").exists():
            transitions.extend(json.loads((path / "transitions.json").read_text()))
    return transitions


def export_archive(staging, active, bundles):
    versions, releases = {}, []
    transitions = load_transitions(bundles)
    for identifier, (path, descriptor) in bundles.items():
        versions[identifier] = json.loads((path / "taxonomy.json").read_text())
        destination = staging / "downloads" / identifier
        destination.mkdir(parents=True)
        basename = f"Checklist-of-the-Birds-of-Kenya-{identifier}"
        shutil.copy2(path / "checklist.csv", destination / f"{basename}.csv")
        shutil.copy2(path / "checklist.csv", destination / "checklist.csv")
        if descriptor["pdf"]:
            shutil.copy2(path / descriptor["pdf"], destination / f"{basename}.pdf")
            if descriptor["pdf"] != f"{basename}.pdf":
                shutil.copy2(path / descriptor["pdf"], destination / descriptor["pdf"])
        releases.append({"id": identifier, "status": descriptor["status"],
                         "pdf": f'downloads/{identifier}/{basename}.pdf' if descriptor["pdf"] else "",
                         "csv": f"downloads/{identifier}/{basename}.csv",
                         "taxonomy_excluded_rows": descriptor.get("taxonomy_excluded_rows", 0),
                         "comparison_note": descriptor.get("comparison_note", ""),
                         "pdf_label": descriptor.get("pdf_label", "Checklist PDF")})
    pairs = []
    for source in versions:
        for target in versions:
            pair = compare_versions(versions, transitions, source, target)
            destination = staging / "data/comparisons" / source / target
            destination.mkdir(parents=True)
            write_comparison(destination, pair)
            prefix = f"data/comparisons/{source}/{target}"
            pairs.append({"revision": hashlib.sha256((destination / "taxonomy-changes.json").read_bytes() + (destination / "taxonomy-changes.csv").read_bytes()).hexdigest()[:16], "from_release": source, "to_release": target, "group_count": pair["group_count"],
                          "files": {"json": prefix + "/taxonomy-changes.json", "csv": prefix + "/taxonomy-changes.csv"}})
    catalog = {"active_release": active, "releases": releases, "pairs": pairs}
    (staging / "data/releases.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    return catalog


def write_comparison(destination, pair):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "taxonomy-changes.json").write_text(json.dumps(pair, ensure_ascii=False, indent=2) + "\n")
    with (destination / "taxonomy-changes.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["group", "change", "side", "avibase_id", "english_name", "scientific_name", "order", "family", "family_english_name"])
        for group in pair["groups"]:
            for side in ["old", "new"]:
                for row in group[side]:
                    writer.writerow([group["id"], group["relationship"], side, row["id"], row["english"], row["scientific"], row["order"], row["family"], row["family_english"]])
