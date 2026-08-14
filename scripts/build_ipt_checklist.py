#!/usr/bin/env python3
"""Build an IPT-uploadable Darwin Core Taxon checklist from a release bundle."""

import argparse
import csv
import json
import tomllib
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from build_release import read_xlsx


ROOT = Path(__file__).resolve().parents[1]
TAXON_CORE = "https://rs.gbif.org/core/dwc_taxon_2025-07-10.xml"
FIELDS = [
    "taxonID", "taxonConceptID", "parentNameUsageID", "acceptedNameUsageID",
    "nameAccordingToID", "nameAccordingTo", "datasetID", "datasetName", "scientificName",
    "scientificNameAuthorship", "taxonRank", "taxonomicStatus", "nomenclaturalCode",
    "kingdom", "phylum", "class", "order", "family", "genus", "specificEpithet",
    "vernacularName", "language", "taxonRemarks",
]


def root_path(value):
    return ROOT / value


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def higher_taxon_id(dataset_id, rank, name):
    return f"{dataset_id}#taxon-{rank}-{quote(name, safe='')}"


def species_taxon_id(dataset_id, avilist_id):
    return f"{dataset_id}#taxon-species-{avilist_id}"


def species_concept_id(avilist_id):
    return f"https://avibase.bsc-eoc.org/species.jsp?avibaseid={avilist_id.removeprefix('avibase-')}"


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def taxon_record(taxon_id, parent_id, name, rank, dataset_id, dataset_name, name_according_to_id,
                 name_according_to, authority="", taxon_concept_id="", **classification):
    scientific_name = f"{name} {authority}" if authority else name
    return {
        "taxonID": taxon_id,
        "taxonConceptID": taxon_concept_id,
        "parentNameUsageID": parent_id,
        "acceptedNameUsageID": "",
        "nameAccordingToID": name_according_to_id,
        "nameAccordingTo": name_according_to,
        "datasetID": dataset_id,
        "datasetName": dataset_name,
        "scientificName": scientific_name,
        "scientificNameAuthorship": authority,
        "taxonRank": rank,
        "taxonomicStatus": "accepted",
        "nomenclaturalCode": "ICZN",
        "kingdom": "Animalia",
        "phylum": classification.get("phylum", ""),
        "class": classification.get("class_name", ""),
        "order": classification.get("order", ""),
        "family": classification.get("family", ""),
        "genus": classification.get("genus", ""),
        "specificEpithet": classification.get("specific_epithet", ""),
        "vernacularName": classification.get("vernacular_name", ""),
        "language": classification.get("language", ""),
        "taxonRemarks": classification.get("remarks", ""),
    }


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
    for obsolete_path in [output_dir / "vernacular_names.csv", output_dir / "distributions.csv"]:
        obsolete_path.unlink(missing_ok=True)
    ipt = metadata["ipt"]
    dataset_id = ipt["dataset_id"]
    dataset_name = metadata["document"]["title"]
    avilist_version = manifest["avilist_version"]
    name_according_to_id = ipt["taxonomic_reference_id"].strip()
    name_according_to = ipt["taxonomic_reference"].strip()
    if not name_according_to_id.endswith(f"avilist.{avilist_version}") or avilist_version not in name_according_to:
        raise ValueError("IPT taxonomic reference does not match the release AviList version")
    citation = metadata["document"]["recommended_citation"].strip()
    license_value = metadata["publisher"]["licence"].strip()
    rights_holder = metadata["publisher"]["copyright_holder"].strip()

    ordered_rows = sorted(rows, key=lambda item: float(item["sequence"]))
    avilist_path = root_path(manifest["sources"]["avilist_path"]["path"])
    avilist_rows = read_xlsx(avilist_path)
    avilist_by_rank_name = {
        (row["Taxon_rank"], row["Scientific_name"]): row for row in avilist_rows
        if row.get("Taxon_rank") in {"order", "family", "genus", "species"}
    }
    avilist_by_id = {row["AvibaseID"]: row for row in avilist_rows if row.get("AvibaseID")}
    family_orders = {}
    genus_families = {}
    for row in ordered_rows:
        family_orders.setdefault(row["family"], row["order"])
        genus = row["scientific_name"].split()[0]
        genus_families.setdefault(genus, row["family"])
        if family_orders[row["family"]] != row["order"]:
            raise ValueError(f"family {row['family']} occurs in more than one order")
        if genus_families[genus] != row["family"]:
            raise ValueError(f"genus {genus} occurs in more than one family")

    taxon_rows = [
        taxon_record(higher_taxon_id(dataset_id, "kingdom", "Animalia"), "", "Animalia", "kingdom",
                     dataset_id, dataset_name, name_according_to_id, name_according_to),
        taxon_record(higher_taxon_id(dataset_id, "phylum", "Chordata"), higher_taxon_id(dataset_id, "kingdom", "Animalia"),
                     "Chordata", "phylum", dataset_id, dataset_name, name_according_to_id, name_according_to,
                     phylum="Chordata"),
        taxon_record(higher_taxon_id(dataset_id, "class", "Aves"), higher_taxon_id(dataset_id, "phylum", "Chordata"),
                     "Aves", "class", dataset_id, dataset_name, name_according_to_id, name_according_to,
                     phylum="Chordata", class_name="Aves"),
    ]
    for order in dict.fromkeys(row["order"] for row in ordered_rows):
        authority = avilist_by_rank_name[("order", order)]["Authority"]
        taxon_rows.append(taxon_record(
            higher_taxon_id(dataset_id, "order", order), higher_taxon_id(dataset_id, "class", "Aves"), order, "order",
            dataset_id, dataset_name, name_according_to_id, name_according_to, authority=authority,
            phylum="Chordata", class_name="Aves", order=order,
        ))
    for family, order in family_orders.items():
        authority = avilist_by_rank_name[("family", family)]["Authority"]
        taxon_rows.append(taxon_record(
            higher_taxon_id(dataset_id, "family", family), higher_taxon_id(dataset_id, "order", order), family, "family",
            dataset_id, dataset_name, name_according_to_id, name_according_to, authority=authority,
            phylum="Chordata", class_name="Aves", order=order, family=family,
        ))
    for genus, family in genus_families.items():
        order = family_orders[family]
        authority = avilist_by_rank_name[("genus", genus)]["Authority"]
        taxon_rows.append(taxon_record(
            higher_taxon_id(dataset_id, "genus", genus), higher_taxon_id(dataset_id, "family", family), genus, "genus",
            dataset_id, dataset_name, name_according_to_id, name_according_to, authority=authority,
            phylum="Chordata", class_name="Aves", order=order, family=family, genus=genus,
        ))

    for row in ordered_rows:
        genus = row["scientific_name"].split()[0]
        specific_epithet = row["scientific_name"].split()[1]
        taxon_id = species_taxon_id(dataset_id, row["avilist_id"])
        authority = avilist_by_id[row["avilist_id"]]["Authority"]
        taxon_rows.append(taxon_record(
            taxon_id, higher_taxon_id(dataset_id, "genus", genus), row["scientific_name"], "species",
            dataset_id, dataset_name, name_according_to_id, name_according_to, authority=authority,
            taxon_concept_id=species_concept_id(row["avilist_id"]), phylum="Chordata", class_name="Aves",
            order=row["order"], family=row["family"], genus=genus, specific_epithet=specific_epithet,
            vernacular_name=row["english_name"], language="en",
            remarks=(f"Checklist membership source: {row['membership_source']}; "
                     f"regional status: {row['exotic_status']}.")
        ))

    write_csv(checklist_path, FIELDS, taxon_rows)

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
            "taxon_core": TAXON_CORE,
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
            "taxon_core_records": len(taxon_rows),
            "source": "checklist.csv Taxon core with normalized hierarchy; one accepted AviList species per Kenya checklist entry",
        },
        "missing_publish_metadata": missing_publish_metadata,
    }
    metadata_path.write_text(json.dumps(ipt_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    display_path = checklist_path.relative_to(ROOT) if checklist_path.is_relative_to(ROOT) else checklist_path
    print(f"Wrote {len(rows):,} species in {len(taxon_rows):,} Darwin Core taxon records to {display_path}")
    if missing_publish_metadata:
        print(f"Complete before IPT publication: {', '.join(missing_publish_metadata)}")


if __name__ == "__main__":
    main()
