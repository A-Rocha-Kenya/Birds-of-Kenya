#!/usr/bin/env python3
"""Validate editable metadata for a checklist PDF publication."""

import argparse
import csv
import json
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GBIF_LICENSES = {
    "https://creativecommons.org/publicdomain/zero/1.0/",
    "https://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/licenses/by-nc/4.0/",
}
REQUIRED_SECTIONS = {
    "document", "publisher", "history", "editorial", "source_credits", "scope",
    "sources", "checklist", "ipt", "render", "gbif",
}
REQUIRED_DOCUMENT_FIELDS = {
    "title", "short_title", "edition", "corporate_author", "version_label",
    "publication_date", "editorial_cutoff_date", "recommended_citation",
}


def root_path(value):
    return ROOT / value


def read_header(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("metadata", type=Path)
    args = parser.parse_args()
    metadata_path = args.metadata.resolve()
    metadata = tomllib.loads(metadata_path.read_text(encoding="utf-8"))

    missing_sections = sorted(REQUIRED_SECTIONS - metadata.keys())
    if missing_sections:
        raise ValueError(f"missing metadata sections: {', '.join(missing_sections)}")
    missing_fields = sorted(REQUIRED_DOCUMENT_FIELDS - metadata["document"].keys())
    if missing_fields:
        raise ValueError(f"missing document fields: {', '.join(missing_fields)}")
    if metadata["schema_version"] != 1:
        raise ValueError("unsupported publication metadata schema")

    release = root_path(metadata["sources"]["release_directory"])
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
    if metadata["release_id"] != release.name or metadata["release_id"] != manifest["release_id"]:
        raise ValueError("publication release_id does not match its release directory and manifest")

    linked_paths = [metadata["sources"]["policy"], metadata["sources"]["category_definitions"]]
    missing_paths = [value for value in linked_paths if not root_path(value).exists()]
    if missing_paths:
        raise ValueError(f"missing linked publication files: {', '.join(missing_paths)}")

    category_path = root_path(metadata["sources"]["category_definitions"])
    with category_path.open(encoding="utf-8-sig", newline="") as handle:
        definitions = list(csv.DictReader(handle))
    required_category_fields = {
        "code", "label", "definition", "display_group", "display_token",
        "display_order", "authority", "assessment_rule", "status",
    }
    if set(definitions[0]) != required_category_fields:
        raise ValueError("category definition schema does not match the publication contract")
    codes = [row["code"] for row in definitions]
    if any(not row[field] for row in definitions for field in required_category_fields):
        raise ValueError("category definitions contain blank values")
    if len(codes) != len(set(codes)):
        raise ValueError("category definition codes must be unique")

    category_columns = read_header(ROOT / "data" / "curation" / "categories.csv")[1:] + ["water_bird"]
    if set(codes) != set(category_columns):
        raise ValueError("category definitions and categories.csv columns do not agree")
    if metadata["checklist"]["group_by"] != "family":
        raise ValueError("PDF checklist must be grouped by family")
    if metadata["checklist"]["family_order"] != "avilist_sequence" or metadata["checklist"]["species_order"] != "avilist_sequence":
        raise ValueError("PDF family and species order must follow AviList sequence")
    if metadata["checklist"]["include_references"]:
        raise ValueError("references are not part of the requested PDF")
    ipt_required = {"resource_shortname", "dataset_id", "description", "country", "country_code"}
    missing_ipt_fields = sorted(ipt_required - metadata["ipt"].keys())
    if missing_ipt_fields:
        raise ValueError(f"missing IPT fields: {', '.join(missing_ipt_fields)}")
    if metadata["ipt"]["country_code"] != "KE":
        raise ValueError("IPT checklist export must use Kenya country code KE")
    if metadata["publisher"]["licence"] not in GBIF_LICENSES:
        raise ValueError("publication licence must be a GBIF-supported Creative Commons licence")

    editable = [
        metadata["document"]["edition"], metadata["document"]["publication_date"],
        metadata["document"]["recommended_citation"], metadata["publisher"]["name"],
        metadata["editorial"]["approving_body"], metadata["scope"]["geographic_scope"],
    ]
    print(f"Validated publication metadata for {metadata['release_id']}: {len(definitions)} category definitions")
    print(f"Editorial fields still blank: {sum(not value for value in editable)} of {len(editable)} priority fields")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, json.JSONDecodeError, tomllib.TOMLDecodeError, csv.Error) as error:
        print(f"Publication validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
