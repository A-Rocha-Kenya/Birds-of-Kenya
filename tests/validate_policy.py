#!/usr/bin/env python3
"""Contract checks for the planned AviList-based core checklist."""

import sys
from collections import Counter

ALLOWED_RANKS = {"species", "subspecies"}
ALLOWED_OCCURRENCE = {"accepted", "historical", "introduced"}


def validate_core_rows(rows):
    """Return policy violations for normalized core rows."""
    errors = []
    ids = [row.get("AvibaseID", "") for row in rows]
    if any(not value for value in ids):
        errors.append("every row must have a nonblank AvibaseID")
    duplicates = sorted(identifier for identifier, count in Counter(ids).items() if identifier and count > 1)
    if duplicates:
        errors.append(f"duplicate AvibaseID values: {', '.join(duplicates)}")

    by_id = {row.get("AvibaseID"): row for row in rows}
    for row in rows:
        identifier = row.get("AvibaseID", "<missing>")
        rank = row.get("Taxon_rank", "")
        if rank not in ALLOWED_RANKS:
            errors.append(f"{identifier} has invalid public rank {rank!r}")
        if row.get("occurrence_status") not in ALLOWED_OCCURRENCE:
            errors.append(f"{identifier} has invalid occurrence status")
        if not row.get("evidence_ids"):
            errors.append(f"{identifier} has no evidence reference")
        if rank == "subspecies":
            parent_id = row.get("parent_AvibaseID")
            parent = by_id.get(parent_id)
            if not parent or parent.get("Taxon_rank") != "species":
                errors.append(f"{identifier} has no species parent row")
            elif "water_bird" in row and "water_bird" in parent and row["water_bird"] != parent["water_bird"]:
                errors.append(f"{identifier} disagrees with its species parent on water_bird")
    return errors


def main():
    valid_rows = [
        {"AvibaseID": "sp-1", "Taxon_rank": "species", "occurrence_status": "accepted", "evidence_ids": "E1", "water_bird": "TRUE"},
        {"AvibaseID": "ss-1", "Taxon_rank": "subspecies", "parent_AvibaseID": "sp-1", "occurrence_status": "accepted", "evidence_ids": "E2", "water_bird": "TRUE"},
    ]
    if validate_core_rows(valid_rows):
        raise ValueError("valid policy fixture failed")

    invalid_rows = [
        {"AvibaseID": "sp-1", "Taxon_rank": "species", "occurrence_status": "accepted", "evidence_ids": "E1"},
        {"AvibaseID": "sp-1", "Taxon_rank": "subspecies", "parent_AvibaseID": "missing", "occurrence_status": "accepted", "evidence_ids": "E2"},
    ]
    errors = validate_core_rows(invalid_rows)
    if not any("duplicate AvibaseID" in error for error in errors):
        raise ValueError("duplicate AvibaseID rule is not enforced")
    if not any("no species parent row" in error for error in errors):
        raise ValueError("species parent rule is not enforced")

    incoherent_rows = [
        {"AvibaseID": "sp-2", "Taxon_rank": "species", "occurrence_status": "accepted", "evidence_ids": "E1", "water_bird": "TRUE"},
        {"AvibaseID": "ss-2", "Taxon_rank": "subspecies", "parent_AvibaseID": "sp-2", "occurrence_status": "accepted", "evidence_ids": "E2", "water_bird": "FALSE"},
    ]
    errors = validate_core_rows(incoherent_rows)
    if not any("disagrees with its species parent on water_bird" in error for error in errors):
        raise ValueError("inherited classification coherence rule is not enforced")

    invalid_values = [{"AvibaseID": "bad-1", "Taxon_rank": "group", "occurrence_status": "pending"}]
    errors = validate_core_rows(invalid_values)
    if not any("invalid public rank" in error for error in errors):
        raise ValueError("allowed rank rule is not enforced")
    if not any("invalid occurrence status" in error for error in errors):
        raise ValueError("occurrence status rule is not enforced")
    if not any("no evidence reference" in error for error in errors):
        raise ValueError("evidence rule is not enforced")
    print("Validated policy contract fixtures: unique IDs, allowed ranks/statuses, evidence, parentage, and inherited classification coherence")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"Policy validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
