#!/usr/bin/env python3
"""Render an editable publication package and release checklist to PDF via Typst."""

import argparse
import csv
import json
import subprocess
import tomllib
from collections import OrderedDict
from pathlib import Path

from publication_metadata import load, pending_earc_ids, render_provenance


ROOT = Path(__file__).resolve().parents[1]
HIDDEN_CATEGORY_GROUPS = {"Regular movement", "Regional visitors", "Regional vagrants"}
HIDDEN_CATEGORY_CODES = {"E", "ES", "water_bird"}
PDF_STATUS_DEFINITIONS = [
    {"code": "NAT", "label": "Naturalized", "definition": "Established non-native species in Kenya", "display_group": "Origin status", "display_token": "NAT", "display_order": "55"},
    {"code": "PE", "label": "Pending EARC", "definition": "Added since 2019 and not represented in the curated EARC decision list", "display_group": "Review status", "display_token": "PE", "display_order": "59"},
    {"code": "IUCN", "label": "Conservation concern", "definition": "Global IUCN Red List category above Least Concern", "display_group": "Conservation status", "display_token": "NT–EX", "display_order": "70"},
]
CONSERVATION_CONCERN_CODES = {"NT", "VU", "EN", "CR", "EW", "EX"}
IUCN_COLORS = {
    "NT": 'rgb("78923e")',
    "VU": 'rgb("b5752a")',
    "EN": 'rgb("bf5a27")',
    "CR": 'rgb("9f2d2d")',
    "EW": 'rgb("9f2d2d")',
    "EX": 'rgb("9f2d2d")',
}
ACCENT = 'rgb("2d6a4f")'
MUTED = 'rgb("5b6470")'
BADGE_COLORS = {
    "HIST": ('rgb("e7edf5")', 'rgb("49657c")'),
    "RAR": ('rgb("e6f2ed")', ACCENT),
    "NAT": ('rgb("f8ecd7")', 'rgb("98621a")'),
    "PE": ('rgb("f7e5e3")', 'rgb("9a3e38")'),
}


def root_path(value):
    return ROOT / value


def typst_string(value):
    return json.dumps(str(value), ensure_ascii=False)


def typst_content(value):
    return f"#text({typst_string(value)})"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def markdown_to_typst(path):
    result = subprocess.run(
        ["pandoc", str(path), "--from=gfm", "--to=typst"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def typst_text(value, size=None, weight=None, style=None, fill=None):
    options = []
    if size:
        options.append(f"size: {size}")
    if weight:
        options.append(f"weight: {typst_string(weight)}")
    if style:
        options.append(f"style: {typst_string(style)}")
    if fill:
        options.append(f"fill: {fill}")
    suffix = f"{', '.join(options)}" if options else ""
    return f"#text({suffix})[{typst_string(value)}]" if suffix else f"[{typst_string(value)}]"


def badge_markup(token, fill='rgb(230, 240, 234)', text_fill=ACCENT, size="6.2pt"):
    return (
        f"#box(fill: {fill}, inset: (x: 2pt, y: 1pt), radius: 2pt)["
        f"#text(size: {size}, weight: \"bold\", fill: {text_fill})[{typst_content(token)}]]"
    )


def category_badge(code, token, size="6.2pt"):
    if code == "IUCN":
        return badge_markup(token, IUCN_COLORS[token], "white", size)
    fill, text_fill = BADGE_COLORS.get(code, ('rgb(230, 240, 234)', ACCENT))
    return badge_markup(token, fill, text_fill, size)


def category_chips(row, definitions):
    chips = []
    for definition in definitions:
        code = definition["code"]
        assigned = (
            row.get(code) == "TRUE"
            or code == "NAT" and row.get("exotic_status") == "naturalized"
            or code == "PE" and row.get("pending_earc") == "TRUE"
            or code == "S" and row.get("sensitive") == "TRUE"
            or code == "IUCN" and row.get("iucn_red_list_category") in CONSERVATION_CONCERN_CODES
        )
        if assigned:
            token = row["iucn_red_list_category"] if code == "IUCN" else definition["display_token"]
            chips.append(category_badge(code, token))
    return " ".join(chips) if chips else ""


def checklist_markup(rows, definitions, checkbox_count):
    grouped = OrderedDict()
    for row in sorted(rows, key=lambda item: float(item["sequence"])):
        grouped.setdefault((row["family"], row["family_english_name"]), []).append(row)

    parts = []
    for (family, family_english), family_rows in grouped.items():
        parts.append(
            f"#block(breakable: false, above: 0.55em, below: 0.15em)["
            f"#text(size: 10.5pt, weight: \"bold\", fill: {ACCENT})[{typst_content(family_english)}] "
            f"#text(size: 8.5pt, fill: {MUTED})[{typst_content(family)}]]"
        )
        row_markup = []
        for row in family_rows:
            boxes = "".join("#box(stroke: 0.45pt + rgb(150, 160, 155), width: 0.58em, height: 0.58em)[]" for _ in range(checkbox_count))
            chips = category_chips(row, definitions)
            suffix = f" #h(0.35em) {chips}" if chips else ""
            row_markup.append(
                f"[#grid(columns: (3.8em, 1fr), gutter: 0.35em, align: (left, horizon), "
                f"[{boxes}], [{typst_content(row['english_name'])} "
                f"#text(size: 8.2pt, fill: {MUTED})[#emph({typst_string(row['scientific_name'])})]{suffix}])]"
            )
        parts.append(f"#stack(spacing: 0.28em, {', '.join(row_markup)})")
    return "\n".join(parts)


def category_key_markup(definitions):
    rows = []
    for definition in sorted(definitions, key=lambda item: int(item["display_order"])):
        key_width = "10em"
        if definition["code"] == "IUCN":
            badge = " #h(0.12em) ".join(category_badge("IUCN", code, "7pt") for code in ("NT", "VU", "EN", "CR"))
        else:
            badge = category_badge(definition["code"], definition["display_token"], "7pt")
        rows.append(
            f"#grid(columns: ({key_width}, 1fr), gutter: 0.45em, align: (left, horizon), "
            f"[{badge}], "
            f"[#text(weight: \"bold\")[{typst_content(definition['label'])}] "
            f"#text(size: 8.2pt, fill: {MUTED})[{typst_content('- ' + definition['definition'])}]])"
        )
    return "\n#v(0.45em)\n".join(rows)


def family_index_markup(rows):
    families = OrderedDict()
    for row in sorted(rows, key=lambda item: float(item["sequence"])):
        families.setdefault((row["family"], row["family_english_name"]), row["sequence"])
    return "\n".join(
        f"#grid(columns: (4.2em, 1fr), gutter: 0.45em, [{typst_content(sequence)}], "
        f"[{typst_content(family)} #text(fill: {MUTED})[{typst_content(english)}]])"
        for (family, english), sequence in families.items()
    )


def build_typst(metadata, rows, definitions, policy):
    document = metadata["document"]
    render = metadata["render"]
    checklist = metadata["checklist"]
    edition = document["edition"]
    subtitle = document.get("subtitle", "")
    edition_markup = f'''#v(7mm)
  #text(size: 13pt, weight: "bold", fill: {ACCENT})[{typst_content(edition)}]''' if edition else ""
    subtitle_markup = f'''#v(4mm)
  #text(size: 13pt, fill: {MUTED})[{typst_content(subtitle)}]''' if subtitle else ""
    publisher = metadata["publisher"]
    publisher_markup = f'''#v(11mm)
  #text(size: 9.5pt, weight: "bold", fill: {ACCENT})[{typst_content(publisher["imprint"])}]
  #v(2mm)
  #text(size: 8.4pt, fill: {MUTED})[{typst_content(publisher["address"])}]
  #v(2mm)
  #text(size: 8.6pt, fill: {ACCENT})[{typst_content(f"birds@naturekenya.org · {publisher['website']}")}]
  #v(4mm)
  #text(size: 7.8pt, fill: {MUTED})[{typst_content("Recommended citation: " + document["recommended_citation"])}]'''
    orientation = render.get("orientation", "portrait")
    page_size = f'paper: "{render["paper_size"]}",' if orientation == "portrait" else "width: 210mm, height: 148mm,"
    title_page = f'''#set page(
  {page_size}
  margin: (top: 9mm, bottom: 9mm, left: 11mm, right: 11mm),
  footer: context align(center)[#text(size: 7.5pt, fill: {MUTED})[#counter(page).display()]],
)
#set text(font: "Libertinus Serif", size: 8.3pt, lang: "en")
#set par(leading: 0.45em, justify: true)
#set heading(numbering: none)
#show heading.where(level: 1): it => block(above: 0.5em, below: 0.25em)[#text(size: 13pt, weight: "bold", fill: {ACCENT})[#it.body]]
#show heading.where(level: 2): it => block(above: 0.4em, below: 0.15em)[#text(size: 10pt, weight: "bold", fill: {ACCENT})[#it.body]]

#align(center)[
  #image("../../../website/assets/images/nature-kenya-logo.png", width: 52mm)
  #v(7mm)
  #text(size: 23pt, weight: "bold", fill: {ACCENT})[{typst_content(document["title"])}]
  {subtitle_markup}
  {edition_markup}
  #v(3mm)
  #text(size: 11pt, weight: "bold", fill: {ACCENT})[{typst_content(document["version_label"])}]
  {publisher_markup}
]
#pagebreak()

{policy}
#v(3mm)
= Category key

{category_key_markup(definitions)}
#pagebreak()
= The checklist

{checklist_markup(rows, definitions, int(checklist["checkbox_count"]))}
'''
    if checklist["include_family_index"]:
        title_page += f'''\n#pagebreak()\n= Index of families\n\n{family_index_markup(rows)}\n'''
    if checklist["include_notes_page"]:
        title_page += "\n#pagebreak()\n= Notes\n\n"
    return title_page


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("metadata", type=Path)
    parser.add_argument("--profile", type=Path, help="Optional public-facing publication profile")
    parser.add_argument("--keep-typ", action="store_true")
    args = parser.parse_args()
    metadata_path = args.metadata.resolve()
    metadata = load(metadata_path, args.profile.resolve() if args.profile else None)
    release = root_path(metadata["sources"]["release_directory"]).resolve()
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
    if metadata["release_id"] != release.name or metadata["release_id"] != manifest["release_id"]:
        raise ValueError("publication release_id does not match its release directory and manifest")
    rows = read_csv(release / "checklist.csv")
    definitions = [
        definition for definition in read_csv(root_path(metadata["sources"]["category_definitions"]))
        if definition["display_group"] not in HIDDEN_CATEGORY_GROUPS
        and definition["code"] not in HIDDEN_CATEGORY_CODES
    ] + [
        definition for definition in PDF_STATUS_DEFINITIONS
        if definition["code"] != "PE" or metadata["checklist"].get("show_pending_earc", True)
    ]
    pending_ids = pending_earc_ids(metadata, ROOT, release)
    for row in rows:
        row["pending_earc"] = "TRUE" if row["avibase_id"] in pending_ids else ""

    introduction = metadata["sources"].get("introduction") or metadata["sources"]["policy"]
    policy = markdown_to_typst(root_path(introduction))
    typst_dir = ROOT / "tmp" / "pdfs" / metadata["release_id"]
    output_dir = release
    typst_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    typst_path = typst_dir / "checklist.typ"
    pdf_path = output_dir / metadata["render"]["output_filename"]
    typst_path.write_text(build_typst(metadata, rows, definitions, policy), encoding="utf-8")

    subprocess.run(["quarto", "typst", "compile", "--root", str(ROOT), str(typst_path), str(pdf_path)], check=True)
    provenance = render_provenance(metadata, ROOT, release, pdf_path)
    pdf_path.with_suffix(".inputs.json").write_text(json.dumps(provenance, indent=2))
    print(f"Rendered {len(rows):,} species to {pdf_path.relative_to(ROOT)}")
    if not args.keep_typ:
        typst_path.unlink()


if __name__ == "__main__":
    main()
