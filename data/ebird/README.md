# Pinned eBird sources

The licensed `ebd_KE_relJun-2026.zip` is interpreted using its matching `eBird_taxonomy_v2025-4.csv`. Both remain unchanged: the October 2026 taxonomy cannot replace the source taxonomy when reading this older EBD.

The current reference is Cornell's `eBird_Taxonomy_v2026_5-tab_27Oct2026.xlsx`, obtained on 31 October 2026 from the [official common-names download](https://support.ebird.org/en/support/solutions/articles/48000804865) and its [public Box file](https://cornell.box.com/s/fjp112mh25nlvbyr1p28r9ya7nriblls). Its publisher SHA-1 was `80154576a1b33c2593dd27a920bb5803e6769a5b`, verified after download. The `Sparse` tab supplies concept IDs, codes, names, categories and parent codes; translations are not needed for the build.

Run `uv run --with openpyxl python scripts/prepare_ebird_taxonomy.py` to extract `eBird_taxonomy_v2026.csv`. `sparse_report_as` supplies the actual parent pointer; the filled `report_as` field also contains self-codes and must not be treated as evidence that an unidentified form has a species parent. The raw workbook and extracted reference are local ignored inputs. Both paths and SHA-256 hashes are recorded in the release manifest.

The build matches compact source concepts to current eBird concepts by ID before deriving current reportable-species evidence. A retired ID needs a documented override; a reused code is not sufficient. A current slash remains unidentified: the 8,134 pre-split Spotted/Mediterranean Flycatcher records are retained in the source cache and exclusion/alignment audits, while the 43 records explicitly identified as the striata group support Spotted Flycatcher. No records are split between descendants by name or inferred proportions.

`derived/` remains the checksum-controlled, archived-taxonomy compaction cache. Current alignment does not modify it. `dist/v2026.0/audit/ebird_taxonomy_alignment.csv` records the route and record count of every compact source group. `scripts/check_taxonomy_coherence.py` checks current species codes against AviList, the historical atlas and the Comparison source links.
