#!/usr/bin/env python3
"""Validate an assembled Birds of Kenya website."""

import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path, nargs="?", default=Path("_site"))
    args = parser.parse_args()
    site = args.site.resolve()

    required_paths = [
        "index.html", "checklist/index.html", "changes/index.html", "policy/index.html",
        "assets/style.css", "assets/site.js", "checklist/checklist.js",
        "assets/images/favicon.svg", "assets/images/nature-kenya-logo.png", "assets/images/a-rocha-kenya-logo.svg",
        "assets/images/kenya-bird-map-logo.png", "assets/images/avilist-logo.png", "assets/images/ebird-kenya-logo.svg",
        "assets/images/national-museums-kenya-logo.png", "assets/images/orcid-id.svg",
        "assets/images/east-african-rarities-committee-logo.png",
        "changes/changes.js", "data/site.json", "data/checklist.csv", "data/category-definitions.json",
        "data/taxonomy-changes.json", "data/manifest.json", ".nojekyll",
    ]
    missing = [path for path in required_paths if not (site / path).exists()]
    if missing:
        raise ValueError(f"assembled website is missing: {', '.join(missing)}")

    with (site / "data" / "checklist.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    metadata = json.loads((site / "data" / "site.json").read_text(encoding="utf-8"))
    manifest = json.loads((site / "data" / "manifest.json").read_text(encoding="utf-8"))
    comparison = json.loads((site / "data" / "taxonomy-changes.json").read_text(encoding="utf-8"))
    categories = json.loads((site / "data" / "category-definitions.json").read_text(encoding="utf-8"))

    identifiers = [row["avibase_id"] for row in rows]
    if len(rows) != manifest["counts"]["species"] or len(identifiers) != len(set(identifiers)):
        raise ValueError("website checklist does not match the release manifest")
    if "safring_numbers" not in rows[0] or not any(row["safring_numbers"].strip() for row in rows):
        raise ValueError("website checklist contains no KBM numbers")
    if metadata["release"]["id"] != manifest["release_id"] or comparison["to_release"] != manifest["release_id"]:
        raise ValueError("website, comparison, and manifest release identifiers do not match")
    if "endemic_species" in metadata["counts"]:
        raise ValueError("website metadata exposes discontinued endemic status")
    if not categories or {"code", "label", "display_group", "display_order"} - set(categories[0]):
        raise ValueError("website category definitions are incomplete")
    if any(category["display_group"] in {"Regular movement", "Regional visitors", "Regional vagrants"} for category in categories):
        raise ValueError("website exposes hidden status categories")
    if {"E", "ES", "AM", "IO", "VIO"} & set(rows[0]):
        raise ValueError("website checklist exposes hidden status fields")
    if {"E", "ES"} & {category["code"] for category in categories}:
        raise ValueError("website category definitions expose discontinued endemic status")
    pending_earc_ids = {
        row["id"]
        for group in comparison["groups"] if group.get("pending_earc")
        for row in group["new"]
    }
    if {row["avibase_id"] for row in rows if row["pending_earc"] == "TRUE"} != pending_earc_ids:
        raise ValueError("website checklist has incorrect pending EARC coverage")
    if "pending_earc" not in rows[0]:
        raise ValueError("website checklist export is missing the pending EARC column")

    missing_downloads = [path for path in metadata["downloads"].values() if path and not (site / path).exists()]
    if missing_downloads:
        raise ValueError(f"website downloads are missing: {', '.join(missing_downloads)}")

    home = (site / "index.html").read_text(encoding="utf-8")
    checklist_page = (site / "checklist" / "index.html").read_text(encoding="utf-8")
    changes_page = (site / "changes" / "index.html").read_text(encoding="utf-8")
    policy_page = (site / "policy" / "index.html").read_text(encoding="utf-8")
    if 'href="checklist/"' not in home or 'href="changes/"' not in home or home.count('href="policy/"') < 2:
        raise ValueError("home page does not link to all primary site sections")
    if any(page.count('href="../policy/"') < 2 for page in (checklist_page, changes_page)):
        raise ValueError("section pages do not link to the checklist policy in both navigation areas")
    if "Explore the checklist" in policy_page:
        raise ValueError("policy page still includes the Explore the checklist link")
    if ("Taxonomy and species names" not in policy_page or "Acceptance rules" not in policy_page
            or 'href="https://www.eararities.org/"' not in policy_page
            or "defining authority" not in policy_page
            or "Pending Committee decision" in policy_page
            or "POLICY_CONTENT" in policy_page):
        raise ValueError("website policy page was not generated from the checklist policy")
    if "Sixth edition" not in home or not all(str(year) in home for year in (1981, 1986, 1996, 2009, 2019)):
        raise ValueError("home page does not present the checklist publishing history")
    if "Nature Kenya" not in home or "data-contributors" not in home:
        raise ValueError("home page does not present the organization and contributor credits")
    if "data-download=\"checklist_pdf\"" not in home + checklist_page + changes_page:
        raise ValueError("checklist PDF is not promoted across the website")
    if "data-gbif-link" not in home + checklist_page:
        raise ValueError("GBIF publication links are not represented in the website source")
    checklist_script = (site / "checklist" / "checklist.js").read_text(encoding="utf-8")
    if "safring_numbers" not in checklist_script or "https://kenya.birdmap.africa/species/" not in checklist_script:
        raise ValueError("website checklist does not link KBM numbers to Kenya Bird Map")
    if "columnHeaders: true" not in checklist_script:
        raise ValueError("current-view CSV export does not include column headers")
    if "pending_earc" not in checklist_script:
        raise ValueError("current-view CSV export does not expose the pending EARC column")
    if "data-filter=\"endemic\"" in checklist_page or "endemicCount" in checklist_script:
        raise ValueError("checklist page exposes the discontinued endemic filter")
    print(f"Validated assembled website: four pages, {len(rows):,} species, and {comparison['group_count']:,} change groups")


if __name__ == "__main__":
    main()
