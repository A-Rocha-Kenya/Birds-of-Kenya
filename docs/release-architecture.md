# Release archive and taxonomic comparisons

## Boundary between preparation and publication

`config/release.toml` and `publication/publication.toml` describe an editable candidate. `publication/releases.toml` is the ordered archive registry and has a separate `active_release`. The default website includes only sealed released versions and uses that active ID. `--preview-release v2026.1` explicitly includes that draft for local review. Merging candidate code or data does not activate it on the public site.

Each `release-assets/<id>/` bundle contains a canonical checklist CSV, a taxonomy snapshot, exactly one checklist PDF, the publication metadata, frozen policy/category definitions and curated inputs, and a `release.json` seal recording file hashes. The 2019.1 reference preserves the corrected CSV and labels its PDF as the original printed 2019 edition, which does not incorporate transcription corrections. No comparison PDF is generated, staged or served. Old comparison PDFs remain retrievable from Git history only.

Released bundles are immutable. Staging refuses to replace one; edits require a new release ID. Draft bundles can be replaced. The PDF renderer records the checklist, publication metadata, renderer, version-specific pending-review table, editorial source and PDF hashes in a local sidecar. Staging rejects stale renders, checks curated inputs against the build manifest and freezes them. The website verifies bundle hashes before use. A candidate's current curation can never annotate or rewrite an older published checklist.

## Taxonomy is distinct from evidence and editorial decisions

A comparison snapshot contains only Avibase ID, English name, scientific name, order, family, English family name and a display sequence. Sequence changes alone are ignored: inserting an unrelated species must not make every later species a taxonomic change. Observation counts/dates, rarity, historical/native/exotic status, EARC decisions and other manual checklist categories do not enter the comparison model.

Exact Avibase IDs establish shared concepts. Version-specific `transition.json` files can supply reviewed old-to-new concept links, including splits and lumps; they belong to the target release and are sealed with it. Names are never matching keys. Any two archived versions can be compared in either direction. The engine follows identity and reviewed links through intervening versions, groups connected endpoint concepts and reports changed names/classification or changed concept IDs. Unknown classification fields in historical versions are not treated as classification changes.

Connected lineages are not claims of taxonomic equivalence. A lump followed by a split can yield a many-to-many group; it does not prove which observations belong to which descendant. Intermediate curated occurrence decisions are not transferred. Endpoint taxa without shared IDs or reviewed connecting links are counted as unlinked and omitted: national-list additions/removals alone are outside taxonomic comparison. Ambiguous histories should remain unlinked until a taxonomic relationship can be reviewed.

The build writes every directed pair (including empty same-version pairs) as JSON and CSV. This small static matrix keeps the Python engine as the single comparison implementation; the browser fetches only the selected pair. It avoids divergent browser/server matching logic and allows deterministic tests of every pair. For a much larger archive, pair generation can become cached or on-demand without changing the snapshot or result schemas.

## Curated inputs and historical reconstruction

Candidate decisions live under `data/curation/releases/<id>/`; the build configuration pins their paths and the manifest pins their hashes. This includes evidence corrections, category assignments, species membership, sensitive taxa and EARC decisions. Pending-review membership is explicitly maintained for that version rather than inferred from whichever comparison the reader selects. Curation is also copied into each sealed release bundle. The root historical curation files are retained as source/history, not used to mutate accepted releases.

Existing accepted checklists are imported rather than rerun against today's inputs. The one-time `bootstrap_archive.py` imports 2019.1 and the tagged v2026.0 data, recovering older curated inputs from the corresponding Git tag and verifying their original manifest hashes. There is no need to recompact old EBD archives merely to compare taxonomies. Missing accepted data must be recovered from its tagged release/source; it must not be silently reconstructed using current curation.

The original v2019.0 tag is also imported byte-for-byte. Nine rows have missing or duplicate Avibase IDs; their original data remain downloadable and are audited in `taxonomy-exclusions.json`. They are excluded from taxonomic matching, and comparisons involving that version show a warning. No replacement IDs are guessed from names.

## Workflow

1. Create a new candidate ID and its curation directory. Pin source paths/versions and use the same ID in publication metadata. Keep `status = "draft"`. Register its bundle as a draft in `publication/releases.toml`; leave `active_release` unchanged.
2. Build and validate the release. Review its scientific inputs and version-scoped exceptions. The current September EBD candidate is provisional; this architecture does not resolve the upstream taxonomy transition.
3. Render the canonical checklist PDF and stage the draft bundle. Staging freezes policy, definitions and decisions. No pair-specific comparison or comparison PDF is a prerequisite.
4. Build the preview with `--preview-release <id>`. Check every relevant pair, downloads, reverse comparisons and historical versions.
5. After scientific/editorial acceptance, change the candidate publication status to `released`, rerender and stage once. Review the seal, then mark the registry entry `released` and change `active_release` explicitly. Commit the bundle, metadata and registry together. Subsequent staging of that released ID is rejected.
6. Tag and publish the corresponding GitHub Release using the same ID and canonical PDF/CSV/manifest. GBIF/IPT publication remains separate. The website's versioned local downloads do not depend on GitHub Release availability.

## Validation

Run `tests/validate_taxonomy_archive.py` for taxonomy-only semantics, all name/classification fields, excluded membership/status changes, forward/reverse/transitive relationships, splits/lumps, same-version behavior and draft isolation. Run `tests/validate_stage_release_assets.py` after building/rendering the candidate for stale-render rejection, curation snapshots and immutability. Run `tests/validate_site.py <site>` for the complete pair matrix, downloadable assets, absence of comparison PDFs and absence of evidence/review fields in comparison payloads. Script and stylesheet URLs are fingerprinted, comparison downloads carry content revisions, and the small release catalogs are revalidated so a newly activated version cannot silently reuse an older comparison payload. UI checks cover pair switching, deep links, empty results, downloads and mobile layout. Existing scientific pipeline and publication validators remain separate checks.
