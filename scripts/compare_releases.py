#!/usr/bin/env python3
"""Create machine-readable, narrative, and interactive release comparisons."""

import argparse
import csv
import html
import json
from collections import Counter
from pathlib import Path

CORE_FIELDS = {
    "sequence", "avilist_id", "order", "family", "family_english_name",
    "scientific_name", "english_name", "ebird_species_code", "membership_source",
    "sensitive", "exotic_status",
    "source_avibase_ids", "observations", "observation_record_count", "first_observation_date",
    "last_observation_date", "ebd_taxon_concept_ids", "ebd_source_categories",
    "mapping_methods", "record_count_lt_5", "last_record_year",
}
FIELDS = [
    "change", "avilist_id", "old_scientific_name", "new_scientific_name",
    "old_english_name", "new_english_name", "old_observations",
    "new_observations", "changed_fields",
]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def compare(old_rows, new_rows):
    old = {row["avilist_id"]: row for row in old_rows}
    new = {row["avilist_id"]: row for row in new_rows}
    category_fields = (set(old_rows[0]) | set(new_rows[0])) - CORE_FIELDS if old_rows and new_rows else set()
    changes = []
    for identifier in sorted(set(old) | set(new)):
        before = old.get(identifier, {})
        after = new.get(identifier, {})
        changed_fields = sorted(field for field in set(before) | set(after) if before.get(field, "") != after.get(field, ""))
        if not before:
            change = "added"
        elif not after:
            change = "removed"
        elif set(changed_fields) & category_fields:
            change = "categories_changed"
        elif set(changed_fields) & {"scientific_name", "english_name", "order", "family", "family_english_name"}:
            change = "taxonomy_changed"
        elif set(changed_fields) & {"membership_source", "sensitive", "exotic_status", "observations", "observation_record_count", "first_observation_date", "last_observation_date", "source_avibase_ids", "ebird_species_code"}:
            change = "evidence_changed"
        else:
            continue
        changes.append({
            "change": change,
            "avilist_id": identifier,
            "old_scientific_name": before.get("scientific_name", ""),
            "new_scientific_name": after.get("scientific_name", ""),
            "old_english_name": before.get("english_name", ""),
            "new_english_name": after.get("english_name", ""),
            "old_observations": before.get("observations", before.get("observation_record_count", "")),
            "new_observations": after.get("observations", ""),
            "changed_fields": ";".join(changed_fields),
        })
    return changes


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path, old_name, new_name, rows):
    counts = Counter(row["change"] for row in rows)
    path.write_text(
        f"# {old_name} to {new_name}\n\n"
        "Differences are computed by `avilist_id`. Added and removed identifiers are review prompts: "
        "a taxonomic split, lump, or identifier replacement may require an explicit migration mapping.\n\n"
        "| Change | Taxa |\n| --- | ---: |\n"
        f"| Added | {counts['added']:,} |\n"
        f"| Removed | {counts['removed']:,} |\n"
        f"| Taxonomy or name changed | {counts['taxonomy_changed']:,} |\n"
        f"| Observation evidence or exotic status changed | {counts['evidence_changed']:,} |\n"
        f"| Curated categories changed | {counts['categories_changed']:,} |\n\n"
        "See `changes.csv` for the row-level report and `migration-report.html` for the interactive view.\n",
        encoding="utf-8",
    )


def write_html(path, old_name, new_name, rows):
    data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(f"{old_name} to {new_name} migration report")
    path.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
body{{font:16px system-ui,sans-serif;max-width:1400px;margin:auto;padding:2rem;color:#17211b}}h1{{margin-bottom:.25rem}}
.controls{{display:flex;gap:.75rem;flex-wrap:wrap;margin:1.5rem 0}}button,input{{font:inherit;padding:.55rem .75rem}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}th,td{{padding:.55rem;text-align:left;border-bottom:1px solid #d7ded9;vertical-align:top}}
th{{position:sticky;top:0;background:#f3f6f4}}.added{{color:#176b36}}.removed{{color:#a12828}}.count{{font-variant-numeric:tabular-nums}}
</style></head><body><h1>{title}</h1><p id="summary"></p>
<div class="controls"><input id="search" type="search" placeholder="Search names or identifiers"><span id="filters"></span></div>
<table><thead><tr><th>Change</th><th>AviList ID</th><th>Previous</th><th>New</th><th>Fields</th></tr></thead><tbody id="rows"></tbody></table>
<script>const data={data};let selected='all';
const labels={{all:'All',added:'Added',removed:'Removed',taxonomy_changed:'Taxonomy/name',evidence_changed:'Evidence/status',categories_changed:'Categories'}};
const counts=Object.fromEntries(Object.keys(labels).map(k=>[k,k==='all'?data.length:data.filter(x=>x.change===k).length]));
filters.innerHTML=Object.entries(labels).map(([k,v])=>`<button data-filter="${{k}}">${{v}} (${{counts[k]}})</button>`).join(' ');
summary.textContent=`${{data.length.toLocaleString()}} material changes between the two releases.`;
function esc(x){{const e=document.createElement('span');e.textContent=x||'';return e.innerHTML}}
function render(){{const q=search.value.toLowerCase();const shown=data.filter(x=>(selected==='all'||x.change===selected)&&Object.values(x).join(' ').toLowerCase().includes(q));rows.innerHTML=shown.map(x=>`<tr><td class="${{x.change}}">${{esc(labels[x.change])}}</td><td>${{esc(x.avilist_id)}}</td><td><b>${{esc(x.old_english_name)}}</b><br><i>${{esc(x.old_scientific_name)}}</i><br><span class="count">${{esc(x.old_observations)}}</span></td><td><b>${{esc(x.new_english_name)}}</b><br><i>${{esc(x.new_scientific_name)}}</i><br><span class="count">${{esc(x.new_observations)}}</span></td><td>${{esc(x.changed_fields)}}</td></tr>`).join('')}}
filters.addEventListener('click',e=>{{if(e.target.dataset.filter){{selected=e.target.dataset.filter;render()}}}});search.addEventListener('input',render);render();</script></body></html>""", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("old", type=Path, help="previous checklist.csv")
    parser.add_argument("new", type=Path, help="new checklist.csv")
    parser.add_argument("output", type=Path, help="comparison output directory")
    args = parser.parse_args()
    rows = compare(read_csv(args.old), read_csv(args.new))
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "changes.csv", rows)
    write_markdown(args.output / "changelog.md", args.old.parent.name, args.new.parent.name, rows)
    write_html(args.output / "migration-report.html", args.old.parent.name, args.new.parent.name, rows)
    print(f"Wrote {args.output} ({len(rows):,} material changes)")


if __name__ == "__main__":
    main()
