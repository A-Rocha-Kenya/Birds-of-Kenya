#!/usr/bin/env python3
"""Validate the EBD/AviList release helpers with small deterministic fixtures."""

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    build = load("build_release", ROOT / "scripts" / "build_release.py")
    compare = load("compare_releases", ROOT / "scripts" / "compare_releases.py")

    avilist_by_code, avilist_by_id = build.avilist_indexes([
        {"AvibaseID": "avibase-00000001", "Taxon_rank": "species", "Scientific_name": "Alpha beta", "Species_code_Cornell_Lab": "alpha1"},
        {"AvibaseID": "avibase-00000002", "Taxon_rank": "species", "Scientific_name": "Gamma delta", "Species_code_Cornell_Lab": "gamma1"},
        {"AvibaseID": "avibase-00000003", "Taxon_rank": "subspecies", "Scientific_name": "Alpha beta minor", "Species_code_Cornell_Lab": "alpha2"},
    ])

    taxon, method = build.resolve_ebird_code("alpha1", avilist_by_code, {})
    if taxon["AvibaseID"] != "avibase-00000001" or method != "ebird_species_code":
        raise ValueError("eBird species-code mapping failed")
    taxon, method = build.resolve_ebird_code("alpha2", avilist_by_code, {})
    if taxon is not None or method != "ebird_species_code_to_non_species_avilist_taxon":
        raise ValueError("AviList subspecies must not be promoted automatically")
    taxon, method = build.resolve_ebird_code("alpha2", avilist_by_code, {"alpha2": avilist_by_id["avibase-00000001"]})
    if taxon["AvibaseID"] != "avibase-00000001" or method != "curated_override":
        raise ValueError("curated eBird code override failed")
    if build.resolve_ebird_code("missing", avilist_by_code, {})[0] is not None:
        raise ValueError("missing eBird code must not fall back to a name")

    if build.release_id({"ebd_version": "2026-06", "release_revision": 0}) != "2026-06.0":
        raise ValueError("automatic release identifier failed")

    clustered = [
        {"observation_date": "2024-01-01", "latitude": 0.0, "longitude": 0.0},
        {"observation_date": "2024-01-01", "latitude": 0.0, "longitude": 0.005},
        {"observation_date": "2024-01-01", "latitude": 0.0, "longitude": 0.02},
        {"observation_date": "2024-01-02", "latitude": 0.0, "longitude": 0.0},
    ]
    if build.count_observations(clustered) != 3:
        raise ValueError("same-day one-kilometre observation clustering failed")

    reported, latest = build.aggregate_reported([
        {"ebd_category": "species", "exotic_code": "N", "REPORTED_SPECIES_CODE": "alpha1", "source_taxon_concept_id": "source-1", "record_count": "3", "first_observation_date": "2020-01-01", "last_observation_date": "2021-01-01"},
        {"ebd_category": "issf", "exotic_code": "P", "REPORTED_SPECIES_CODE": "alpha1", "source_taxon_concept_id": "source-2", "record_count": "4", "first_observation_date": "2019-01-01", "last_observation_date": "2022-01-01"},
        {"ebd_category": "species", "exotic_code": "X", "REPORTED_SPECIES_CODE": "alpha1", "source_taxon_concept_id": "source-1", "record_count": "2", "first_observation_date": "2022-02-01", "last_observation_date": "2022-02-02"},
    ], [])
    if reported[0]["record_count"] != 7 or reported[0]["first_observation_date"] != "2019-01-01" or reported[0]["last_observation_date"] != "2022-01-01" or reported[0]["exotic_status"] != "naturalized":
        raise ValueError("exotic-aware species evidence aggregation failed")

    reportable_form = {
        "ebd_category": "form", "ebird_report_as": "alpha1", "exotic_code": "", "REPORTED_SPECIES_CODE": "alpha1",
        "source_taxon_concept_id": "source-3", "record_count": "2",
        "first_observation_date": "2023-01-01", "last_observation_date": "2023-01-02",
    }
    unreported_form = {
        "ebd_category": "form", "ebird_report_as": "", "exotic_code": "", "REPORTED_SPECIES_CODE": "form1",
        "source_taxon_concept_id": "source-4", "record_count": "3",
        "first_observation_date": "2023-02-01", "last_observation_date": "2023-02-03",
    }
    if not build.is_species_evidence(reportable_form) or build.is_taxonomic_entity(reportable_form):
        raise ValueError("form with REPORT_AS was not routed to species evidence")
    if build.is_species_evidence(unreported_form) or not build.is_taxonomic_entity(unreported_form):
        raise ValueError("form without REPORT_AS was not routed to taxonomic entities")
    entities, entity_latest = build.aggregate_taxonomic_entities(
        [unreported_form], [], {
            "source-4": {
                "TAXON_ORDER": "10", "CATEGORY": "form", "SPECIES_CODE": "form1",
                "PRIMARY_COM_NAME": "Example form", "SCI_NAME": "Example [undescribed form]",
                "ORDER": "Exampleformes", "FAMILY": "Exampleidae (Examples)", "REPORT_AS": "",
            }
        },
    )
    if len(entities) != 1 or entities[0]["family"] != "Exampleidae" or entity_latest:
        raise ValueError("taxonomic-entity aggregation failed")

    naturalized_domestic = {**reportable_form, "ebd_category": "domestic", "exotic_code": "N"}
    escapee_species = {**reportable_form, "ebd_category": "species", "exotic_code": "X"}
    naturalized_hybrid = {**unreported_form, "ebd_category": "hybrid", "exotic_code": "N"}
    if not build.is_species_evidence(naturalized_domestic) or build.is_taxonomic_entity(naturalized_domestic):
        raise ValueError("naturalized domestic taxon with REPORT_AS was not folded into species evidence")
    if build.is_species_evidence(escapee_species) or not build.is_taxonomic_entity(escapee_species):
        raise ValueError("escapee species observation was not routed to taxonomic entities")
    if build.is_species_evidence(naturalized_hybrid) or not build.is_taxonomic_entity(naturalized_hybrid):
        raise ValueError("naturalized hybrid incorrectly entered species evidence")

    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        categories_path = directory / "categories.csv"
        categories_path.write_text("avilist_id,AM\navibase-00000001,TRUE\n", encoding="utf-8")
        categories, fields = build.read_categories(categories_path)
        if fields != ["AM"] or categories["avibase-00000001"]["AM"] != "TRUE":
            raise ValueError("categories keying failed")

        categories_path.write_text("avilist_id,AM,E\n", encoding="utf-8")
        categories, fields = build.read_categories(categories_path)
        if categories or fields != ["AM", "E"]:
            raise ValueError("empty categories schema was not preserved")

        categories_path.write_text("avilist_id,water_bird\n", encoding="utf-8")
        try:
            build.read_categories(categories_path)
        except ValueError as error:
            if "derived category columns" not in str(error):
                raise
        else:
            raise ValueError("manually curated waterbird category was accepted")

        overrides_path = directory / "ebird_avilist_overrides.csv"
        overrides_path.write_text(
            "reported_species_code,avilist_id,note\nalpha2,avibase-00000001,Example alignment\n",
            encoding="utf-8",
        )
        overrides = build.read_ebird_avilist_overrides(overrides_path, avilist_by_id)
        if overrides["alpha2"]["Scientific_name"] != "Alpha beta":
            raise ValueError("curated override parsing failed")

        exotic_overrides_path = directory / "ebird_exotic_overrides.csv"
        exotic_overrides_path.write_text(
            "ebd_version,source_taxon_concept_id,source_exotic_code,corrected_exotic_code,reason\n"
            "2026-06,source-1,,N,Temporary upstream correction\n",
            encoding="utf-8",
        )
        exotic_overrides = build.read_exotic_overrides(exotic_overrides_path, "2026-06")
        if exotic_overrides[("source-1", "")]["corrected_exotic_code"] != "N":
            raise ValueError("versioned exotic-code override parsing failed")

        sensitive_path = directory / "sensitive_species.csv"
        sensitive_path.write_text(
            "avilist_id,reason,reference\n"
            "avibase-00000002,Sensitive species,https://example.org/gamma\n",
            encoding="utf-8",
        )
        sensitive = build.read_sensitive_species(sensitive_path, avilist_by_id)
        if sensitive["avibase-00000002"]["reason"] != "Sensitive species":
            raise ValueError("sensitive-species curation parsing failed")

    if "Anatidae" not in build.WATERBIRD_FAMILIES or "Accipitridae" in build.WATERBIRD_FAMILIES:
        raise ValueError("Ramsar waterbird family definition is incorrect")

    changes = compare.compare(
        [{"avilist_id": "avibase-00000001", "scientific_name": "Alpha beta", "english_name": "Old Alpha", "AM": ""}],
        [
            {"avilist_id": "avibase-00000001", "scientific_name": "Alpha beta", "english_name": "Alpha", "AM": ""},
            {"avilist_id": "avibase-00000002", "scientific_name": "Gamma delta", "english_name": "Gamma", "AM": "TRUE"},
        ],
    )
    if [row["change"] for row in changes] != ["taxonomy_changed", "added"]:
        raise ValueError("release comparison classification failed")
    print("Validated release naming, evidence aggregation, eBird code mapping, categories, and comparison")


if __name__ == "__main__":
    main()
