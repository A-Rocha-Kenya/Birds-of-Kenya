# Birds of Kenya

**Version v2025.0 of the *Checklist of the Birds of Kenya*** uses AviList v2025b, eBird taxonomy 2025 and the June 2026 EBD. The release year identifies its taxonomic baseline, independently of the observation dataset month and publication date. The checklist continues a national publishing tradition established by editions in 1981, 1986, 1996, 2009, and 2019.

The corporate author is the **Bird Committee of Nature Kenya—the East Africa Natural History Society**. Nature Kenya is the official publisher and institutional home of the checklist.

## Nature Kenya—the East Africa Natural History Society

[Nature Kenya](https://naturekenya.org/) is the East Africa Natural History Society (EANHS) in Kenya. Founded in 1909, it is a membership-based organization that invites everyone to join an active society, participate in the study of nature, and support conservation activities.

## Organizations and contributors

- **Publisher and institutional home:** Nature Kenya—the East Africa Natural History Society
- **Partners and contributing organizations:** A Rocha Kenya; National Museums of Kenya (NMK); Kenya Bird Map; eBird Kenya; East African Rarities Committee (EARC)
- **Named contributors:** Brian Finch; Colin Jackson; Don Turner; Fleur Ng’weno; James Bradley (eBird record management); John Fanshawe; Nigel Hunter; Okech; Raphaël Nussbaumer (data curation); Richard Stratton Hatfield; Victor Ikawa; Washington Wachira

The publication, interactive website, downloadable data, and taxonomy comparison are assembled from the same versioned release. The full editorial metadata is maintained in [`publication/publication.toml`](publication/publication.toml).

## Data source

Each release pins one [eBird Basic Dataset](https://ebird.org/about/download-ebird-data-products) month, its matching [eBird taxonomy](https://www.birds.cornell.edu/clementschecklist/download/), and one compatible [AviList](https://www.avilist.org/) version. Curated tables supply species membership, source-taxonomy corrections and eBird-to-AviList exceptions, exotic-code corrections, occurrence-review decisions, and Kenya checklist categories.

## Checklist policy

The [checklist policy](docs/policy.md) defines the scope, evidence, stewardship, categories, and publication rules.

## Checklist build logic

The [checklist build documentation](docs/release-pipeline.md) defines exactly how the pinned source
data and curated decisions become `dist/<release-id>/checklist.csv`. It covers taxonomy matching,
observation clustering, evidence routing, AviList mapping, sensitive species, outputs, and audits. It
does not describe publication or website deployment.

## Release and publication workflow

The editable candidate is separate from the public website version. `config/release.toml` and `publication/publication.toml` prepare a release; `publication/releases.toml` explicitly selects the active published version. The active published release is v2025.0. Future candidates can be prepared without changing the public website.

Each archived release has its own checklist CSV, taxonomic snapshot, curated decisions, publication metadata and one canonical checklist PDF. Older checklists remain downloadable on the website. The original printed 2019 PDF is labeled separately from its corrected 2019.1 CSV transcription. Comparison PDFs are retired.

The Changes page compares any two available versions, in either direction, using species additions/removals, names, classification and reviewed Avibase concept relationships. Species additions and removals are included. Observation counts, occurrence status and review decisions are excluded. Comparisons are generated from frozen snapshots without rerunning historical EBD analyses.

The selected edition is already published. Preview it with `uv run python scripts/build_site.py` followed by `uv run python scripts/serve_site.py`. After configuring a new draft ID, use the candidate refresh:

```sh
uv run python scripts/refresh_website.py
uv run python scripts/serve_site.py
```

This rebuilds and validates the candidate, regenerates its canonical PDF, stages a sealed draft bundle and builds its local preview. It does not change the public active release. For the published website, use `uv run python scripts/build_site.py`.

Follow [the future-release guide](docs/future-releases.md) and [release architecture](docs/release-architecture.md) for version-specific curation, scientific validation, immutable archives, stale-PDF checks, activation, GitHub Releases and tests. GBIF/IPT publication remains separate; see [the GBIF guide](docs/gbif-publication.md).

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

## Current source versions

The published v2025.0 archive retains the accepted 2025 taxonomy and June 2026 EBD evidence. The 2026 taxonomy/data upgrade is separate work and is not registered or shipped in this branch.
