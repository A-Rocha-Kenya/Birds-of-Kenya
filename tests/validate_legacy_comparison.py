#!/usr/bin/env python3
"""Validate the minimal v2019.1 taxonomy mapping and category audit."""

import importlib.util
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "compare_2019.1_to_2026.0.py"


def load_comparison():
    spec = importlib.util.spec_from_file_location("legacy_comparison", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def old_row(identifier, name, am="", endemic=""):
    return {
        "avibaseid": identifier, "common_name": name, "scientific_name": name,
        "family_scientific": "Exampleidae", "family_english": "Examples", "AM": am, "E": endemic,
    }


def new_row(identifier, name):
    return {
        "avilist_id": identifier, "english_name": name, "scientific_name": name,
        "family": "Exampleidae", "family_english_name": "Examples", "source_avibase_ids": "",
    }


def main():
    comparison = load_comparison()
    old = [
        old_row("stable", "Stable", am="TRUE"),
        old_row("old-split", "Old split", endemic="TRUE"),
        old_row("old-lump-a", "Old lump A"),
        old_row("old-lump-b", "Old lump B"),
        old_row("unresolved", "Unresolved", am="TRUE"),
    ]
    current = [
        new_row("stable", "Stable"), new_row("new-a", "New A"), new_row("new-b", "New B"),
        new_row("new-lump", "New lump"),
    ]
    mapping = [
        {"old_avilist_id": "old-split", "new_avilist_ids": "new-a;new-b"},
        {"old_avilist_id": "old-lump-a", "new_avilist_ids": "new-lump"},
        {"old_avilist_id": "old-lump-b", "new_avilist_ids": "new-lump"},
        {"old_avilist_id": "unresolved", "new_avilist_ids": ""},
    ]

    changes, unresolved, current_only, audit, converted = comparison.compare(
        old, current, mapping, ["AM", "E"],
    )
    expected = [
        {"avilist_id": "stable", "AM": "TRUE", "E": ""},
        {"avilist_id": "new-a", "AM": "", "E": "TRUE"},
        {"avilist_id": "new-b", "AM": "", "E": "TRUE"},
        {"avilist_id": "new-lump", "AM": "", "E": ""},
    ]
    if converted != expected:
        raise ValueError("category flags were not propagated through curated mappings")
    if [row["old_avilist_id"] for row in unresolved] != ["unresolved"]:
        raise ValueError("blank mappings were not preserved as unresolved")
    if Counter(row["relationship"] for row in changes) != {"split": 2, "lump": 2, "unresolved": 1}:
        raise ValueError("split and lump relationships were not derived from the minimal mapping")

    implicit_identity = comparison.mapping_edges({"old-a": {"stable"}}, {"old-a", "stable"})
    if {row[1] for row in implicit_identity} != {"lump"}:
        raise ValueError("stable target concepts were not included when deriving lump relationships")
    if current_only or len(audit) != 5:
        raise ValueError("comparison coverage or category audit is incomplete")
    apostrophe_old = old_row("apostrophe", "Jouanin’s Petrel")
    apostrophe_new = new_row("apostrophe", "Jouanin's Petrel")
    apostrophe_old["scientific_name"] = apostrophe_new["scientific_name"] = "Bulweria fallax"
    if comparison.changed_direct_relationship(apostrophe_old, apostrophe_new):
        raise ValueError("typographic apostrophe variants must not be reported as name changes")
    family_old = old_row("family", "Example")
    family_new = new_row("family", "Example")
    family_new["family"] = "Differentidae"
    if comparison.changed_direct_relationship(family_old, family_new):
        raise ValueError("family changes must not be reported as taxonomy changes")
    print("Validated minimal legacy mapping, derived split/lump groups, and category propagation")


if __name__ == "__main__":
    main()
