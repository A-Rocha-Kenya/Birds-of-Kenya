#!/usr/bin/env python3
"""Validate every archived version, comparison direction and downloadable asset."""

import argparse
import csv
import json
import re
import hashlib
import sys
from urllib.parse import urlsplit, parse_qs
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from taxonomy_comparison import compare_versions


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
        directory = site / "downloads" / release["id"]
        assert (directory / "checklist.csv").read_bytes() == (site / release["csv"]).read_bytes()
        if release["pdf"]:
            assert all(pdf.read_bytes() == (site / release["pdf"]).read_bytes() for pdf in directory.glob("*.pdf"))
            assert Path(release["pdf"]).name == f"Checklist-of-the-Birds-of-Kenya-{release['id']}.pdf"
        assert Path(release["csv"]).name == f"Checklist-of-the-Birds-of-Kenya-{release['id']}.csv"
    graph = json.loads((site / "data/taxon-concept-graph.json").read_text())
    for release in archive["releases"]:
        identifier = release["id"]
        with (site / release["csv"]).open(encoding="utf-8-sig", newline="") as f:
            expected_rows = len(list(csv.DictReader(f)))
        assert sum(identifier in editions for editions in graph["concepts"].values()) + len(graph["excluded_entries"].get(identifier, [])) == expected_rows
    assert all(edge[key] in graph["concepts"] for edge in graph["relationships"] for key in ("subject_id", "object_id"))
    assert "legacy_transitions" not in graph
    snapshots = {
        release["id"]: sorted(
            ({"id": concept, **editions[release["id"]]} for concept, editions in graph["concepts"].items()
             if release["id"] in editions),
            key=lambda row: (row["sequence"], row["id"]),
        )
        for release in archive["releases"]
    }
    forbidden = {"observations", "earc_decisions", "pending_earc", "exotic_status", "HIST", "RAR", "record_count"}
    pair_counts = {(p["from_release"], p["to_release"]): p["group_count"] for p in archive["pairs"]}
    assert all(count == pair_counts[(b, a)] for (a, b), count in pair_counts.items())
    for entry in archive["pairs"]:
        assert (site / entry["files"]["csv"]).is_file()
        comparison = json.loads((site / entry["files"]["json"]).read_text())
        assert comparison["from_release"] == entry["from_release"] and comparison["to_release"] == entry["to_release"]
        assert len(comparison["groups"]) == entry["group_count"]
        expected = compare_versions(snapshots, (), entry["from_release"], entry["to_release"], graph["relationships"])
        assert comparison == expected, "Website comparison differs from the shared concept graph"
        latest = list(archive["latest_by_year"].values())
        key = (entry["from_release"], entry["to_release"])
        if key in zip(latest, latest[1:]):
            review = archive["membership_reviews"].get("/".join(key), {})
            for relationship, side, statuses in [
                ("added", "new", {"listed", "possible", "addition"}),
                ("removed", "old", {"removal"}),
            ]:
                assert {g[side][0]["id"] for g in comparison["groups"] if g["relationship"] == relationship} == {
                    identifier for identifier, row in review.items() if row["status"] in statuses and row["reason"]
                }
        for group in comparison["groups"]:
            assert group["old"] or group["new"]
            assert not forbidden & set(group)
            if group["relationship"] in {"added", "removed"}:
                assert group["cardinality"] in {"0:1", "1:0"}
                assert bool(group["old"]) != bool(group["new"])
                assert not group["concept_changed"]
            else:
                assert group["old"] and group["new"]
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
    print(f"Validated {len(versions)} archived versions, {len(archive['pairs'])} comparison pairs, standard download names and identical legacy URL aliases")


if __name__ == "__main__":
    main()
