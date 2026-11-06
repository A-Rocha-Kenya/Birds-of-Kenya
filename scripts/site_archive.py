"""Export archived checklists and all directed taxonomy comparison pairs."""

import csv
import hashlib
import json
import re
import shutil
import tomllib
from pathlib import Path

from release_archive import read_csv, verify
from taxonomy_comparison import compare_versions


def load_archive(root, preview=None):
    registry = tomllib.loads((root / "publication/releases.toml").read_text())
    active = preview or registry["active_release"]
    bundles = {}
    for entry in registry["releases"]:
        if entry.get("status") == "draft" and entry["id"] != preview:
            continue
        path = root / entry["path"]
        if not (path / "release.json").exists() and entry.get("status") == "draft":
            continue
        descriptor = verify(path)
        if descriptor["id"] != entry["id"]:
            raise ValueError(f"Registry ID differs from sealed release: {entry['id']}")
        if descriptor["status"] == "released" or preview and entry["id"] == preview:
            bundles[entry["id"]] = (path, descriptor)
    if active not in bundles:
        raise ValueError(f"Active release {active} must be an archived published release or explicit preview")
    return active, bundles


def load_transitions(bundles):
    transitions = []
    for path, _ in bundles.values():
        if (path / "transition.json").exists():
            transitions.append(json.loads((path / "transition.json").read_text()))
        if (path / "transitions.json").exists():
            for transition in json.loads((path / "transitions.json").read_text()):
                corrections = path / "corrections.csv"
                if corrections.exists() and transition["to_release"] == path.name:
                    transition["assignment_corrections"] = [
                        {"old_id": row["before"], "new_id": row["after"]}
                        for row in read_csv(corrections) if row["field"] == "avibaseid"
                    ]
                transitions.append(transition)
    return transitions


def load_concept_relationships(root):
    path = root / "data/curation/taxon_concept_relationships.csv"
    relations = {"includes", "isCongruentWith", "partiallyOverlaps", "intersects", "isDisjointFrom"}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    pairs = set()
    for row in rows:
        subject, relation, object_id = (row[key] for key in ("subject_id", "relationship", "object_id"))
        if (relation not in relations or subject == object_id
                or not all(re.fullmatch(r"avibase-[0-9A-F]{8}", value) for value in (subject, object_id))
                or not row["source_url"].startswith("https://")):
            raise ValueError(f"Invalid concept relationship in {path}: {row}")
        pair = frozenset((subject, object_id))
        if pair in pairs:
            raise ValueError(f"Multiple relationships for one concept pair in {path}: {row}")
        pairs.add(pair)
    return rows


def format_family_label(label):
    """Use one capitalization style for English family labels on the website."""
    connectors = {"and", "or", "of", "the", "in", "with"}
    words = list(re.finditer(r"[^\W\d_]+(?:['’][^\W\d_]+)*", label, flags=re.UNICODE))
    first = words[0].start() if words else 0

    def capitalize(match):
        word = match.group().lower()
        return word if match.start() != first and word in connectors else word.capitalize()

    return re.sub(r"[^\W\d_]+(?:['’][^\W\d_]+)*", capitalize, label)


def export_archive(staging, active, bundles, relationships=()):
    versions, releases = {}, []
    for identifier, (path, descriptor) in bundles.items():
        versions[identifier] = json.loads((path / "taxonomy.json").read_text())
        for row in versions[identifier]:
            row["family_english"] = format_family_label(row["family_english"])
        destination = staging / "downloads" / identifier
        destination.mkdir(parents=True)
        basename = f"Checklist-of-the-Birds-of-Kenya-{identifier}"
        shutil.copy2(path / "checklist.csv", destination / f"{basename}.csv")
        shutil.copy2(path / "checklist.csv", destination / "checklist.csv")
        if descriptor["pdf"]:
            shutil.copy2(path / descriptor["pdf"], destination / f"{basename}.pdf")
            if descriptor["pdf"] != f"{basename}.pdf":
                shutil.copy2(path / descriptor["pdf"], destination / descriptor["pdf"])
        releases.append({"id": identifier, "status": descriptor["status"],
                         "pdf": f'downloads/{identifier}/{basename}.pdf' if descriptor["pdf"] else "",
                         "csv": f"downloads/{identifier}/{basename}.csv",
                         "taxonomy_excluded_rows": descriptor.get("taxonomy_excluded_rows", 0),
                         "pdf_label": descriptor.get("pdf_label", "Checklist PDF")})
    # Every concept has an edition membership, including those with no curated edges.
    concepts = {}
    excluded_entries = {}
    for identifier, rows in versions.items():
        for row in rows:
            concepts.setdefault(row["id"], {})[identifier] = {key: value for key, value in row.items() if key != "id"}
        path, _ = bundles[identifier]
        exclusions = path / "taxonomy-exclusions.json"
        if exclusions.exists():
            excluded_entries[identifier] = [
                {key: row[key] for key in ("sort", "common_name", "scientific_name", "avibaseid")}
                for row in json.loads(exclusions.read_text())
            ]
    for edge in relationships:
        for endpoint in ("subject_id", "object_id"):
            concepts.setdefault(edge[endpoint], {})
    concept_graph = {"concepts": concepts, "relationships": relationships,
                     "excluded_entries": excluded_entries}
    (staging / "data/taxon-concept-graph.json").write_text(json.dumps(concept_graph, ensure_ascii=False, sort_keys=True) + "\n")
    pairs = []
    for source in versions:
        for target in versions:
            pair = compare_versions(versions, (), source, target, relationships)
            destination = staging / "data/comparisons" / source / target
            destination.mkdir(parents=True)
            write_comparison(destination, pair)
            prefix = f"data/comparisons/{source}/{target}"
            pairs.append({"revision": hashlib.sha256((destination / "taxonomy-changes.json").read_bytes() + (destination / "taxonomy-changes.csv").read_bytes()).hexdigest()[:16], "from_release": source, "to_release": target, "group_count": pair["group_count"],
                          "files": {"json": prefix + "/taxonomy-changes.json", "csv": prefix + "/taxonomy-changes.csv"}})
    latest_by_year = {}
    for release in sorted(releases, key=lambda item: tuple(map(int, item["id"][1:].split(".")))):
        latest_by_year[release["id"][1:5]] = release["id"]
    review_path = Path(__file__).resolve().parents[1] / "data/curation/checklist_membership_reviews.csv"
    earc_decisions = {}
    for identifier, (path, _) in bundles.items():
        decisions = path / "curation/earc_decisions.csv"
        if decisions.exists():
            earc_decisions[identifier] = {row["avibase_id"]: row for row in read_csv(decisions)}
    membership_reviews = {}
    for row in read_csv(review_path):
        source, target, identifier = (row[key] for key in ("from_release", "to_release", "avibase_id"))
        if source in versions and target in versions:
            review = {field: row[field] for field in ("status", "entry_previous", "reason")}
            review["sighting_urls"] = row["sighting_urls"].split()
            if source.startswith("v2019.") and target.startswith("v2025.") and row["status"] != "removal":
                decision = earc_decisions.get(target, {}).get(identifier, {})
                if decision.get("decision") == "accepted":
                    review["earc_status"] = "accepted"
                    review["earc_url"] = decision["source_url"]
                elif decision or identifier in bundles[target][1].get("pending_earc", []):
                    review["earc_status"] = "review"
            membership_reviews.setdefault(f"{source}/{target}", {})[identifier] = review
    catalog = {"active_release": active, "releases": releases, "pairs": pairs,
               "latest_by_year": latest_by_year, "membership_reviews": membership_reviews}
    (staging / "data/releases.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    return catalog


def write_comparison(destination, pair):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "taxonomy-changes.json").write_text(json.dumps(pair, ensure_ascii=False, indent=2) + "\n")
    with (destination / "taxonomy-changes.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["group", "change", "side", "avibase_id", "english_name", "scientific_name", "order", "family", "family_english_name"])
        for group in pair["groups"]:
            for side in ["old", "new"]:
                for row in group[side]:
                    writer.writerow([group["id"], group["relationship"], side, row["id"], row["english"], row["scientific"], row["order"], row["family"], row["family_english"]])
