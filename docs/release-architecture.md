# Release archive and taxonomic comparisons

## Boundary between preparation and publication

`config/release.toml` and `publication/publication.toml` describe an editable candidate. `publication/releases.toml` is the ordered archive registry and has a separate `active_release`. The default website includes only sealed released versions and uses that active ID. `--preview-release <candidate-id>` explicitly includes a registered draft for local review. Merging candidate code or data does not activate it on the public site.

Each `release-assets/<id>/` bundle contains a canonical checklist CSV, a taxonomy snapshot, exactly one checklist PDF, the publication metadata, frozen policy/category definitions and curated inputs, and a `release.json` seal recording file hashes. The 2019 references label their PDF as the original printed edition, which does not incorporate digital transcription corrections. v2019.2 applies three reviewed identifier corrections in a new bundle; v2009.0 preserves the fourth edition with its 2017 corrections and discloses 49 unresolved IDs. See [historical checklists](historical-checklists.md). No comparison PDF is generated, staged or served. Old comparison PDFs remain retrievable from Git history only.

Released bundles are immutable. Staging refuses to replace one; edits require a new release ID. Draft bundles can be replaced. The PDF renderer records the checklist, publication metadata, renderer, version-specific pending-review table, editorial source and PDF hashes in a local sidecar. Staging rejects stale renders, checks curated inputs against the build manifest and freezes them. The website verifies bundle hashes before use. A candidate's current curation can never annotate or rewrite an older published checklist.

## Taxonomy is distinct from evidence and editorial decisions

A comparison snapshot contains only Avibase ID, English name, scientific name, order, family, English family name and a display sequence. Capitalization and whitespace-only differences are ignored when comparing names/classification; original display text is preserved. English family labels are retained for display but never trigger a change; only scientific family names affect family-change detection. Sequence changes alone are ignored: inserting an unrelated species must not make every later species a taxonomic change. Observation counts/dates, rarity, historical/native/exotic status, EARC decisions and other manual checklist categories do not enter the comparison model.

The [shared taxon concept graph](taxon-concept-relationships.md) records reviewed relationships once and projects them onto the selected editions. Archived transition files preserve earlier decisions for reference.

Exact Avibase IDs establish shared concepts. The website and command-line comparison use the shared table for relationships between different IDs. Any two archived versions can be compared in either direction. The engine projects the graph onto the two selected editions, groups the resulting links and reports changes in names, classification or concept IDs. Unknown classification fields in historical versions are not treated as classification changes.

Connected lineages are not claims of taxonomic equivalence. A lump followed by a split can yield a many-to-many group; it does not prove which observations belong to which descendant. Intermediate curated occurrence decisions are not transferred. Endpoint taxa without shared IDs or reviewed connecting links appear as added or removed species, with the absent version explicitly labeled. These indicate checklist membership differences, not necessarily new arrivals, extinction or taxonomic splits. Reviewed concept links prevent a known taxon replacement from being counted again as a separate addition and removal. Ambiguous histories remain unlinked and may require editorial interpretation.

The build writes every directed pair (including empty same-version pairs) as JSON and CSV. This small static matrix keeps the Python engine as the single comparison implementation; the browser fetches only the selected pair. It avoids divergent browser/server matching logic and allows deterministic tests of every pair. For a much larger archive, pair generation can become cached or on-demand without changing the snapshot or result schemas.

## Curated inputs and historical reconstruction

Candidate decisions live under `data/curation/releases/<id>/`; the build configuration pins their paths and the manifest pins their hashes. This includes evidence corrections, category assignments, species membership, sensitive taxa and EARC decisions. Pending-review membership is explicitly maintained for that version rather than inferred from whichever comparison the reader selects. Curation is also copied into each sealed release bundle. The root historical curation files are retained as source/history, not used to mutate accepted releases.

Existing accepted checklists are imported rather than rerun against today's inputs. The one-time `bootstrap_archive.py` imports 2019.1 and the tagged v2025.0 data, recovering older curated inputs from the corresponding Git tag and verifying their original manifest hashes. There is no need to recompact old EBD archives merely to compare taxonomies. Missing accepted data must be recovered from its tagged release/source; it must not be silently reconstructed using current curation.

The original v2019.0 tag is also imported byte-for-byte. Nine rows have missing or duplicate Avibase IDs; their original data remain downloadable and are audited in `taxonomy-exclusions.json`. They are excluded from taxonomic matching, and comparisons involving that version show a warning. No replacement IDs are guessed from names.

## Workflow

1. Create a new candidate ID and its curation directory. Pin source paths/versions and use the same ID in publication metadata. Keep `status = "draft"`. Register its bundle as a draft in `publication/releases.toml`; leave `active_release` unchanged.
2. Build and validate the release. Review its scientific inputs and version-scoped exceptions. The current September EBD candidate is provisional; this architecture does not resolve the upstream taxonomy transition.
3. Render the canonical checklist PDF and stage the draft bundle. Staging freezes policy, definitions and decisions. No pair-specific comparison or comparison PDF is a prerequisite.
4. Build the preview with `--preview-release <id>`. Check every relevant pair, downloads, reverse comparisons and historical versions.
5. After scientific/editorial acceptance, change the candidate publication status to `released`, rerender and stage once. Review the seal, then mark the registry entry `released` and change `active_release` explicitly. Commit the bundle, metadata and registry together. Subsequent staging of that released ID is rejected.
6. Tag and publish the corresponding GitHub Release using the same ID and canonical PDF/CSV/manifest. GBIF/IPT publication remains separate. The website's versioned local downloads do not depend on GitHub Release availability.

## Validation

Run `tests/validate_taxonomy_archive.py` for taxonomy-only semantics, all name/classification fields, species additions/removals and excluded status changes, forward/reverse/transitive relationships, splits/lumps, same-version behavior and draft isolation. Run `tests/validate_stage_release_assets.py` after building/rendering the candidate for stale-render rejection, curation snapshots and immutability. Run `tests/validate_site.py <site>` for the complete pair matrix, downloadable assets, absence of comparison PDFs and absence of evidence/review fields in comparison payloads. Script and stylesheet URLs are fingerprinted, comparison downloads carry content revisions, and the small release catalogs are revalidated so a newly activated version cannot silently reuse an older comparison payload. UI checks cover pair switching, deep links, empty results, downloads and mobile layout. Existing scientific pipeline and publication validators remain separate checks.

## Taxonomy-year naming correction (3 November 2026)

Release IDs now use the taxonomic baseline year followed by the checklist revision. The previously published `v2026.0` (AviList v2025b, eBird taxonomy 2025, EBD June 2026) was renamed `v2025.0` by explicit author request before external use. Its checklist rows and observation evidence are unchanged; the PDF label, citations, archive metadata and links were corrected. Publication remains dated 1 October 2026. The original source commit `4476eb7cd6d754c8df1f37906f984db5ee065c58` is retained under the renamed tag; its historical tree contains the original release label. The one-time archive importer pins that commit and translates its old labels explicitly.

The name `v2026.0` is reserved for a future 2026-taxonomy candidate, maintained separately until compatible EBD data is available. No 2026 candidate is registered or included in this infrastructure branch. The EBD month and publication date remain independent of the taxonomy-year release ID.
