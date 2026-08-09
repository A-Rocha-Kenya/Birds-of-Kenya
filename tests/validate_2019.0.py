#!/usr/bin/env python3
"""Validate the checklist data used by the static site."""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "v2019.0" / "main.csv"
REQUIRED = {
    "sort", "family_scientific", "family_english", "common_name", "scientific_name",
    "red_list", "status_birdlife", "water_bird", "strict_water_bird",
    "ADU", "avibaseid", "wikiDataID", "iNaturalisttaxonID", "ITIS",
    "IUCNtaxonID", "ObservationorgID", "GBIFID", "entry_checklist_of_kenya",
    "note_2009", "note_2019",
}
STATUS_FIELDS = {"AM", "AMR", "E", "EX", "HIST", "IO", "MM", "N", "NR", "NRR", "OM", "PM", "PMR", "RAR", "RS", "SO", "VIO", "VM", "VN", "VO", "VP", "VSO", "VSA"}


def main():
    with DATA.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED - fields
        if missing:
            raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
        rows = list(reader)

    if not rows:
        raise ValueError("the checklist contains no records")
    if any(len(row) != len(fields) for row in rows):
        raise ValueError("one or more rows has a different number of fields")
    if any(not row["common_name"] or not row["scientific_name"] for row in rows):
        raise ValueError("every record must have a common and scientific name")
    if any(row["water_bird"] not in {"", "TRUE", "FALSE"} for row in rows):
        raise ValueError("water_bird must be blank, TRUE, or FALSE")
    if any(row["strict_water_bird"] not in {"", "TRUE", "FALSE"} for row in rows):
        raise ValueError("strict_water_bird must be blank, TRUE, or FALSE")
    if any(row["status_birdlife"] not in {"", "Endemic", "Introduced species", "Rare/Accidental"} for row in rows):
        raise ValueError("unexpected BirdLife status")
    if any(row["red_list"] not in {"", "Least Concern", "Near Threatened", "Vulnerable", "Endangered", "Critically Endangered", "Data Deficient", "Not Recognized"} for row in rows):
        raise ValueError("unexpected Red List category")
    if not STATUS_FIELDS.issubset(fields):
        raise ValueError("one or more status fields is missing")
    print(f"Validated {len(rows):,} records and {len(fields)} columns")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
