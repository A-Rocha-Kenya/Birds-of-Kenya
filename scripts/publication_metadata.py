"""Load publication metadata and an optional public-facing profile."""

import csv
import json
import tomllib
from pathlib import Path


def merge(base, overlay):
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def load(metadata_path, profile_path=None):
    metadata = tomllib.loads(Path(metadata_path).read_text(encoding="utf-8"))
    if profile_path:
        profile = tomllib.loads(Path(profile_path).read_text(encoding="utf-8"))
        merge(metadata, profile)
    return metadata


def pending_earc_ids(metadata, root, release):
    """Keep unresolved historical additions visible across successive releases."""
    if metadata["sources"].get("pending_earc"):
        with (root / metadata["sources"]["pending_earc"]).open(newline="") as handle:
            return {r["avibase_id"] for r in csv.DictReader(handle)}
    comparisons = [json.loads((release / "comparison/taxonomy-changes.json").read_text(encoding="utf-8"))]
    if metadata["sources"].get("review_baseline_comparison"):
        baseline = json.loads((root / metadata["sources"]["review_baseline_comparison"]).read_text(encoding="utf-8"))
        previous = comparisons[0]["from_release"]
        while previous != baseline["to_release"]:
            path = root / "release-assets" / previous / "comparison/taxonomy-changes.json"
            comparison = json.loads(path.read_text(encoding="utf-8"))
            comparisons.insert(0, comparison)
            previous = comparison["from_release"]
        comparisons.insert(0, baseline)
    pending = set()
    for comparison in comparisons:
        for group in comparison["groups"]:
            if group["cardinality"] == "1:0":
                pending.difference_update(row["id"] for row in group["old"])
            elif group.get("pending_earc", group["cardinality"] == "0:1"):
                pending.update(row["id"] for row in group["new"])
    with (root / "data/curation/earc_decisions.csv").open(encoding="utf-8", newline="") as handle:
        pending.difference_update(row["avibase_id"] for row in csv.DictReader(handle))
    return pending


def render_provenance(metadata, root, release, pdf):
    import hashlib
    digest = lambda data: hashlib.sha256(data).hexdigest()
    editorial = [metadata["sources"]["policy"], metadata["sources"]["category_definitions"]]
    if metadata["sources"].get("pending_earc"):
        editorial.append(metadata["sources"]["pending_earc"])
    if metadata["sources"].get("introduction"):
        editorial.append(metadata["sources"]["introduction"])
    return {"renderer_sha256": digest((root / "scripts/render_checklist_pdf.py").read_bytes()),
            "checklist_sha256": digest((release / "checklist.csv").read_bytes()),
            "publication_sha256": digest(json.dumps(metadata, sort_keys=True).encode()),
            "editorial_sha256": digest(b"".join((root / name).read_bytes() for name in editorial)),
            "pdf_sha256": digest(pdf.read_bytes())}
