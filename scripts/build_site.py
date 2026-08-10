#!/usr/bin/env python3
"""Assemble the GitHub Pages website from maintained source and one release bundle."""

import argparse
import csv
import json
import shutil
import tempfile
import tomllib
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
PUBLICATION = ROOT / "publication" / "publication.toml"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require(path):
    if not path.exists():
        raise ValueError(f"required site input is missing: {path}")
    return path


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def public_metadata(metadata, manifest, rows, comparison, downloads):
    gbif_doi = metadata["gbif"]["doi"].strip()
    citation = metadata["document"]["recommended_citation"].strip()
    return {
        "release": {
            "id": manifest["release_id"],
            "label": metadata["document"]["version_label"],
            "publication_date": metadata["document"]["publication_date"],
            "status": metadata["status"],
        },
        "counts": {
            "species": f"{len(rows):,}",
            "families": f"{len({row['family'] for row in rows}):,}",
            "observations": f"{manifest['counts']['species_observation_records']:,}",
            "changes": f"{comparison['group_count']:,}",
            "sensitive_species": f"{manifest['counts']['curated_sensitive_species']:,}",
        },
        "sources": {
            "avilist": f"AviList {manifest['avilist_version']}",
            "ebird_taxonomy": f"eBird taxonomy {manifest['ebird_taxonomy_version']}",
            "ebd": manifest["ebd_version"],
        },
        "publication": {
            "title": metadata["document"]["title"],
            "citation": citation or "Formal publication metadata is being prepared.",
            "publisher": metadata["publisher"]["name"],
        },
        "gbif": {
            "dataset_url": metadata["gbif"]["dataset_url"].strip(),
            "doi": gbif_doi,
            "doi_url": f"https://doi.org/{gbif_doi}" if gbif_doi else "",
        },
        "comparison": {
            "from_release": comparison["from_release"],
            "to_release": comparison["to_release"],
            "relationship_counts": comparison["relationship_counts"],
        },
        "downloads": downloads,
    }


def validate_publication(metadata, allow_draft):
    if metadata["status"] != "draft":
        required = {
            "publication date": metadata["document"]["publication_date"],
            "recommended citation": metadata["document"]["recommended_citation"],
            "publisher": metadata["publisher"]["name"],
            "GBIF dataset URL": metadata["gbif"]["dataset_url"],
            "GBIF DOI": metadata["gbif"]["doi"],
        }
        missing = [label for label, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"published website metadata is incomplete: {', '.join(missing)}")
    elif not allow_draft:
        raise ValueError("publication metadata is still draft; pass --allow-draft for a preview build")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication", type=Path, default=PUBLICATION)
    parser.add_argument("--release-dir", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()

    metadata = tomllib.loads(args.publication.resolve().read_text(encoding="utf-8"))
    validate_publication(metadata, args.allow_draft)
    release = (args.release_dir or ROOT / metadata["sources"]["release_directory"]).resolve()
    manifest = json.loads(require(release / "manifest.json").read_text(encoding="utf-8"))
    if manifest["release_id"] != metadata["release_id"] or release.name != metadata["release_id"]:
        raise ValueError("website, publication, and release identifiers do not match")

    checklist = require(release / "checklist.csv")
    rows = read_csv(checklist)
    category_definitions = read_csv(require(ROOT / metadata["sources"]["category_definitions"]))
    comparison_path = require(release / "comparison" / "taxonomy-changes.json")
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    if comparison["to_release"] != manifest["release_id"]:
        raise ValueError("comparison target does not match the website release")

    checklist_pdf = require(release / metadata["render"]["output_filename"])
    comparison_csv = require(release / "comparison" / "taxonomy-changes.csv")
    comparison_pdfs = list((release / "comparison").glob("Taxonomy-changes-*.pdf"))
    if len(comparison_pdfs) > 1:
        raise ValueError("release has more than one taxonomy comparison PDF")
    comparison_pdf = comparison_pdfs[0] if comparison_pdfs else None
    downloads = {
        "checklist_pdf": f"downloads/{checklist_pdf.name}",
        "checklist_csv": f"downloads/Birds-of-Kenya-{manifest['release_id']}.csv",
        "comparison_csv": "downloads/Taxonomy-changes-2019.1-to-2026.0.csv",
        "comparison_pdf": f"downloads/{comparison_pdf.name}" if comparison_pdf else "",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="birds-of-kenya-site-", dir=output.parent) as temporary:
        staging = Path(temporary) / "site"
        shutil.copytree(WEBSITE, staging)
        copy(checklist, staging / "data" / "checklist.csv")
        (staging / "data" / "category-definitions.json").write_text(
            json.dumps(category_definitions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        copy(release / "manifest.json", staging / "data" / "manifest.json")
        copy(comparison_path, staging / "data" / "taxonomy-changes.json")
        copy(checklist_pdf, staging / downloads["checklist_pdf"])
        copy(checklist, staging / downloads["checklist_csv"])
        copy(comparison_csv, staging / downloads["comparison_csv"])
        if comparison_pdf:
            copy(comparison_pdf, staging / downloads["comparison_pdf"])
        site_metadata = public_metadata(metadata, manifest, rows, comparison, downloads)
        (staging / "data" / "site.json").write_text(
            json.dumps(site_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (staging / ".nojekyll").touch()
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(staging, output)

    relationships = Counter(group["relationship"] for group in comparison["groups"])
    print(f"Built {output} for {manifest['release_id']}: {len(rows):,} species and {sum(relationships.values()):,} change groups")


if __name__ == "__main__":
    main()
