#!/usr/bin/env python3
"""Build corrected historical data and seal new archives without editing old releases."""

import csv
import json
import shutil
from pathlib import Path

from release_archive import checksum, read_csv, seal, verify

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "data/legacy"
original = read_csv(ROOT / "release-assets/v2019.1/checklist.csv")
columns = ["note" if c == "note_2019" else c for c in original[0] if c not in {"sort_1996", "sort_2009", "note_2009"}]
rows = [{("note" if k == "note_2019" else k): v for k, v in row.items() if k not in {"sort_1996", "sort_2009", "note_2009"}} for row in original]
directory = LEGACY / "2019.2"
directory.mkdir(exist_ok=True)
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

# Original 2019.1 stays sealed. The new revision carries corrected relationships.
links = json.loads((ROOT / "release-assets/v2025.0/transition.json").read_text())["links"]
links = [edge for edge in links if edge["old_id"] != "avibase-2F9F81C9"]
links += [{"old_id": "avibase-2F9F81C9", "new_id": "avibase-" + identifier} for identifier in ["E10D0809", "DB4998D1", "2B55E679", "F375B25B"]]
links.append({"old_id": "avibase-5C17300B", "new_id": "avibase-3F0EE474"})
transitions = [
    {"from_release": "v2019.1", "to_release": "v2019.2", "links": [{"old_id": "avibase-3F0EE474", "new_id": "avibase-5C17300B"}], "reason": "Correction of an over-broad Eurasian Reed Warbler identifier; source names and membership unchanged."},
    {"from_release": "v2019.2", "to_release": "v2025.0", "links": links},
]

for version, pdf, label in [
    ("2009.0", LEGACY / "2009.0/source.pdf", "Fourth edition, 2009 with corrections of 13 December 2017"),
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
    if version == "2019.2":
        shutil.copy2(source / "corrections.csv", destination / "corrections.csv")
        (destination / "transitions.json").write_text(json.dumps(transitions, indent=2) + "\n")
    else:
        shutil.copy2(source / "avibase/unresolved.csv", destination / "taxonomy-unresolved.csv")
        excluded = [row for row in read_csv(source / "checklist.csv") if not row["avibaseid"]]
        (destination / "taxonomy-exclusions.json").write_text(json.dumps(excluded, ensure_ascii=False, indent=2) + "\n")
    shutil.copy2(source / "README.md", destination / "README.md")
    descriptor = seal(destination, {"release_id": identifier, "archive_date": "2026-11-06", "render": {"output_filename": filename}}, "released")
    descriptor.update(pdf_label=label, taxonomy_excluded_rows=49 if version == "2009.0" else 0, comparison_note=("The 2009 source includes minor corrections dated 13 December 2017." if version == "2009.0" else "v2019.2 corrects three digital identifiers; printed names and checklist membership are unchanged from v2019.1."))
    (destination / "release.json").write_text(json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n")
    print(f"Sealed {identifier}")
