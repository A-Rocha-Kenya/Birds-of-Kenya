# Pinned eBird sources

The v2026.1 draft uses the licensed `ebd_KE_smp_relSep-2026.zip` and awaits the official eBird 2026 taxonomy CSV. Configuration has one taxonomy input: `ebird_taxonomy_path = "data/ebird/eBird_taxonomy_v2026.csv"`. Place the official file there when released; update the exact filename if needed. The names/translations workbook and CSV extracted from it are not source taxonomy inputs.

The September archive contains 4,948,157 observation rows plus a companion sampling-event file. The reader selects the observation file. A source scan matched the observed IDs and categories against the older eBird 2025 taxonomy, so compatibility with the official 2026 CSV must be checked before building. If IDs or categories disagree, the existing build writes a mismatch audit and stops. Do not bypass this check by introducing a second taxonomy or inferring identifications from names.

The June EBD and eBird 2025 source CSV remain local historical inputs. The experimental names-workbook-derived CSV and provisional v2026.1 outputs have been moved under ignored `tmp/provisional-taxonomy-workaround/`; they are not release assets. The official 2026 file remains missing at the configured path.

`derived/` is the checksum-controlled compaction cache. Replacing the source taxonomy invalidates its cache checksum. When the official CSV is available and compatible, run the documented build and validations, review curated eBird-to-AviList mappings, and generate new public assets. The September source still contains the Rock Dove and Rose-ringed Parakeet coding issues; the version-scoped corrections remain in `data/curation/ebird_exotic_overrides.csv`.
