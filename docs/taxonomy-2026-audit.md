# 2026 taxonomy audit

The v2026.0 draft uses AviList v2026 and the official `eBird_Taxonomy_v2026-october-2026.csv`, supplied on 3 November 2026. There is one eBird taxonomy input. The names workbook, API and integrated checklist are not used to construct or supplement it.

The official file has 18,631 unique, nonblank Avibase concept IDs. Its lowercase column names are normalized on read; the original file and hash remain pinned in the manifest. `sparse_report_as` supplies parent pointers. The self-codes in `report_as` do not establish a species identification.

The September 2026 Kenya EBD contains 4,948,157 observation rows and four source concept/category combinations requiring explicit treatment. The maintained table is `data/curation/ebird_taxon_corrections.csv`; every entry is scoped to EBD 2026-09 and audited by affected record count.

| Source concept | Source category | Official target | Treatment | Records |
| --- | --- | --- | --- | ---: |
| `avibase-EE8206E7` | species | Same ID, slash | Broad Spotted/Mediterranean Flycatcher remains unidentified | 8,174 |
| `avibase-B142856F` | issf | Same ID, species | Identified striata-group records support Spotted Flycatcher | 44 |
| `avibase-D209A90C` | species | `avibase-4D28A0CD` | Old Little Swift falls within the 2026 Little/House Swift lump | 28,424 |
| `avibase-4E923B31` | species | `avibase-EB9CE6A2` | Explicit Kenyan Rufous-naped assignment; Athi was already separate, while the other split descendants have AviList ranges outside Kenya | 6,235 |

The Rufous-naped treatment is a regional assignment, not global synonymy. Original source IDs are retained in the evidence, including retired IDs. Current eBird species links are checked against the official taxonomy and AviList IDs, allowing only the maintained eBird-to-AviList exceptions. Unlisted ID/category discrepancies remain build failures. No records are assigned to descendants by scientific-name matching, guessed identification or proportions.

The historical lark crosswalk associates Athi Lark with the Rufous-naped complex; the old Red-winged entry is not an ancestor of Athi Lark. The release comparison separately documents the changed Little Swift and Spotted Flycatcher concepts. Those display links do not control evidence routing. Published v2025.0 assets remain unchanged.

Reproduce the source and correction checks with `uv run python tests/validate_ebird_taxonomy.py`; run `tests/validate_release_pipeline.py` and `tests/validate_release.py dist/v2026.0` for the complete release checks. The optional cross-project audit additionally requires the sibling atlas-comparison and digitization repositories, which are absent from this workspace.
