"""Compare frozen taxonomies through reviewed, version-specific concept links."""

from collections import defaultdict, Counter

FIELDS = ("english", "scientific", "order", "family", "family_english")


def snapshot(rows):
    if rows and "avibaseid" in rows[0]:
        counts = Counter(r["avibaseid"] for r in rows)
        rows = [r for r in rows if r["avibaseid"].startswith("avibase-") and counts[r["avibaseid"]] == 1]
        rows = [{"avibase_id": r["avibaseid"], "sequence": r["sort"], "english_name": r["common_name"],
                 "scientific_name": r["scientific_name"], "family": r["family_scientific"],
                 "family_english_name": r["family_english"], "order": ""} for r in rows]
    return [{"id": r["avibase_id"], "sequence": float(r["sequence"]),
             **{field: r.get(source, "") for field, source in zip(FIELDS, (
                 "english_name", "scientific_name", "order", "family", "family_english_name"))}}
            for r in rows]


def compare_versions(versions, transitions, source, target):
    """Compose lineage through intervening snapshots; never infer links from names."""
    ids = list(versions)
    start, end = sorted((ids.index(source), ids.index(target)))
    relevant = ids[start:end + 1]
    graph = defaultdict(set)

    def link(a, b):
        graph[a].add(b)
        graph[b].add(a)

    for left, right in zip(relevant, relevant[1:]):
        shared = {r["id"] for r in versions[left]} & {r["id"] for r in versions[right]}
        for identifier in shared:
            link((left, identifier), (right, identifier))
    for transition in transitions:
        left, right = transition["from_release"], transition["to_release"]
        if left in relevant and right in relevant:
            for edge in transition["links"]:
                if edge["old_id"] in {r["id"] for r in versions[left]} and edge["new_id"] in {r["id"] for r in versions[right]}:
                    link((left, edge["old_id"]), (right, edge["new_id"]))
    old = {r["id"]: r for r in versions[source]}
    new = {r["id"]: r for r in versions[target]}
    for identifier in old.keys() & new.keys():
        link((source, identifier), (target, identifier))
    seen, groups, linked_old, linked_new = set(), [], set(), set()
    for identifier in old:
        node = (source, identifier)
        if node in seen:
            continue
        pending, component = [node], set()
        while pending:
            node = pending.pop()
            if node in component:
                continue
            component.add(node)
            pending.extend(graph[node] - component)
        seen.update(component)
        before = [old[i] for v, i in component if v == source and i in old]
        after = [new[i] for v, i in component if v == target and i in new]
        if not before or not after:
            continue
        before.sort(key=lambda r: (r["sequence"], r["id"]))
        after.sort(key=lambda r: (r["sequence"], r["id"]))
        linked_old.update(r["id"] for r in before)
        linked_new.update(r["id"] for r in after)
        changed = [f for f in FIELDS if f != "family_english" and all(r[f] for r in before + after) and {" ".join(r[f].split()).casefold() for r in before} != {" ".join(r[f].split()).casefold() for r in after}]
        concept = {r["id"] for r in before} != {r["id"] for r in after}
        if not changed and not concept:
            continue
        cardinality = f'{"1" if len(before) == 1 else "n"}:{"1" if len(after) == 1 else "n"}'
        groups.append({"id": f'change-{identifier}', "title": " / ".join(r["english"] for r in after),
                       "old": before, "new": after, "tags": changed,
                       "cardinality": cardinality, "concept_changed": concept,
                       "relationship": "taxonomy_changed",
                       "relationship_label": "Linked concepts" if concept else "Taxonomy/name changed",
                       "sort_order": after[0]["sequence"], "order": after[0]["order"],
                       "family": after[0]["family"], "family_english": after[0]["family_english"]})
    for relationship, rows, matched in [("added", new, linked_new), ("removed", old, linked_old)]:
        for identifier in rows.keys() - matched:
            row = rows[identifier]
            groups.append({"id": f"{relationship}-{identifier}", "title": row["english"],
                           "old": [row] if relationship == "removed" else [],
                           "new": [row] if relationship == "added" else [],
                           "tags": [], "concept_changed": False,
                           "cardinality": "0:1" if relationship == "added" else "1:0",
                           "relationship": relationship,
                           "relationship_label": "Added species" if relationship == "added" else "Removed species",
                           "sort_order": row["sequence"], "order": row["order"],
                           "family": row["family"], "family_english": row["family_english"]})
    groups.sort(key=lambda g: (g["sort_order"], g["id"]))
    return {"from_release": source, "to_release": target, "group_count": len(groups), "groups": groups,
            "unlinked_old": len(old.keys() - linked_old), "unlinked_new": len(new.keys() - linked_new)}
