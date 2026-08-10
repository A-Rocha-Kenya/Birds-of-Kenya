#!/usr/bin/env python3
"""Build the provisional Kenya checklist release 2026.0."""

import csv
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
EBIRD = ROOT / "data" / "sources" / "ebird" / "KE.json"
AVILIST = ROOT / "data" / "sources" / "avilist" / "AviList-v2025b-10Jun2026-extended.xlsx"
OUTPUT = ROOT / "data" / "2026.0"
CORE = OUTPUT / "core.csv"
MAIN = OUTPUT / "main.csv"
AUDIT = OUTPUT / "audit" / "ebird_codes_not_mapped.csv"
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

CORE_FIELDS = [
    "avilist_id", "ebird_species_code", "occurrence_status", "initial_source",
    "kenya_english_name", "kenya_status_codes", "committee_note",
]
MAIN_FIELDS = [
    "sequence", "avilist_id", "ebird_species_code", "taxon_rank", "order", "family",
    "family_english_name", "scientific_name", "english_name_avilist", "english_name_clements",
    "range", "iucn_red_list_category", "birdlife_datazone_url", "birds_of_the_world_url",
    "occurrence_status", "kenya_english_name", "kenya_status_codes", "committee_note",
]


def read_xlsx(path):
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(item.itertext()) for item in root.findall("x:si", NS)]
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in sheet.findall(".//x:sheetData/x:row", NS):
            values = []
            for cell in row.findall("x:c", NS):
                column = 0
                for char in "".join(filter(str.isalpha, cell.attrib["r"])):
                    column = column * 26 + ord(char.upper()) - 64
                while len(values) < column:
                    values.append("")
                value = cell.find("x:v", NS)
                text = "" if value is None else value.text or ""
                values[column - 1] = shared[int(text)] if cell.attrib.get("t") == "s" else text
            rows.append(values)
    headers = rows[0]
    return [dict(zip(headers, row)) for row in rows[2:]]


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    ebird_codes = json.loads(EBIRD.read_text(encoding="utf-8"))
    avilist_rows = read_xlsx(AVILIST)
    avilist_by_code = defaultdict(list)
    for row in avilist_rows:
        code = row.get("Species_code_Cornell_Lab", "").strip()
        if code and row.get("Taxon_rank", "").lower() == "species":
            avilist_by_code[code].append(row)

    core_rows = []
    main_rows = []
    audit_rows = []
    for code in ebird_codes:
        matches = avilist_by_code.get(code, [])
        if len(matches) != 1:
            audit_rows.append({
                "ebird_species_code": code,
                "error": "not_in_avilist_species" if not matches else "multiple_avilist_species",
                "matched_avilist_ids": ";".join(row["AvibaseID"] for row in matches),
                "matched_scientific_names": ";".join(row["Scientific_name"] for row in matches),
            })
            continue
        taxon = matches[0]
        core = {
            "avilist_id": taxon["AvibaseID"],
            "ebird_species_code": code,
            "occurrence_status": "provisional",
            "initial_source": "eBird Kenya snapshot",
            "kenya_english_name": "",
            "kenya_status_codes": "",
            "committee_note": "",
        }
        core_rows.append(core)
        main_rows.append({
            "sequence": taxon["Sequence"],
            "avilist_id": taxon["AvibaseID"],
            "ebird_species_code": code,
            "taxon_rank": taxon["Taxon_rank"],
            "order": taxon["Order"],
            "family": taxon["Family"],
            "family_english_name": taxon["Family_English_name"],
            "scientific_name": taxon["Scientific_name"],
            "english_name_avilist": taxon["English_name_AviList"],
            "english_name_clements": taxon["English_name_Clements_v2025"],
            "range": taxon["Range"],
            "iucn_red_list_category": taxon["IUCN_Red_List_Category"],
            "birdlife_datazone_url": taxon["BirdLife_DataZone_URL"],
            "birds_of_the_world_url": taxon["Birds_of_the_World_URL"],
            "occurrence_status": core["occurrence_status"],
            "kenya_english_name": core["kenya_english_name"],
            "kenya_status_codes": core["kenya_status_codes"],
            "committee_note": core["committee_note"],
        })

    main_rows.sort(key=lambda row: float(row["sequence"]))
    core_by_id = {row["avilist_id"]: row for row in core_rows}
    core_rows = [core_by_id[row["avilist_id"]] for row in main_rows]
    write_csv(CORE, CORE_FIELDS, core_rows)
    write_csv(MAIN, MAIN_FIELDS, main_rows)
    write_csv(AUDIT, ["ebird_species_code", "error", "matched_avilist_ids", "matched_scientific_names"], audit_rows)
    print(f"eBird codes: {len(ebird_codes):,}")
    print(f"Mapped AviList species: {len(main_rows):,}")
    print(f"Unmapped or ambiguous codes: {len(audit_rows):,}")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        raise SystemExit(1)
