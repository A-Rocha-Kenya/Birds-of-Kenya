#!/usr/bin/env python3
"""Build an IPT-uploadable Darwin Core Taxon checklist from a release bundle."""

import argparse
import csv
import json
import tomllib
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "taxonID", "datasetID", "datasetName", "scientificName", "taxonRank", "taxonomicStatus",
    "vernacularName", "kingdom", "phylum", "class", "order", "family", "taxonRemarks",
]


def root_path(value):
    return ROOT / value


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("publication", type=Path, nargs="?", default=ROOT / "publication" / "publication.toml")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    metadata = tomllib.loads(args.publication.resolve().read_text(encoding="utf-8"))
    release = root_path(metadata["sources"]["release_directory"])
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
    if metadata["release_id"] != release.name or metadata["release_id"] != manifest["release_id"]:
        raise ValueError("publication release_id does not match its release directory and manifest")

    rows = read_csv(release / "checklist.csv")
    identifiers = [row["avilist_id"] for row in rows]
    duplicates = [key for key, count in Counter(identifiers).items() if count > 1]
    if any(not key for key in identifiers) or duplicates:
        raise ValueError("checklist avilist_id values must be nonblank and unique")

    output_dir = (args.output_dir or release / "gbif").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    checklist_path = output_dir / "checklist.csv"
    metadata_path = output_dir / "ipt-metadata.json"
    ipt = metadata["ipt"]
    citation = metadata["document"]["recommended_citation"].strip()
    license_value = metadata["publisher"]["licence"].strip()
    rights_holder = metadata["publisher"]["copyright_holder"].strip()

    with checklist_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: float(item["sequence"])):
            writer.writerow({
                "taxonID": row["avilist_id"],
                "datasetID": ipt["dataset_id"],
                "datasetName": metadata["document"]["title"],
                "scientificName": row["scientific_name"],
                "taxonRank": "species",
                "taxonomicStatus": "accepted",
                "vernacularName": row["english_name"],
                "kingdom": "Animalia",
                "phylum": "Chordata",
                "class": "Aves",
                "order": row["order"],
                "family": row["family"],
                "taxonRemarks": f"Kenya checklist; membership source: {row['membership_source']}; regional status: {row['exotic_status']}.",
            })

    missing_publish_metadata = [
        label for label, value in {
            "recommended citation": citation,
            "publisher": metadata["publisher"]["name"].strip(),
            "publisher contact email": metadata["publisher"]["email"].strip(),
            "licence": license_value,
            "rights holder": rights_holder,
        }.items() if not value
    ]
    credits = metadata["editorial"]["credits"]
    contributors = []
    for credit in credits:
        if "contributor" not in credit["roles"]:
            continue
        contributor = {
            "name": credit["name"].strip(),
            "role": next((role for role in credit["roles"] if role != "contributor"), "contributor"),
        }
        if credit.get("orcid", "").strip():
            contributor["orcid"] = credit["orcid"].strip()
        if credit.get("email", "").strip():
            contributor["email"] = credit["email"].strip()
        if credit.get("alternate_emails"):
            contributor["alternate_emails"] = [email.strip() for email in credit["alternate_emails"] if email.strip()]
        if credit.get("affiliations"):
            contributor["affiliations"] = [affiliation.strip() for affiliation in credit["affiliations"] if affiliation.strip()]
        contributors.append(contributor)

    creator_credits = [credit for credit in credits if "corporate author" in credit["roles"] or "data curator" in credit["roles"]]
    creators = []
    for credit in creator_credits:
        role = "corporate author" if "corporate author" in credit["roles"] else "data curator"
        creator = {"name": credit["name"].strip(), "role": role}
        if credit.get("orcid", "").strip():
            creator["orcid"] = credit["orcid"].strip()
        if credit.get("email", "").strip():
            creator["email"] = credit["email"].strip()
        creators.append(creator)

    ipt_metadata = {
        "resource": {
            "shortname": ipt["resource_shortname"],
            "title": metadata["document"]["title"],
            "description": ipt["description"],
            "dataset_id": ipt["dataset_id"],
            "language": metadata["language"],
            "citation": citation,
            "license": license_value,
            "rights_holder": rights_holder,
        },
        "contacts": {
            "organization": metadata["publisher"]["name"].strip(),
            "address": metadata["publisher"]["address"].strip(),
            "telephone": metadata["publisher"].get("telephone", "").strip(),
            "email": metadata["publisher"]["email"].strip(),
            "website": metadata["publisher"]["website"].strip(),
        },
        "creators": creators,
        "contributors": contributors,
        "coverage": {"country": ipt["country"], "country_code": ipt["country_code"]},
        "release": {
            "id": manifest["release_id"],
            "ebd_version": manifest["ebd_version"],
            "ebird_taxonomy_version": manifest["ebird_taxonomy_version"],
            "avilist_version": manifest["avilist_version"],
            "checklist_taxa": len(rows),
            "source": "checklist.csv; one accepted AviList species per Kenya checklist entry",
        },
        "missing_publish_metadata": missing_publish_metadata,
    }
    metadata_path.write_text(json.dumps(ipt_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows):,} Darwin Core checklist taxa to {checklist_path.relative_to(ROOT)}")
    if missing_publish_metadata:
        print(f"Complete before IPT publication: {', '.join(missing_publish_metadata)}")


if __name__ == "__main__":
    main()
