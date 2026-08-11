#!/usr/bin/env python3
"""Build a versioned Kenya checklist from EBD observations and AviList."""

import argparse
import csv
import hashlib
import heapq
import io
import json
import sys
import tomllib
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
COMPACTION_SCHEMA_VERSION = 3
SPECIES_EVIDENCE_CATEGORIES = {"species", "issf"}
ENTITY_CATEGORIES = {"domestic", "hybrid"}
EXOTIC_STATUS = {"": "native", "N": "naturalized", "P": "provisional", "X": "escapee"}
EXOTIC_PRIORITY = {"native": 0, "naturalized": 1, "provisional": 2, "escapee": 3}
WATERBIRD_FAMILIES = frozenset({
    "Anatidae", "Anhimidae", "Anhingidae", "Anseranatidae", "Aramidae", "Ardeidae",
    "Balaenicipitidae", "Burhinidae", "Charadriidae", "Chionidae", "Ciconiidae",
    "Dromadidae", "Eurypygidae", "Gaviidae", "Glareolidae", "Gruidae",
    "Haematopodidae", "Heliornithidae", "Ibidorhynchidae", "Jacanidae", "Laridae",
    "Pedionomidae", "Pelecanidae", "Phalacrocoracidae", "Phoenicopteridae",
    "Podicipedidae", "Rallidae", "Recurvirostridae", "Rostratulidae", "Scolopacidae",
    "Scopidae", "Thinocoridae", "Threskiornithidae",
})
DERIVED_CATEGORY_FIELDS = ["water_bird"]
COMPACT_FIELDS = [
    "source_taxon_concept_id", "ebd_category", "ebd_scientific_name",
    "ebd_subspecies_scientific_name", "ebird_species_code", "ebird_report_as",
    "REPORTED_SPECIES_CODE", "source_exotic_code", "exotic_code",
    "observation_record_count", "first_observation_date", "last_observation_date",
]
LOCAL_RECORD_FIELDS = [
    "REPORTED_SPECIES_CODE", "ebd_category", "ebird_report_as", "source_taxon_concept_id", "source_exotic_code",
    "exotic_code", "sampling_event_identifier", "global_unique_identifier", "observation_date", "observation_count",
    "checklist_comments", "species_comments",
]
REPORTED_FIELDS = [
    "REPORTED_SPECIES_CODE", "source_avibase_ids", "exotic_status", "observation_record_count",
    "first_observation_date", "last_observation_date",
]
CHECKLIST_FIELDS = [
    "sequence", "avilist_id", "order", "family", "family_english_name",
    "scientific_name", "english_name", "taxonomy_comment", "ebird_species_code", "source_avibase_ids",
    "membership_source", "sensitive", "exotic_status", "observation_record_count",
    "first_observation_date", "last_observation_date",
]
PUBLIC_RECORD_FIELDS = [
    "avilist_id", "sampling_event_identifier", "source_taxon_concept_id",
    "exotic_code", "global_unique_identifier", "observation_date", "observation_count",
]
ENTITY_FIELDS = [
    "sequence", "source_taxon_concept_id", "entity_category", "exotic_status", "order", "family",
    "family_english_name", "scientific_name", "english_name", "ebird_species_code",
    "source_avibase_ids", "observation_record_count", "first_observation_date",
    "last_observation_date",
]
ENTITY_PUBLIC_RECORD_FIELDS = [
    "source_taxon_concept_id", "exotic_status", "sampling_event_identifier", "exotic_code",
    "global_unique_identifier", "observation_date", "observation_count",
]
EXOTIC_OVERRIDE_FIELDS = [
    "ebd_version", "source_taxon_concept_id", "source_exotic_code",
    "corrected_exotic_code", "observation_record_count", "reason",
]
SENSITIVE_AUDIT_FIELDS = [
    "avilist_id", "scientific_name", "english_name", "ebird_species_code",
    "membership_source", "reason", "reference",
]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_xlsx(path):
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(item.itertext()) for item in root.findall("x:si", NS)]
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rels = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        first_sheet = workbook.find("x:sheets/x:sheet", NS)
        relationship_id = first_sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = rels[relationship_id].lstrip("/")
        sheet_path = target if target.startswith("xl/") else f"xl/{target}"
        sheet = ElementTree.fromstring(archive.read(sheet_path))
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
    start = 2 if len(rows) > 1 and not any(rows[1]) else 1
    return [dict(zip(headers, row)) for row in rows[start:]]


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def release_id(config):
    return f"{config['ebd_version']}.{int(config['release_revision'])}"


def source_paths(config):
    return {key: ROOT / config[key] for key in [
        "ebd_path", "avilist_path", "ebird_taxonomy_path", "categories_path",
        "ebird_avilist_overrides_path", "ebird_exotic_overrides_path",
        "sensitive_species_path",
    ]}


def derived_paths(ebd_path):
    directory = ebd_path.parent / "derived"
    stem = ebd_path.stem
    return {
        "compact": directory / f"{stem}_compact_summary.csv",
        "compact_latest": directory / f"{stem}_compact_latest_records.csv",
        "reported": directory / f"{stem}_reported_species_summary.csv",
        "reported_latest": directory / f"{stem}_reported_species_latest_records.csv",
        "excluded": directory / f"{stem}_excluded_non_species_observations.csv",
        "exotic_overrides": directory / f"{stem}_exotic_code_overrides.csv",
        "mismatch": directory / f"{stem}_taxonomy_mismatch.csv",
        "metadata": directory / f"{stem}_compaction.json",
    }


def taxonomy_index(path):
    rows = read_csv(path)
    duplicates = sorted(identifier for identifier, count in Counter(
        row["TAXON_CONCEPT_ID"].strip() for row in rows
    ).items() if identifier and count > 1)
    if duplicates:
        raise ValueError(f"eBird taxonomy contains duplicate TAXON_CONCEPT_ID values: {', '.join(duplicates[:10])}")
    if any(not row["TAXON_CONCEPT_ID"].strip() for row in rows):
        raise ValueError("eBird taxonomy contains a blank TAXON_CONCEPT_ID")
    return {row["TAXON_CONCEPT_ID"].strip(): row for row in rows}


def open_ebd(path):
    archive = zipfile.ZipFile(path)
    members = [name for name in archive.namelist() if name.startswith("ebd_") and name.endswith(".txt")]
    if len(members) != 1:
        archive.close()
        raise ValueError(f"expected one EBD text file in {path.name}, found {len(members)}")
    binary = archive.open(members[0])
    return archive, binary, io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")


def push_latest(heap, row):
    item = (row["observation_date"], row["global_unique_identifier"], row)
    heapq.heappush(heap, item)
    if len(heap) > 5:
        heapq.heappop(heap)


def flatten_latest(heaps):
    rows = []
    for key in sorted(heaps, key=str):
        rows.extend(item[2] for item in sorted(heaps[key], reverse=True))
    return rows


def exotic_status(code):
    return EXOTIC_STATUS[code]


def preferred_exotic_status(left, right):
    return min((left, right), key=EXOTIC_PRIORITY.get)


def is_species_evidence(row):
    if row["exotic_code"] == "X":
        return False
    if row["ebd_category"] in SPECIES_EVIDENCE_CATEGORIES:
        return True
    if row["ebd_category"] == "form" and row["ebird_report_as"]:
        return True
    return row["ebd_category"] == "domestic" and row["ebird_report_as"] and row["exotic_code"] in {"N", "P"}


def is_taxonomic_entity(row):
    if is_species_evidence(row):
        return False
    if row["exotic_code"] == "X":
        return True
    return row["ebd_category"] in ENTITY_CATEGORIES or (
        row["ebd_category"] == "form" and not row["ebird_report_as"]
    )


def aggregate_reported(compact_rows, compact_latest_rows):
    reported = {}
    for row in compact_rows:
        if not is_species_evidence(row):
            continue
        code = row["REPORTED_SPECIES_CODE"]
        item = reported.setdefault(code, {
            "REPORTED_SPECIES_CODE": code,
            "source_avibase_ids": set(),
            "exotic_status": exotic_status(row["exotic_code"]),
            "observation_record_count": 0,
            "first_observation_date": row["first_observation_date"],
            "last_observation_date": row["last_observation_date"],
        })
        item["source_avibase_ids"].add(row["source_taxon_concept_id"])
        item["exotic_status"] = preferred_exotic_status(item["exotic_status"], exotic_status(row["exotic_code"]))
        item["observation_record_count"] += int(row["observation_record_count"])
        item["first_observation_date"] = min(item["first_observation_date"], row["first_observation_date"])
        item["last_observation_date"] = max(item["last_observation_date"], row["last_observation_date"])
    summary = [{
        **item,
        "source_avibase_ids": ";".join(sorted(item["source_avibase_ids"])),
    } for item in sorted(reported.values(), key=lambda item: item["REPORTED_SPECIES_CODE"])]
    latest = defaultdict(list)
    for row in compact_latest_rows:
        if is_species_evidence(row) and row["REPORTED_SPECIES_CODE"] in reported:
            push_latest(latest[row["REPORTED_SPECIES_CODE"]], row)
    return summary, flatten_latest(latest)


def family_fields(value):
    family, english_name = value.split(" (", maxsplit=1)
    return family, english_name.removesuffix(")")


def aggregate_taxonomic_entities(compact_rows, compact_latest_rows, taxonomy):
    entities = {}
    for row in compact_rows:
        if not is_taxonomic_entity(row):
            continue
        source_id = row["source_taxon_concept_id"]
        status = exotic_status(row["exotic_code"])
        key = (source_id, status)
        taxon = taxonomy[source_id]
        family, family_english_name = family_fields(taxon["FAMILY"])
        item = entities.setdefault(key, {
            "sequence": taxon["TAXON_ORDER"],
            "source_taxon_concept_id": source_id,
            "entity_category": row["ebd_category"],
            "exotic_status": status,
            "order": taxon["ORDER"],
            "family": family,
            "family_english_name": family_english_name,
            "scientific_name": taxon["SCI_NAME"],
            "english_name": taxon["PRIMARY_COM_NAME"],
            "ebird_species_code": taxon["SPECIES_CODE"],
            "source_avibase_ids": source_id,
            "observation_record_count": 0,
            "first_observation_date": row["first_observation_date"],
            "last_observation_date": row["last_observation_date"],
        })
        item["observation_record_count"] += int(row["observation_record_count"])
        item["first_observation_date"] = min(item["first_observation_date"], row["first_observation_date"])
        item["last_observation_date"] = max(item["last_observation_date"], row["last_observation_date"])
    latest = defaultdict(list)
    for row in compact_latest_rows:
        key = (row["source_taxon_concept_id"], exotic_status(row["exotic_code"]))
        if is_taxonomic_entity(row) and key in entities:
            push_latest(latest[key], row)
    summary = sorted(entities.values(), key=lambda row: float(row["sequence"]))
    return summary, flatten_latest(latest)


def write_derived_summaries(derived, compact_rows=None, compact_latest_rows=None):
    compact_rows = compact_rows or read_csv(derived["compact"])
    compact_latest_rows = compact_latest_rows or read_csv(derived["compact_latest"])
    reported_rows, reported_latest_rows = aggregate_reported(compact_rows, compact_latest_rows)
    excluded = defaultdict(int)
    for row in compact_rows:
        if not is_species_evidence(row) and not is_taxonomic_entity(row):
            excluded[(row["ebd_category"], row["ebd_scientific_name"])] += int(row["observation_record_count"])
    excluded_rows = [{
        "category": key[0], "scientific_name": key[1], "observation_record_count": count,
    } for key, count in sorted(excluded.items())]
    write_csv(derived["reported"], REPORTED_FIELDS, reported_rows)
    write_csv(derived["reported_latest"], LOCAL_RECORD_FIELDS, reported_latest_rows)
    write_csv(derived["excluded"], ["category", "scientific_name", "observation_record_count"], excluded_rows)


def read_exotic_overrides(path, ebd_version):
    rows = [row for row in read_csv(path) if row["ebd_version"].strip() == ebd_version]
    overrides = {}
    for row in rows:
        key = (row["source_taxon_concept_id"].strip(), row["source_exotic_code"].strip().upper())
        overrides[key] = {
            "corrected_exotic_code": row["corrected_exotic_code"].strip().upper(),
            "reason": row["reason"].strip(),
        }
    return overrides


def warn_exotic_overrides(path):
    rows = read_csv(path)
    applied = sum(int(row["observation_record_count"]) for row in rows)
    if applied:
        print(f"WARNING: Applied {applied:,} curated EBD EXOTIC CODE corrections; inspect {path.relative_to(ROOT)}")


def prepare_ebd(paths, ebd_version, force=False):
    derived = derived_paths(paths["ebd_path"])
    metadata = {
        "schema_version": COMPACTION_SCHEMA_VERSION,
        "ebd_sha256": checksum(paths["ebd_path"]),
        "ebird_taxonomy_sha256": checksum(paths["ebird_taxonomy_path"]),
        "ebird_exotic_overrides_sha256": checksum(paths["ebird_exotic_overrides_path"]),
    }
    required = [derived[key] for key in ["compact", "compact_latest", "reported", "reported_latest", "excluded", "exotic_overrides"]]
    if not force and derived["metadata"].exists() and all(path.exists() for path in required):
        cached = json.loads(derived["metadata"].read_text(encoding="utf-8"))
        if cached == metadata:
            write_derived_summaries(derived)
            warn_exotic_overrides(derived["exotic_overrides"])
            print(f"Reusing compact EBD data in {derived['compact'].parent.relative_to(ROOT)}")
            return derived

    taxonomy = taxonomy_index(paths["ebird_taxonomy_path"])
    exotic_overrides = read_exotic_overrides(paths["ebird_exotic_overrides_path"], ebd_version)
    applied_exotic_overrides = Counter()
    compact = {}
    latest = defaultdict(list)
    mismatches = Counter()
    archive, binary, handle = open_ebd(paths["ebd_path"])
    try:
        for row in csv.DictReader(handle, delimiter="\t"):
            source_id = row["TAXON CONCEPT ID"].strip()
            category = row["CATEGORY"].strip().lower()
            taxon = taxonomy.get(source_id)
            if not taxon:
                mismatches[(source_id, category, row["SCIENTIFIC NAME"].strip(), "taxon_concept_id_not_found")] += 1
                continue
            if taxon["CATEGORY"].strip().lower() != category:
                mismatches[(source_id, category, row["SCIENTIFIC NAME"].strip(), "category_mismatch")] += 1
                continue
            species_code = taxon["SPECIES_CODE"].strip()
            report_as = taxon["REPORT_AS"].strip()
            reported_code = report_as or species_code
            if category in SPECIES_EVIDENCE_CATEGORIES and not reported_code:
                mismatches[(source_id, category, row["SCIENTIFIC NAME"].strip(), "missing_reported_species_code")] += 1
                continue
            scientific_name = row["SCIENTIFIC NAME"].strip()
            subspecies_name = row["SUBSPECIES SCIENTIFIC NAME"].strip()
            source_exotic_code = row["EXOTIC CODE"].strip().upper()
            if source_exotic_code not in EXOTIC_STATUS:
                raise ValueError(f"unexpected EBD EXOTIC CODE: {source_exotic_code}")
            override = exotic_overrides.get((source_id, source_exotic_code))
            effective_exotic_code = override["corrected_exotic_code"] if override else source_exotic_code
            if effective_exotic_code not in EXOTIC_STATUS:
                raise ValueError(f"unexpected corrected EBD EXOTIC CODE: {effective_exotic_code}")
            if override:
                applied_exotic_overrides[(source_id, source_exotic_code)] += 1
            key = (source_id, category, scientific_name, subspecies_name, reported_code, source_exotic_code, effective_exotic_code)
            date = row["OBSERVATION DATE"].strip()
            item = compact.setdefault(key, {
                "source_taxon_concept_id": source_id,
                "ebd_category": category,
                "ebd_scientific_name": scientific_name,
                "ebd_subspecies_scientific_name": subspecies_name,
                "ebird_species_code": species_code,
                "ebird_report_as": report_as,
                "REPORTED_SPECIES_CODE": reported_code,
                "source_exotic_code": source_exotic_code,
                "exotic_code": effective_exotic_code,
                "observation_record_count": 0,
                "first_observation_date": date,
                "last_observation_date": date,
            })
            item["observation_record_count"] += 1
            item["first_observation_date"] = min(item["first_observation_date"], date)
            item["last_observation_date"] = max(item["last_observation_date"], date)
            record = {
                "REPORTED_SPECIES_CODE": reported_code,
                "ebd_category": category,
                "ebird_report_as": report_as,
                "source_taxon_concept_id": source_id,
                "source_exotic_code": source_exotic_code,
                "exotic_code": effective_exotic_code,
                "sampling_event_identifier": row["SAMPLING EVENT IDENTIFIER"].strip(),
                "global_unique_identifier": row["GLOBAL UNIQUE IDENTIFIER"].strip(),
                "observation_date": date,
                "observation_count": row["OBSERVATION COUNT"].strip(),
                "checklist_comments": row["CHECKLIST COMMENTS"].strip(),
                "species_comments": row["SPECIES COMMENTS"].strip(),
            }
            push_latest(latest[key], record)
    finally:
        handle.close()
        binary.close()
        archive.close()

    if mismatches:
        mismatch_rows = [{
            "source_taxon_concept_id": key[0], "ebd_category": key[1],
            "ebd_scientific_name": key[2], "error": key[3], "observation_record_count": count,
        } for key, count in sorted(mismatches.items())]
        write_csv(derived["mismatch"], [
            "source_taxon_concept_id", "ebd_category", "ebd_scientific_name", "error",
            "observation_record_count",
        ], mismatch_rows)
        raise ValueError(
            f"EBD and eBird taxonomy do not match; inspect {derived['mismatch'].relative_to(ROOT)}"
        )
    derived["mismatch"].unlink(missing_ok=True)

    override_rows = [{
        "ebd_version": ebd_version,
        "source_taxon_concept_id": key[0],
        "source_exotic_code": key[1],
        "corrected_exotic_code": value["corrected_exotic_code"],
        "observation_record_count": applied_exotic_overrides[key],
        "reason": value["reason"],
    } for key, value in sorted(exotic_overrides.items())]
    write_csv(derived["exotic_overrides"], EXOTIC_OVERRIDE_FIELDS, override_rows)
    warn_exotic_overrides(derived["exotic_overrides"])

    compact_rows = sorted(compact.values(), key=lambda row: (
        row["ebd_category"], row["ebd_scientific_name"], row["REPORTED_SPECIES_CODE"],
    ))
    compact_latest_rows = flatten_latest(latest)
    write_csv(derived["compact"], COMPACT_FIELDS, compact_rows)
    write_csv(derived["compact_latest"], LOCAL_RECORD_FIELDS, compact_latest_rows)
    write_derived_summaries(derived, compact_rows, compact_latest_rows)
    derived["metadata"].write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Compacted EBD into {len(compact_rows):,} source groups and {len(read_csv(derived['reported'])):,} reportable codes")
    return derived


def avilist_indexes(rows):
    by_code = {}
    by_id = {}
    for row in rows:
        if row.get("AvibaseID"):
            by_id[row["AvibaseID"]] = row
        code = row.get("Species_code_Cornell_Lab", "").strip()
        if code:
            by_code[code] = row
    return by_code, by_id


def resolve_ebird_code(species_code, avilist_by_code, overrides):
    if species_code in overrides:
        return overrides[species_code], "curated_override"
    taxon = avilist_by_code.get(species_code)
    if not taxon:
        return None, "ebird_species_code_not_in_avilist"
    if taxon["Taxon_rank"].lower() == "species":
        return taxon, "ebird_species_code"
    return None, "ebird_species_code_to_non_species_avilist_taxon"


def read_ebird_avilist_overrides(path, avilist_by_id):
    rows = read_csv(path)
    codes = [row["reported_species_code"].strip() for row in rows]
    if any(not code for code in codes):
        raise ValueError("ebird_avilist_overrides.csv contains a blank reported_species_code")
    duplicates = sorted(code for code, count in Counter(codes).items() if count > 1)
    if duplicates:
        raise ValueError(f"ebird_avilist_overrides.csv contains duplicate reported_species_code values: {', '.join(duplicates)}")
    overrides = {}
    for row in rows:
        code = row["reported_species_code"].strip()
        avilist_id = row["avilist_id"].strip()
        taxon = avilist_by_id.get(avilist_id)
        if not taxon or taxon["Taxon_rank"].lower() != "species":
            raise ValueError(f"ebird_avilist_overrides.csv maps {code} to a missing or non-species AviList ID: {avilist_id}")
        overrides[code] = taxon
    return overrides


def read_sensitive_species(path, avilist_by_id):
    rows = read_csv(path)
    identifiers = [row["avilist_id"].strip() for row in rows]
    duplicates = sorted(identifier for identifier, count in Counter(identifiers).items() if count > 1)
    if any(not identifier for identifier in identifiers) or duplicates:
        raise ValueError("sensitive_species.csv avilist_id values must be nonblank and unique")
    for identifier in identifiers:
        taxon = avilist_by_id.get(identifier)
        if not taxon or taxon["Taxon_rank"].lower() != "species":
            raise ValueError(f"sensitive_species.csv contains a missing or non-species AviList ID: {identifier}")
    return {row["avilist_id"].strip(): row for row in rows}


def read_categories(path):
    if not path.exists():
        return {}, []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = [field for field in reader.fieldnames or [] if field != "avilist_id"]
        rows = list(reader)
    derived = sorted(set(fields) & set(DERIVED_CATEGORY_FIELDS))
    if derived:
        raise ValueError(f"categories.csv contains derived category columns: {', '.join(derived)}")
    identifiers = [row["avilist_id"].strip() for row in rows]
    if any(not identifier for identifier in identifiers):
        raise ValueError("categories.csv contains a blank avilist_id")
    duplicates = sorted(identifier for identifier, count in Counter(identifiers).items() if count > 1)
    if duplicates:
        raise ValueError(f"categories.csv contains duplicate avilist_id values: {', '.join(duplicates)}")
    return {row["avilist_id"]: row for row in rows}, fields


def merge_evidence(target, row, code):
    target["codes"].add(code)
    target["source_ids"].update(filter(None, row["source_avibase_ids"].split(";")))
    target["exotic_status"] = preferred_exotic_status(target["exotic_status"], row["exotic_status"])
    target["count"] += int(row["observation_record_count"])
    target["first"] = min(target["first"], row["first_observation_date"]) if target["first"] else row["first_observation_date"]
    target["last"] = max(target["last"], row["last_observation_date"])


def build(config_path, force_compaction=False):
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    paths = source_paths(config)
    for key, path in paths.items():
        if key != "categories_path" and not path.exists():
            raise FileNotFoundError(f"{key} does not exist: {path.relative_to(ROOT)}")
    derived = prepare_ebd(paths, config["ebd_version"], force_compaction)
    reported = read_csv(derived["reported"])
    reported_latest = read_csv(derived["reported_latest"])
    excluded = read_csv(derived["excluded"])
    exotic_override_audit = read_csv(derived["exotic_overrides"])
    compact = read_csv(derived["compact"])
    compact_latest = read_csv(derived["compact_latest"])
    entity_rows, entity_latest = aggregate_taxonomic_entities(
        compact, compact_latest, taxonomy_index(paths["ebird_taxonomy_path"])
    )
    avilist_by_code, avilist_by_id = avilist_indexes(read_xlsx(paths["avilist_path"]))
    overrides = read_ebird_avilist_overrides(paths["ebird_avilist_overrides_path"], avilist_by_id)
    sensitive_species = read_sensitive_species(paths["sensitive_species_path"], avilist_by_id)
    categories, category_fields = read_categories(paths["categories_path"])
    output_category_fields = category_fields + DERIVED_CATEGORY_FIELDS

    observations = {}
    code_to_avilist = {}
    overrides_used = set()
    unmapped = []
    for row in reported:
        code = row["REPORTED_SPECIES_CODE"]
        taxon, method = resolve_ebird_code(code, avilist_by_code, overrides)
        if not taxon:
            unmapped.append({**row, "mapping_result": method})
            continue
        code_to_avilist[code] = taxon["AvibaseID"]
        if method == "curated_override":
            overrides_used.add(code)
        item = observations.setdefault(taxon["AvibaseID"], {
            "taxon": taxon, "codes": set(), "source_ids": set(), "count": 0,
            "first": "", "last": "", "exotic_status": row["exotic_status"],
            "membership_source": "ebd", "sensitive": "FALSE",
        })
        merge_evidence(item, row, code)

    sensitive_audit = []
    for avilist_id, curated_sensitive in sensitive_species.items():
        taxon = avilist_by_id[avilist_id]
        evidence = observations.get(avilist_id)
        membership_source = "ebd" if evidence else "curated_sensitive_species"
        if evidence:
            evidence["sensitive"] = "TRUE"
        else:
            observations[avilist_id] = {
                "taxon": taxon,
                "codes": {taxon["Species_code_Cornell_Lab"]},
                "source_ids": set(),
                "count": None,
                "first": "",
                "last": "",
                "exotic_status": "native",
                "membership_source": membership_source,
                "sensitive": "TRUE",
            }
        sensitive_audit.append({
            "avilist_id": avilist_id,
            "scientific_name": taxon["Scientific_name"],
            "english_name": taxon["English_name_AviList"],
            "ebird_species_code": taxon["Species_code_Cornell_Lab"],
            "membership_source": membership_source,
            "reason": curated_sensitive["reason"],
            "reference": curated_sensitive["reference"],
        })

    latest = defaultdict(list)
    for row in reported_latest:
        identifier = code_to_avilist.get(row["REPORTED_SPECIES_CODE"])
        if identifier:
            push_latest(latest[identifier], row)

    checklist = []
    used_categories = set()
    for identifier, evidence in observations.items():
        taxon = evidence["taxon"]
        curated = categories.get(identifier, {})
        used_categories.add(identifier)
        checklist.append({
            "sequence": taxon["Sequence"],
            "avilist_id": identifier,
            "order": taxon["Order"],
            "family": taxon["Family"],
            "family_english_name": taxon["Family_English_name"],
            "scientific_name": taxon["Scientific_name"],
            "english_name": taxon["English_name_AviList"],
            "taxonomy_comment": taxon["Decision_summary"].strip(),
            "ebird_species_code": ";".join(sorted(evidence["codes"])),
            "source_avibase_ids": ";".join(sorted(evidence["source_ids"])),
            "membership_source": evidence["membership_source"],
            "sensitive": evidence["sensitive"],
            "exotic_status": evidence["exotic_status"],
            "observation_record_count": "" if evidence["count"] is None else evidence["count"],
            "first_observation_date": evidence["first"],
            "last_observation_date": evidence["last"],
            **{field: curated.get(field, "") for field in category_fields},
            "water_bird": "TRUE" if taxon["Family"] in WATERBIRD_FAMILIES else "FALSE",
        })
    checklist.sort(key=lambda row: float(row["sequence"]))
    latest_rows = [{"avilist_id": identifier, **item[2]} for identifier in sorted(latest) for item in sorted(latest[identifier], reverse=True)]

    identifier = release_id(config)
    output = ROOT / "dist" / identifier
    write_csv(output / "checklist.csv", CHECKLIST_FIELDS + output_category_fields, checklist)
    write_csv(output / "latest_records.csv", PUBLIC_RECORD_FIELDS, latest_rows)
    write_csv(output / "supplementary_taxa.csv", ENTITY_FIELDS, entity_rows)
    write_csv(output / "supplementary_taxa_latest_records.csv", ENTITY_PUBLIC_RECORD_FIELDS, [
        {"source_taxon_concept_id": row["source_taxon_concept_id"], "exotic_status": exotic_status(row["exotic_code"]), **row}
        for row in entity_latest
    ])
    write_csv(output / "audit" / "ebd_taxa_not_in_avilist.csv", REPORTED_FIELDS + ["mapping_result"], unmapped)
    write_csv(output / "audit" / "excluded_non_species_observations.csv", [
        "category", "scientific_name", "observation_record_count",
    ], excluded)
    write_csv(output / "audit" / "unused_category_rows.csv", ["avilist_id"] + category_fields, [
        row for avilist_id, row in categories.items() if avilist_id not in used_categories
    ])
    write_csv(output / "audit" / "exotic_code_overrides.csv", EXOTIC_OVERRIDE_FIELDS, exotic_override_audit)
    write_csv(output / "audit" / "sensitive_species.csv", SENSITIVE_AUDIT_FIELDS, sensitive_audit)

    manifest = {
        "release_id": identifier,
        "ebd_version": config["ebd_version"],
        "release_revision": int(config["release_revision"]),
        "ebird_taxonomy_version": config["ebird_taxonomy_version"],
        "avilist_version": config["avilist_version"],
        "sources": {
            key: {"path": str(path.relative_to(ROOT)), "sha256": checksum(path)}
            for key, path in paths.items() if path.exists()
        },
        "counts": {
            "species": len(checklist),
            "species_observation_records": sum(int(row["observation_record_count"]) for row in checklist if row["observation_record_count"]),
            "latest_records": len(latest_rows),
            "taxonomic_entities": len(entity_rows),
            "taxonomic_entity_observation_records": sum(
                int(row["observation_record_count"]) for row in entity_rows
            ),
            "taxonomic_entity_latest_records": len(entity_latest),
            "curated_ebird_avilist_overrides_used": len(overrides_used),
            "curated_exotic_code_overrides_used": sum(
                int(row["observation_record_count"]) > 0 for row in exotic_override_audit
            ),
            "curated_exotic_code_observations": sum(
                int(row["observation_record_count"]) for row in exotic_override_audit
            ),
            "curated_sensitive_species": len(sensitive_audit),
            "curated_sensitive_species_without_ebd_records": sum(
                row["membership_source"] == "curated_sensitive_species" for row in sensitive_audit
            ),
            "species_by_exotic_status": dict(sorted(Counter(row["exotic_status"] for row in checklist).items())),
            "taxonomic_entities_by_exotic_status": dict(sorted(Counter(row["exotic_status"] for row in entity_rows).items())),
            "unmapped_reported_species_codes": len(unmapped),
            "excluded_other_taxa": len(excluded),
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Built {identifier}: {len(checklist):,} species from {manifest['counts']['species_observation_records']:,} observation records")
    print(f"Wrote {output.relative_to(ROOT)}")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path, help="release TOML file")
    parser.add_argument("--force-compaction", action="store_true", help="rebuild the compact EBD cache")
    args = parser.parse_args()
    build(args.config.resolve(), args.force_compaction)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, csv.Error, zipfile.BadZipFile, json.JSONDecodeError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        raise SystemExit(1)
