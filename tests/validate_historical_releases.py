#!/usr/bin/env python3
"""Validate historical transcription, corrections, exclusions and archive integration."""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from release_archive import read_csv, verify
from site_archive import load_archive, load_concept_relationships, load_transitions
from taxonomy_comparison import compare_versions, concept_matches


def main():
    original = read_csv(ROOT / "release-assets/v2019.1/checklist.csv")
    cleaned = [{("note" if key == "note_2019" else key): value for key, value in row.items() if key not in {"note_2009", "sort_1996", "sort_2009"}} for row in original]
    assert cleaned == read_csv(ROOT / "data/legacy/2019.1/checklist.csv")
    corrected = read_csv(ROOT / "data/legacy/2019.2/checklist.csv")
    differences = [(a["sort"], key, a[key], b[key]) for a, b in zip(cleaned, corrected) for key in a if a[key] != b[key]]
    decisions = read_csv(ROOT / "data/legacy/2019.2/corrections.csv")
    assert differences == [(r["sort"], r["field"], r["before"], r["after"]) for r in decisions]
    assert len(corrected) == len({r["avibaseid"] for r in corrected}) == 1181
    historical = read_csv(ROOT / "data/legacy/2009.0/checklist.csv")
    assert len(historical) == 1100 and len(historical[0]) == 33
    assert list(historical[0]) == list(corrected[0])
    assert "note" in historical[0] and not {"note_2009", "note_2019", "sort_1996", "sort_2009"} & historical[0].keys()
    assert [r["sort"] for r in historical] == [str(i) for i in range(1, 1101)]
    unresolved = read_csv(ROOT / "release-assets/v2009.0/taxonomy-unresolved.csv")
    assert [r["sort"] for r in historical if not r["avibaseid"]] == [r["sort"] for r in unresolved]
    assert len(unresolved) == 49
    active, bundles = load_archive(ROOT)
    assert active == "v2025.0"
    versions = {identifier: json.loads((path / "taxonomy.json").read_text()) for identifier, (path, _) in bundles.items()}
    assert len(versions["v2009.0"]) == 1051
    for identifier, rows in [("v2009.0", historical), ("v2019.2", corrected)]:
        path, descriptor = bundles[identifier]
        verify(path)
        assert read_csv(path / "checklist.csv") == rows
        assert descriptor["taxonomy_excluded_rows"] == (49 if identifier == "v2009.0" else 0)
    transitions = load_transitions(bundles)
    relationships = load_concept_relationships(ROOT)
    broad, common, somali = ("avibase-" + key for key in ("5D14080C", "2247CB05", "40329BB6"))
    matches = concept_matches(relationships)
    assert {common, somali} <= matches[broad]
    assert somali not in matches[common]
    for edition in ("v2019.0", "v2019.1", "v2019.2", "v2025.0"):
        for source, target, cardinality in [("v2009.0", edition, "1:n"), (edition, "v2009.0", "n:1")]:
            result = compare_versions(versions, transitions, source, target, relationships)
            ostrich = [group for group in result["groups"]
                       if any(row["id"] in {broad, common, somali} for row in group["old"] + group["new"])]
            assert len(ostrich) == 1 and ostrich[0]["cardinality"] == cardinality
    pair = compare_versions(versions, transitions, "v2019.2", "v2025.0")
    reed = next(g for g in pair["groups"] if any(r["id"] == "avibase-5C17300B" for r in g["old"]))
    assert {r["id"] for r in reed["new"]} == {"avibase-3F0EE474"}
    sparrows = next(g for g in pair["groups"] if any(r["id"] == "avibase-2F9F81C9" for r in g["old"]))
    assert {r["id"] for r in sparrows["new"]} == {"avibase-" + i for i in ["E10D0809", "DB4998D1", "2B55E679", "F375B25B"]}
    forward = compare_versions(versions, transitions, "v2019.1", "v2019.2", relationships)
    assert not any(g["relationship"] in {"added", "removed"} for g in forward["groups"])
    assert len(forward["groups"]) == 3
    assert all(group["cardinality"] == "1:1" and group["concept_changed"] and not group["tags"] for group in forward["groups"])
    print("Validated 1,100 historical entries, 49 exclusions, exactly three 2019 identifier corrections, immutable archives and corrected forward relationships")


if __name__ == "__main__":
    main()
