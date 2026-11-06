#!/usr/bin/env python3
"""Resolve supported 2009 Avibase matches and retain ambiguous concepts for review."""

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/legacy/2009.0"
EVIDENCE = DIRECTORY / "avibase"

with (DIRECTORY / "checklist.csv").open() as handle:
    reader = csv.DictReader(handle)
    columns, rows = reader.fieldnames, list(reader)
with (EVIDENCE / "source_taxa.csv").open() as handle:
    sources = list(csv.DictReader(handle))
with (EVIDENCE / "profile_evidence.csv").open() as handle:
    profiles = {row["avibase_id"]: row for row in csv.DictReader(handle)}
with (EVIDENCE / "reviewed_matches.csv").open() as handle:
    reviewed = {row["sort"]: row for row in csv.DictReader(handle)}

audit = []
for row in rows:
    matches = [item for item in sources if item["scientific_name"].casefold() == row["scientific_name"].casefold()]
    historical = [item for item in matches if item["taxonomy"] in {"Howard and Moore 3rd edition", "Clements 2009"}]
    preferred = historical or matches
    candidates = sorted({item["avibase_id"] for item in preferred})
    identifier = candidates[0] if len(candidates) == 1 else ""
    status = ("historical_name_match" if historical else "consistent_name_match") if identifier else "unresolved"
    reason = "Unique exact-name concept in the historical comparison tables." if historical else "Unique exact-name concept across the available Avibase tables."
    if not identifier:
        reason = "Competing taxon concepts; the PDF does not establish all global boundaries." if candidates else "No exact-name match in the available tables."
    if row["sort"] in reviewed:
        decision = reviewed[row["sort"]]
        identifier, reason = decision["avibase_id"], decision["reason"]
        status = "reviewed" if identifier else "unresolved"
        candidates = sorted(set(candidates + decision["candidate_ids"].split(";")) - {""})
    row["avibaseid"] = identifier
    urls = {item["url"] for item in preferred if item["avibase_id"] == identifier}
    urls.update(profiles[item]["url"] for item in candidates if item in profiles)
    if identifier:
        urls.add("https://avibase.bsc-eoc.org/species.jsp?avibaseid=" + identifier.removeprefix("avibase-") + "&lang=EN")
    audit.append(dict(sort=row["sort"], common_name=row["common_name"], scientific_name=row["scientific_name"], avibase_id=identifier, status=status, candidate_ids=";".join(candidates), reason=reason, source_taxonomies=";".join(sorted({item["taxonomy"] for item in preferred})), source_urls=";".join(sorted(urls))))

# A shared identifier between separate printed species requires editorial review.
counts = Counter(row["avibaseid"] for row in rows if row["avibaseid"])
for row, record in zip(rows, audit):
    if row["avibaseid"] and counts[row["avibaseid"]] > 1:
        row["avibaseid"] = record["avibase_id"] = ""
        record.update(status="unresolved", reason="The candidate concept also matches another separately listed PDF species.")
    assert not row["avibaseid"] or re.fullmatch(r"avibase-[0-9A-F]{8}", row["avibaseid"])

with (DIRECTORY / "checklist.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
for filename, records in [("matches.csv", audit), ("unresolved.csv", [row for row in audit if not row["avibase_id"]])]:
    with (EVIDENCE / filename).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
print(dict(Counter(record["status"] for record in audit)))
