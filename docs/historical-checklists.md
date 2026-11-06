# Historical checklist archive

The public archive includes v2009.0, v2009.1, v2019.0, v2019.1, v2019.2, v2019.3 and v2025.0. The active national checklist remains v2025.0. Any separately prepared 2026 candidate remains outside the public released archive.

v2009.0 transcribes the fourth edition of September 2009 with minor corrections dated 13 December 2017. It contains 1,100 entries. A complete source audit passes; 49 historical Avibase concepts remain unresolved and are excluded from taxonomy comparisons, with a warning on the Changes page. They remain in the full checklist download. The public PDF includes the front matter and all 48 main-source pages.

v2019.2 corrects three identifier cells from v2019.1, including the Grey-headed Sparrow parent/child placement and the over-broad Eurasian Reed Warbler concept. The scientific and English names, original entry lines, status flags and notes are unchanged. Its PDF is explicitly labeled as the original printed 2019 edition, which does not contain these digital corrections.

v2019.3 assigns the Tibetan Sand Plover and African Woolly-necked Stork concepts to the corresponding 2019 Kenyan entries. The [correction record](../data/legacy/2019.3/README.md) gives both old and new IDs. The original printed names and checklist membership are preserved.

Maintained historical inputs use `data/legacy/<year.revision>/checklist.csv`, `README.md`, and `source.pdf` where applicable. The new CSV schema has one `note` field. The v2009.0 tag preserves the original workbook and detailed audit and lookup evidence. The maintained legacy folder contains the final data and its source PDF. The audit regenerates reports under `tmp/audit-2009/`. Public downloads consistently use `Checklist-of-the-Birds-of-Kenya-v<year.revision>.csv` and `.pdf`; older archived files are copied under these download names without changing their content. Existing GitHub assets and sealed bundles remain byte-for-byte historical snapshots. Previous website CSV/PDF download URLs remain available as byte-identical compatibility aliases.

Reproduction:

```sh
python3 scripts/extract_2009_checklist.py
python3 scripts/audit_2009_checklist.py
python3 scripts/build_legacy_releases.py
python3 tests/validate_historical_releases.py
python3 scripts/build_site.py --output _site
python3 tests/validate_site.py _site
```

The PDF audit requires Poppler, pdfplumber and openpyxl; archive and site builds use Python 3.11 standard-library modules. Staging is immutable: an existing historical archive is verified, not resealed. Existing transition files remain in sealed bundles as provenance. New comparisons use the shared concept relationship table. The comparison dropdown shows the latest revision of each year and redirects older revision links to that year’s latest revision.

## Search for the third edition

The 1990s national checklist is the 1996 third edition, published by the Ornithological Sub-committee of the East Africa Natural History Society. The fourth-edition source cites it and describes how it was revised. A search of local Documents, Downloads and CloudStorage filenames, the available Science SharePoint taxonomy folder, and online references has not located a complete copy suitable for transcription.

The [1999 Arabuko-Sokoke Forest checklist](https://www.arocha.or.ke/wp-content/uploads/sites/16/2015/04/ASF-Bird-Checklist-1999.pdf) explicitly follows the 1996 national checklist, but is a regional subset and cannot substitute for it. No v1996 release is fabricated from later cross-references or this subset.

A further local lead is `KenyaListComparedToWBDBFinal.xls` in the old Kagu DB atlas archive. It contains a Nature Kenya–World Bird Database comparison with 1,366 data rows, including subspecies, but no verified edition date. It has not been treated as the 1996 national checklist or published as such.
