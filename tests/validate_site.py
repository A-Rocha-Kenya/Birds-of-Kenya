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
        "index.html", "checklist/index.html", "changes/index.html",
        "assets/style.css", "assets/site.js", "checklist/checklist.js",
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

    identifiers = [row["avilist_id"] for row in rows]
    if len(rows) != manifest["counts"]["species"] or len(identifiers) != len(set(identifiers)):
        raise ValueError("website checklist does not match the release manifest")
    if metadata["release"]["id"] != manifest["release_id"] or comparison["to_release"] != manifest["release_id"]:
        raise ValueError("website, comparison, and manifest release identifiers do not match")
    endemic_species = sum(bool(row["E"].strip()) for row in rows)
    endemic_subspecies = sum(bool(row["ES"].strip()) for row in rows)
    if metadata["counts"]["endemic_species"] != f"{endemic_species:,}":
        raise ValueError("website endemic-species count is incorrect")
    if metadata["counts"]["endemic_subspecies"] != f"{endemic_subspecies:,}":
        raise ValueError("website endemic-subspecies count is incorrect")
    if not categories or {"code", "label", "display_group", "display_order"} - set(categories[0]):
        raise ValueError("website category definitions are incomplete")

    missing_downloads = [path for path in metadata["downloads"].values() if path and not (site / path).exists()]
    if missing_downloads:
        raise ValueError(f"website downloads are missing: {', '.join(missing_downloads)}")

    home = (site / "index.html").read_text(encoding="utf-8")
    checklist_page = (site / "checklist" / "index.html").read_text(encoding="utf-8")
    changes_page = (site / "changes" / "index.html").read_text(encoding="utf-8")
    if 'href="checklist/"' not in home or 'href="changes/"' not in home:
        raise ValueError("home page does not link to both primary site sections")
    if "data-download=\"checklist_pdf\"" not in home + checklist_page + changes_page:
        raise ValueError("checklist PDF is not promoted across the website")
    if "data-gbif-link" not in home + checklist_page:
        raise ValueError("GBIF publication links are not represented in the website source")

    print(f"Validated assembled website: three pages, {len(rows):,} species, and {comparison['group_count']:,} change groups")


if __name__ == "__main__":
    main()
