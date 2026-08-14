# Birds of Kenya

The **sixth edition of the *Checklist of the Birds of Kenya*** continues a national publishing tradition established by editions in 1981, 1986, 1996, 2009, and 2019. It is a public, reproducible, and versioned account of the bird species represented in Kenya, following [AviList](https://www.avilist.org/) taxonomy and names and grounded in [Kenya eBird records](https://ebird.org/region/KE).

The corporate author is the **Bird Committee of Nature Kenya—the East Africa Natural History Society**. Nature Kenya is the official publisher and institutional home of the checklist.

## Nature Kenya—the East Africa Natural History Society

[Nature Kenya](https://naturekenya.org/) is the East Africa Natural History Society (EANHS) in Kenya. Founded in 1909, it is a membership-based organization that invites everyone to join an active society, participate in the study of nature, and support conservation activities.

## Organizations and contributors

- **Publisher and institutional home:** Nature Kenya—the East Africa Natural History Society
- **Partners and contributing organizations:** A Rocha Kenya; National Museums of Kenya (NMK); Kenya Bird Map; eBird Kenya; East African Rarities Committee (EARC)
- **Named contributors:** Brian Finch; Colin Jackson; Don Turner; Fleur Ng’weno; James Bradley (eBird record management); John Fanshawe; Nigel Hunter; Okech; Raphaël Nussbaumer (data curation); Richard Stratton Hatfield; Victor Ikawa; Washington Wachira

The publication, interactive website, downloadable data, and taxonomy comparison are assembled from the same versioned release. The full editorial metadata is maintained in [`publication/publication.toml`](publication/publication.toml).

## Data source

Each release pins one [eBird Basic Dataset](https://ebird.org/about/download-ebird-data-products) month, its matching [eBird taxonomy](https://www.birds.cornell.edu/clementschecklist/download/), and one compatible [AviList](https://www.avilist.org/) version. In addition, four curated tables are used for (1) sensitive species, (2) exceptional eBird-to-AviList alignments, (3) version-scoped exotic-code corrections, and (4) Kenya checklist categories.

## Checklist policy

The [checklist policy](docs/policy.md) defines the scope, evidence, stewardship, categories, and publication rules.

## Checklist build logic

The [checklist build documentation](docs/release-pipeline.md) defines exactly how the pinned source
data and curated decisions become `dist/<release-id>/checklist.csv`. It covers taxonomy matching,
observation clustering, evidence routing, AviList mapping, sensitive species, outputs, and audits. It
does not describe publication or website deployment.

## Release and publication workflow

Run these stages in order. The checklist can be rebuilt repeatedly during review; only stage public
assets after the checklist and all publication products have been accepted.

### 1. Prepare the release

Place the licensed EBD, matching eBird taxonomy, and AviList files at the paths configured in
`config/release.toml`. Update `publication/publication.toml` to use the same release ID and release
directory. The commands below obtain the active ID from the publication metadata:

```sh
release_id=$(python3 -c 'import tomllib; print(tomllib.load(open("publication/publication.toml", "rb"))["release_id"])')
```

### 2. Build and validate the checklist

```sh
uv run python scripts/build_release.py config/release.toml
uv run python tests/validate_release_pipeline.py
uv run python tests/validate_release.py "dist/$release_id"
uv run python tests/validate_publication.py publication/publication.toml
```

Review `dist/$release_id/checklist.csv`, `manifest.json`, and every file under `audit/`. If a curated
mapping, category, sensitive-species entry, or exotic-code correction changes, rebuild and validate
again. Publication validation ensures that the release ID, configured release directory, and generated
manifest agree. The complete `dist/<release-id>/` directory is the canonical local release output.

### 3. Generate and review the release comparison

For the first EBD/AviList release, generate the one-time comparison with the corrected 2019.1
edition:

```sh
uv run python scripts/compare_2019.1_to_2026.0.py
uv run python scripts/render_2019.1_taxonomy_report.py
```

The first command writes the comparison CSV, JSON, HTML, and review audits. The second renders the
accepted comparison PDF. Review the generated files under `dist/$release_id/comparison/` before
continuing. The detailed procedure is documented in
[`docs/2019.1-to-2026.0.md`](docs/2019.1-to-2026.0.md).

For later releases, compare the previous public checklist with the new checklist:

```sh
uv run python scripts/compare_releases.py \
  "release-assets/<previous-release-id>/checklist.csv" \
  "dist/$release_id/checklist.csv" \
  "dist/$release_id/comparison"
```

### 4. Prepare the GBIF/IPT package

Complete the citation, publisher, licence, rights holder, and other known publication fields in
`publication/publication.toml`, then run:

```sh
uv run python tests/validate_publication.py publication/publication.toml
uv run python scripts/build_ipt_checklist.py publication/publication.toml
uv run python tests/validate_ipt_checklist.py "dist/$release_id/gbif"
```

Upload `dist/$release_id/gbif/checklist.csv` to IPT and map it to the GBIF Taxon core definition
recorded in `ipt-metadata.json`. It contains a normalized kingdom-to-species hierarchy linked by
`parentNameUsageID`. `acceptedNameUsageID` is blank because this export contains accepted taxa only;
use it only if synonym or misapplied-name records are added later. Taxon concepts cite the pinned
AviList release through `nameAccordingTo` and `nameAccordingToID`. English names are mapped directly
to the Taxon core's `vernacularName` field with the ISO 639-1 language code `en`. There are no IPT
extension tables. Use `ipt-metadata.json` to complete the IPT metadata form. GBIF publication is an
external manual step.
After publication, record the GBIF dataset URL and DOI in `publication/publication.toml`, complete
the publication and editorial dates, and change `status` from `draft` to the final status.

### 5. Render the final checklist PDF

```sh
uv run python tests/validate_publication.py publication/publication.toml
uv run python scripts/render_checklist_pdf.py publication/publication.toml --keep-typ
```

The PDF is written into the canonical `dist/$release_id/` bundle. Category definitions are maintained
in `data/curation/category_definitions.csv`; species assignments are maintained in
`data/curation/categories.csv`, except `water_bird`, which is derived during the checklist build.

### 6. Build a local website preview

Before staging, the website can be built directly from the complete local release:

```sh
uv run python scripts/build_site.py \
  --release-dir "dist/$release_id" \
  --output _site \
  --allow-draft
uv run python tests/validate_site.py _site
uv run python scripts/serve_site.py
```

The preview server starts at `http://127.0.0.1:8000` when available, otherwise it uses the next free local port and prints the URL. Stop it with `Ctrl+C`.

`--allow-draft` allows the website to be previewed or deployed before the formal release metadata is
complete. The publication status is informational and does not control GitHub Pages deployment.

### 7. Stage the accepted public assets

Once the checklist, audits, comparison, GBIF package, metadata, PDF, and website preview have been
reviewed and accepted:

```sh
uv run python scripts/stage_release_assets.py
```

This copies, without transforming, `manifest.json`, `checklist.csv`, the checklist PDF, the
comparison CSV/JSON, and the comparison PDF when available from `dist/$release_id/` into the tracked
`release-assets/$release_id/` directory. It excludes raw inputs, audits, latest records,
supplementary taxa, and GBIF export files.

### 8. Verify and publish the staged website

```sh
uv run python scripts/build_site.py \
  --release-dir "release-assets/$release_id" \
  --output _site
uv run python tests/validate_site.py _site
```

Commit the accepted source changes, `publication/publication.toml`, and
`release-assets/$release_id/`. Push the publication branch to update GitHub Pages. When the formal
release is ready, create an annotated Git tag named exactly `$release_id` and a GitHub Release with
the same name. GitHub Actions rebuilds and validates the website from the committed staged assets
before deploying GitHub Pages, regardless of the publication status.

Publishing organizations, project partners, data sources, and contributors are described at the start of this README and maintained in `publication/publication.toml`.


## Structure

| Layer | Location | Role |
| --- | --- | --- |
| Release configuration | [`config/release.toml`](config/release.toml) | Pins the source versions and paths for the release being prepared. |
| External inputs | `data/ebird/`, `data/avilist/` | Local licensed EBD and versioned taxonomy sources. |
| Project decisions | [`data/curation/`](data/curation) | Maintained mappings, corrections, categories, and sensitive-species membership. |
| Release build | [`scripts/build_release.py`](scripts/build_release.py) | Produces the ignored `dist/<release-id>/` bundle. |
| Website release assets | `release-assets/<release-id>/` | Versioned public website inputs staged from a local release build. |
| Publication source | [`publication/`](publication) | Editable metadata and prose used by the PDF and website. |
| Website source | [`website/`](website) | Maintained home, checklist, and changes pages. |
| Public website | GitHub Pages | Builds the live website from the active, versioned public asset bundle. |


## Data use and licensing

The new checklist data and publication material are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), matching the GBIF checklist dataset. The repository code is licensed under MIT. The 2019 edition, raw eBird data, AviList source files, and other third-party material retain their own terms; see [`LICENSE`](LICENSE).
