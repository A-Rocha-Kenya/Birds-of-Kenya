#!/usr/bin/env python3
"""Validate the species and subspecies endemicity assignments."""

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPECIES_ENDEMICS = {
    "avibase-3C79F1AC",  # Aberdare Cisticola
    "avibase-224B2B08",  # Hinde's Babbler
    "avibase-6483A467",  # Kikuyu White-eye
    "avibase-2A2CC7B3",  # Kilifi Weaver
    "avibase-FED54E53",  # Sharpe's Longclaw
    "avibase-D5549C6D",  # Taita Apalis
    "avibase-FC085C6D",  # Taita Thrush
    "avibase-B24BD4A1",  # Taita White-eye
    "avibase-2E0E6C82",  # Tana River Cisticola
    "avibase-4E61514C",  # Williams's Lark
}


def main():
    with (ROOT / "data" / "curation" / "categories.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    species = {row["avibase_id"] for row in rows if row["E"] == "TRUE"}
    subspecies = {row["avibase_id"] for row in rows if row["ES"] == "TRUE"}
    if species != SPECIES_ENDEMICS:
        raise ValueError("endemic species assignments do not match the approved list")
    if species & subspecies:
        raise ValueError("a taxon cannot be both an endemic species and endemic subspecies")
    if len(species) + len(subspecies) != 42:
        raise ValueError("endemicity assignments do not match the approved list")
    print(f"Validated {len(species)} endemic species and {len(subspecies)} endemic subspecies")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"Endemic-category validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
