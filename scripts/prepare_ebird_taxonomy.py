#!/usr/bin/env python3
"""Extract the official 2026 names workbook's taxonomy fields.

Run: uv run --with openpyxl python scripts/prepare_ebird_taxonomy.py
The workbook is downloaded from Cornell's public Box link in data/ebird/README.md.
"""
import csv
import tomllib
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
config = tomllib.loads((ROOT / "config/release.toml").read_text())
workbook = load_workbook(ROOT / config["current_ebird_names_path"], read_only=True, data_only=True)
rows = workbook["Sparse"].iter_rows(values_only=True)
headers = next(rows)
columns = {
    "taxon_order": "TAXON_ORDER", "category": "CATEGORY", "species_code": "SPECIES_CODE",
    "bio_concept_code": "TAXON_CONCEPT_ID", "primary_com_name": "PRIMARY_COM_NAME",
    "sci_name": "SCI_NAME", "order1": "ORDER", "family": "FAMILY", "sparse_report_as": "REPORT_AS",
}
with (ROOT / config["current_ebird_taxonomy_path"]).open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(columns.values()), lineterminator="\n")
    writer.writeheader()
    for values in rows:
        row = dict(zip(headers, values))
        writer.writerow({target: row[source] if row[source] is not None else "" for source, target in columns.items()})
workbook.close()
print(f"Extracted {config['current_ebird_taxonomy_path']}")
