# GBIF and release readiness: v2026.0

Updated 1 October 2026 after the release decisions and rebuild. The earlier assessment has been superseded by this completion record. The local version is ready for the existing IPT resource; it has not been published to GBIF or released on GitHub by this work.

## Decisions finalized

- Release name, tag, and directory: **v2026.0**. June 2026 remains the EBD source month.
- This is a normal version release, not a numbered sixth edition or a GitHub prerelease. Canonical metadata has `status = "released"`; release/editorial dates are 1 October 2026.
- The website changes subtitle is exactly **From the 2019.1 to 2026.0**.
- Pending EARC review remains unresolved for this release and can be revisited next version. It does not block publication.
- EARC decisions concern national-record evidence, not taxonomic validity. Retain species and source evidence even when a curated record decision is rejected.
- Categories can remain draft in the repository; they are not exported to GBIF.
- Keep the existing June 2026 EBD/eBird 2025/AviList v2025b source pins, exotic corrections, sensitive-species treatment, and outstanding KBM links.
- Keep the separate September 2026 draft PDF profile for the requested editorial variant; canonical downloads use the v2026.0 PDF.
- An IPT resource already exists. Its URL is still needed for direct inspection/update. Nature Kenya is already registered and endorsed as a GBIF publisher.

- GBIF creators: Raphaël Nussbaumer first, Colin Jackson second, remaining named authors alphabetically by surname, Fleur Ng'weno penultimate, Richard Stratton Hatfield last. Nature Kenya remains publisher; PDF corporate authorship/citation is separate.

## Completed changes

| Earlier finding | Resolution |
| --- | --- |
| Stale GBIF export | Rebuilt `dist/v2026.0/gbif/`: 1,148 species in 1,714 Taxon core rows. Species `taxonID` now uses `avibase_id` directly; higher taxa and parent links use rank-prefixed names. |
| Internal membership labels in remarks | Removed `taxonRemarks`, redundant `datasetID`/`datasetName`, and the entirely blank `acceptedNameUsageID` from the GBIF table. Pipeline membership sources are explained in the publishing guide; national-record review is documented at dataset level with links to review material. |
| Mixed PDF identities | Rebuilt the canonical v2026.0 PDF and separate September draft variant. Staged the canonical PDF and regenerated comparisons. |
| Stale comparison tags | Rebuilt CSV/JSON/HTML/PDF together: 378 comparison groups, 15 Pending EARC groups, including 13 present species. |
| EARC filtering/provenance | Removed taxon-level rejection filters from checklist, retained records, and comparisons. Added `earc_decision` annotations to the checklist and the EARC input hash to the manifest. |
| Release status versus missing DOI | Released local versions can validate/build before the GBIF DOI exists. Required release dates/citation are checked; GBIF links are added after registration. |
| Stale documentation | Updated README, policy, pipeline/migration docs, HIST definition, colophon, and website wording. Supplementary tables are explicitly local, outside the website/GBIF export. |
| SAFRING/exotic/minor audits | Retained as requested; no new curation decisions. |
| Broken 2019.0 validator | Reads the archived input directly from the existing `v2019.0` Git tag; it now passes. |

Restoring the rejected-record species adds **Ruddy Shelduck** and **Brown Skua**, changing the checklist from 1,146 to **1,148 species**: 1,143 native and five naturalized. The records themselves remain intact. There are 875,099 derived observations and 5,443 retained latest-record rows. A rejected EARC annotation must not be read as acceptance of that evidence, or as invalidity of all other evidence for that species.

`membership_source` is local provenance: `ebd`, `accepted_earc`, `curated_species`, or `curated_sensitive_species`. It is distinct from the EARC record-review annotation and from GBIF taxonomic name status. GBIF continues to export accepted AviList taxa with no categories or internal membership labels.

## Validation and prepared outputs

The current pipeline, release tables, EARC retention/annotations, endemic categories, publication metadata, GBIF table, policy fixtures, legacy migration, staging fixtures, both historical checklists, and assembled website were checked. Canonical and comparison PDFs were rendered; representative pages were visually checked. The matching compacted EBD cache was reused rather than rebuilding raw compaction.

Canonical assets are under `dist/v2026.0/` and staged public assets under `release-assets/v2026.0/`; the renamed pre-release staging directory `2026-06.0` is replaced. The local website is `_site/`. GBIF preparation consists only of `dist/v2026.0/gbif/`; no ZIP input bundle is generated. Checksums remain for the other release products. The editorial draft PDF is retained in `dist/v2026.0/` as a separate output.

The [GBIF publishing guide](gbif-publication.md) provides source mapping, metadata text, expected counts, record-review treatment, and DOI timing. [Release notes](releases/v2026.0.md) describe the resulting version and can be used for the GitHub Release.

## Next step

1. Open the **existing IPT resource**, replace its CSV with `dist/v2026.0/gbif/checklist.csv`, remove obsolete mappings for `datasetID`, `datasetName`, `acceptedNameUsageID`, and `taxonRemarks`, and update metadata from `ipt-metadata.json` and the guide.
2. Preview/validate the Taxon mapping and IPT-generated Darwin Core Archive; check 1,148 species / 1,714 total core rows and review any GBIF interpretation issues.
3. Publish publicly and register with GBIF. Normally GBIF assigns a DOI at registration; IPT can optionally reserve one earlier when configured with DataCite. See the [official DOI workflow](https://ipt.gbif.org/manual/en/ipt/latest/doi-workflow).
4. Record the GBIF URL/DOI in publication TOML and append the DOI to `ipt.recommended_citation`; rebuild the metadata-bearing products and checksums.
5. Commit the reviewed source/staged assets, publish the annotated `v2026.0` tag and normal GitHub Release, and update Pages. External publication, commits, tags, and deployment have not been performed during this preparation.

Remaining limits: no authenticated IPT resource inspection or GBIF archive validation has occurred; national records are not independently adjudicated; categories remain draft by decision. Source-use obligations and applicable eBird citations continue to apply, but no additional editorial approval is being introduced as a release blocker.
