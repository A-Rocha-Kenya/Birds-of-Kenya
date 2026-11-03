#!/usr/bin/env python3
"""Release comparisons must describe taxonomy, never evidence or review state."""

import copy
import json
import sys
import tempfile
import tomllib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from taxonomy_comparison import snapshot, compare_versions
from release_archive import verify
from site_archive import load_archive


def row(identifier, **changes):
    return {"id": identifier, "sequence": 1, "english": "Example", "scientific": "Alpha beta",
            "order": "Order", "family": "Family", "family_english": "Family name", **changes}


def main():
    (ROOT / "tmp").mkdir(exist_ok=True)
    assert snapshot([{'avibaseid': '', 'sort': '1'}, {'avibaseid': 'avibase-duplicate', 'sort': '2'}, {'avibaseid': 'avibase-duplicate', 'sort': '3'}]) == []
    source = [{"avibase_id": "same", "sequence": "1", "english_name": "Example", "scientific_name": "Alpha beta", "observations": "1", "RAR": "TRUE", "earc_decision": ""}]
    target = [{**source[0], "sequence": "999", "observations": "900", "RAR": "FALSE", "earc_decision": "accepted"}]
    assert snapshot(source) != snapshot(target)  # Sequence is retained for display only.
    assert compare_versions({"a": snapshot(source), "b": snapshot(target)}, [], "a", "b")["groups"] == []
    for field in ("english", "scientific", "order", "family"):
        result = compare_versions({"a": [row("same")], "b": [row("same", **{field: "Changed"})]}, [], "a", "b")
        assert result["groups"][0]["tags"] == [field]
        original = row("same")
        cosmetic = row("same", **{field: "  " + original[field].swapcase().replace(" ", "   ") + "  "})
        assert compare_versions({"a": [original], "b": [cosmetic]}, [], "a", "b")["groups"] == []
        changed = row("same", **{field: "Changed"})
        group = compare_versions({"a": [original], "b": [changed]}, [], "a", "b")["groups"][0]
        assert group["old"][0][field] == original[field] and group["new"][0][field] == "Changed"
    assert compare_versions({"a": [row("same")], "b": [row("same", family_english="Different English family name")]}, [], "a", "b")["groups"] == []
    family_change = compare_versions({"a": [row("same")], "b": [row("same", family="Otheridae", family_english="Other family")]}, [], "a", "b")["groups"][0]
    assert family_change["tags"] == ["family"]
    assert family_change["new"][0]["family_english"] == "Other family"
    assert compare_versions({"a": [row("old")], "b": [row("new")]}, [], "a", "b")["groups"] == []
    versions = {"a": [row("parent")], "b": [row("child1"), row("child2")], "c": [row("later"), row("child2")]}
    links = [{"from_release": "a", "to_release": "b", "links": [{"old_id": "parent", "new_id": x} for x in ("child1", "child2")]},
             {"from_release": "b", "to_release": "c", "links": [{"old_id": "child1", "new_id": "later"}]}]
    assert compare_versions(versions, links, "a", "c")["groups"][0]["cardinality"] == "1:n"
    assert compare_versions(versions, links, "c", "a")["groups"][0]["cardinality"] == "n:1"
    assert compare_versions(versions, links, "a", "a")["groups"] == []
    # A lump then split is a connected lineage, not a claimed direct split of one member.
    versions = {"a": [row("a1"), row("a2")], "b": [row("lump")], "c": [row("c1"), row("c2")]}
    links = [{"from_release": "a", "to_release": "b", "links": [{"old_id": x, "new_id": "lump"} for x in ("a1", "a2")]},
             {"from_release": "b", "to_release": "c", "links": [{"old_id": "lump", "new_id": x} for x in ("c1", "c2")]}]
    assert compare_versions(versions, links, "a", "c")["groups"][0]["cardinality"] == "n:n"
    registry = tomllib.loads((ROOT / "publication/releases.toml").read_text())
    candidate = tomllib.loads((ROOT / "publication/publication.toml").read_text())["release_id"]
    active, bundles = load_archive(ROOT)
    assert active == registry["active_release"]
    assert all(d["status"] == "released" for _, d in bundles.values())
    active, preview = load_archive(ROOT, candidate)
    assert active == candidate and candidate in preview
    for path, descriptor in preview.values():
        verify(path)
        taxonomy = json.loads((path / "taxonomy.json").read_text())
        assert len(taxonomy) == len({r["id"] for r in taxonomy})
        assert not any(set(r) & {"observations", "earc_decision", "RAR", "HIST"} for r in taxonomy)
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as directory:
        directory = Path(directory)
        (directory / "publication").mkdir()
        shutil.copy2(ROOT / "publication/releases.toml", directory / "publication/releases.toml")
        shutil.copytree(ROOT / "release-assets", directory / "release-assets")
        if candidate != registry["active_release"]:
            (directory / "release-assets" / candidate / "checklist.csv").write_text("Incomplete candidate")
            assert load_archive(directory)[0] == registry["active_release"]
            try:
                load_archive(directory, candidate)
            except ValueError:
                pass
            else:
                raise AssertionError("preview accepted a corrupt candidate")
    print("Validated taxonomy-only comparison, every field, excluded membership, forward/reverse/transitive splits and lumps, same-version comparison, sealed archives and draft isolation")


if __name__ == "__main__":
    main()
