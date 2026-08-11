# Birds of Kenya

A reproducible, versioned checklist of bird species represented in Kenya, following [AviList](https://www.avilist.org/) taxonomy and names and grounded in [Kenya eBird records](https://ebird.org/region/KE).

## Data source

Each release pins one [eBird Basic Dataset](https://ebird.org/about/download-ebird-data-products) month, its matching [eBird taxonomy](https://www.birds.cornell.edu/clementschecklist/download/), and one compatible [AviList](https://www.avilist.org/) version. In addition, four curated tables are used for (1) sensitive species, (2) exceptional eBird-to-AviList alignments, (3) version-scoped exotic-code corrections, and (4) Kenya checklist categories.

## Checklist policy

The [checklist policy](docs/policy.md) defines the scope, evidence, stewardship, categories, and publication rules.

## Release pipeline

A new release is generated with
```
uv run python scripts/build_release.py config/release.toml
```
The [release pipeline](docs/release-pipeline.md) explains inputs, mapping rules, outputs, audits, comparisons, validation, and the complete release sequence.


## PDF publication

Render the PDF with:
```sh
uv run python scripts/render_checklist_pdf.py publication/publication.toml --keep-typ
```
The `publication.toml` file supplies the website's public release label, citation, publisher, and, once available, its GBIF dataset URL and DOI.

Category names and legend metadata are maintained in `data/curation/category_definitions.csv`. Species assignments are maintained in `data/curation/categories.csv`, except `water_bird`, which is derived from the [Ramsar Waterbird Population Estimates](https://www.ramsar.org/sites/default/files/2024-03/SC63_20_waterbird_population_estimates_e.pdf) family definition during each release build.

## GBIF IPT checklist export

Build the IPT-uploadable Darwin Core checklist and a companion metadata summary with:

```sh
uv run python scripts/build_ipt_checklist.py publication/publication.toml
uv run python tests/validate_ipt_checklist.py dist/2026-06.0/gbif
```

The export contains one accepted AviList species per Kenya checklist entry. Upload `checklist.csv` to the IPT as a Checklist resource, map its Darwin Core Taxon headers, and use `ipt-metadata.json` to complete the IPT metadata form. Complete the citation, publisher, licence, and rights holder in `publication.toml` before publishing through GBIF.

The official publishing organization is Nature Kenya—the East Africa Natural History Society. Partner organizations are Nature Kenya, A Rocha Kenya, and the National Museums of Kenya (NMK). Contributors include the East African Rarities Committee (EARC), eBird Kenya, Victor Ikawa, Fleur Ng'weno, Colin Jackson, Nigel Hunter, Okech, Washington Wachira, James Bradley, Raphaël Nussbaumer, and Richard Stratton Hatfield.

## Website

Generate the comparison data and assemble the website with:
```sh
uv run python scripts/render_2019.1_taxonomy_report.py
uv run python scripts/stage_release_assets.py
uv run python scripts/build_site.py \
  --release-dir release-assets/2026-06.0 \
  --output _site \
  --allow-draft
uv run python tests/validate_site.py _site
uv run python -m http.server --directory _site
```

`release-assets/<release-id>/` is the versioned, Git-tracked public subset of a local `dist/<release-id>/` build. It contains only the assets needed to assemble the website; raw source data, audits, and local build output remain untracked. `--allow-draft` is intentionally required while `publication/publication.toml` has `status = "draft"`. A production build rejects incomplete publication metadata, including missing GBIF links.


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
