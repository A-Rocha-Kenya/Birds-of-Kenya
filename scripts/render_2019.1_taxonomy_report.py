#!/usr/bin/env python3
"""Render the one-time v2019.1 to 2026.0 taxonomy review as HTML and Typst."""

import argparse
import bisect
import csv
import importlib.util
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "data" / "legacy" / "2019.1" / "checklist.csv"
CURRENT = ROOT / "dist" / "2026-06.0" / "checklist.csv"
MAPPING = ROOT / "data" / "curation" / "taxonomy_2019.1_to_2026.0.csv"
OUTPUT = ROOT / "dist" / "2026-06.0" / "comparison"
PDF = OUTPUT / "Taxonomy-changes-2019.1-to-2026.0.pdf"
COMPARE_SCRIPT = ROOT / "scripts" / "compare_2019.1_to_2026.0.py"

RELATIONSHIP_LABELS = {
    "retained": "Same taxon",
    "replacement": "One-to-one revision",
    "split": "Split",
    "lump": "Lump",
    "many_to_many": "Complex revision",
    "unresolved": "Mapping pending",
    "added": "Added to current checklist",
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
    new_by_id = {row["avilist_id"]: row for row in current_rows}
    mapping = comparison.read_mapping_rows(mapping_rows, old_by_id, new_by_id)
    edges = comparison.mapping_edges(mapping)
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
        title_names = new_names or old_names
        title = title_names[0] if len(title_names) == 1 else " / ".join(title_names[:3])
        if len(title_names) > 3:
            title += f" +{len(title_names) - 3}"
        return {
            "id": group_id,
            "relationship": relationship,
            "relationship_label": RELATIONSHIP_LABELS[relationship],
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
                    "id": row["avilist_id"], "english": row["english_name"].strip(),
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
        if row["avilist_id"] not in connected_new_ids:
            groups.append(make_group(f"added-{row['avilist_id']}", "added", [], [row]))
    return sorted(groups, key=lambda group: (group["sort_order"], group["id"]))


def html_report(groups):
    data = json.dumps(groups, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Taxonomy changes · Birds of Kenya · 2019.1 to 2026.0</title>
<style>
:root{{--ink:#18241e;--muted:#68736d;--paper:#f6f3eb;--card:#fffefa;--green:#1f6848;--green-soft:#e5f1e9;--ochre:#b5752a;--ochre-soft:#f6ead8;--line:#d9ded8;--shadow:0 14px 36px rgba(28,48,37,.08)}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.hero{{background:linear-gradient(135deg,#133e2d 0%,#24694c 62%,#89743c 140%);color:white;padding:4.5rem max(1.25rem,calc((100vw - 1240px)/2));position:relative;overflow:hidden}}
.hero:after{{content:"";position:absolute;right:-8rem;top:-12rem;width:32rem;height:32rem;border:1px solid rgba(255,255,255,.18);border-radius:50%;box-shadow:0 0 0 4rem rgba(255,255,255,.04),0 0 0 9rem rgba(255,255,255,.025)}}
.eyebrow{{font-size:.77rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:#d9ebdf}}h1{{font-family:Georgia,serif;font-size:clamp(2.35rem,5vw,4.6rem);line-height:.98;max-width:850px;margin:.7rem 0 1rem;letter-spacing:-.035em}}.lede{{font-size:1.08rem;max-width:760px;color:#e7f0ea}}
.toolbar-wrap{{position:sticky;top:0;z-index:20;background:rgba(246,243,235,.94);backdrop-filter:blur(16px);border-bottom:1px solid rgba(45,70,55,.12)}}.toolbar{{max-width:1240px;margin:auto;padding:.9rem 1.25rem}}
.top-controls{{display:grid;grid-template-columns:minmax(220px,1fr) auto;gap:.8rem;align-items:center}}input[type=search]{{width:100%;border:1px solid #cbd4cd;background:white;border-radius:10px;padding:.72rem .85rem;font:inherit;color:var(--ink);outline:none}}input[type=search]:focus{{border-color:var(--green);box-shadow:0 0 0 3px rgba(31,104,72,.12)}}
.clear{{border:0;background:transparent;color:var(--green);font-weight:750;cursor:pointer;padding:.6rem}}.filter-row{{display:flex;gap:.45rem;align-items:center;flex-wrap:wrap;margin-top:.7rem}}.filter-label{{font-size:.74rem;font-weight:850;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);margin-right:.25rem}}
.filter{{border:1px solid #cbd4cd;background:#fff;border-radius:999px;padding:.38rem .66rem;font:700 .76rem/1 system-ui;color:#415047;cursor:pointer}}.filter:hover{{border-color:#7e9a88}}.filter[aria-pressed=true]{{background:var(--green);border-color:var(--green);color:white}}.filter .count{{opacity:.7;margin-left:.2rem}}
main{{max-width:1240px;margin:auto;padding:1.15rem 1.25rem 5rem}}.result-line{{display:flex;justify-content:space-between;gap:1rem;color:var(--muted);font-size:.82rem;margin-bottom:.55rem}}.result-line b{{color:var(--ink)}}.column-legend{{display:grid;grid-template-columns:minmax(0,1fr) 2rem minmax(0,1fr);gap:.65rem;padding:0 .75rem;color:var(--muted);font-size:.68rem;font-weight:850;text-transform:uppercase;letter-spacing:.11em}}.column-legend span:last-child{{text-align:right}}
.order-heading{{font-family:Georgia,serif;font-size:1.55rem;margin:2.2rem 0 .15rem;color:#173e2e;border-bottom:2px solid var(--green);padding-bottom:.25rem}}.family-heading{{display:flex;gap:.5rem;align-items:baseline;margin:1.15rem 0 .45rem;font-size:1rem}}.family-heading span{{color:var(--muted);font-size:.8rem;font-weight:500}}
.change-card{{background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:0 8px 24px rgba(28,48,37,.055);margin:.42rem 0;padding:.68rem .72rem;scroll-margin-top:11rem}}.card-head{{display:flex;justify-content:space-between;gap:.75rem;align-items:center;margin-bottom:.42rem}}.card-title{{font-family:Georgia,serif;font-size:1rem;font-weight:700;line-height:1.22}}.badges{{display:flex;gap:.28rem;flex-wrap:wrap;justify-content:flex-end}}.badge{{font-size:.62rem;font-weight:850;text-transform:uppercase;letter-spacing:.05em;border-radius:999px;padding:.22rem .4rem;background:var(--green-soft);color:var(--green)}}.badge.relationship{{background:var(--ochre-soft);color:#8a541a}}.badge.unresolved{{background:#f8dddd;color:#8b2c2c}}
.concept-grid{{display:grid;grid-template-columns:minmax(0,1fr) 2rem minmax(0,1fr);gap:.65rem;align-items:stretch}}.side{{border-radius:8px;padding:.52rem .6rem}}.side.old{{background:#f5eee3;border:1px solid #eadbc5}}.side.new{{background:#eaf3ed;border:1px solid #d1e4d8}}.taxon+.taxon{{border-top:1px solid rgba(60,80,68,.13);margin-top:.38rem;padding-top:.38rem}}.taxon-row{{display:flex;align-items:flex-start;justify-content:space-between;gap:.55rem}}.taxon-names{{min-width:0;flex:1;line-height:1.32}}.taxon .english{{font-weight:800}}.taxon .scientific{{font-family:Georgia,serif;font-style:italic;color:#38463e;margin-left:.24rem}}.taxon a{{color:#416b58;text-decoration:none}}.taxon a:hover{{color:var(--green);text-decoration:underline;text-underline-offset:2px}}.source-links{{display:flex;justify-content:flex-end;gap:.25rem;flex-wrap:wrap;flex:0 1 auto;max-width:48%}}.source-link{{display:inline-block;border:1px solid rgba(31,104,72,.22);border-radius:999px;padding:.14rem .32rem;font:750 .59rem/1.15 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:nowrap;background:rgba(255,255,255,.62)}}.arrow{{display:flex;align-items:center;justify-content:center;color:var(--ochre);font-weight:900}}.arrow .symbol{{font-size:1.5rem}}
.taxonomy-note{{margin-top:.45rem;padding:.42rem .5rem;border-left:3px solid var(--ochre);background:rgba(255,255,255,.48);color:var(--muted);font-size:.73rem;line-height:1.4}}.taxonomy-note strong{{display:block;margin-bottom:.12rem;color:var(--ink);font-size:.67rem;letter-spacing:.04em;text-transform:uppercase}}.empty{{color:var(--muted);font-style:italic}}.no-results{{padding:4rem 1rem;text-align:center;color:var(--muted)}}footer{{max-width:1240px;margin:auto;padding:0 1.25rem 2.5rem;color:var(--muted);font-size:.78rem}}
@media(max-width:760px){{.hero{{padding-top:3rem;padding-bottom:3rem}}.top-controls{{grid-template-columns:1fr}}.column-legend{{display:none}}.concept-grid{{grid-template-columns:1fr}}.arrow{{min-height:1.4rem}}.arrow .symbol{{transform:rotate(90deg)}}.card-head{{display:block}}.badges{{justify-content:flex-start;margin-top:.35rem}}.source-links{{max-width:46%}}.toolbar-wrap{{position:relative}}}}
@media print{{.toolbar-wrap{{display:none}}.hero{{padding:1.2cm;background:#173e2e!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}}main{{padding:.5cm}}.change-card{{box-shadow:none;break-inside:avoid}}}}
</style></head>
<body><header class="hero"><div class="eyebrow">Birds of Kenya · Taxonomy review</div><h1>From the 2019 checklist to AviList 2026</h1><p class="lede">A taxonomically ordered view of name changes and concept changes. Splits, lumps and related taxa stay together as a single species complex.</p>
</header>
<div class="toolbar-wrap"><div class="toolbar"><div class="top-controls"><input id="search" type="search" placeholder="Search names, families or AviList IDs" aria-label="Search taxonomy changes"><button class="clear" id="clear">Clear filters</button></div>
<div class="filter-row" id="nameFilters"><span class="filter-label">Changed field</span></div><div class="filter-row" id="conceptFilters"><span class="filter-label">Concept change</span></div></div></div>
<main><div class="result-line"><span id="resultCount"></span><span>Ordered by current AviList sequence</span></div><div class="column-legend" aria-hidden="true"><span>2019.1 historical concept</span><span></span><span>2026.0 current concept</span></div><div id="report"></div></main>
<footer>Generated from the corrected v2019.1 checklist, the 2026.0 checklist and the project’s one-time taxonomy mapping. This is a review aid, not a taxonomic authority.</footer>
<script>const groups={data};
const filterConfig={{names:[['english_name','English name'],['scientific_name','Scientific name'],['classification','Family placement']],concepts:[['retained','Same taxon'],['replacement','One-to-one revision'],['split','Split'],['lump','Lump'],['many_to_many','Complex revision'],['added','Added to current checklist'],['unresolved','Mapping pending']]}};
const selected={{names:new Set(),concepts:new Set()}};const esc=s=>{{const e=document.createElement('span');e.textContent=s??'';return e.innerHTML}};
function button([key,label],kind){{const count=groups.filter(g=>kind==='names'?g.tags.includes(key):g.relationship===key).length;return `<button class="filter" data-kind="${{kind}}" data-key="${{key}}" aria-pressed="false">${{label}} <span class="count">${{count}}</span></button>`}}
nameFilters.insertAdjacentHTML('beforeend',filterConfig.names.map(x=>button(x,'names')).join(''));conceptFilters.insertAdjacentHTML('beforeend',filterConfig.concepts.map(x=>button(x,'concepts')).join(''));
function avibaseLink(id){{const shortId=id.replace(/^avibase-/,'');return `<a class="source-link" href="https://avibase.bsc-eoc.org/species.jsp?avibaseid=${{encodeURIComponent(shortId)}}" target="_blank" rel="noopener" title="Open ${{esc(id)}} in Avibase">Avibase · ${{esc(shortId)}}</a>`}}
function ebirdLinks(row){{return (row.ebird_codes||[]).map(code=>`<a class="source-link" href="https://ebird.org/species/${{encodeURIComponent(code)}}/KE" target="_blank" rel="noopener" title="Open ${{esc(code)}} in eBird for Kenya">eBird · ${{esc(code)}}</a>`).join('')}}
function taxon(row){{const note=row.taxonomy_comment?`<div class="taxonomy-note"><strong>AviList taxonomy decision</strong>${{esc(row.taxonomy_comment)}}</div>`:'';return `<div class="taxon"><div class="taxon-row"><div class="taxon-names"><span class="english">${{esc(row.english)}}</span><span class="scientific">${{esc(row.scientific)}}</span></div><div class="source-links">${{avibaseLink(row.id)}}${{ebirdLinks(row)}}</div></div>${{note}}</div>`}}
function side(rows,kind){{return `<div class="side ${{kind}}">${{rows.length?rows.map(taxon).join(''):'<div class="empty">None listed</div>'}}</div>`}}
function card(g){{const tags=g.tags.filter(x=>x!=='concept').map(x=>`<span class="badge">${{esc(dict[x])}}</span>`).join('');const relClass=g.relationship==='unresolved'?' unresolved':'';return `<article class="change-card" id="${{esc(g.id)}}"><div class="card-head"><div class="card-title">${{esc(g.title)}}</div><div class="badges"><span class="badge relationship${{relClass}}">${{esc(g.relationship_label)}}</span>${{tags}}</div></div><div class="concept-grid">${{side(g.old,'old')}}<div class="arrow" aria-hidden="true"><span class="symbol">→</span></div>${{side(g.new,'new')}}</div></article>`}}
const dict={{english_name:'English name',scientific_name:'Scientific name',classification:'Family placement'}};
function render(){{const q=search.value.trim().toLowerCase();const visible=groups.filter(g=>{{const namesOk=!selected.names.size||[...selected.names].every(x=>g.tags.includes(x));const conceptOk=!selected.concepts.size||selected.concepts.has(g.relationship);const text=JSON.stringify(g).toLowerCase();return namesOk&&conceptOk&&(!q||text.includes(q))}});resultCount.innerHTML=`Showing <b>${{visible.length.toLocaleString()}}</b> of ${{groups.length.toLocaleString()}} change groups`;let out='',order='',family='';for(const g of visible){{if(g.order!==order){{order=g.order;family='';out+=`<h2 class="order-heading">${{esc(order)}}</h2>`}}if(g.family!==family){{family=g.family;out+=`<h3 class="family-heading">${{esc(family)}} <span>${{esc(g.family_english)}}</span></h3>`}}out+=card(g)}}report.innerHTML=out||'<div class="no-results">No changes match these filters.</div>'}}
document.querySelectorAll('.filter').forEach(el=>el.addEventListener('click',()=>{{const set=selected[el.dataset.kind];set.has(el.dataset.key)?set.delete(el.dataset.key):set.add(el.dataset.key);el.setAttribute('aria-pressed',set.has(el.dataset.key));render()}}));search.addEventListener('input',render);clear.addEventListener('click',()=>{{search.value='';selected.names.clear();selected.concepts.clear();document.querySelectorAll('.filter').forEach(x=>x.setAttribute('aria-pressed','false'));render()}});render();
</script></body></html>'''


def write_json(path, groups):
    relationships = Counter(group["relationship"] for group in groups)
    payload = {
        "from_release": "2019.1",
        "to_release": "2026-06.0",
        "group_count": len(groups),
        "relationship_counts": dict(sorted(relationships.items())),
        "groups": groups,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def typst_text(value):
    return f"#text({json.dumps(str(value), ensure_ascii=False)})"


def typst_report(groups):
    parts = [f'''#set page(paper: "a4", margin: (top: 18mm, bottom: 17mm, x: 17mm), footer: context align(center)[#text(size: 7pt, fill: rgb("68736d"))[#counter(page).display()]])
#set text(font: "Libertinus Serif", size: 9pt, fill: rgb("18241e"))
#set par(leading: 0.62em)
#set heading(numbering: none)
#show heading.where(level: 1): it => block(above: 1em, below: .35em)[#text(size: 17pt, weight: "bold", fill: rgb("1f6848"))[#it.body]]
#show heading.where(level: 2): it => block(above: .7em, below: .2em)[#text(size: 11pt, weight: "bold", fill: rgb("1f6848"))[#it.body]]
#let badge(body) = box(fill: rgb("f6ead8"), radius: 3pt, inset: (x: 4pt, y: 2pt), text(size: 7pt, weight: "bold", fill: rgb("8a541a"), body))
#align(center)[
  #v(24mm)
  #text(size: 29pt, weight: "bold", fill: rgb("173e2e"))[Taxonomy changes]
  #v(4mm)
  #text(size: 17pt)[Birds of Kenya, 2019.1 to 2026.0]
  #v(8mm)
  #text(size: 10pt, fill: rgb("68736d"))[Taxonomically ordered; related concepts grouped as species complexes]
  #v(18mm)
  #text(size: 11pt, weight: "bold", fill: rgb("1f6848"))[{len(groups):,} change groups]
]
#pagebreak()
''']
    order = family = ""
    for group in groups:
        if group["order"] != order:
            order = group["order"]
            family = ""
            parts.append(f"= {typst_text(order)}\n")
        if group["family"] != family:
            family = group["family"]
            parts.append(f"== {typst_text(family)} #text(size: 8pt, fill: rgb(\"68736d\"))[{typst_text(group['family_english'])}]\n")
        old_taxa = "\\\n".join(
            f"#strong[{typst_text(row['english'])}] #emph({json.dumps(row['scientific'], ensure_ascii=False)}) #text(size: 6.5pt, fill: rgb(\"68736d\"))[{typst_text(row['id'])}]"
            for row in group["old"]
        ) or "#text(fill: rgb(\"68736d\"), style: \"italic\")[None listed]"
        new_taxa = "\\\n".join(
            f"#strong[{typst_text(row['english'])}] #emph({json.dumps(row['scientific'], ensure_ascii=False)}) #text(size: 6.5pt, fill: rgb(\"68736d\"))[{typst_text(row['id'])}]"
            for row in group["new"]
        ) or "#text(fill: rgb(\"68736d\"), style: \"italic\")[None listed]"
        parts.append(
            f'''#block(breakable: true, stroke: .5pt + rgb("d9ded8"), radius: 4pt, inset: 7pt, above: 4pt, below: 4pt)[
#grid(columns: (1fr, 52pt, 1fr), gutter: 7pt,
  [#text(size: 6.5pt, weight: "bold", fill: rgb("68736d"))[2019.1]\\ {old_taxa}],
  [#align(center + horizon)[#badge[{typst_text(group["relationship_label"])}]]],
  [#text(size: 6.5pt, weight: "bold", fill: rgb("68736d"))[2026.0]\\ {new_taxa}]
)]
''')
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy", type=Path, default=LEGACY)
    parser.add_argument("--current", type=Path, default=CURRENT)
    parser.add_argument("--mapping", type=Path, default=MAPPING)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--pdf", type=Path, default=PDF)
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--keep-typst", action="store_true")
    args = parser.parse_args()

    groups = taxonomy_groups(read_csv(args.legacy), read_csv(args.current), read_csv(args.mapping))
    args.output.mkdir(parents=True, exist_ok=True)
    json_path = args.output / "taxonomy-changes.json"
    write_json(json_path, groups)
    html_path = args.output / "taxonomy-changes.html"
    html_path.write_text(html_report(groups), encoding="utf-8")
    print(f"Rendered {len(groups):,} taxonomic change groups to {json_path} and {html_path}")

    if not args.no_pdf:
        typst_dir = ROOT / "tmp" / "pdfs" / "taxonomy-2019.1-to-2026.0"
        typst_dir.mkdir(parents=True, exist_ok=True)
        typst_path = typst_dir / "taxonomy-changes.typ"
        typst_path.write_text(typst_report(groups), encoding="utf-8")
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["quarto", "typst", "compile", str(typst_path), str(args.pdf)], check=True)
        print(f"Rendered printable report to {args.pdf}")
        if not args.keep_typst:
            typst_path.unlink()


if __name__ == "__main__":
    main()
