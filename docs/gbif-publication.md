# Publishing v2026.0 through the existing IPT resource

The public release is **v2026.0**, a versioned checklist rather than a numbered edition. June 2026 is the source EBD month, not the release identifier. This release retains unresolved national-record review for a later version. The separate September 2026 draft PDF remains an editorial variant.

Use the existing IPT resource; do not create a duplicate dataset. Nature Kenya is the registered publishing organization, key `2700b39d-c627-49c2-909a-2bd7a00c1035`. Its [GBIF publisher page](https://www.gbif.org/publisher/2700b39d-c627-49c2-909a-2bd7a00c1035) is already endorsed. Confirm that the existing resource is associated with this organization before first registration.

## Files and expected counts

```sh
python3 tests/validate_publication.py publication/publication.toml
python3 scripts/build_ipt_checklist.py publication/publication.toml
python3 tests/validate_ipt_checklist.py dist/v2026.0/gbif
```

- `dist/v2026.0/gbif/checklist.csv`: the CSV to upload as the IPT data source.
- `dist/v2026.0/gbif/ipt-metadata.json`: a worksheet for filling the IPT metadata editor; it is not EML or an IPT import configuration.

There are **1,148 species** and **1,714 Taxon core rows** including their higher taxa. A GBIF taxon-row count can therefore exceed the species count. The dataset is a **Checklist**, with a **Taxon core**, not an occurrence dataset. Source observation summaries do not become occurrence records.

## Dataset creators and PDF authorship

GBIF creators are explicitly ordered in `ipt.creator_ids`, separately from the corporate PDF author and general contributor list:

1. Raphaël Nussbaumer
2. Colin Jackson
3. James Bradley
4. John Fanshawe
5. Brian Finch
6. Nigel Hunter
7. Victor Ikawa
8. Okech
9. Don Turner
10. Washington Wachira
11. Fleur Ng'weno
12. Richard Stratton Hatfield

The first two and final two positions are fixed by the agreed authorship; intervening authors are alphabetical by surname. “Okech” is retained as supplied; a fuller name can be added when available. Creators retain their available ORCIDs and contact/affiliation metadata. They are not duplicated in the associated contributor list.

Nature Kenya remains publisher and the Bird Committee remains corporate author of the PDF. The separate draft profile keeps the requested *Checklist of the Birds of Kenya — 2026 Draft* citation. Dataset authorship does not change the PDF's authorship.

`ipt.recommended_citation` is the dataset citation; `document.recommended_citation` is the canonical PDF citation. IPT/GBIF can generate their displayed citations from structured metadata, so preserving the creator order in IPT is essential. GBIF's generated version can be the IPT resource version rather than the repository label v2026.0. See [IPT creator and citation guidance](https://ipt.gbif.org/manual/en/ipt/latest/manage-resources).

The `gbif/` folder is sufficient; no ZIP input bundle is generated.

## Source mapping

Replace/update the existing CSV source and check its mapping after replacement. Preserve the existing IPT resource shortname and published identifiers. Use UTF-8, comma-separated columns, double-quote text qualifier, and one header row.

The core definition used by the exporter is [Darwin Core Taxon](https://rs.gbif.org/core/dwc_taxon_2025-07-10.xml). Map each exported header to the corresponding term and use `taxonID` as the core record identifier.

| Fields | Meaning |
| --- | --- |
| `taxonID` | Species use the checklist's `avibase_id` directly, including its `avibase-` prefix. Higher taxa use rank-prefixed names such as `family-Anatidae`. |
| `parentNameUsageID` | Identifier of the immediate higher taxon in this file; blank only for the kingdom. |
| `taxonConceptID` | Avibase concept URL for species. |
| `nameAccordingTo`, `nameAccordingToID` | Pinned AviList v2025b reference and DOI. |
| `scientificName`, `scientificNameAuthorship`, `taxonRank` | AviList name including authorship, separate authorship, and rank. |
| `taxonomicStatus`, `nomenclaturalCode` | Accepted taxonomic names; ICZN. These do not assess national occurrence records. |
| `kingdom`, `phylum`, `class`, `order`, `family`, `genus`, `specificEpithet` | Classification and parsed species name. |
| `vernacularName`, `language` | Single English species name, with language code `en`. |

There are no extension tables. Remove obsolete mappings for `datasetID`, `datasetName`, `acceptedNameUsageID`, and `taxonRemarks` when replacing an earlier CSV. These columns are omitted: IPT metadata supplies dataset identity/title, and this checklist contains no synonyms. No categories, EARC flags, internal membership sources, sensitive-species flags, raw observations, dates, or counts are exported as Taxon core columns. A single English vernacular name is supported in this core; a Vernacular Name extension is unnecessary for this design.

Keep these row identifiers stable across releases. `parentNameUsageID` uses the corresponding higher-taxon identifier. Avibase web links remain in `taxonConceptID`; the dataset DOI belongs in the citation/GBIF links. This export replaces the earlier repository-URL-prefixed row identifiers before first publication.

## Metadata to enter or update

The structured source is `publication/publication.toml`; the generated JSON mirrors its current values. Select English in the IPT language field (`en-KE` in publication metadata describes the document locale).

**Do not upload `ipt-metadata.json` through “Replace metadata”.** That control expects EML XML for this checklist. Enter the worksheet values in the IPT metadata editor; upload `checklist.csv` separately as the Taxon source. Renaming the JSON to `.xml` does not convert it to EML. See the [official metadata instructions](https://ipt.gbif.org/manual/en/ipt/latest/resource-metadata).

If IPT reports “Failed to create EML validator”, first check the uploaded file format. The [IPT implementation](https://github.com/gbif/ipt/blob/master/src/main/java/org/gbif/ipt/service/manage/impl/ResourceManagerImpl.java) parses the file as XML before constructing the validator, and its [error handler](https://github.com/gbif/ipt/blob/master/src/main/java/org/gbif/ipt/action/manage/OverviewAction.java) uses this message for XML parsing errors as well as validator initialization failures. The message alone does not establish a server problem. If a genuine EML XML file produces the same error, record the IPT URL/version and ask its administrator to inspect the corresponding server log exception.

1. **Title/citation:** Checklist of the Birds of Kenya, version v2026.0. Use the ordered individual creators and dataset citation from the JSON. The PDF keeps its separate Committee-authored citation. Do not describe the release as the sixth edition or a prerelease.
2. **Publisher/contact/creators/contributors:** copy the approved fields from the JSON, preserving creator order. Nature Kenya is publisher; the Bird Committee remains the corporate author of the PDF. Creator and contributor roles are metadata roles, not taxonomic annotations.
3. **License:** CC BY 4.0; rights holder is the Bird Committee of the East Africa Natural History Society (Nature Kenya). Source materials retain their applicable terms.
4. **Abstract:** use `resource.description`. This is a general description intended to remain applicable across releases: purpose, geographic and species scope, evidence sources, taxonomy, interpretation limits, and versioning. Keep release labels, source dates/versions, species counts, and individual pending cases in the citation, methods, coverage, and version-specific documentation rather than the abstract.
5. **Sampling Methods:** use the four IPT fields listed below. The workflow uses pinned sources, exact eBird taxon-concept matching, curated crosswalks, and deterministic validation. Describe the repository checks without claiming they independently verify every national occurrence.
6. **Geographic coverage:** copy `coverage.geographic_description`, followed by `coverage.bounding_coordinates_description`, and enter `coverage.bounding_coordinates` in the west/east/north/south fields. For v2026.0: west **33.943264**, east **42.4992619**, north **4.6900784**, south **−4.789943** (decimal degrees). These bounds were calculated from all 4,636,644 supporting EBD records using the checklist's `source_avibase_ids`, excluding escapees after release exotic-code overrides. They include marine evidence and describe observation extent, not the country's political boundary or EEZ. Recalculate when the source evidence changes; source version and record count are recorded in `scope.geographic_bounds`.
7. **Temporal coverage:** select a date range and use `coverage.temporal_start` and `coverage.temporal_end`, derived from the checklist's supporting EBD dates. For v2026.0 these are 14 August 1888 and 30 June 2026. Include `coverage.temporal_description` in additional information to explain historical evidence, uneven sampling, and curated entries without public EBD dates. The range is not the publication date.
8. **Taxonomic coverage:** birds (Aves), species-level membership following AviList v2025b, with higher taxa included to link the hierarchy.
9. **Additional information/limitations:** use `additional_information.record_review` and `additional_information.sensitive_record_limitation`, and link the website policy and changes pages from `references`.
10. **References/maintenance:** cite AviList v2025b and the June 2026 EBD using the applicable eBird source citation. Describe updates as separately versioned, curated snapshots; do not promise a fixed schedule. Add funding only where applicable and established.
11. **Acknowledgements:** copy `resource.acknowledgements` into Additional Information (or an acknowledgement field if the IPT provides one). This credits observers, earlier checklist compilers, partner organizations, and data/taxonomy providers; the individual creators remain in the authorship and citation.

The worksheet follows the [IPT Sampling Methods structure](https://ipt.gbif.org/manual/en/ipt/latest/manage-resources#sampling-methods):

| IPT field | Worksheet field |
| --- | --- |
| Study Extent | `methods.study_extent` |
| Sampling Description | `methods.sampling_description` |
| Quality Control | `methods.quality_control` |
| Step Description (repeat using “Add new method step”) | Each entry in `methods.method_steps`, in order |

The method steps retain the previous compilation wording, split into four steps. Study extent combines the existing geographic scope with the observed evidence date range. Sampling description and quality control explain the same compilation process in their respective IPT fields. The source's `ipt.methods` prose remains available for existing consumers, and printed-publication fields are unchanged by this restructuring.

Internal `membership_source` explains how a species enters the repository checklist:

| Value | Interpretation |
| --- | --- |
| `ebd` | Qualifying EBD evidence maps to the species. |
| `accepted_earc` | Accepted EARC evidence supplies membership without EBD evidence. |
| `curated_species` | Maintained checklist addition, including historical membership. |
| `curated_sensitive_species` | Curated sensitive membership without public EBD evidence. |

These are pipeline provenance labels and are intentionally omitted from GBIF taxonomy remarks. `Pending EARC` means that an addition/removal since 2019.1 lacks a mapped decision in this repository. It does not mean an invalid taxon, a rejected record, or a confirmed active submission. Accepted/rejected EARC decisions concern occurrence evidence. This release retains species and their source evidence regardless of rejected decisions and exposes those decisions in repository/website annotations.

The 13 current Pending EARC species are Cotton Pygmy Goose, Little Gull, Caspian Gull, Red-tailed Tropicbird, Böhm's Bee-eater, Ethiopian Bee-eater, Melodious Lark, Ethiopian Cisticola, Bamboo Warbler, Yellow-eyed Bristlebill, Green White-eye, Yellow-breasted Forest Robin, and Siberian Stonechat. Speckled Tinkerbird and Great Grey Shrike are two historical removals flagged for review. This unresolved review is accepted for v2026.0 and does not block the release. Repository categories may remain draft because they are outside this GBIF export.

## Publish, register, then record the DOI

Review the resource preview, validate the mappings, and confirm the counts before publishing. IPT generates the actual Darwin Core Archive, its `meta.xml`, and EML. Check that generated archive with GBIF's validation tools and inspect any name/hierarchy interpretation issues.

Publish the existing IPT resource publicly and register it with GBIF if it is not already registered. In the normal workflow, **GBIF assigns a dataset DOI on registration**. Merely creating an unpublished IPT resource does not require a DOI. With a configured DataCite account, IPT can instead reserve a DOI before publication; this is optional and not required for the normal GBIF-assigned DOI. See the [official DOI workflow](https://ipt.gbif.org/manual/en/ipt/latest/doi-workflow) and [publishing workflow](https://ipt.gbif.org/manual/en/ipt/latest/how-to-publish).

After registration, set `gbif.dataset_url` to the GBIF dataset page and `gbif.doi` to the bare DOI, for example `10.15468/…`, in `publication/publication.toml`. Append its `https://doi.org/…` URL to `ipt.recommended_citation`; the PDF citation is maintained separately under `document.recommended_citation`. Keep the local version `v2026.0` separate from IPT's own numeric resource version. The local release date is recorded as 1 October 2026; IPT records its actual publication date separately.

Rebuild the GBIF worksheet, PDF, staged bundle, and website after adding the DOI. The absence of a GBIF DOI does not force the repository version back to draft. The September editorial draft PDF remains a separate profile and is not the canonical release download.

The final GitHub tag and Release are both named `v2026.0`, with prerelease disabled. Attach the canonical checklist CSV/PDF, comparison CSV/JSON/PDF, manifest, checksums, and the individual files from `dist/v2026.0/gbif/`. Do not attach raw EBD, retained source-record extracts, or the entire local `dist/` directory. Submit the derived product to eBird through the responsible data user according to its [data-use requirements](https://support.ebird.org/en/support/solutions/articles/48001078113-ebird-data-privacy-and-data-use).
