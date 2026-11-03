#!/usr/bin/env python3
"""Historical occurrence-review helpers retained for legacy audit validation."""

import bisect
import csv
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "data" / "legacy" / "2019.1" / "checklist.csv"
CURRENT = ROOT / "dist" / "v2026.0" / "checklist.csv"
MAPPING = ROOT / "data" / "curation" / "taxonomy_2019.1_to_2026.0.csv"
EARC_DECISIONS = ROOT / "data" / "curation" / "earc_decisions.csv"
COMPARE_SCRIPT = ROOT / "scripts" / "compare_2019.1_to_2026.0.py"

RELATIONSHIP_LABELS = {
    "1:1": "1:1", "n:1": "n:1", "1:n": "1:n", "n:n": "n:n",
    "1:0": "Discontinued", "0:1": "New",
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_comparison():
    spec = importlib.util.spec_from_file_location("legacy_comparison", COMPARE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def number(value):
    return float(value) if value else 0.0


def normalized(values, normalize_value=lambda value: value):
    return {" ".join(normalize_value(value).split()).casefold() for value in values if value.strip()}


def taxonomy_groups(legacy_rows, current_rows, mapping_rows):
    comparison = load_comparison()
    old_by_id = {row["avibaseid"]: row for row in legacy_rows}
    new_by_id = {row["avibase_id"]: row for row in current_rows}
    mapping = comparison.read_mapping_rows(mapping_rows, old_by_id, new_by_id)
    edges = comparison.mapping_edges(mapping, old_by_id)
    current_sorted = sorted(current_rows, key=lambda row: number(row["sequence"]))
    current_sequences = [number(row["sequence"]) for row in current_sorted]

    anchors = []
    for old in legacy_rows:
        identifier = old["avibaseid"]
        targets = mapping.get(identifier, [])
        if identifier in new_by_id:
            anchors.append((number(old["sort"]), number(new_by_id[identifier]["sequence"])))
        elif targets:
            anchors.append((number(old["sort"]), min(number(new_by_id[target]["sequence"]) for target in targets)))
    anchors.sort()
    anchor_positions = [position for position, _ in anchors]

    def estimated_sequence(old_rows):
        position = min(number(row["sort"]) for row in old_rows)
        index = bisect.bisect_left(anchor_positions, position)
        if index == 0:
            return anchors[0][1] - (anchors[0][0] - position)
        if index == len(anchors):
            return anchors[-1][1] + (position - anchors[-1][0])
        old_a, new_a = anchors[index - 1]
        old_b, new_b = anchors[index]
        fraction = (position - old_a) / (old_b - old_a)
        return new_a + fraction * (new_b - new_a)

    def primary_taxon(new_rows, old_rows):
        if new_rows:
            return min(new_rows, key=lambda row: number(row["sequence"]))
        estimate = estimated_sequence(old_rows)
        index = min(bisect.bisect_left(current_sequences, estimate), len(current_sorted) - 1)
        return current_sorted[index]

    def make_group(group_id, relationship, old_rows, new_rows):
        old_rows = sorted(old_rows, key=lambda row: number(row["sort"]))
        new_rows = sorted(new_rows, key=lambda row: number(row["sequence"]))
        primary = primary_taxon(new_rows, old_rows)
        sort_order = number(new_rows[0]["sequence"]) if new_rows else estimated_sequence(old_rows)
        tags = []
        if old_rows and new_rows:
            if normalized(
                (row["common_name"] for row in old_rows), comparison.normalized_english_name,
            ) != normalized((row["english_name"] for row in new_rows), comparison.normalized_english_name):
                tags.append("english_name")
            if normalized(row["scientific_name"] for row in old_rows) != normalized(row["scientific_name"] for row in new_rows):
                tags.append("scientific_name")
            if normalized(row["family_scientific"] for row in old_rows) != normalized(row["family"] for row in new_rows):
                tags.append("classification")
        old_names = [row["common_name"].strip() for row in old_rows]
        new_names = [row["english_name"].strip() for row in new_rows]
        if any(row.get("membership_source") == "curated_species" for row in new_rows):
            tags.append("curated_species")
        cardinality = (
            "1:1" if len(old_rows) == 1 and len(new_rows) == 1 else
            "n:1" if len(old_rows) > 1 and len(new_rows) == 1 else
            "1:n" if len(old_rows) == 1 and len(new_rows) > 1 else
            "n:n" if old_rows and new_rows else
            "1:0" if old_rows else "0:1"
        )
        title_names = new_names or old_names
        title = title_names[0] if len(title_names) == 1 else " / ".join(title_names[:3])
        if len(title_names) > 3:
            title += f" +{len(title_names) - 3}"
        return {
            "id": group_id,
            "relationship": relationship,
            "cardinality": cardinality,
            "relationship_label": RELATIONSHIP_LABELS[cardinality],
            "tags": tags,
            "title": title,
            "sort_order": sort_order,
            "order": primary["order"],
            "family": primary["family"] if new_rows else old_rows[0]["family_scientific"],
            "family_english": primary["family_english_name"] if new_rows else old_rows[0]["family_english"],
            "old": [
                {
                    "id": row["avibaseid"], "english": row["common_name"].strip(),
                    "scientific": row["scientific_name"].strip(), "family": row["family_scientific"],
                }
                for row in old_rows
            ],
            "new": [
                {
                    "id": row["avibase_id"], "english": row["english_name"].strip(),
                    "scientific": row["scientific_name"].strip(), "family": row["family"],
                    "sequence": number(row["sequence"]),
                    "ebird_codes": [code for code in row.get("ebird_species_code", "").split(";") if code],
                    "taxonomy_comment": row.get("taxonomy_comment", "").strip(),
                }
                for row in new_rows
            ],
        }

    grouped_edges = defaultdict(list)
    for group_id, relationship, old_id, new_id in edges:
        grouped_edges[group_id].append((relationship, old_id, new_id))
    groups = []
    for group_id, group_edges in grouped_edges.items():
        relationship = group_edges[0][0]
        old_ids = list(dict.fromkeys(edge[1] for edge in group_edges))
        new_ids = list(dict.fromkeys(edge[2] for edge in group_edges if edge[2]))
        old_ids.extend(identifier for identifier in new_ids if identifier in old_by_id and identifier not in old_ids)
        groups.append(make_group(
            group_id, relationship,
            [old_by_id[identifier] for identifier in old_ids],
            [new_by_id[identifier] for identifier in new_ids],
        ))

    mapped_old_ids = set(mapping) | {identifier for targets in mapping.values() for identifier in targets if identifier in old_by_id}
    mapped_new_ids = {identifier for targets in mapping.values() for identifier in targets}
    for identifier in sorted((set(old_by_id) & set(new_by_id)) - mapped_old_ids):
        old, new = old_by_id[identifier], new_by_id[identifier]
        if comparison.changed_direct_relationship(old, new):
            groups.append(make_group(f"stable-{identifier}", "retained", [old], [new]))
    connected_new_ids = (set(old_by_id) & set(new_by_id)) | mapped_new_ids
    for row in current_rows:
        if row["avibase_id"] not in connected_new_ids:
            groups.append(make_group(f"added-{row['avibase_id']}", "added", [], [row]))
    return sorted(groups, key=lambda group: (group["sort_order"], group["id"]))


def annotate_earc(groups, decision_rows):
    decisions_by_taxon = defaultdict(list)
    for row in decision_rows:
        decision = {
            "decision_id": row["decision_id"],
            "decision": row["decision"],
            "report_year": row["report_year_published"],
            "source_url": row["source_url"],
            "reference": row["reference"],
        }
        decisions_by_taxon[row["avibase_id"].strip()].append(decision)

    for group in groups:
        taxon_ids = {row["id"] for side in ("old", "new") for row in group[side]}
        decisions = [decision for identifier in taxon_ids for decision in decisions_by_taxon[identifier]]
        group["earc_decisions"] = sorted(decisions, key=lambda row: row["decision_id"])
        group["pending_earc"] = group["cardinality"] in {"0:1", "1:0"} and not decisions
    return groups


