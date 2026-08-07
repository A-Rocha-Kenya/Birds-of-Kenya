# Kenya AviList Checklist: design brief

## Purpose

Create an authoritative, versioned checklist of bird taxa recorded at least once in Kenya. It will use AviList as its taxonomic authority, include species and subspecies, and be maintained by the Bird Committee through its curator.

The immediate goal is to migrate the 2019 checklist to the current AviList version. This is a major curation exercise, not simply a name update: each historical record, Kenyan status, and subspecies occurrence must be reviewed against the current AviList concept.

## The intended product

The project has three clearly different layers.

| Layer | Role | Who changes it |
| --- | --- | --- |
| Core Kenya checklist | The Committee's curated list of Kenyan taxa and Kenya-specific information. It is the only project data edited as a checklist. | Bird Committee decisions, entered by the curator. |
| External reference data | A pinned AviList release and its supplied crosswalks or source attributes. It supplies taxonomy and is never manually changed by the Committee. | AviList; updated as an explicit upgrade. |
| Published releases | Website, downloadable tables, possible printable checklist, citation, and DOI record. They are generated from the first two layers. | Build/release process. |

### Core Kenya checklist

The Committee needs one understandable, shareable working table. Its rows include both species and subspecies occurring in Kenya. Each row uses the stable `AvibaseID` as its join key.

The core table should contain only information the Committee owns or decides, including:

- `AvibaseID`;
- a Kenya-specific English display name where the Committee chooses one;
- the Kenyan occurrence decision and Kenya status flags;
- Kenyan endemicity, waterbird, vulnerability, and similar Committee classifications;
- notes, evidence, decision date, and decision source.

It must not become a second copy of AviList. Scientific names, taxonomic rank, family, sequence, and AviList range are looked up from the pinned AviList source when a release is built. External information is added by the automatic enrichment process described below. These generated fields may be shown in the Committee's workbook as read-only context, but are not fields that the Committee edits.

The working table may begin as a protected Excel workbook because that is the most accessible interface for Committee members. The repository remains the versioned source of record, and the curator controls imports/exports and release preparation.

### External reference data

Each release uses one fixed AviList version. The first proposed basis is AviList v2025b. The build process automatically joins the core Kenya table to AviList using `AvibaseID`, then enriches those records with eBird/Clements, BirdLife, GBIF, and other related information.

The mapping process is automatic and reproducible, not manually maintained by Committee members. It may use crosswalks supplied by AviList, stable identifiers from the external source, or a project-maintained mapping rule when a source requires one. The source files, mapping logic, and mapping results are versioned with the release. If no reliable match exists, the generated field remains blank and the build report records the unmapped record for review; the Committee does not need to enter external taxonomy into the core table.

### Published releases

Every public release should provide:

- a downloadable machine-readable checklist (CSV and Excel at minimum);
- the website view;
- a human-readable change summary;
- release metadata recording source version, dates, editors, and output information;
- a recommended citation and a DOI, using a GitHub Release archived by Zenodo.

A printable checklist is a desirable output but should be designed after the migrated data and public download are stable.

## Fixed decisions

- AviList is the taxonomic authority for every release.
- `AvibaseID` is the project join key.
- The Bird Committee remains the editorial authority; the curator records its decisions and produces releases.
- The 2019 checklist’s admission, rarity, historical-record, and status principles are carried forward in the [draft policy](policy.md).
- Existing status codes are retained through the first migration.
- Releases are versioned as `KE-<AviList-version>.<Kenya-release-number>`, for example `KE-v2025b.1`. This communicates the AviList base while distinguishing the Kenya publication.
