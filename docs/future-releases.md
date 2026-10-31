# Preparing a future release

Release identifiers are explicit strings, independent of the eBird source month.
`v2027.01` is supported exactly as written; use the same identifier in the configuration,
publication metadata, asset directory, Git tag, and GitHub Release.

## Prepare and build

1. Update `config/release.toml`: set `release_id = "v2027.01"`, pin the new source
   versions and paths, update the historical reference date, and set `release_revision`
   to the revision intended for this release. The revision is provenance metadata;
   it does not generate the release ID.
2. Update `publication/publication.toml`: set the same `release_id` and `document.version_label`, set `sources.release_directory = "dist/v2027.01"`, and set `render.output_filename = "Checklist-of-the-Birds-of-Kenya-v2027.01.pdf"`. Update dates, citations, source descriptions, versioned repository links, and editorial prose. Retain `sources.review_baseline_comparison` so unresolved additions since 2019.1 remain visible across releases. Use `status = "draft"` during preparation and `"released"` after review. Follow [the GBIF update steps](gbif-publication.md) for the existing dataset.
3. Edit the curated tables and publication prose as needed. Keep the previous
   `release-assets/v2026.0/` directory intact. Published versions are snapshots;
   corrections after publication should receive a new release ID and tag.

Run from the repository root:

```sh
release_id=v2027.01
previous_release_id=v2026.0

uv run python scripts/build_release.py config/release.toml
uv run python tests/validate_release_pipeline.py
uv run python tests/validate_release.py "dist/$release_id"
uv run python tests/validate_publication.py publication/publication.toml

uv run python scripts/compare_releases.py \
  "release-assets/$previous_release_id/checklist.csv" \
  "dist/$release_id/checklist.csv" "dist/$release_id/comparison"

uv run python scripts/build_ipt_checklist.py publication/publication.toml
uv run python tests/validate_ipt_checklist.py "dist/$release_id/gbif"
uv run python scripts/render_checklist_pdf.py publication/publication.toml --keep-typ
uv run python scripts/stage_release_assets.py
uv run python scripts/build_site.py --release-dir "release-assets/$release_id" --output _site --allow-draft
uv run python tests/validate_site.py _site
uv run python scripts/serve_site.py
```

Review the checklist, audits, comparison, PDF, GBIF package, and website before
publishing. The generic comparison matches Avibase IDs: new taxonomy splits,
lumps, or identifier replacements need editorial interpretation. It produces CSV,
JSON, Markdown, and HTML; it does not render a comparison PDF. The existing
`compare_2019.1_to_2026.0.py` and comparison PDF renderer are specific to the
historical comparison and are not steps for subsequent releases.

The routine `refresh_website.py` command expects the release PDF and comparison
to have already been generated. For a new release, complete the sequence above
first; regenerate these publication products whenever their inputs change.

## Preserve comparisons for version selection

Each release keeps its reviewed comparison under
`release-assets/<to-release-id>/comparison/`. Retain these directories when adding
a new release: the existing `2019.1 → v2026.0` comparison stays alongside the new
`v2026.0 → v2027.01` comparison. Their JSON files explicitly identify
`from_release` and `to_release` and use the same group format for the Changes view.

The website build copies every staged pair to
`_site/data/comparisons/<to-release-id>/` and generates `data/comparisons.json`,
listing each pair, group count, and JSON/CSV/optional PDF paths relative to the site
root. The active release remains available at `data/taxonomy-changes.json`.
Archived comparisons are copied as published rather than recomputed using new
curation or EARC decisions.

The Changes page currently displays the active pair. A future selector can read
the catalog and offer `2019.1 → v2026.0` or `v2026.0 → v2027.01`, then load the
chosen JSON and update its heading and download links. Only reviewed, built pairs
should be selectable; arbitrary combinations, such as `2019.1 → v2027.01`, need
their own reviewed comparison. The current convention stores one baseline
comparison per release; additional baselines would need separate pair directories
and catalog entries.

## Publish and preserve

Write reviewed release notes in `docs/releases/v2027.01.md`. Commit the source,
metadata, notes, and new public assets, then push `main`. GitHub Actions deploys
the active version from the committed assets. The live website shows the active
release; earlier versions remain in Git and GitHub Releases.

After committing all reviewed changes and pushing the publication commit:

```sh
git tag -a "$release_id" -m "Checklist of the Birds of Kenya $release_id"
git push origin "$release_id"
gh release create "$release_id" --verify-tag \
  --title "Checklist of the Birds of Kenya $release_id" \
  --notes-file "docs/releases/$release_id.md" \
  "release-assets/$release_id/"*.pdf \
  "release-assets/$release_id/checklist.csv" \
  "release-assets/$release_id/manifest.json" \
  "release-assets/$release_id/comparison/taxonomy-changes.csv" \
  "release-assets/$release_id/comparison/taxonomy-changes.json"
```

Attach a reviewed comparison PDF separately if one was prepared. Tags and GitHub
Releases are explicit publication steps, not automatically created by pushing
`main`; see the [GitHub CLI release documentation](https://cli.github.com/manual/gh_release_create).
Do not move published tags or replace their assets when preparing later versions.
Raw licensed source inputs and local caches remain excluded from Git; retain the
pinned inputs separately to reproduce the complete build from its tagged source.
