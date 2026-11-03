# Preparing a future release

See [the release architecture](release-architecture.md) for archive schemas, taxonomy-only comparisons, version-scoped curation and activation rules. Release IDs are explicit; the EBD source month does not determine them.

Create `data/curation/releases/<new-id>/`, pin those curated files in `config/release.toml`, and update `publication/publication.toml` to the same candidate ID, dates and output filename. Keep its status `draft`. Add it to the ordered `publication/releases.toml` registry with `status = "draft"`; leave the live `active_release` unchanged. Supply reviewed concept links in the candidate's `transition.json` when needed. Copying earlier decisions is a starting point for review, not automatic inheritance across changed concepts.

```sh
uv run python scripts/build_release.py config/release.toml
uv run python tests/validate_release_pipeline.py
uv run python tests/validate_release.py dist/<new-id>
uv run python tests/validate_publication.py publication/publication.toml
uv run python scripts/render_checklist_pdf.py publication/publication.toml --keep-typ
uv run python scripts/stage_release_assets.py
uv run python scripts/build_site.py --preview-release <new-id> --output tmp/site-preview
uv run python tests/validate_site.py tmp/site-preview
uv run python scripts/serve_site.py --directory tmp/site-preview
```

`refresh_website.py` performs the build, validation, canonical PDF render, staging and candidate preview together. It never activates the candidate publicly. To build the actual public site, run `scripts/build_site.py` without a preview flag.

The website builds all taxonomy comparison pairs from sealed snapshots. Export a selected pair separately with:

```sh
uv run python scripts/compare_releases.py v2019.1 v2026.0 --output tmp/comparison
```

Add `--preview-release <new-id>` to compare a draft. Comparisons exclude observation evidence, national-list membership changes and manual status decisions. No comparison PDF is supported. Historical versions and their canonical PDFs remain available through the website's version archive.

After review, set publication status to `released`, rerender and stage, then mark its registry entry `released` and explicitly update `active_release`. Commit and publish the bundle, metadata and registry together. Staging cannot overwrite a released bundle. Tag the publication commit using exactly the release ID and attach its one canonical PDF, checklist CSV and manifest to the matching GitHub Release. Update the existing GBIF/IPT resource separately using [the GBIF guide](gbif-publication.md).
