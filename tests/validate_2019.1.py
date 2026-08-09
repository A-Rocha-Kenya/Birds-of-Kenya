#!/usr/bin/env python3
"""Validate v2019.1 keys and write any errors for editorial review."""

import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "v2019.1" / "main.csv"
AUDIT = ROOT / "data" / "v2019.1" / "audit_errors.csv"
AVIBASE_ID = re.compile(r"avibase-[0-9A-F]{8}$")


def main():
    with DATA.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    sorts = Counter(row["sort"].strip() for row in rows)
    identifiers = Counter(row["avibaseid"].strip() for row in rows)
    errors = []
    for number, row in enumerate(rows, start=2):
        for field, values, pattern in [("sort", sorts, None), ("avibaseid", identifiers, AVIBASE_ID)]:
            value = row[field].strip()
            if value in {"", "#N/A"}:
                error = "missing"
            elif values[value] > 1:
                error = "duplicate"
            elif pattern and not pattern.fullmatch(value):
                error = "invalid_format"
            else:
                continue
            errors.append({
                "row": number,
                "sort": row["sort"],
                "entry_checklist_of_kenya": row["entry_checklist_of_kenya"],
                "field": field,
                "value": value,
                "error": error,
            })
    with AUDIT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row", "sort", "entry_checklist_of_kenya", "field", "value", "error"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(errors)
    if errors:
        raise ValueError(f"Found {len(errors)} v2019.1 key errors; see {AUDIT.relative_to(ROOT)}")
    print(f"Validated {len(rows):,} v2019.1 records")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
