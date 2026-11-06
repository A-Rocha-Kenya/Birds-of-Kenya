#!/usr/bin/env python3
"""Build corrected historical data and seal new archives without editing old releases."""

import csv
import json
import shutil
import subprocess
from pathlib import Path

from release_archive import checksum, read_csv, seal, verify

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "data/legacy"
original = read_csv(ROOT / "release-assets/v2019.1/checklist.csv")
columns = ["note" if c == "note_2019" else c for c in original[0] if c not in {"sort_1996", "sort_2009", "note_2009"}]
rows = [{("note" if k == "note_2019" else k): v for k, v in row.items() if k not in {"sort_1996", "sort_2009", "note_2009"}} for row in original]
for version in ("2019.2", "2019.3"):
    directory = LEGACY / version
    corrections = read_csv(directory / "corrections.csv")
    for correction in corrections:
        row = next(row for row in rows if row["sort"] == correction["sort"])
        assert row[correction["field"]] == correction["before"]
        row[correction["field"]] = correction["after"]
    assert len(rows) == len({row["avibaseid"] for row in rows}) == 1181
    with (directory / "checklist.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

# The 2009 revision applies ID decisions to the sealed transcription by printed position.
historical = read_csv(ROOT / "release-assets/v2009.0/checklist.csv")
directory = LEGACY / "2009.1"
assignments = {row["sort"]: row for row in read_csv(directory / "avibase_assignments.csv")}
assert assignments.keys() == {row["sort"] for row in historical if not row["avibaseid"]}
for row in historical:
    if row["sort"] in assignments:
        assignment = assignments[row["sort"]]
        assert row["common_name"] == assignment["printed_name"]
        row["avibaseid"] = assignment["avibase_id"]
assert len({row["avibaseid"] for row in historical}) == len(historical) == 1100
with (directory / "checklist.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(historical[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(historical)

for version, pdf, label in [
    ("2009.0", LEGACY / "2009.0/source.pdf", "Fourth edition, 2009 with corrections of 13 December 2017"),
    ("2009.1", LEGACY / "2009.0/source.pdf", "Fourth edition, 2009 with 2017 corrections and revised digital IDs"),
    ("2019.3", LEGACY / "2019.1/source.pdf", "Original printed 2019 edition"),
    ("2019.2", LEGACY / "2019.1/source.pdf", "Original printed 2019 edition; CSV includes v2019.2 corrections"),
]:
    identifier = "v" + version
    source = LEGACY / version
    destination = ROOT / "release-assets" / identifier
    if destination.exists():
        verify(destination)
        assert checksum(source / "checklist.csv") == checksum(destination / "checklist.csv"), "Use a new revision to change a sealed archive"
        print(f"Verified existing {identifier}")
        continue
    destination.mkdir()
    shutil.copy2(source / "checklist.csv", destination / "checklist.csv")
    filename = f"Checklist-of-the-Birds-of-Kenya-{identifier}.pdf"
    shutil.copy2(pdf, destination / filename)
    if version.startswith("2019."):
        shutil.copy2(source / "corrections.csv", destination / "corrections.csv")
    if version == "2019.2":
        (destination / "transitions.json").write_bytes(subprocess.check_output(
            ["git", "show", "v2019.2:release-assets/v2019.2/transitions.json"], cwd=ROOT
        ))
    elif version == "2009.1":
        shutil.copy2(source / "avibase_assignments.csv", destination / "avibase_assignments.csv")
    elif version == "2009.0":
        (destination / "taxonomy-unresolved.csv").write_bytes(subprocess.check_output(["git", "show", "v2009.0:release-assets/v2009.0/taxonomy-unresolved.csv"], cwd=ROOT))
        excluded = [row for row in read_csv(source / "checklist.csv") if not row["avibaseid"]]
        (destination / "taxonomy-exclusions.json").write_text(json.dumps(excluded, ensure_ascii=False, indent=2) + "\n")
    shutil.copy2(source / "README.md", destination / "README.md")
    descriptor = seal(destination, {"release_id": identifier, "archive_date": "2026-11-06", "render": {"output_filename": filename}}, "released")
    notes = {
        "2009.0": "The 2009 source includes minor corrections dated 13 December 2017.",
        "2009.1": "v2009.1 assigns the 49 previously blank Avibase IDs, including interpretations based on the 2019 Kenyan accounts.",
        "2019.3": "Corrects the Avibase IDs of Lesser Sand Plover and Woolly-necked Stork for the Kenyan checklist.",
        "2019.2": "v2019.2 corrects three digital identifiers; printed names and checklist membership are unchanged from v2019.1.",
    }
    descriptor.update(pdf_label=label, taxonomy_excluded_rows=49 if version == "2009.0" else 0, comparison_note=notes[version])
    (destination / "release.json").write_text(json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n")
    print(f"Sealed {identifier}")
