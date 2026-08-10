#!/usr/bin/env python3
"""Validate a Darwin Core Taxon checklist produced for IPT upload."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REQUIRED_FIELDS = {
    "taxonID", "datasetID", "datasetName", "scientificName", "taxonRank", "taxonomicStatus",
    "vernacularName", "kingdom", "phylum", "class", "order", "family",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    with (directory / "checklist.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    metadata = json.loads((directory / "ipt-metadata.json").read_text(encoding="utf-8"))

    missing = REQUIRED_FIELDS - set(rows[0])
    if missing:
        raise ValueError(f"checklist.csv is missing Darwin Core fields: {', '.join(sorted(missing))}")
    identifiers = [row["taxonID"] for row in rows]
    if any(not value for value in identifiers) or any(count > 1 for count in Counter(identifiers).values()):
        raise ValueError("taxonID values must be nonblank and unique")
    if any(row["taxonRank"] != "species" or row["taxonomicStatus"] != "accepted" for row in rows):
        raise ValueError("checklist rows must be accepted species")
    if any(row["kingdom"] != "Animalia" or row["phylum"] != "Chordata" or row["class"] != "Aves" for row in rows):
        raise ValueError("checklist taxonomy is not consistently bird taxonomy")
    if metadata["coverage"]["country"] != "Kenya" or metadata["coverage"]["country_code"] != "KE":
        raise ValueError("metadata country coverage must be Kenya (KE)")
    if metadata["release"]["checklist_taxa"] != len(rows):
        raise ValueError("metadata checklist count does not match checklist.csv")
    print(f"Validated IPT checklist export: {len(rows):,} Darwin Core taxa")


if __name__ == "__main__":
    main()
