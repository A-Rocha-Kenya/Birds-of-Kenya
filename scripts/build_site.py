#!/usr/bin/env python3
"""Assemble the GitHub Pages website from maintained source and one release bundle."""

import argparse
import csv
import html
import hashlib
import json
import re
import shutil
import tempfile
import tomllib
from pathlib import Path

from site_archive import load_archive, export_archive, format_family_label, load_concept_relationships


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
PUBLICATION = ROOT / "publication" / "publication.toml"
EARC_DECISIONS = ROOT / "data" / "curation" / "earc_decisions.csv"
HIDDEN_CATEGORY_GROUPS = {"Regular movement", "Regional visitors", "Regional vagrants"}
HIDDEN_CATEGORY_CODES = {"E", "ES"}
ORDER_NAMES = ROOT / "data" / "curation" / "order_english_names.csv"
# Pinned commit so illustrations cannot change under a published release.
STICKER_CDN = "https://cdn.jsdelivr.net/gh/alchaincyf/huashu-bird-sticker@01264126448bd3d5d3bf69102abbfe98d9e3b489/"
STICKER_CREDIT = {
    "name": "huashu-bird-sticker",
    "url": "https://github.com/alchaincyf/huashu-bird-sticker",
    "licence": "CC BY 4.0",
    "licence_url": "https://creativecommons.org/licenses/by/4.0/",
    "note": "AI-generated illustrations, not verified by experts.",
}
# Website-only rarity classes from the release's clustered eBird observations. "Very rare" matches the
# release RAR threshold (fewer than five observations). This reflects how often a species is recorded,
# not its population size or conservation status.
RARITY_CLASSES = [
    {"id": "very-rare", "label": "Very rare", "min": 0, "max": 4},
    {"id": "rare", "label": "Rare", "min": 5, "max": 49},
    {"id": "scarce", "label": "Scarce", "min": 50, "max": 299},
    {"id": "common", "label": "Common", "min": 300, "max": 1999},
    {"id": "very-common", "label": "Very common", "min": 2000, "max": None},
]
POLICY_CONTENT_MARKER = "<!-- POLICY_CONTENT -->"
INLINE_MARKDOWN = re.compile(r"(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)")


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require(path):
    if not path.exists():
        raise ValueError(f"required site input is missing: {path}")
    return path


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_inline_markdown(text):
    rendered = []
    position = 0
    for match in INLINE_MARKDOWN.finditer(text):
        rendered.append(html.escape(text[position:match.start()]))
        token = match.group()
        link = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", token)
        if link:
            rendered.append(f'<a href="{html.escape(link.group(2), quote=True)}">{html.escape(link.group(1))}</a>')
        elif token.startswith("**"):
            rendered.append(f"<strong>{render_inline_markdown(token[2:-2])}</strong>")
        elif token.startswith("`"):
            rendered.append(f"<code>{html.escape(token[1:-1])}</code>")
        else:
            rendered.append(f"<em>{render_inline_markdown(token[1:-1])}</em>")
        position = match.end()
    rendered.append(html.escape(text[position:]))
    return "".join(rendered)


def render_policy(markdown):
    rendered = []
    paragraph = []

    def flush_paragraph():
        if paragraph:
            rendered.append(f"<p>{render_inline_markdown(' '.join(paragraph))}</p>")
            paragraph.clear()

    for line in markdown.splitlines():
        if line.startswith("#"):
            flush_paragraph()
            level = len(line) - len(line.lstrip("#"))
            if level > 1:
                rendered.append(f"<h{level}>{render_inline_markdown(line[level:].strip())}</h{level}>")
        elif line.strip():
            paragraph.append(line.strip())
        else:
            flush_paragraph()
    flush_paragraph()
    return "\n".join(rendered)


def annotate_earc(comparison, decision_rows):
    decisions_by_taxon = {}
    for decision in decision_rows:
        public_decision = {
            "decision_id": decision["decision_id"],
            "decision": decision["decision"],
            "report_year": decision["report_year_published"],
            "source_url": decision["source_url"],
            "reference": decision["reference"],
        }
        decisions_by_taxon.setdefault(decision["avibase_id"].strip(), []).append(public_decision)

    for group in comparison["groups"]:
        if "pending_earc" in group:
            continue
        taxon_ids = {row["id"] for side in ("old", "new") for row in group[side]}
        decisions = [decision for identifier in taxon_ids for decision in decisions_by_taxon.get(identifier, [])]
        group["earc_decisions"] = sorted(decisions, key=lambda decision: decision["decision_id"])
        group["pending_earc"] = group["cardinality"] in {"0:1", "1:0"} and not decisions
    return comparison


def public_metadata(metadata, manifest, rows, comparison, downloads):
    gbif_doi = metadata["gbif"]["doi"].strip()
    citation = metadata["document"]["recommended_citation"].strip()
    return {
        "release": {
            "id": manifest["release_id"],
            "year": manifest["release_id"][1:5],
            "label": metadata["document"]["version_label"],
            "publication_date": metadata["document"]["publication_date"],
            "status": metadata["status"],
        },
        "counts": {
            "species": f"{len(rows):,}",
            "families": f"{len({row['family'] for row in rows}):,}",
            "sensitive_species": f"{manifest['counts']['curated_sensitive_species']:,}",
        },
        "sources": {
            "avilist": f"AviList {manifest['avilist_version']}",
            "ebird_taxonomy": f"eBird taxonomy {manifest['ebird_taxonomy_version']}",
            "ebd": manifest["ebd_version"],
        },
        "publication": {
            "title": metadata["document"]["title"],
            "citation": citation or "Formal publication metadata is being prepared.",
            "publisher": metadata["publisher"]["name"],
        },
        "contributors": [
            {
                "name": credit["name"],
                "roles": credit["roles"],
                "affiliations": credit.get("affiliations", []),
                "orcid": credit["orcid"],
            }
            for credit in metadata["editorial"]["credits"]
            if credit["type"] == "person"
        ],
        "gbif": {
            "dataset_url": metadata["gbif"]["dataset_url"].strip(),
            "doi": gbif_doi,
            "doi_url": f"https://doi.org/{gbif_doi}" if gbif_doi else "",
        },
        "comparison": {
            "from_release": comparison["from_release"],
            "to_release": comparison["to_release"],
            "relationship_counts": comparison["relationship_counts"],
        },
        "downloads": downloads,
    }


def taxonomy_tree(rows, release_id):
    """Group checklist rows into AviList order > family > species, in checklist sequence."""
    # English order names are copied from AviList; styled like the family labels on the site.
    order_names = {row["order"]: format_family_label(row["english_name"]) for row in read_csv(require(ORDER_NAMES))}
    missing = sorted({row["order"] for row in rows} - set(order_names))
    if missing:
        raise ValueError(f"orders missing an English name in {ORDER_NAMES.name}: {', '.join(missing)}")

    def rarity(row):
        if row["sensitive"] == "TRUE" or row["observations"] == "":
            return "not-assessed"
        count = int(row["observations"])
        return next(item["id"] for item in RARITY_CLASSES if count >= item["min"] and (item["max"] is None or count <= item["max"]))

    def representative(species):
        # The most observed species stands for its group; sensitive species carry no evidence.
        return max(species, key=lambda item: item["observations"])["id"]

    orders = {}
    for row in sorted(rows, key=lambda item: int(item["sequence"])):
        order = orders.setdefault(row["order"], {
            "order": row["order"], "english_name": order_names[row["order"]], "families": {},
        })
        family = order["families"].setdefault(row["family"], {
            "family": row["family"], "english_name": row["family_english_name"], "species": [],
        })
        family["species"].append({
            "id": row["avibase_id"],
            "english_name": row["english_name"],
            "scientific_name": row["scientific_name"],
            "sticker": f"stickers/{row['order']}/{row['family']}/{row['scientific_name'].replace(' ', '_')}.webp",
            "rarity": rarity(row),
            "iucn": row["iucn_red_list_category"],
            "naturalized": row["exotic_status"] == "naturalized",
            "pending_earc": row["pending_earc"] == "TRUE",
            "historical": row.get("HIST") == "TRUE",
            "rare": row.get("RAR") == "TRUE",
            "waterbird": row.get("water_bird") == "TRUE",
            "sensitive": row["sensitive"] == "TRUE",
            "observations": int(row["observations"] or 0) if row["sensitive"] != "TRUE" else 0,
            "first_observation": row["first_observation_date"],
            "last_observation": row["last_observation_date"],
            "earc_decision": row["earc_decision"],
            "taxonomy_comment": row["taxonomy_comment"],
            "birds_of_the_world_url": row["birds_of_the_world_url"],
            "birdlife_datazone_url": row["birdlife_datazone_url"],
        })

    tree = []
    for order in orders.values():
        families = list(order["families"].values())
        for family in families:
            family["representative"] = representative(family["species"])
        tree.append({**order, "families": families,
                     "representative": representative([s for f in families for s in f["species"]])})
    return {
        "release_id": release_id,
        "sticker_cdn": STICKER_CDN,
        "sticker_credit": STICKER_CREDIT,
        "rarity_classes": RARITY_CLASSES,
        "counts": {
            "orders": len(tree),
            "families": sum(len(order["families"]) for order in tree),
            "species": len(rows),
        },
        "orders": tree,
    }


PHYLOGENY = ROOT / "data" / "phylogeny"


def parse_newick(text):
    """Parse a Newick tree into nested [branch_length, label] leaves and [branch_length, children] clades."""
    text = text.strip().rstrip(";")
    position = 0

    def node():
        nonlocal position
        children = None
        if text[position] == "(":
            position += 1
            children = [node()]
            while text[position] == ",":
                position += 1
                children.append(node())
            if text[position] != ")":
                raise ValueError(f"malformed Newick tree near character {position}")
            position += 1
        label = re.match(r"[^:,()]*", text[position:]).group()
        position += len(label)
        length = 0.0
        if position < len(text) and text[position] == ":":
            number = re.match(r":([0-9.eE+-]+)", text[position:]).group(1)
            position += len(number) + 1
            length = float(number)
        return [length, children if children is not None else label]

    return node()


def phylogeny_tree(rows):
    """Dated tree of the release's species from clootl, with tips renamed to Avibase IDs."""
    source = json.loads(require(PHYLOGENY / "source.json").read_text())
    tips = {row["tip"]: row["avibase_id"] for row in read_csv(require(PHYLOGENY / "tips.csv"))}
    tree = parse_newick(require(PHYLOGENY / "kenya.tre").read_text())
    seen = []

    def convert(node):
        length, content = node
        if isinstance(content, list):
            return [round(length, 3), [convert(child) for child in content]]
        seen.append(tips[content])
        return [round(length, 3), tips[content]]

    tree = convert(tree)
    expected = {row["avibase_id"] for row in rows}
    if len(seen) != len(set(seen)) or set(seen) != expected:
        missing = sorted(expected - set(seen))
        raise ValueError(
            f"data/phylogeny does not match the active release ({len(missing)} species missing); "
            "rerun `Rscript scripts/build_phylogeny.R`"
        )
    return {**source, "tree": tree}


def validate_publication(metadata, allow_draft):
    if metadata["status"] != "draft":
        required = {
            "publication date": metadata["document"]["publication_date"],
            "recommended citation": metadata["document"]["recommended_citation"],
            "publisher": metadata["publisher"]["name"],
        }
        missing = [label for label, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"published website metadata is incomplete: {', '.join(missing)}")
    elif not allow_draft:
        raise ValueError("publication metadata is still draft; pass --allow-draft for a preview build")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    parser.add_argument("--preview-release", help="explicitly include and activate this draft in the generated site")
    args = parser.parse_args()
    identifier, bundles = load_archive(ROOT, args.preview_release)
    release, descriptor = bundles[identifier]
    metadata = descriptor["publication"]
    manifest = json.loads((release / "manifest.json").read_text())
    checklist = require(release / "checklist.csv")
    policy = require(release / "policy.md")
    rows = read_csv(checklist)
    all_category_definitions = read_csv(require(release / "category_definitions.csv"))
    category_definitions = [
        definition for definition in all_category_definitions
        if definition["display_group"] not in HIDDEN_CATEGORY_GROUPS
        and definition["code"] not in HIDDEN_CATEGORY_CODES
    ]
    hidden_category_codes = {
        definition["code"] for definition in all_category_definitions
        if definition["display_group"] in HIDDEN_CATEGORY_GROUPS
        or definition["code"] in HIDDEN_CATEGORY_CODES
    }
    public_rows = [{field: value for field, value in row.items() if field not in hidden_category_codes} for row in rows]
    public_fields = [field for field in rows[0] if field not in hidden_category_codes]
    for row in public_rows:
        row["family_english_name"] = format_family_label(row["family_english_name"])
        row["pending_earc"] = "TRUE" if row["avibase_id"] in descriptor["pending_earc"] else ""
    public_fields.append("pending_earc")
    downloads = {"checklist_pdf": f"downloads/{identifier}/{descriptor['pdf']}",
                 "checklist_csv": f"downloads/{identifier}/checklist.csv"}
    prior = list(bundles)[max(0, list(bundles).index(identifier) - 1)]
    comparison = {"from_release": prior, "to_release": identifier, "relationship_counts": {}}
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="birds-of-kenya-site-", dir=output.parent) as temporary:
        staging = Path(temporary) / "site"
        shutil.copytree(WEBSITE, staging)
        replacements = {
            "{{RELEASE_ID}}": metadata["release_id"],
            "{{CHECKLIST_YEAR}}": identifier[1:5],
            "{{PUBLICATION_YEAR}}": metadata["document"]["publication_date"][:4],
            "{{FROM_YEAR}}": comparison["from_release"][1:5],
        }
        for page in staging.rglob("*.html"):
            content = page.read_text(encoding="utf-8")
            for marker, value in replacements.items():
                content = content.replace(marker, html.escape(value))
            page.write_text(content, encoding="utf-8")
        policy_page = staging / "policy" / "index.html"
        policy_template = policy_page.read_text(encoding="utf-8")
        if POLICY_CONTENT_MARKER not in policy_template:
            raise ValueError("website policy page is missing its content marker")
        policy_page.write_text(
            policy_template.replace(POLICY_CONTENT_MARKER, render_policy(policy.read_text(encoding="utf-8"))),
            encoding="utf-8",
        )
        write_csv(staging / "data" / "checklist.csv", public_fields, public_rows)
        (staging / "data" / "category-definitions.json").write_text(
            json.dumps(category_definitions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (staging / "data" / "taxonomy.json").write_text(
            json.dumps(taxonomy_tree(public_rows, identifier), ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        (staging / "data" / "phylogeny.json").write_text(
            json.dumps(phylogeny_tree(public_rows), ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
        )
        copy(PHYLOGENY / "citations.csv", staging / "data" / "phylogeny-citations.csv")
        copy(release / "manifest.json", staging / "data" / "manifest.json")
        catalog = export_archive(staging, identifier, bundles, load_concept_relationships(ROOT))
        site_metadata = public_metadata(metadata, manifest, rows, comparison, downloads)
        (staging / "data" / "site.json").write_text(
            json.dumps(site_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        for page in staging.rglob("*.html"):
            def fingerprint(match):
                attribute, url = match.groups()
                asset = page.parent / url
                if url.startswith(("https://", "http://")) or not asset.is_file():
                    return match.group(0)
                digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:16]
                return f'{attribute}="{url}?v={digest}"'
            page.write_text(re.sub(r'(src|href)="([^"?]+\.(?:js|css))(?:\?[^\"]*)?"', fingerprint, page.read_text()), encoding="utf-8")
        (staging / ".nojekyll").touch()
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(staging, output)

    print(f"Built {output} for {identifier}: {len(rows):,} species, {len(bundles)} archived versions")


if __name__ == "__main__":
    main()
