#!/usr/bin/env python3
"""Compare v2019.1 with 2026.0 and migrate unambiguous historical categories."""

import argparse
import csv
import re
import subprocess
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "data" / "legacy" / "2019.1" / "checklist.csv"
CURRENT = ROOT / "dist" / "2026-06.0" / "checklist.csv"
MAPPING = ROOT / "data" / "curation" / "taxonomy_2019.1_to_2026.0.csv"
CATEGORIES = ROOT / "data" / "curation" / "categories.csv"
OUTPUT = ROOT / "dist" / "2026-06.0" / "comparison"

CHANGE_FIELDS = [
    "group_id", "relationship", "mapping_basis",
    "old_avilist_id", "old_english_name", "old_scientific_name",
    "new_avilist_id", "new_english_name", "new_scientific_name",
]
CATEGORY_AUDIT_FIELDS = [
    "old_avilist_id", "old_english_name", "old_scientific_name",
    "categories", "resolution", "new_avilist_ids",
]
UNRESOLVED_FIELDS = [
    "old_avilist_id", "old_english_name", "old_scientific_name", "categories",
]
CURRENT_ONLY_FIELDS = ["new_avilist_id", "new_english_name", "new_scientific_name"]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def mapping_edges(mapping):
    old_to_new = {old_id: set(targets) for old_id, targets in mapping.items()}
    new_to_old = defaultdict(set)
    for old_id, targets in old_to_new.items():
        for target in targets:
            new_to_old[target].add(old_id)

    seen = set()
    edges = []
    group_number = 0
    for starting_old in mapping:
        if starting_old in seen:
            continue
        group_number += 1
        old_ids = set()
        new_ids = set()
        queue = deque([("old", starting_old)])
        while queue:
            kind, identifier = queue.popleft()
            if kind == "old":
                if identifier in old_ids:
                    continue
                old_ids.add(identifier)
                seen.add(identifier)
                queue.extend(("new", target) for target in old_to_new[identifier])
            else:
                if identifier in new_ids:
                    continue
                new_ids.add(identifier)
                queue.extend(("old", old_id) for old_id in new_to_old[identifier])

        if not new_ids:
            relationship = "unresolved"
        elif len(old_ids) == 1 and len(new_ids) == 1:
            relationship = "replacement"
        elif len(old_ids) == 1:
            relationship = "split"
        elif len(new_ids) == 1:
            relationship = "lump"
        else:
            relationship = "many_to_many"
        group_id = f"legacy-map-{group_number:03d}"
        for old_id in mapping:
            if old_id not in old_ids:
                continue
            for new_id in mapping[old_id] or [""]:
                edges.append((group_id, relationship, old_id, new_id))
    return edges


def category_fields(categories_path):
    with categories_path.open(encoding="utf-8-sig", newline="") as handle:
        return [field for field in csv.DictReader(handle).fieldnames or [] if field != "avilist_id"]


def changed_direct_relationship(old, new):
    names_changed = (
        old["common_name"].strip() != new["english_name"].strip()
        or old["scientific_name"].strip() != new["scientific_name"].strip()
    )
    classification_changed = (
        old["family_scientific"].strip() != new["family"].strip()
        or old["family_english"].strip() != new["family_english_name"].strip()
    )
    if names_changed and classification_changed:
        return "name_and_classification_change"
    if names_changed:
        return "name_change"
    if classification_changed:
        return "classification_change"
    return ""


def change_row(group_id, relationship, basis, old, new):
    return {
        "group_id": group_id,
        "relationship": relationship,
        "mapping_basis": basis,
        "old_avilist_id": old.get("avibaseid", ""),
        "old_english_name": old.get("common_name", ""),
        "old_scientific_name": old.get("scientific_name", ""),
        "new_avilist_id": new.get("avilist_id", ""),
        "new_english_name": new.get("english_name", ""),
        "new_scientific_name": new.get("scientific_name", ""),
    }


def compare(legacy_rows, current_rows, mapping_rows, fields):
    old_by_id = {row["avibaseid"]: row for row in legacy_rows}
    new_by_id = {row["avilist_id"]: row for row in current_rows}
    mapping = read_mapping_rows(mapping_rows, old_by_id, new_by_id)
    edges = mapping_edges(mapping)
    mapped_new_ids = {target for targets in mapping.values() for target in targets}
    changes = [
        change_row(group_id, relationship, "curated_mapping", old_by_id[old_id], new_by_id.get(new_id, {}))
        for group_id, relationship, old_id, new_id in edges
    ]

    for identifier in sorted((set(old_by_id) & set(new_by_id)) - set(mapping)):
        old, new = old_by_id[identifier], new_by_id[identifier]
        relationship = changed_direct_relationship(old, new)
        if relationship:
            changes.append(change_row(f"stable-{identifier}", relationship, "stable_avilist_id", old, new))

    converted = defaultdict(lambda: {field: "" for field in fields})
    category_audit = []
    unresolved = []
    for old in legacy_rows:
        identifier = old["avibaseid"]
        assigned = [field for field in fields if old.get(field, "").strip()]
        targets = mapping.get(identifier, [])
        if identifier in mapping:
            resolution = "mapped_taxonomic_change" if targets else "no_current_equivalent"
        elif identifier in new_by_id:
            resolution = "stable_avilist_id"
            targets = [identifier]
        else:
            resolution = "not_curated"

        # Carry historical category flags to every curated current concept.
        # This handles both splits (one old taxon to several current taxa) and
        # lumps (several old taxa contributing flags to one current taxon).
        for target in targets:
            for field in assigned:
                converted[target][field] = "TRUE"

        if assigned or resolution != "stable_avilist_id":
            category_audit.append({
                "old_avilist_id": identifier,
                "old_english_name": old["common_name"],
                "old_scientific_name": old["scientific_name"],
                "categories": ";".join(assigned),
                "resolution": resolution,
                "new_avilist_ids": ";".join(targets),
            })
        if resolution in {"no_current_equivalent", "not_curated"}:
            unresolved.append({
                "old_avilist_id": identifier,
                "old_english_name": old["common_name"],
                "old_scientific_name": old["scientific_name"],
                "categories": ";".join(assigned),
            })

    connected_new_ids = (set(old_by_id) & set(new_by_id)) | mapped_new_ids
    current_only = [
        {
            "new_avilist_id": row["avilist_id"],
            "new_english_name": row["english_name"],
            "new_scientific_name": row["scientific_name"],
        }
        for row in current_rows if row["avilist_id"] not in connected_new_ids
    ]
    converted_rows = [
        {"avilist_id": row["avilist_id"], **converted[row["avilist_id"]]}
        for row in current_rows
    ]
    return changes, unresolved, current_only, category_audit, converted_rows


def read_mapping_rows(rows, old_by_id, new_by_id):
    identifiers = [row["old_avilist_id"].strip() for row in rows]
    duplicates = [identifier for identifier, count in Counter(identifiers).items() if count > 1]
    if any(not identifier for identifier in identifiers) or duplicates:
        raise ValueError("taxonomy mapping old_avilist_id values must be nonblank and unique")
    mapping = {}
    for row in rows:
        old_id = row["old_avilist_id"].strip()
        if old_id not in old_by_id:
            raise ValueError(f"unknown old_avilist_id: {old_id}")
        targets = [item.strip() for item in re.split(r"[;\r\n]+", row["new_avilist_ids"]) if item.strip()]
        unknown = [target for target in targets if target not in new_by_id]
        if unknown:
            raise ValueError(f"unknown current AviList ID for {old_id}: {', '.join(unknown)}")
        mapping[old_id] = targets
    return mapping


def write_summary(path, changes, unresolved, current_only, category_audit, converted_rows):
    relationships = Counter(row["relationship"] for row in changes)
    mapped_old = {row["old_avilist_id"] for row in changes if row["mapping_basis"] == "curated_mapping" and row["new_avilist_id"]}
    pending_categories = sum(row["resolution"] != "stable_avilist_id" and bool(row["categories"]) for row in category_audit)
    relationship_table = "".join(f"| {name} | {count:,} |\n" for name, count in sorted(relationships.items()))
    path.write_text(
        "# v2019.1 to 2026.0 taxonomy and category migration\n\n"
        "The maintained crosswalk has only `old_avilist_id` and `new_avilist_ids`. Relationship groups "
        "are derived automatically. Categories cross stable IDs automatically; changed concepts remain "
        "in the category audit for a separate decision.\n\n"
        "## Taxonomic change edges\n\n| Relationship | Edges |\n| --- | ---: |\n"
        f"{relationship_table}\n"
        "## Review status\n\n"
        f"- Old taxa mapped to current concepts: {len(mapped_old):,}\n"
        f"- Old taxa without a current equivalent: {len(unresolved):,}\n"
        f"- Changed or unresolved taxa carrying categories: {pending_categories:,}\n"
        f"- Current taxa not connected to v2019.1: {len(current_only):,}\n"
        f"- Current category rows written (including blank rows): {len(converted_rows):,}\n\n"
        "Review `category-migration-audit.csv` before making the remaining one-off category decisions. "
        "Use `--write-categories` only after reviewing `categories-converted.csv`.\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy", type=Path, default=LEGACY)
    parser.add_argument("--current", type=Path, default=CURRENT)
    parser.add_argument("--mapping", type=Path, default=MAPPING)
    parser.add_argument("--categories", type=Path, default=CATEGORIES)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--write-categories", action="store_true")
    args = parser.parse_args()

    legacy_rows = read_csv(args.legacy)
    current_rows = read_csv(args.current)
    mapping_rows = read_csv(args.mapping)
    fields = category_fields(args.categories)
    changes, unresolved, current_only, audit, converted = compare(
        legacy_rows, current_rows, mapping_rows, fields,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "taxonomy-changes.csv", CHANGE_FIELDS, changes)
    write_csv(args.output / "unresolved-old-taxa.csv", UNRESOLVED_FIELDS, unresolved)
    write_csv(args.output / "current-only-taxa.csv", CURRENT_ONLY_FIELDS, current_only)
    write_csv(args.output / "category-migration-audit.csv", CATEGORY_AUDIT_FIELDS, audit)
    write_csv(args.output / "categories-converted.csv", ["avilist_id", *fields], converted)
    write_summary(args.output / "legacy-summary.md", changes, unresolved, current_only, audit, converted)
    if args.write_categories:
        write_csv(args.categories, ["avilist_id", *fields], converted)

    subprocess.run([
        sys.executable, str(ROOT / "scripts" / "render_2019.1_taxonomy_report.py"),
        "--legacy", str(args.legacy), "--current", str(args.current),
        "--mapping", str(args.mapping), "--output", str(args.output), "--no-pdf",
    ], check=True)

    print(f"Wrote {args.output}")
    print(f"Taxonomic change edges: {len(changes):,}")
    print(f"Old taxa without an equivalent: {len(unresolved):,}")
    print(f"Current category rows written (including blank rows): {len(converted):,}")
    if args.write_categories:
        print(f"Updated {args.categories}")


if __name__ == "__main__":
    main()
