#!/usr/bin/env python3
"""Render an editable publication package and release checklist to PDF via Typst."""

import argparse
import csv
import json
import subprocess
import tomllib
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HIDDEN_CATEGORY_GROUPS = {"Regular movement", "Regional visitors", "Regional vagrants"}
HIDDEN_CATEGORY_CODES = {"E", "ES", "water_bird"}
PDF_STATUS_DEFINITIONS = [
    {"code": "NAT", "label": "Naturalized", "definition": "Established non-native species in Kenya", "display_group": "Origin status", "display_token": "NAT", "display_order": "55"},
    {"code": "PE", "label": "Pending EARC", "definition": "Added since 2019 and not represented in the curated EARC decision list", "display_group": "Review status", "display_token": "PE", "display_order": "59"},
    {"code": "S", "label": "Sensitive species", "definition": "Species with observation details withheld for conservation reasons", "display_group": "Data handling", "display_token": "S", "display_order": "60"},
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
            chips.append(badge_markup(token, IUCN_COLORS[token], "white") if code == "IUCN" else badge_markup(token))
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
                f"#emph({typst_string(row['scientific_name'])}){suffix}])]"
            )
        parts.append(f"#stack(spacing: 0.16em, {', '.join(row_markup)})")
    return "\n".join(parts)


def category_key_markup(definitions):
    groups = OrderedDict()
    for definition in sorted(definitions, key=lambda item: int(item["display_order"])):
        groups.setdefault(definition["display_group"], []).append(definition)

    sections = []
    for group, group_definitions in groups.items():
        rows = []
        for definition in group_definitions:
            if definition["code"] == "IUCN":
                badge = " #h(0.12em) ".join(badge_markup(code, IUCN_COLORS[code], "white", "7pt") for code in ("NT", "VU", "EN", "CR"))
                key_width = "7.5em"
            else:
                badge = badge_markup(definition["display_token"], size="7pt")
                key_width = "4.5em"
            rows.append(
                f"#grid(columns: ({key_width}, 1fr), gutter: 0.45em, align: (left, horizon), "
                f"[{badge}], "
                f"[#text(weight: \"bold\")[{typst_content(definition['label'])}] "
                f"#text(size: 8.2pt, fill: {MUTED})[{typst_content('- ' + definition['definition'])}]])"
            )
        sections.append(f"#text(size: 9.5pt, weight: \"bold\", fill: {ACCENT})[{typst_content(group)}]\n" + "\n".join(rows))
    return "\n#v(0.55em)\n".join(sections)


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
    subtitle_markup = f'''#v(4mm)
  #text(size: 13pt, fill: {MUTED})[{typst_content(subtitle)}]''' if subtitle else ""
    title_page = f'''#set page(
  paper: "{render["paper_size"]}",
  margin: (top: 15mm, bottom: 14mm, left: 13mm, right: 13mm),
  footer: context align(center)[#text(size: 7.5pt, fill: {MUTED})[#counter(page).display()]],
)
#set text(font: "Libertinus Serif", size: 9pt, lang: "en")
#set par(leading: 0.58em, justify: true)
#set heading(numbering: none)
#show heading.where(level: 1): it => block(above: 0.7em, below: 0.35em)[#text(size: 15pt, weight: "bold", fill: {ACCENT})[#it.body]]
#show heading.where(level: 2): it => block(above: 0.55em, below: 0.2em)[#text(size: 11pt, weight: "bold", fill: {ACCENT})[#it.body]]

#align(center)[
  #v(22mm)
  #rect(width: 34mm, height: 4mm, fill: {ACCENT})
  #v(8mm)
  #text(size: 25pt, weight: "bold")[{typst_content(document["title"])}]
  {subtitle_markup}
  #v(7mm)
  #text(size: 13pt, weight: "bold", fill: {ACCENT})[{typst_content(edition)}]
  #v(4mm)
  #text(size: 11pt, weight: "bold", fill: {ACCENT})[{typst_content(document["version_label"])}]
  #v(20mm)
  #text(size: 9pt, fill: {MUTED})[{typst_content("Draft editorial edition")}]
]
#pagebreak()

{policy}
#pagebreak()
= Category key

#text(size: 8.5pt, fill: {MUTED})[{typst_content("Draft definitions shown for editorial review. Final category meanings and assignments require approval.")}]
#v(0.35em)
{category_key_markup(definitions)}
#pagebreak()
= The checklist

#text(size: 8.5pt, fill: {MUTED})[{typst_content("Grouped by family and ordered by AviList sequence. Category chips are shown only where the release contains an assignment.")}]
#v(0.25em)
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
    parser.add_argument("--keep-typ", action="store_true")
    args = parser.parse_args()
    metadata_path = args.metadata.resolve()
    metadata = tomllib.loads(metadata_path.read_text(encoding="utf-8"))
    release = root_path(metadata["sources"]["release_directory"]).resolve()
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
    if metadata["release_id"] != release.name or metadata["release_id"] != manifest["release_id"]:
        raise ValueError("publication release_id does not match its release directory and manifest")
    rows = read_csv(release / "checklist.csv")
    definitions = [
        definition for definition in read_csv(root_path(metadata["sources"]["category_definitions"]))
        if definition["display_group"] not in HIDDEN_CATEGORY_GROUPS
        and definition["code"] not in HIDDEN_CATEGORY_CODES
    ] + PDF_STATUS_DEFINITIONS
    comparison = json.loads((release / "comparison" / "taxonomy-changes.json").read_text(encoding="utf-8"))
    pending_earc_ids = {
        row["id"]
        for group in comparison["groups"] if group.get("pending_earc")
        for row in group["new"]
    }
    for row in rows:
        row["pending_earc"] = "TRUE" if row["avibase_id"] in pending_earc_ids else ""

    policy = markdown_to_typst(root_path(metadata["sources"]["policy"]))
    typst_dir = ROOT / "tmp" / "pdfs" / metadata["release_id"]
    output_dir = release
    typst_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    typst_path = typst_dir / "checklist.typ"
    pdf_path = output_dir / metadata["render"]["output_filename"]
    typst_path.write_text(build_typst(metadata, rows, definitions, policy), encoding="utf-8")

    subprocess.run(["quarto", "typst", "compile", str(typst_path), str(pdf_path)], check=True)
    print(f"Rendered {len(rows):,} species to {pdf_path.relative_to(ROOT)}")
    if not args.keep_typ:
        typst_path.unlink()


if __name__ == "__main__":
    main()
