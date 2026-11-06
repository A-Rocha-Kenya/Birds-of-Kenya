#!/usr/bin/env python3
"""Extract the corrected fourth-edition PDF using the 2019 CSV schema."""

import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data" / "legacy" / "2009.0"
PDF = DIRECTORY / "source.pdf"

# Extract the embedded text; OCR is unnecessary for this searchable PDF.
text = subprocess.check_output(["pdftotext", "-layout", str(PDF), "-"], text=True)
with (ROOT / "data" / "legacy" / "2019.1" / "checklist.csv").open(newline="", encoding="utf-8-sig") as handle:
    columns = next(csv.reader(handle))

family_pattern = re.compile(r"^([A-Za-z]+idae): (.+)$")
species_pattern = re.compile(r"^c (.+?) ([A-Z][a-z]+ [a-z][a-z-]+(?: x [a-z]+)?)(.*)$")
status_columns = {
    "AM": "AM", "am": "AMR", "PM": "PM", "pm": "PMR", "E": "E", "Ex": "EX",
    "IO": "IO", "io": "IO", "MM": "MM", "mm": "MM", "OM": "OM", "om": "OM",
    "RS": "RS", "SO": "SO", "VIO": "VIO", "VN": "VN", "VP": "VP", "VS": "VSO", "VSA": "VSA",
}
rows = []
family_scientific = family_english = ""
species_notes = False

# Printed checklist pages 1–39 follow three front-matter pages.
for page_number, page in enumerate(text.split("\f")[3:42], start=1):
    lines = [line.rstrip() for line in page.splitlines() if line.strip()]
    lines = lines[2 if page_number == 1 else 1:-1]  # Remove running headers and footers.
    for line in lines:
        family = family_pattern.fullmatch(line.strip())
        species = species_pattern.fullmatch(line)
        if family:
            family_scientific, family_english = family.groups()
            species_notes = False
        elif species:
            common_name, scientific_name, suffix = species.groups()
            row = dict.fromkeys(columns, "")
            row.update(
                sort=str(len(rows) + 1),
                family_scientific=family_scientific, family_english=family_english,
                common_name=common_name, scientific_name=scientific_name,
                entry_checklist_of_kenya=line[2:],
            )
            # Inline corrections are notes, rather than migration/status codes.
            status, _, correction = suffix.partition(" — ")
            row["note"] = correction
            for token in re.findall(r"\b[A-Za-z]+\b", status):
                if token in status_columns:
                    row[status_columns[token]] = "TRUE"
            rows.append(row)
            species_notes = True
        elif line.startswith(" ") and species_notes:
            # Keep subspecies annotations in their species' note, not as extra taxa.
            previous = rows[-1]["note"]
            separator = "" if previous.endswith("-") else " "
            rows[-1]["note"] = (previous + separator + line.strip()).strip()
        else:
            # Unindented commentary describes a family or a subsequent group of taxa.
            species_notes = False

assert len(rows) == 1100, f"Expected the PDF's stated 1,100 entries, found {len(rows)}"
assert len({row["scientific_name"] for row in rows}) == len(rows)
assert all(row["family_scientific"] for row in rows)
assert sum(line.startswith("c ") for line in text.splitlines()) == len(rows)
# Reuse the reviewed IDs from the sealed edition by printed scientific name.
with (ROOT / "release-assets/v2009.0/checklist.csv").open(newline="", encoding="utf-8") as handle:
    identifiers = {row["scientific_name"]: row["avibaseid"] for row in csv.DictReader(handle)}
for row in rows:
    row["avibaseid"] = identifiers[row["scientific_name"]]
with (DIRECTORY / "checklist.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
print(f"Extracted {len(rows):,} entries in {len({row['family_scientific'] for row in rows})} families to {DIRECTORY / 'checklist.csv'}")
