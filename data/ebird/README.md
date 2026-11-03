# Pinned eBird sources

The active v2025.0 baseline uses `ebd_KE_relJun-2026.zip` and `eBird_taxonomy_v2025-4.csv`. Release IDs identify the taxonomic baseline; EBD months remain independent provenance. Licensed raw inputs and local compaction caches stay outside Git.

Future releases can read the official lowercase taxonomy CSV format directly (`bio_concept_code` and `sparse_report_as`) or the historical uppercase format. The source file is never modified. Explicit version-specific source corrections, if needed, are stored under that release's curation directory and audited. The v2025.0 correction table is empty; no 2026 taxonomic decisions are applied to this release.
