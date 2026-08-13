#!/usr/bin/env python3
"""Validate the curated EARC decisions and pending-review derivation."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_2019.1_taxonomy_report.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("taxonomy_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    renderer = load_renderer()
    decisions = renderer.read_csv(renderer.EARC_DECISIONS)
    identifiers = [row["decision_id"] for row in decisions]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("EARC decision IDs must be unique")
    if len(decisions) != 8 or any(row["decision"] != "accepted" for row in decisions):
        raise ValueError("unexpected curated EARC decision coverage")

    groups = renderer.taxonomy_groups(
        renderer.read_csv(renderer.LEGACY),
        renderer.read_csv(renderer.CURRENT),
        renderer.read_csv(renderer.MAPPING),
    )
    groups = renderer.annotate_earc(groups, decisions)
    additions_and_removals = [group for group in groups if group["cardinality"] in {"0:1", "1:0"}]
    decided = [group for group in additions_and_removals if group["earc_decisions"]]
    pending = [group for group in additions_and_removals if group["pending_earc"]]
    if (len(additions_and_removals), len(decided), len(pending)) != (30, 8, 22):
        raise ValueError("pending EARC must equal additions/removals minus matched decisions")
    if sum(bool(group["new"]) for group in pending) != 16:
        raise ValueError("unexpected number of current checklist species pending EARC")

    print("Validated 8 relevant EARC decisions, 8 decided changes, and 22 pending change groups")


if __name__ == "__main__":
    main()
