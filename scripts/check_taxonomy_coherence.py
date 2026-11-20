#!/usr/bin/env python3
"""Audit current eBird codes across the checklist and sibling comparison project."""
import json
import tomllib
from pathlib import Path

from build_release import ROOT, checksum, read_csv, taxonomy_index, write_csv

config = tomllib.loads((ROOT / "config/release.toml").read_text())
release = ROOT / "dist" / config["release_id"]
comparison = ROOT.parent / "KenyaAtlasComparison"
digitization = ROOT.parent / "Digitization-of-A-Bird-Atlas-of-Kenya"
current = {r["SPECIES_CODE"]: r for r in taxonomy_index(ROOT / config["ebird_taxonomy_path"]).values()}
overrides = {r["reported_species_code"]: r["avibase_id"] for r in read_csv(ROOT / config["ebird_avilist_overrides_path"])}
taxa = {r["avibase_id"]: r for r in read_csv(comparison / "data/species_base_list.csv")}
checklist = {r["avibase_id"]: r for r in read_csv(release / "checklist.csv")}
audit = []
for row in read_csv(comparison / "data/eBird/species_mapping.csv"):
    code = row["link_code"]
    if not code:
        continue
    taxon = current[code]
    members = taxa[row["avibase_id"]]["avilist_ids"].split("|")
    assert taxon["CATEGORY"] == "species", (code, taxon["CATEGORY"])
    assert taxon["TAXON_CONCEPT_ID"] in members or overrides.get(code) in members, row
    member = taxon["TAXON_CONCEPT_ID"] if taxon["TAXON_CONCEPT_ID"] in members else overrides[code]
    if member in checklist:
        assert code in checklist[member]["ebird_species_code"].split(";"), (member, code)
    audit.append({
        "comparison_avibase_id": row["avibase_id"], "comparison_seq": taxa[row["avibase_id"]]["SEQ"],
        "source_scientific_name": row["scientific_name"], "source_species_code": row["species_code"],
        "current_species_code": code, "current_ebird_avibase_id": taxon["TAXON_CONCEPT_ID"],
        "avilist_member_id": member,
        "status": "national_checklist_match" if member in checklist else "historical_member_outside_current_national_checklist",
    })
for row in checklist.values():
    for code in row["ebird_species_code"].split(";"):
        taxon = current[code]
        assert taxon["CATEGORY"] == "species", (row["avibase_id"], code)
        assert taxon["TAXON_CONCEPT_ID"] == row["avibase_id"] or overrides.get(code) == row["avibase_id"], row
export = {r["avibase_id"]: r for r in json.loads((comparison / "export/website/sp_base.json").read_text())}
assert set(export) == set(taxa)
source_rows = read_csv(comparison / "data/eBird/species_mapping.csv")
for identifier, row in export.items():
    expected = {r["link_code"] for r in source_rows if r["avibase_id"] == identifier and r["link_code"]}
    assert set(row["ebird"]) == expected, identifier
for identifier, taxon in taxa.items():
    members = taxon["avilist_ids"].split("|")
    required = {code for code, row in current.items() if row["CATEGORY"] == "species"
                and (row["TAXON_CONCEPT_ID"] in members or overrides.get(code) in members)}
    assert required <= set(export[identifier]["ebird"]), (identifier, required - set(export[identifier]["ebird"]))
trends = ROOT.parent / "KenyaBirdTrends"
for name in ["sp_base.json", "map_data.json", "grid.json"]:
    assert (comparison / "export/website" / name).read_bytes() == (trends / "src/assets" / name).read_bytes(), name
historical = {r["SEQ"]: r for r in read_csv(digitization / "data/curated/atlas_taxonomy.csv")}
for row in read_csv(comparison / "data/taxonomy/atlas_mapping.csv"):
    assert row["atlas_avibase_id"] == historical[row["atlas_seq"]]["avibase_id"], row
assert checksum(ROOT / config["avilist_path"]) == checksum(digitization / "data/raw/taxonomy" / Path(config["avilist_path"]).name)
write_csv(release / "audit/comparison_ebird_codes.csv", list(audit[0]), audit)
print(f"Verified {len(checklist)} checklist taxa and {len(audit)} comparison source links against eBird 2026.")
