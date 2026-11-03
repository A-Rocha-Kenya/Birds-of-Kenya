#!/usr/bin/env python3
"""Check official taxonomy columns and explicit EBD concept/category corrections."""

import csv
import io
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_release import prepare_ebd, read_csv, taxonomy_index, write_csv


def main():
    (ROOT / "tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as directory:
        directory = Path(directory)
        taxonomy = directory / "taxonomy.csv"
        fields = ["taxon_order", "category", "species_code", "bio_concept_code", "primary_com_name", "sci_name", "order1", "family", "sparse_report_as", "report_as"]
        write_csv(taxonomy, fields, [dict(zip(fields, row)) for row in [
            [1, "slash", "broad1", "broad", "Broad slash", "Alpha/beta", "Order", "Family", "", "broad1"],
            [2, "species", "narrow1", "narrow", "Narrow species", "Alpha beta", "Order", "Family", "", "narrow1"],
            [3, "species", "lump1", "lump", "Lumped species", "Gamma delta", "Order", "Family", "", "lump1"],
        ]])
        if taxonomy_index(taxonomy)["broad"]["REPORT_AS"]:
            raise ValueError("self-code report_as must not become a species parent")
        corrections = directory / "corrections.csv"
        fields = ["ebd_version", "source_taxon_concept_id", "source_category", "taxon_concept_id", "reason"]
        correction_rows = [dict(zip(fields, row)) for row in [
            ["fixture", "broad", "species", "broad", "Broad concept remains unidentified"],
            ["fixture", "narrow", "issf", "narrow", "Identified subgroup becomes species"],
            ["fixture", "retired", "species", "lump", "Retired species contained in lump"],
        ]]
        write_csv(corrections, fields, correction_rows)
        exotic = directory / "exotic.csv"
        exotic.write_text("ebd_version,source_taxon_concept_id,source_exotic_code,corrected_exotic_code,reason\n")
        columns = ["TAXON CONCEPT ID", "CATEGORY", "SCIENTIFIC NAME", "SUBSPECIES SCIENTIFIC NAME", "EXOTIC CODE", "OBSERVATION DATE", "SAMPLING EVENT IDENTIFIER", "GLOBAL UNIQUE IDENTIFIER", "OBSERVATION COUNT", "LATITUDE", "LONGITUDE", "CHECKLIST COMMENTS", "SPECIES COMMENTS", "PROTOCOL NAME", "EFFORT DISTANCE KM"]
        data = io.StringIO()
        writer = csv.DictWriter(data, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        for identifier, category in [("broad", "species"), ("narrow", "issf"), ("retired", "species")]:
            writer.writerow({**dict.fromkeys(columns, ""), "TAXON CONCEPT ID": identifier,
                             "CATEGORY": category, "SCIENTIFIC NAME": "Original identification",
                             "OBSERVATION DATE": "2026-09-01", "GLOBAL UNIQUE IDENTIFIER": identifier})
        ebd = directory / "ebd_fixture.zip"
        with zipfile.ZipFile(ebd, "w") as archive:
            archive.writestr("ebd_fixture.txt", data.getvalue())
            archive.writestr("ebd_fixture_sampling.txt", "unused sampling data")
        paths = {"ebd_path": ebd, "ebird_taxonomy_path": taxonomy,
                 "ebird_taxon_corrections_path": corrections, "ebird_exotic_overrides_path": exotic}
        derived = prepare_ebd(paths, "fixture")
        reported = read_csv(derived["reported"])
        if {row["REPORTED_SPECIES_CODE"] for row in reported} != {"narrow1", "lump1"}:
            raise ValueError("broad unidentified records entered species evidence")
        if {row["source_avibase_ids"] for row in reported} != {"narrow", "retired"}:
            raise ValueError("original source concept IDs were not preserved")
        if read_csv(derived["excluded"])[0]["record_count"] != "1":
            raise ValueError("broad record was lost instead of excluded")
        if [row["record_count"] for row in read_csv(derived["taxon_corrections"])] != ["1", "1", "1"]:
            raise ValueError("taxon corrections were not counted in the audit")
        write_csv(corrections, fields, correction_rows[:2])
        try:
            prepare_ebd(paths, "fixture")
        except ValueError as error:
            if "taxonomy do not match" not in str(error):
                raise
        else:
            raise ValueError("an undocumented retired concept was accepted or stale cache reused")
        if read_csv(derived["mismatch"])[0]["source_taxon_concept_id"] != "retired":
            raise ValueError("mismatch audit did not identify the uncorrected concept")
    print("Validated official taxonomy schema, source-ID retention, corrections, unidentified evidence, and cache invalidation")


if __name__ == "__main__":
    main()
