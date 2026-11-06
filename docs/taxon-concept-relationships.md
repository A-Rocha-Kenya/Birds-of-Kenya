# Taxon concept relationships

The [shared curation table](../data/curation/taxon_concept_relationships.csv) records relationships between Avibase concepts once. Each archived checklist supplies the concepts that edition uses. The website and command-line comparison project the shared relationships onto the selected editions.

The table uses terms from the [TDWG Taxon Concept Standard](https://tcs.tdwg.org/terms/), based on RCC-5 set relationships. Each row records `subject_id`, `relationship`, `object_id` and `source_url`. Use `includes` from a strictly broader concept to a narrower one. The reverse direction is implicit. Use `isCongruentWith` for concepts with the same scope, `partiallyOverlaps` for shared scope without containment, `intersects` when concepts share some scope but the precise relationship is unspecified, and `isDisjointFrom` to record a reviewed exclusion. An absent relationship means unknown.

The comparison follows chains of inclusion in one direction, with congruence usable in either direction. Direct partial overlaps and intersections are shown as links and do not imply links to other concepts. Disjointness is recorded as evidence and does not produce a link. Concepts with a shared broader parent do not become matches merely through that parent. A linked group shows relationships among entries present in the chosen editions. Its counts describe those entries, and full coverage of a broader concept requires separate evidence.

The initial curation covers published concept definitions for groups including ostriches, batises, white-eyes, and reed warblers. The 2009 broad concept includes Common and Somali Ostrich. The same two assertions support the split or reverse lump for every archived edition that lists both narrower concepts. [Avibase concept](https://avibase.bsc-eoc.org/species.jsp?avibaseid=5D14080CFAE85394&lang=EN)

The website and command-line comparison match identical Avibase IDs and use this table for links between different IDs. Historical edition crosswalks and assignment corrections remain in their release records for provenance. A historical link becomes available to the comparison once its biological relationship is reviewed and added to the shared table. This means a direct comparison of a corrected edition can display a changed concept assignment. The correction records explain the editorial change.

Run `uv run python scripts/compare_releases.py v2009.0 v2019.2 --output tmp/comparison` to inspect a pair. The archive validator checks Ostrich in both directions and checks that the two narrower concepts do not match each other.

The Changes page exports the full graph as JSON. Its concept index contains every assigned ID in the selected archive, with names and membership by edition. It also carries the shared relationship table and excluded checklist rows as separate collections. An isolated node is still part of the graph. A blank or duplicate historical assignment is preserved as an excluded entry until its concept can be established.

The graph carries shared-scope links from the reviewed 2019–2025 and provisional 2025–2026 crosswalks as `intersects` where their exact boundaries were unspecified. The CSV cites the archived crosswalk for these assertions. Source-backed inclusion and disjointness are more specific where Avibase supplies the scope. Some old links may reflect a regional checklist assignment rather than global biological overlap. For example, Avibase separates Asian and African Woolly-necked Stork and Siberian and Tibetan Sand Plover. The historical broad concepts connect to their supported narrower concepts. The distinct narrower concepts stay separate.

## Review coverage

Every assigned concept is included. The remaining unlinked entries in the main edition comparisons are visible in the Changes page and its comparison CSV. These counts exclude rows without a unique Avibase ID. A count includes both possible changes in checklist membership and concepts that need a scope or assignment review.

| Comparison | Unlinked in source | Unlinked in target |
| --- | ---: | ---: |
| v2009.0 → v2019.0 | 15 | 69 |
| v2019.0 → v2019.1 | 3 | 17 |
| v2019.1 → v2019.2 | 0 | 0 |
| v2009.0 → v2019.2 | 2 | 68 |
| v2019.2 → v2025.0 | 5 | 24 |
| v2025.0 → v2026.0 preview | 0 | 1 |

Review an unlinked entry against the original checklist and Avibase concept definitions before adding an assertion. A confirmed addition or removal does not require a taxonomic edge. An incorrect printed-entry assignment belongs in the checklist's correction record.

The two assigned 2009 entries with no link to v2019.2 are Matsudaira’s Storm-petrel and Brown-headed Apalis. Neither has a printed entry in the 2019 transcription. Of the five older unlinked entries in v2019.2 → v2025.0, the stork and sand plover need edition assignment review. The hybrid lovebird, Speckled Tinkerbird and Great Grey Shrike concepts have no corresponding supported entry in the v2025.0 species snapshot. The 49 unassigned 2009 rows remain available in the source checklist and its unresolved-concept table.
