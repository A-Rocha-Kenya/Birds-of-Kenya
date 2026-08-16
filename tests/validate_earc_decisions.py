#!/usr/bin/env python3
"""Validate the curated EARC decisions and pending-review derivation."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_2019.1_taxonomy_report.py"
SITE_SCRIPT = ROOT / "scripts" / "build_site.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("taxonomy_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_site_builder():
    spec = importlib.util.spec_from_file_location("site_builder", SITE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    renderer = load_renderer()
    decisions = renderer.read_csv(renderer.EARC_DECISIONS)
    identifiers = [row["decision_id"] for row in decisions]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("EARC decision IDs must be unique")
    if len(decisions) != 11 or {row["decision"] for row in decisions} != {"accepted", "rejected"}:
        raise ValueError("unexpected curated EARC decision coverage")
    if any(not row["avibase_id"] for row in decisions):
        raise ValueError("EARC decisions must use a current Avibase identifier")

    groups = renderer.taxonomy_groups(
        renderer.read_csv(renderer.LEGACY),
        renderer.read_csv(renderer.CURRENT),
        renderer.read_csv(renderer.MAPPING),
    )
    groups = renderer.annotate_earc(groups, decisions)
    rejected_ids = {row["avibase_id"] for row in decisions if row["decision"] == "rejected"}
    if rejected_ids & {row["id"] for group in groups for side in ("old", "new") for row in group[side]}:
        raise ValueError("rejected EARC taxa must be absent from the comparison")
    additions_and_removals = [group for group in groups if group["cardinality"] in {"0:1", "1:0"}]
    decided = [group for group in additions_and_removals if group["earc_decisions"]]
    pending = [group for group in additions_and_removals if group["pending_earc"]]
    if len(pending) != len(additions_and_removals) - len(decided):
        raise ValueError("pending EARC must equal additions/removals minus matched decisions")
    if sum(bool(group["new"]) for group in pending) != 13:
        raise ValueError("unexpected number of current checklist species pending EARC")

    old_comparison = {"groups": [
        {"cardinality": "0:1", "old": [], "new": [{"id": "avibase-DDEF7228"}]},
        {"cardinality": "0:1", "old": [], "new": [{"id": "avibase-90AAE188"}]},
    ]}
    old_comparison = load_site_builder().annotate_earc(old_comparison, decisions)
    if [group["pending_earc"] for group in old_comparison["groups"]] != [False, True]:
        raise ValueError("site builder did not derive pending EARC for a legacy comparison")

    print("Validated 11 EARC decisions, rejected-taxon exclusion, and legacy-site compatibility")


if __name__ == "__main__":
    main()
