#!/usr/bin/env python3
"""Create the corrected historical v2019.1 checklist."""

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "v2019.0" / "main.csv"
REPAIRS = ROOT / "data" / "v2019.1" / "repairs.csv"
OUTPUT = ROOT / "data" / "v2019.1" / "main.csv"
FIELDS = [
    "sort", "family_scientific", "family_english", "common_name", "scientific_name",
    "AM", "AMR", "E", "EX", "HIST", "IO", "MM", "N", "NR", "NRR", "OM", "PM", "PMR", "RAR", "RS", "SO", "VIO", "VM", "VN", "VO", "VP", "VSO", "VSA",
    "water_bird", "strict_water_bird", "sort_1996", "sort_2009", "avibaseid",
    "entry_checklist_of_kenya", "note_2009", "note_2019",
]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    rows = read_csv(SOURCE)
    repairs = {row["sort"]: row for row in read_csv(REPAIRS)}
    output = []
    sort_counts = Counter()
    for row in rows:
        repair = repairs.get(row["sort"])
        sort_counts[row["sort"]] += 1
        if repair and repair["action"] == "remove_duplicate":
            continue
        if repair and repair["action"] == "remove_duplicate_after_first" and sort_counts[row["sort"]] > 1:
            continue
        result = {field: row[field] for field in FIELDS}
        if repair and repair["replacement_avibaseid"]:
            result["avibaseid"] = repair["replacement_avibaseid"]
        output.append(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(output)} records)")


if __name__ == "__main__":
    main()
