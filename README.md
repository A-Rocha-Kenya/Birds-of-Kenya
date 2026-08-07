# Birds of Kenya

An interactive, browser-based checklist of bird species and subspecies recorded in Kenya. The site loads the repository's checklist data into a searchable, sortable, filterable table and provides links to external taxonomic and biodiversity resources.

The checklist is based on the *Checklist of the Birds of Kenya, 5th Edition (2019)*. The repository data has also received later taxonomy and identifier updates; the most recent committed update is from November 2023.

## What is included

- 1,185 checklist records spanning 107 scientific families.
- Common and scientific names, family names, and the 2019 Kenyan checklist order.
- Residency, migration, endemicity, rarity, historical-record, and extinction flags.
- IUCN Red List categories, BirdLife status, and waterbird classifications.
- Cross-references to ADU/Kenya Bird Map Atlas, Avibase, Wikidata, iNaturalist, ITIS, IUCN, Observation.org, GBIF, eBird/Clements, IOC, Howard & Moore, and HBW/BirdLife taxonomies where identifiers are available.
- Source materials for the 2019 fifth edition in PDF, DOC, and XLSX formats.

The interactive table initially hides the scientific and English family columns, BirdLife status, and the two waterbird columns. They can be revealed with the table's column controls.

## Use the checklist

1. Sort one or more columns using the column headers.
2. Open a header menu to filter by values or conditions.
3. Resize or freeze columns, and show or hide columns, from the table context menu.
4. Select **Export View Table** to download the current filtered view as `Birds_of_Kenya_2019.csv`.
5. Click an identifier in the table to open the corresponding external resource.

The site is read-only: filtering, column settings, and exports affect only the browser session and the downloaded file, never `data/main.csv`.

## Run locally

No package installation is required. Serve the repository directory over HTTP, then open [`src/index.html`](src/index.html) in a browser:

```sh
python3 -m http.server 8000
```

Open <http://localhost:8000/src/>. Serving over HTTP is required because the page fetches `data/main.csv` in the browser. The page uses pinned CDN-hosted copies of [Handsontable](https://handsontable.com/) and [Papa Parse](https://www.papaparse.com/), plus Google Fonts, so an internet connection is needed for the complete interface and styling.

Validate data changes with:

```sh
python3 tests/validate_data.py
```

GitHub Pages is deployed automatically from `main` by [`.github/workflows/pages.yml`](.github/workflows/pages.yml). The workflow validates the CSV, assembles the static site, and deploys it with the official Pages artifact actions.

## Repository layout

| Path | Purpose |
| --- | --- |
| [`src/index.html`](src/index.html) | Accessible page markup and pinned external library imports. |
| [`src/script.js`](src/script.js) | Parses the CSV, configures the table, calculates summaries, builds safe identifier links, and exports the visible view. |
| [`src/style.css`](src/style.css) | Responsive page, controls, summary cards, and loading/error styling. |
| [`data/main.csv`](data/main.csv) | Canonical machine-readable checklist: UTF-8 CSV with 1,185 data records and 68 columns. |
| [`data/sources/`](data/sources/) | Original fifth-edition checklist documents in PDF, DOC, and XLSX formats. |
| [`src/assets/`](src/assets/) | A Rocha Kenya logo assets used as the site favicon. |
| [`tests/validate_data.py`](tests/validate_data.py) | Standard-library data quality checks run before deployment. |
| [`.github/workflows/pages.yml`](.github/workflows/pages.yml) | GitHub Pages validation and deployment workflow. |

## Data dictionary

`data/main.csv` is the canonical data file. Blank values mean that the relevant value or identifier is not supplied. The website preserves all CSV fields, except that the individual status flags below are collapsed into one displayed `status` column.

| Fields | Description |
| --- | --- |
| `sort`, `sort_1996`, `sort_2009` | Display-order keys for the 2019, 1996, and 2009 Kenyan checklists. |
| `family_scientific`, `family_english`, `common_name`, `scientific_name` | Core taxonomy and names. |
| `AM`, `AMR`, `E`, `EX`, `HIST`, `IO`, `MM`, `N`, `NR`, `NRR`, `OM`, `PM`, `PMR`, `RAR`, `RS`, `SO`, `VIO`, `VM`, `VN`, `VO`, `VP`, `VSO`, `VSA` | Checklist status flags; their meanings are listed below. |
| `red_list`, `status_birdlife` | IUCN Red List category and BirdLife designation (Endemic, Introduced species, or Rare/Accidental). |
| `water_bird`, `strict_water_bird` | Waterbird classifications recorded as `TRUE` when applicable. |
| `ADU`, `avibaseid`, `wikiDataID`, `iNaturalisttaxonID`, `ITIS`, `IUCNtaxonID`, `ObservationorgID`, `GBIFID` | Identifiers for external biodiversity and taxonomy services. |
| `IOC--sort`, `IOC--rank`, `IOC--scientific_name`, `IOC--common_name`, `IOC--note`, `IOC--breeding_range`, `IOC--nonbreeding_range` | IOC taxonomy mapping, notes, and ranges. |
| `Clements--sort`, `Clements--code`, `Clements--rank`, `Clements--scientific_name`, `Clements--common_name`, `Clements--range` | eBird/Clements taxonomy mapping and range. |
| `H&M--sort`, `H&M--rank`, `H&M--scientific_name`, `H&M--common_name`, `H&M--range` | Howard & Moore taxonomy mapping and range. |
| `HBW&BL--SISRecID`, `HBW&BL--rank`, `HBW&BL--scientific_name`, `HBW&BL--common_name`, `HBW&BL--note` | Handbook of the Birds of the World / BirdLife taxonomy mapping and notes. |
| `entry_checklist_of_kenya`, `note_2009`, `note_2019` | Original 2019 checklist entry plus notes associated with the 2009 and 2019 checklists. |

### Status codes

| Code | Meaning |
| --- | --- |
| `AM` / `AMR` | Afrotropical migrant / Afrotropical migrant and resident. |
| `E` | Endemic species or race. |
| `EX` | Species thought to have become extinct in Kenya. |
| `HIST` | No record for 50 years (no record since 1968 or earlier). |
| `IO` / `VIO` | Visitor / vagrant from north-west Indian Ocean islands. |
| `MM` / `VM` | Migrant / vagrant from the Malagasy region. |
| `N` / `NR` | Nomadic or wanderer / nomadic or wanderer and resident. |
| `NRR` | Not recently recorded (during 1969–1999). |
| `OM` / `VO` | Migrant / vagrant from the Oriental region. |
| `PM` / `PMR` / `VP` | Palaearctic migrant / Palaearctic migrant and resident / Palaearctic vagrant. |
| `RAR` | Fewer than five East African Rarities Committee records at publication. |
| `RS` | Visitor from the Red Sea. |
| `SO` / `VSO` | Visitor / vagrant from the Southern Ocean or Antarctica. |
| `VN` | Vagrant from the Nearctic region. |
| `VSA` | Vagrant from southern Africa. |

## Maintaining the site and data

Edit `data/main.csv` to update the checklist. Keep its header row and UTF-8 encoding intact: `src/script.js` uses the field names to construct the table and its external links. Rows are expected to follow the value order defined by `sort`.

To add a new external identifier link or modify a current one, update the matching field handling in [`src/script.js`](src/script.js). To change table tooltips or the set of hidden columns, update its configuration there.

Before publishing a data change, run `python3 tests/validate_data.py`, then check that the table loads, filters work, the relevant identifier links resolve, and the export contains the intended view.

## Source documents

The project includes the original source files:

- [PDF checklist](data/sources/2019%20Checklist%20of%20the%20Birds%20of%20Kenya%205th%20Edition%20%282019%29.pdf)
- [Word checklist](data/sources/2019%20Checklist%20of%20the%20Birds%20of%20Kenya%205th%20Edition%20%282019%29.doc)
- [Excel checklist](data/sources/2019%20Checklist%20of%20the%20Birds%20of%20Kenya%205th%20Edition%20%282019%29.xlsx)

## Contributing

Please open an issue or pull request in the [A Rocha Kenya/Birds-of-Kenya repository](https://github.com/A-Rocha-Kenya/Birds-of-Kenya) with the source supporting any checklist, taxonomy, status, or identifier correction. Keep changes focused and explain the taxonomic authority or checklist reference used.

## License

The included PDF identifies the original checklist as copyright © Bird Committee, Nature Kenya—the East Africa Natural History Society, 2019. It does not state a Creative Commons, open-source, or other reuse license. [`LICENSE`](LICENSE) records this conservative position: do not assume permission to redistribute or reuse the checklist data or source documents. Contact [Nature Kenya](https://naturekenya.org/) or the relevant rights holder for clarification.
