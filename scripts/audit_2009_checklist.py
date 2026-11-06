#!/usr/bin/env python3
"""Audit the PDF extraction independently and compare all five Excel sheets.

Requires pdfplumber and openpyxl; writes read-only source comparisons to tmp/audit-2009/.
"""

import csv
import hashlib
import io
import json
import re
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data" / "legacy" / "2009.0"
AUDIT = ROOT / "tmp/audit-2009"
AUDIT.mkdir(parents=True, exist_ok=True)
PDF = DIRECTORY / "source.pdf"
EXCEL = subprocess.check_output(["git", "show", "v2009.0:data/legacy/2009.0/source.xlsx"], cwd=ROOT)


def compact(text):
    return re.sub(r"\s", "", unicodedata.normalize("NFKC", str(text or ""))).replace("\xad", "")


def difference_kind(left, right):
    words = lambda value: re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", str(value or "")).casefold())
    return "punctuation_or_case" if words(left) == words(right) else "text_difference"


def write_csv(name, records, columns):
    with (AUDIT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


# Read the CSV and reconstruct entries using PDF coordinates, not layout indentation.
with (DIRECTORY / "checklist.csv").open(newline="", encoding="utf-8") as handle:
    reader = csv.DictReader(handle)
    columns = reader.fieldnames
    rows = list(reader)
with (ROOT / "data" / "legacy" / "2019.1" / "checklist.csv").open(newline="", encoding="utf-8-sig") as handle:
    assert columns == next(csv.reader(handle)), "CSV schema differs from 2019"

pdf_rows = []
group_lines = []
family = ""
species_notes = False
with pdfplumber.open(PDF) as pdf:
    for page_number, page in enumerate(pdf.pages[3:42], start=1):
        for line in page.extract_text_lines():
            # Running headers end before y=40; footers start after y=565.
            if line["top"] < 40 or line["top"] > 565 or (page_number == 1 and line["top"] < 90):
                continue
            text = line["text"]
            if re.match(r"^[A-Za-z]+idae:", text):
                family = text
                species_notes = False
            elif any(char["fontname"].endswith("Webdings") and char["text"] == "c" for char in line["chars"]):
                pdf_rows.append({"page": page_number, "entry": text[2:], "family": family, "notes": []})
                species_notes = True
            elif line["x0"] > 45 and species_notes:
                pdf_rows[-1]["notes"].append(text)
            elif line["x0"] < 40:
                group_lines.append({"pdf_page": page_number, "text": text})
                species_notes = False
            else:
                raise ValueError(f"Unclassified PDF line on page {page_number}: {text}")

assert len(rows) == len(pdf_rows) == 1100
assert [row["sort"] for row in rows] == list(map(str, range(1, 1101)))
assert len({row["scientific_name"] for row in rows}) == 1100
raw = subprocess.check_output(["pdftotext", "-raw", str(PDF), "-"], text=True)
raw_entries = [line[2:] for line in raw.splitlines() if line.startswith("c ")]
assert len(raw_entries) == 1100
checks = []
failures = []
status_mapping = {
    "AM": "AM", "am": "AMR", "PM": "PM", "pm": "PMR", "E": "E", "Ex": "EX",
    "IO": "IO", "io": "IO", "MM": "MM", "mm": "MM", "OM": "OM", "om": "OM",
    "RS": "RS", "SO": "SO", "VIO": "VIO", "VN": "VN", "VP": "VP", "VS": "VSO", "VSA": "VSA",
}
flag_columns = columns[5:28]
for row, source, raw_entry in zip(rows, pdf_rows, raw_entries):
    expected = {
        "entry_checklist_of_kenya": source["entry"],
        "family_scientific": source["family"].split(":", 1)[0],
        "family_english": source["family"].split(":", 1)[1],
        "note": " ".join(source["notes"]),
    }
    if " — " in source["entry"]:
        expected["note"] = source["entry"].split(" — ", 1)[1] + " " + expected["note"]
    assert compact(row["entry_checklist_of_kenya"]) == compact(raw_entry)
    name = row["common_name"] + " " + row["scientific_name"]
    assert source["entry"].startswith(name), f"Incorrect name split: {row['sort']}"
    suffix = source["entry"][len(name):].partition(" — ")[0]
    expected.update(dict.fromkeys(flag_columns, ""))
    for code in re.findall(r"\b[A-Za-z]+\b", suffix):
        if code in status_mapping:
            expected[status_mapping[code]] = "TRUE"
    for field in ["water_bird", "strict_water_bird"]:
        expected[field] = ""
    for field, value in expected.items():
        if compact(row[field]) != compact(value):
            failures.append({"sort": row["sort"], "pdf_page": source["page"], "field": field, "csv": row[field], "pdf": value})
    checks.append({"sort": row["sort"], "pdf_page": source["page"], "common_name": row["common_name"], "entry": source["entry"], "note": row["note"], "result": "PASS" if not any(f["sort"] == row["sort"] for f in failures) else "FAIL"})

# Excel's 977 is Rüppell's Weaver, explicitly omitted on PDF page 42.
# Keep original Excel numbers distinct from the PDF's contiguous row positions.
workbook = load_workbook(io.BytesIO(EXCEL), data_only=True)
excel_sheets = {}
sheet_summary = []
for sheet in workbook.worksheets[:4]:
    records = {}
    family = ""
    for row_number, values in enumerate(sheet.values, start=1):
        if not isinstance(values[1], (int, float)) or not values[2]:
            continue
        if re.match(r"^[A-Za-z]+idae:", str(values[2])):
            family = values[2]
            continue
        if sheet.title.startswith("Separate"):
            common, scientific, note = values[2:5]
        else:
            match = re.fullmatch(r"(.+?)\s+([A-Z][a-z]+\s+[a-z][a-z-]+(?:\s+x\s+[a-z]+)?)(.*)", values[2])
            common, scientific, suffix = match.groups()
            scientific += suffix  # Retain misplaced threat labels for the discrepancy report.
            note = values[3]
        number = int(values[1])
        assert number not in records
        records[number] = {"row": row_number, "common_name": common or "", "scientific_name": scientific or "", "note": note or "", "family": family}
    assert list(records) == list(range(1, 1102)), sheet.title
    excel_sheets[sheet.title] = records
    sheet_summary.append({"sheet": sheet.title, "entries": len(records)})

differences = []
for sheet_name, records in excel_sheets.items():
    separate = sheet_name.startswith("Separate")
    for row, source in zip(rows, pdf_rows):
        number = int(row["sort"]) + (int(row["sort"]) >= 977)
        record = records[number]
        for field in ["common_name", "scientific_name", "note"]:
            if compact(row[field]) == compact(record[field]):
                continue
            column = {"common_name": "C", "scientific_name": "D" if separate else "C", "note": "E" if separate else "D"}[field]
            differences.append({"sheet": sheet_name, "excel_cell": f"{column}{record['row']}", "excel_number": number, "pdf_sort": row["sort"], "pdf_page": source["page"], "common_name": row["common_name"], "field": field, "pdf_value": row[field], "excel_value": record[field], "kind": difference_kind(row[field], record[field]), "decision": "Retain PDF"})
        if record["family"]:
            for field, value in zip(["family_scientific", "family_english"], record["family"].split(":", 1)):
                if compact(row[field]) != compact(value):
                    differences.append({"sheet": sheet_name, "excel_cell": f"C{record['row']}", "excel_number": number, "pdf_sort": row["sort"], "pdf_page": source["page"], "common_name": row["common_name"], "field": field, "pdf_value": row[field], "excel_value": value.strip(), "kind": difference_kind(row[field], value), "decision": "Retain PDF; Excel family inferred from preceding heading"})
    omitted = records[977]
    assert compact(omitted["common_name"]) == compact("Rüppell’s Weaver")
    differences.append({"sheet": sheet_name, "excel_cell": f"C{omitted['row']}", "excel_number": 977, "pdf_sort": "", "pdf_page": 42, "common_name": "Rüppell’s Weaver", "field": "membership", "pdf_value": "Omitted species", "excel_value": omitted["common_name"] + " " + omitted["scientific_name"], "kind": "text_difference", "decision": "Exclude; PDF explicitly omits this taxon"})

# Compare the workbook's fifth sheet with the printed family headings as well.
pdf_families = list(dict.fromkeys(source["family"] for source in pdf_rows))
sheet = workbook.worksheets[4]
excel_families = [(i, value[3]) for i, value in enumerate(sheet.values, 1) if isinstance(value[3], str) and re.match(r"^[A-Za-z]+idae:", value[3])]
family_by_name = {value.split(":", 1)[0]: (i, value) for i, value in excel_families}
for value in pdf_families:
    name = value.split(":", 1)[0]
    row_number, excel_value = family_by_name.get(name, ("", ""))
    if compact(value) != compact(excel_value):
        differences.append({"sheet": sheet.title, "excel_cell": f"D{row_number}" if row_number else "", "excel_number": "", "pdf_sort": "", "pdf_page": next(source["page"] for source in pdf_rows if source["family"] == value), "common_name": "", "field": "family_heading", "pdf_value": value, "excel_value": excel_value, "kind": difference_kind(value, excel_value), "decision": "Retain PDF"})
sheet_summary.append({"sheet": sheet.title, "families": len(excel_families)})

write_csv("pdf_entry_checks.csv", checks, ["sort", "pdf_page", "common_name", "entry", "note", "result"])
write_csv("pdf_failures.csv", failures, ["sort", "pdf_page", "field", "csv", "pdf"])
write_csv("group_commentary.csv", group_lines, ["pdf_page", "text"])
write_csv("numbering_crosswalk.csv", [{"sort": row["sort"], "excel_2009_number": int(row["sort"]) + (int(row["sort"]) >= 977)} for row in rows], ["sort", "excel_2009_number"])
write_csv("excel_disagreements.csv", differences, ["sheet", "excel_cell", "excel_number", "pdf_sort", "pdf_page", "common_name", "field", "pdf_value", "excel_value", "kind", "decision"])
summary = {
    "pdf_entries": len(rows), "pdf_families": len(pdf_families), "pdf_species_notes": sum(bool(row["note"]) for row in rows),
    "schema_columns": len(columns), "pdf_failures": len(failures), "excel_sheets": sheet_summary,
    "differences_by_sheet_and_field": {sheet.title: dict(Counter(d["field"] for d in differences if d["sheet"] == sheet.title)) for sheet in workbook},
    "source_sha256": {**{path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in [PDF, DIRECTORY / "checklist.csv"]}, "source.xlsx": hashlib.sha256(EXCEL).hexdigest()},
}
(AUDIT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
assert not failures, f"Found {len(failures)} discrepancies against the PDF"
print(json.dumps(summary, indent=2, ensure_ascii=False))
