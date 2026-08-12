# Release pipeline

This document describes the operational definition that makes the release reproducible, following the [checklist policy](policy.md) with:

```python
uv run python scripts/build_release.py config/release.toml
```

The release ID and directory name are identical and are derived as `<ebd_version>.<release_revision>`, for example `2026-06.0`.

## Inputs

Defined in `config/release.toml`:

| Source | Version | Configuration key | Format and location |
| --- | --- | --- | --- |
| eBird Basic Dataset for Kenya | `YYYY-MM` | `ebd_version`, `ebd_path` | Zipped tab-separated EBD under `data/ebird/` |
| Clements/eBird taxonomy | Taxonomy year | `ebird_taxonomy_version`, `ebird_taxonomy_path` | CSV with `TAXON_CONCEPT_ID`, `SPECIES_CODE`, and `REPORT_AS` under `data/ebird/` |
| AviList | Pinned release | `avilist_version`, `avilist_path` | Extended AviList workbook under `data/avilist/` |
| Project categories | Repository revision | `categories_path` | CSV keyed by `avilist_id` under `data/curation/` |
| Crosswalk overrides | Repository revision | `ebird_avilist_overrides_path` | Explicit eBird-code to AviList-species mappings under `data/curation/` |
| Exotic-code corrections | EBD release | `ebird_exotic_overrides_path` | Version-scoped corrections keyed by EBD version, source taxon-concept ID, and original exotic code |
| Sensitive species | Repository revision | `sensitive_species_path` | CSV keyed by `avilist_id`, with rationale and reference under `data/curation/` |

## Pipeline

### 1. Derive `REPORTED_SPECIES_CODE`

Match each EBD `TAXON CONCEPT ID` exactly to eBird taxonomy `TAXON_CONCEPT_ID`. Assign the matched taxonomy `SPECIES_CODE`, then set `REPORTED_SPECIES_CODE` to `REPORT_AS` when present or otherwise to `SPECIES_CODE`. Scientific names are retained for traceability and are not mapping keys.

Every EBD taxon-concept ID must occur exactly once in the matching taxonomy and its category must agree. A missing ID, category mismatch, or missing reportable code indicates incompatible source versions. The build writes a local diagnostic under `data/ebird/derived/` and stops without producing a release.

### 2. Compact the EBD

Read the observation-level EBD `EXOTIC CODE`, preserving both the source value and any effective value from the version-scoped correction table. Group observations by `TAXON CONCEPT ID + CATEGORY + SCIENTIFIC NAME + SUBSPECIES SCIENTIFIC NAME + REPORTED_SPECIES_CODE + source EXOTIC CODE + effective EXOTIC CODE`. For every group, retain the original EBD row total as `record_count`, calculate `observations` as spatial clusters within three calendar months and 3 km, and retain its five newest observation rows. Keeping the exotic code in the key prevents observations with different statuses from being irreversibly merged.

The compact tables are a local development cache under `data/ebird/derived/`. Cache metadata contains the EBD checksum, eBird taxonomy checksum, exotic-correction checksum, and compaction schema version. The build reuses the cache only when all inputs still match; `--force-compaction` rebuilds it explicitly.

An applied exotic-code correction produces a build warning and an audit containing the affected EBD version, source and corrected codes, record count, and rationale. Corrections never modify the raw EBD.

### 3. Route taxonomy evidence

Use the effective observation-level exotic code when routing evidence:

| EBD taxon type | Native, `N`, or `P` | `X` |
| --- | --- | --- |
| `species`, `issf`, or `form` with `REPORT_AS` | Reportable-species evidence | Taxonomic-entity stream |
| `domestic` with `REPORT_AS` | Reportable-species evidence only for `N` or `P` | Taxonomic-entity stream |
| `hybrid`, unreported `form`, and other retained non-species entities | Taxonomic-entity stream | Taxonomic-entity stream |

`N` means Naturalized, `P` Provisional, and `X` Escapee. Hybrids and other non-species units do not become checklist species merely because they carry `N` or `P`. Aggregate unsupported groups by category and scientific name into `audit/excluded_non_species_observations.csv`.

### 4. Re-create reportable-species evidence

Group supported compact rows by `REPORTED_SPECIES_CODE`. Sum `record_count` and `observations` and calculate the first and last observation dates across contributing compact groups; Escapee rows never contribute. Retain the contributing source Avibase IDs and the five newest qualifying observation rows.

Derive the regional checklist status using eBird's precedence: Native, Naturalized, Provisional, Escapee. The main checklist can contain Native, Naturalized, and Provisional species. Escapee-only species remain in the taxonomic-entity output and do not count toward the checklist total.

### 5. Join reportable species to AviList

Apply `data/curation/ebird_avilist_overrides.csv` first, then match all remaining `REPORTED_SPECIES_CODE` values exactly to AviList `Species_code_Cornell_Lab`. Each override must point to an AviList species and records a documented, versioned taxonomy-alignment decision. The build never infers a species by promoting an AviList subspecies to its parent. Codes not resolved by either route go to `audit/ebd_taxa_not_in_avilist.csv`.

### 6. Add curated sensitive species

Join `data/curation/sensitive_species.csv` to AviList by `avilist_id`. When a curated sensitive species already has qualifying EBD evidence, retain its EBD membership and mark it `sensitive=TRUE`. When it is absent from the EBD, add the AviList species with `membership_source=curated_sensitive_species` and `sensitive=TRUE`.

For a sensitive species added through curation, populate taxonomy, names, and the eBird species code from the pinned AviList release. Leave `source_avibase_ids`, observation count, and first/last dates blank: absence of publishable EBD rows is not evidence of zero observations. Write every curated entry and its membership route to `audit/sensitive_species.csv`.

### 7. Generate the release tables

`checklist.csv` contains one row per resolved AviList species:

| Columns | Origin |
| --- | --- |
| `sequence`, `avilist_id`, `order`, `family`, `family_english_name`, `scientific_name`, `english_name` | AviList |
| `ebird_species_code` | Reportable eBird species code or codes folded into the row |
| `source_avibase_ids` | EBD `TAXON CONCEPT ID` values contributing evidence |
| `membership_source` | `ebd` or `curated_sensitive_species` |
| `sensitive` | `TRUE` for entries in the curated sensitive-species table; otherwise `FALSE` |
| `exotic_status` | Derived regional status: `native`, `naturalized`, or `provisional` |
| `observations`, `first_observation_date`, `last_observation_date` | Reports clustered within three calendar months and 3 km; blank for curated sensitive species without EBD rows |
| Additional category columns | Project `categories.csv`, joined by `avilist_id`, plus derived `HIST`, `RAR`, and `water_bird` |

`HIST` is `TRUE` when the latest qualifying Kenyan eBird record predates the configured release reference date by more than 50 years. `RAR` is `TRUE` when the release contains fewer than five derived observations for the species; an observation clusters eBird reports within three calendar months and 3 km. It is a review aid, not a conservation assessment. `water_bird` is `TRUE` when the AviList family is one of the 33 families covered by the Ramsar Convention's [Waterbird Population Estimates scope](https://www.ramsar.org/sites/default/files/2024-03/SC63_20_waterbird_population_estimates_e.pdf), otherwise `FALSE`. None of these derived fields is maintained in `categories.csv`.

The local compact summary retains both `record_count` (original EBD row count) and `observations` (the derived spatial estimate). The public `checklist.csv` contains only `observations`; raw record counts remain in local derived tables and the manifest for provenance.

`latest_records.csv` contains at most five rows per `avilist_id` with:

| Column | EBD origin |
| --- | --- |
| `avilist_id` | Resolved AviList species key |
| `sampling_event_identifier` | `SAMPLING EVENT IDENTIFIER` |
| `source_taxon_concept_id` | `TAXON CONCEPT ID` |
| `exotic_code` | Effective observation-level EBD exotic code |
| `global_unique_identifier` | `GLOBAL UNIQUE IDENTIFIER` |
| `observation_date` | `OBSERVATION DATE` |
| `observation_count` | `OBSERVATION COUNT` |

`supplementary_taxa.csv` retains Escapee observations and requested non-species taxa with equivalent observation summary fields. Its grain is `source_taxon_concept_id + exotic_status`; it uses the pinned eBird taxonomy for sequence, hierarchy, and names and deliberately has no `avilist_id`. A species may therefore occur in the main checklist from qualifying observations and in this table from its Escapee observations. Its companion, `supplementary_taxa_latest_records.csv`, contains at most five rows per taxon-status group.

Checklist and species comments are retained only in the ignored local derived data. They are not included in the release table.

### 8. Validation

Run the validators after the release tables:

```sh
uv run python tests/validate_release.py dist/<release-id>
uv run python scripts/build_ipt_checklist.py publication/publication.toml
uv run python tests/validate_ipt_checklist.py dist/<release-id>/gbif
```

The release validator checks the generated tables, audit counts, manifest counts, identifiers,
observation summaries, status values, curated sensitive-species rows, and latest-record limits. The
IPT validator checks the Darwin Core Taxon checklist, taxon identifiers, Kenya coverage, accepted-species
status, and metadata record count.

### 9. Stage public website assets

After validation, stage the small public subset needed by GitHub Pages:

```sh
uv run python scripts/stage_release_assets.py
```

This writes `release-assets/<release-id>/` with the manifest, checklist CSV and PDF, and taxonomy-comparison JSON, CSV, and PDF. These files are committed with the release branch; raw source data, audit files, and `dist/` remain local.


## EBD reference metadata


| EBD column | Use in this project |
| --- | --- |
| `GLOBAL UNIQUE IDENTIFIER` | Retained-record identity; not used for taxonomy mapping. |
| `SAMPLING EVENT IDENTIFIER` | Checklist reference in the retained-record table. |
| `CATEGORY` | Determines species/ISSF evidence and exclusions. |
| `EXOTIC CODE` | Observation-level Native/blank, Naturalized (`N`), Provisional (`P`), or Escapee (`X`) routing and status. |
| `TAXON CONCEPT ID` | Sole join key from EBD to the matching eBird taxonomy. |
| `COMMON NAME` | Not used. |
| `SCIENTIFIC NAME` | Compaction identity and traceability only. |
| `SUBSPECIES SCIENTIFIC NAME` | Compaction identity and traceability only. |
| `OBSERVATION DATE` | Latest-record selection and first/last dates. |
| `OBSERVATION COUNT` | Retained as supplied for the newest-record table; it is not the EBD row count. |
| `CHECKLIST COMMENTS`, `SPECIES COMMENTS` | Retained locally only and not published. |
