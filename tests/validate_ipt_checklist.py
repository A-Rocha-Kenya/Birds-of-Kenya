#!/usr/bin/env python3
"""Validate a Darwin Core Taxon checklist produced for IPT upload."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REQUIRED_FIELDS = {
    "taxonID", "taxonConceptID", "parentNameUsageID", "acceptedNameUsageID",
    "nameAccordingToID", "nameAccordingTo", "datasetID", "datasetName", "scientificName",
    "scientificNameAuthorship", "taxonRank", "taxonomicStatus", "nomenclaturalCode", "kingdom",
    "vernacularName", "language",
}
RANK_PARENT = {
    "kingdom": None,
    "phylum": "kingdom",
    "class": "phylum",
    "order": "class",
    "family": "order",
    "genus": "family",
    "species": "genus",
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
    by_id = {row["taxonID"]: row for row in rows}
    if any(row["taxonomicStatus"] != "accepted" or row["acceptedNameUsageID"] for row in rows):
        raise ValueError("accepted checklist records must not use acceptedNameUsageID")
    avilist_version = metadata["release"]["avilist_version"]
    avilist_doi = f"https://doi.org/10.2173/avilist.{avilist_version}"
    if any(row["nameAccordingToID"] != avilist_doi or "AviList" not in row["nameAccordingTo"] for row in rows):
        raise ValueError("all taxon concepts must cite the pinned AviList authority")
    if any(row["nomenclaturalCode"] != "ICZN" or row["kingdom"] != "Animalia" for row in rows):
        raise ValueError("checklist taxonomy is not consistently zoological")
    for row in rows:
        expected_parent_rank = RANK_PARENT.get(row["taxonRank"])
        parent_id = row["parentNameUsageID"]
        if expected_parent_rank is None:
            if row["taxonRank"] != "kingdom" or parent_id:
                raise ValueError("only the kingdom record may omit parentNameUsageID")
        elif parent_id not in by_id or by_id[parent_id]["taxonRank"] != expected_parent_rank:
            raise ValueError(f"invalid parentNameUsageID for {row['taxonID']}")
    species_ids = {row["taxonID"] for row in rows if row["taxonRank"] == "species"}
    species = [row for row in rows if row["taxonRank"] == "species"]
    if any(not row["taxonConceptID"].startswith("https://avibase.bsc-eoc.org/species.jsp?avibaseid=")
           or not row["scientificNameAuthorship"] or not row["genus"] or not row["specificEpithet"]
           or not row["vernacularName"] or row["language"] != "en" for row in species):
        raise ValueError("species must include AviList concepts, names, authorship, and English vernacular names")
    if (directory / "vernacular_names.csv").exists() or (directory / "distributions.csv").exists():
        raise ValueError("IPT export must contain only the Taxon core checklist data table")
    if metadata["coverage"]["country"] != "Kenya" or metadata["coverage"]["country_code"] != "KE":
        raise ValueError("metadata country coverage must be Kenya (KE)")
    if metadata["resource"]["taxon_core"] != "https://rs.gbif.org/core/dwc_taxon_2025-07-10.xml":
        raise ValueError("metadata must identify the mapped GBIF Taxon core")
    if metadata["release"]["checklist_taxa"] != len(species_ids):
        raise ValueError("metadata checklist count does not match species records")
    if metadata["release"]["taxon_core_records"] != len(rows):
        raise ValueError("metadata Taxon core count does not match checklist.csv")
    print(f"Validated IPT checklist export: {len(species_ids):,} species in {len(rows):,} Taxon core records")


if __name__ == "__main__":
    main()
