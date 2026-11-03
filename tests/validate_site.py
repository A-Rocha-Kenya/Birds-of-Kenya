#!/usr/bin/env python3
"""Validate every archived version, comparison direction and downloadable asset."""

import argparse
import csv
import json
import re
import hashlib
from urllib.parse import urlsplit, parse_qs
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path, nargs="?", default=Path("_site"))
    site = parser.parse_args().site
    for name in ["index.html", "changes/index.html", "checklist/index.html", "policy/index.html", "data/releases.json"]:
        assert (site / name).is_file(), name
    archive = json.loads((site / "data/releases.json").read_text())
    versions = {r["id"] for r in archive["releases"]}
    assert len(versions) == len(archive["releases"])
    assert {(p["from_release"], p["to_release"]) for p in archive["pairs"]} == {(a, b) for a in versions for b in versions}
    assert len(archive["pairs"]) == len(versions) ** 2
    for release in archive["releases"]:
        assert (site / release["csv"]).is_file()
        if release["pdf"]:
            assert (site / release["pdf"]).is_file()
        assert len(list((site / "downloads" / release["id"]).glob("*.pdf"))) == bool(release["pdf"])
    forbidden = {"observations", "earc_decisions", "pending_earc", "exotic_status", "HIST", "RAR", "record_count"}
    pair_counts = {(p["from_release"], p["to_release"]): p["group_count"] for p in archive["pairs"]}
    assert all(count == pair_counts[(b, a)] for (a, b), count in pair_counts.items())
    for entry in archive["pairs"]:
        assert (site / entry["files"]["csv"]).is_file()
        comparison = json.loads((site / entry["files"]["json"]).read_text())
        assert comparison["from_release"] == entry["from_release"] and comparison["to_release"] == entry["to_release"]
        assert len(comparison["groups"]) == entry["group_count"]
        for group in comparison["groups"]:
            assert group["old"] and group["new"]
            assert not forbidden & set(group)
            assert group["tags"] or group["concept_changed"]
            for row in group["old"] + group["new"]:
                assert not forbidden & set(row)
    metadata = json.loads((site / "data/site.json").read_text())
    assert metadata["release"]["id"] == archive["active_release"]
    manifest = json.loads((site / "data/manifest.json").read_text())
    with (site / "data/checklist.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == manifest["counts"]["species"]
    assert not any(p.name.startswith('Taxonomy-changes-') for p in site.rglob('*.pdf'))
    for page in site.rglob("*.html"):
        for url in re.findall(r'(?:src|href)="([^\"]+\.(?:js|css)\?[^\"]+)"', page.read_text()):
            parsed = urlsplit(url)
            if parsed.scheme:
                continue
            asset = page.parent / parsed.path
            assert parse_qs(parsed.query)["v"][0] == hashlib.sha256(asset.read_bytes()).hexdigest()[:16]
    html = (site / "changes/index.html").read_text()
    assert 'id="fromVersion"' in html and 'id="toVersion"' in html
    assert 'comparison_pdf' not in html
    print(f"Validated {len(versions)} archived versions, {len(archive['pairs'])} comparison pairs and one PDF per downloadable edition")


if __name__ == "__main__":
    main()
