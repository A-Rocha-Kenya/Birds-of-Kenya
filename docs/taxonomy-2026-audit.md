# October 2026 taxonomy coherence review

The development checklist now uses AviList v2026 (20 October 2026) and the official eBird names/taxonomy workbook dated 27 October 2026. The June 2026 EBD and its matching eBird 2025 source taxonomy are retained. Configuration and manifest hashes identify both taxonomy layers. The [AviList release](https://www.avilist.org/checklist/v2026/) and [Cornell download documentation](https://support.ebird.org/en/support/solutions/articles/48000804865) identify the current references.

## Corrected mappings

| Case | Previous problem | Current treatment |
| --- | --- | --- |
| Little Swift | Retired `litswi1` and species ID `avibase-D209A90C` were used as current identifiers | Current species is `avibase-4D28A0CD`, code `y00960`, following the Little/House Swift lump; old source records join through an explicit override |
| Spotted Flycatcher | `spofly1` was treated as one current species | It is now the Spotted/Mediterranean slash; only the source striata-group concept `avibase-B142856F` supports current `spofly2` |
| Rufous-naped Lark | A reused `runlar1` string concealed a changed global concept | Source 2025 `avibase-4E923B31` uses an explicit Kenyan assignment to current `avibase-EB9CE6A2`; Athi was already separate in the 2025 source taxonomy |
| 2019 lark transition | Athi was attached to the Red-winged rather than Rufous-naped ancestor | Old `avibase-6A0D6123` maps to Rufous-naped and Athi; old `avibase-BAA83B0C` maps to Kenyan Red-winged Lark |
| Historical atlas larks | Historical concepts were narrowed to modern single species | Book pp. 306–307 support `6A0D6123` for SEQ 531 and `BAA83B0C` for SEQ 532, explicitly including Ugandan kidepoensis records in the latter |
| Swamphen and Siberian Stonechat | The AviList species has no direct Cornell species code because scope differs | The documented `purswa2` and `sibsto1` overrides remain; they also supply the missing Comparison website links |
| Comparison species pages | Retired source codes or missing aliases omitted current species links | Current member links are checked against the official eBird 2026 species category and concept ID |

The [Avibase Rufous-naped complex](https://avibase.bsc-eoc.org/species.jsp?avibaseid=6A0D6123) includes athi; the [Red-winged/Kidepo complex](https://avibase.bsc-eoc.org/species.jsp?avibaseid=BAA83B0C93850D42) does not. AviList's Corypha decision summaries and the original book scans provide the supporting source evidence. Kidepo's Ugandan atlas records do not establish national Kenyan checklist membership.

eBird calls *Corypha athi* Athi Lark; AviList calls it Sentinel Lark. The concept ID and species code agree despite the different English names.

## Observation evidence

The source cache contains 8,134 undifferentiated pre-split Spotted Flycatcher records and 43 records identified to the striata group. The former now remain in the source cache and the current exclusion/alignment audits. The latter support Spotted Flycatcher and yield 38 observations under the existing clustering definition. This is a change in taxonomic attribution, not evidence of a population decline. No broad source records are allocated among descendants by name, proportional splitting, or guessed identifications.

`audit/ebird_taxonomy_alignment.csv` records every compact source group and its current route, including explicitly curated retired concepts. `audit/comparison_ebird_codes.csv` checks the sibling Comparison associations against current eBird species and the national checklist. Historical members outside the current national checklist are labeled explicitly; a valid global species page does not establish Kenyan occurrence.

The national checklist still contains 1,148 species (1,143 native, five naturalized), with zero unmatched reportable species codes. Current eBird links resolve to species entries and agree with AviList IDs or an explicit override. The 2019 comparison now has 375 groups. The source taxonomy, observation evidence, historical groups and current website links are separate concepts and remain inspectable.

## Limits and review

This audit checks taxonomy identifiers, categories, source routes and project agreement. It does not independently validate every observation or every historical atlas circumscription. The explicit Kenyan Rufous-naped assignment remains a regional interpretation, not global taxonomic synonymy. Unidentified parent records remain unidentified. The existing KBM missing-number audit remains available; missing links are not invented by matching names.

The historical larks' existing narrower COL species IDs are retained for review with `col_publish=false`; occurrence exports retain the broader Avibase IDs and original identifications. These local changes do not update published GBIF datasets or deploy a website.

Reproduce the checks with `uv run python tests/validate_release_pipeline.py`, `uv run python tests/validate_release.py dist/v2026.0` and `uv run python scripts/check_taxonomy_coherence.py`. The last command expects the sibling Comparison and digitization repositories. Rebuild their atlas/comparison outputs before syncing KenyaBirdTrends.
