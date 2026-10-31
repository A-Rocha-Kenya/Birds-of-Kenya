# 2026 taxonomy preparation

The v2026.1 draft targets AviList v2026 and the official eBird 2026 taxonomy CSV. The latter is not yet available. Configuration uses only `ebird_taxonomy_path`; the names workbook, its extracted CSV, and the experimental source-to-current alignment step have been removed from the workflow.

The September 2026 Kenya EBD contains 4,948,157 observation rows. Its observed concept IDs and categories matched eBird 2025 during the source scan. The future official 2026 CSV must be checked against this EBD before release preparation can continue. Exact concept-ID/category mismatches remain build failures and are not resolved by name matching or a second taxonomy layer.

The AviList v2026 column normalization, corrected 2019 lark crosswalk, and curated category changes from the development commit remain proposed changes. The crosswalk associates Athi Lark with the historical Rufous-naped complex; the old Red-winged entry is not an ancestor of Athi Lark. Current codes, taxon concepts and evidence attribution must be revalidated using the official taxonomy CSV before publication.

The previous experimental outputs used the names workbook as a taxonomy substitute. They are retained only in ignored local `tmp/provisional-taxonomy-workaround/` and do not establish a validated v2026.1 checklist or species count. The published v2026.0 assets are restored to the tagged snapshot. See [the release preparation notes](releases/v2026.1.md).
