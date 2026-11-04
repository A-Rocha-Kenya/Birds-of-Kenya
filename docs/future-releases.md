# Preparing a future release

See [the release architecture](release-architecture.md) for archive schemas, taxonomy and species-membership comparisons, version-scoped curation and activation rules. Release IDs are explicit; the EBD source month does not determine them.

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

`refresh_website.py` refuses to rebuild an already published selected edition. Prepare a new draft ID first. It performs the build, validation, canonical PDF render, staging and candidate preview together. It never activates the candidate publicly. To build the actual public site, run `scripts/build_site.py` without a preview flag.

The website builds all taxonomy comparison pairs from sealed snapshots. Export a selected pair separately with:

```sh
uv run python scripts/compare_releases.py v2019.1 v2025.0 --output tmp/comparison
```

Add `--preview-release <new-id>` to compare a draft. Comparisons include species additions/removals and exclude observation evidence and manual status decisions. No comparison PDF is supported. Historical versions and their canonical PDFs remain available through the website's version archive.

After review, set publication status to `released`, rerender and stage, then mark its registry entry `released` and explicitly update `active_release`. Commit and publish the bundle, metadata and registry together. Staging cannot overwrite a released bundle. Tag the publication commit using exactly the release ID and attach its one canonical PDF, checklist CSV and manifest to the matching GitHub Release. Update the existing GBIF/IPT resource separately using [the GBIF guide](gbif-publication.md).

## Public preview without a release

The Pages workflow can deploy a draft at `/preview/` while leaving the root website on the registry's released `active_release`. Push the candidate branch, then dispatch the workflow using that branch and the draft ID:

```sh
gh workflow run pages.yml --ref codex/upgrade-v2026.0 -f preview_release=v2026.0
```

This creates no tag or GitHub Release and does not merge the candidate into main. The preview carries a provisional evidence notice and hides the formal citation panel. Update the draft bundle and redeploy to replace it when a compatible EBD arrives. A subsequent Pages deployment without `preview_release` removes `/preview/`, including an automatic main-branch deployment; dispatch the candidate again if the preview is still needed.
