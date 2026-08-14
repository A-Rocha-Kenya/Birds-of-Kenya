#!/usr/bin/env python3
"""Validate a generated EBD/AviList release directory."""

import argparse
import csv
import datetime
import json
import sys
from collections import Counter
from pathlib import Path


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    release = args.release.resolve()
    checklist = read_csv(release / "checklist.csv")
    latest = read_csv(release / "latest_records.csv")
    entities = read_csv(release / "supplementary_taxa.csv")
    entity_latest = read_csv(release / "supplementary_taxa_latest_records.csv")
    unmapped = read_csv(release / "audit" / "ebd_taxa_not_in_avilist.csv")
    exotic_overrides = read_csv(release / "audit" / "exotic_code_overrides.csv")
    sensitive_species = read_csv(release / "audit" / "sensitive_species.csv")
    missing_safring = read_csv(release / "audit" / "safring_numbers_missing.csv")
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))

    if manifest["release_id"] != release.name:
        raise ValueError("release directory name must equal manifest release_id")
    identifiers = [row["avilist_id"] for row in checklist]
    duplicates = [key for key, count in Counter(identifiers).items() if count > 1]
    if any(not key for key in identifiers) or duplicates:
        raise ValueError("checklist avilist_id values must be nonblank and unique")
    if {row["avilist_id"] for row in missing_safring} != {
        row["avilist_id"] for row in checklist if not row["safring_numbers"]
    }:
        raise ValueError("SAFRING mapping audit does not match checklist coverage")
    for row in checklist:
        safring_numbers = [value for value in row.get("safring_numbers", "").split(";") if value]
        if any(not value.isdigit() or int(value) <= 0 for value in safring_numbers) or len(safring_numbers) != len(set(safring_numbers)):
            raise ValueError("checklist contains an invalid SAFRING number")
    required = ["scientific_name", "english_name", "ebird_species_code", "membership_source", "sensitive", "exotic_status"]
    if any(not row[field] for row in checklist for field in required):
        raise ValueError("checklist contains a blank required value")
    if any(row["membership_source"] not in {"ebd", "curated_sensitive_species", "curated_species"} for row in checklist):
        raise ValueError("checklist contains an invalid membership source")
    if any(row["sensitive"] not in {"TRUE", "FALSE"} for row in checklist):
        raise ValueError("checklist contains an invalid sensitive flag")
    if any(not all(row[field] for field in ["observations", "first_observation_date", "last_observation_date"]) for row in checklist if row["membership_source"] == "ebd"):
        raise ValueError("EBD checklist evidence contains a blank observation summary")
    if any(row["sensitive"] != "TRUE" or any(row[field] for field in ["observations", "first_observation_date", "last_observation_date"]) for row in checklist if row["membership_source"] == "curated_sensitive_species"):
        raise ValueError("curated sensitive membership must be flagged and must not invent observation summaries")
    if any(row["sensitive"] != "FALSE" for row in checklist if row["membership_source"] == "curated_species"):
        raise ValueError("curated checklist membership must not be flagged as sensitive")
    if any(row["first_observation_date"] > row["last_observation_date"] for row in checklist if row["first_observation_date"] and row["last_observation_date"]):
        raise ValueError("checklist contains an invalid observation-date range")
    if any(row["exotic_status"] not in {"native", "naturalized", "provisional"} for row in checklist):
        raise ValueError("checklist contains an invalid exotic status")
    if "EX" in checklist[0]:
        raise ValueError("checklist must not contain an extinct category")
    reference_date = datetime.date.fromisoformat(manifest["historical_reference_date"])
    historical_cutoff = reference_date.replace(year=reference_date.year - manifest["historical_years"])
    if any(
        (row["HIST"] == "TRUE") != (
            bool(row["last_observation_date"])
            and datetime.date.fromisoformat(row["last_observation_date"]) < historical_cutoff
        )
        for row in checklist
    ):
        raise ValueError("checklist historical status does not match the last observation date")
    if any((row["RAR"] == "TRUE") != (bool(row["observations"]) and int(row["observations"]) < 5) for row in checklist):
        raise ValueError("checklist rarity status is inconsistent")
    latest_counts = Counter(row["avilist_id"] for row in latest)
    if any(identifier not in set(identifiers) for identifier in latest_counts):
        raise ValueError("latest_records contains an avilist_id absent from checklist")
    if any(count > 5 for count in latest_counts.values()):
        raise ValueError("latest_records contains more than five rows for an avilist_id")
    entity_keys = [(row["source_taxon_concept_id"], row["exotic_status"]) for row in entities]
    if any(not identifier for identifier, status in entity_keys) or len(entity_keys) != len(set(entity_keys)):
        raise ValueError("supplementary_taxa source_taxon_concept_id and exotic_status pairs must be nonblank and unique")
    entity_required = ["entity_category", "exotic_status", "scientific_name", "english_name", "record_count", "first_observation_date", "last_observation_date"]
    if any(not row[field] for row in entities for field in entity_required):
        raise ValueError("supplementary_taxa contains a blank required value")
    if any(row["first_observation_date"] > row["last_observation_date"] for row in entities):
        raise ValueError("supplementary_taxa contains an invalid observation-date range")
    if any(row["exotic_status"] not in {"native", "naturalized", "provisional", "escapee"} for row in entities):
        raise ValueError("supplementary_taxa contains an invalid exotic status")
    entity_latest_counts = Counter((row["source_taxon_concept_id"], row["exotic_status"]) for row in entity_latest)
    if any(key not in set(entity_keys) for key in entity_latest_counts):
        raise ValueError("supplementary_taxa_latest_records contains a taxon absent from supplementary_taxa")
    if any(count > 5 for count in entity_latest_counts.values()):
        raise ValueError("supplementary_taxa_latest_records contains more than five rows for a taxon")
    if manifest["counts"]["species"] != len(checklist) or manifest["counts"]["latest_records"] != len(latest):
        raise ValueError("manifest output counts do not agree with the tables")
    if manifest["counts"]["taxonomic_entities"] != len(entities) or manifest["counts"]["taxonomic_entity_latest_records"] != len(entity_latest):
        raise ValueError("manifest taxonomic-entity counts do not agree with the tables")
    if manifest["counts"]["unmapped_reported_species_codes"] != len(unmapped):
        raise ValueError("manifest unmatched-code count is inconsistent")
    if manifest["counts"]["curated_exotic_code_records"] != sum(int(row["record_count"]) for row in exotic_overrides):
        raise ValueError("manifest exotic-code override count is inconsistent")
    if manifest["counts"]["curated_sensitive_species"] != len(sensitive_species):
        raise ValueError("manifest sensitive-species count is inconsistent")
    print(f"Validated {manifest['release_id']}: {len(checklist):,} species and {len(latest):,} retained records")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, csv.Error) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
