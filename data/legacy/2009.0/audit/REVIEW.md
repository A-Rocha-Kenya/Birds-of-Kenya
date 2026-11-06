# Fourth-edition source review

All 1,100 PDF checklist entries, 90 families and 313 species notes pass the independent audit. The extraction uses Poppler layout text; the audit reconstructs entries and notes using pdfplumber coordinates and checks entry lines against Poppler raw text. It compares scientific/common names, original entry, family assignment, note content and all representable status flags. Whitespace is normalized for comparison. There are zero failures in `pdf_failures.csv`.

The combined 51-page source PDF is the fourth edition dated September 2009 with corrections of 13 December 2017. Accordingly some differences from the original workbook can reflect later editorial corrections. Its 39 checklist pages were rendered for inspection; targeted visual checks covered the name disagreements and the omitted Weaver account. This was a complete programmatic entry audit with targeted visual review, not manual proofreading of every glyph on every page.

## Excel comparison

All four species sheets contain 1,101 records. The fifth sheet contains 89 families. The PDF has 1,100 entries and 90 families. `excel_disagreements.csv` preserves every non-whitespace discrepancy with sheet, cell, PDF page and both values. The numerous note and English-family differences include codes stored as notes, wording differences, punctuation and inconsistent headings; the count is not a count of independent biological errors. `summary.json` gives counts by sheet and field and SHA-256 hashes of the inputs and output.

Important content disagreements, resolved in favour of the PDF:

| PDF position | PDF reading | Workbook issue |
| --- | --- | --- |
| 25 | Plectropterus gambensis | Plectopterus spelling |
| 166 | Ovambo Sparrowhawk | Ovampo spelling |
| 188 | Spizaetus africanus | Spitzaetus spelling; PDF also has an expanded note |
| 193 | Neotis heuglinii | heuglini spelling |
| 354 | Fischer’s Lovebird, Agapornis fischeri | A. personatus erroneously repeated |
| 427 | Telacanthura ussheri | Telecanthura; PDF explicitly notes the corrected spelling |
| 634 | Psalidoprocne pristoptera | holomelas instead |
| 670–672 | Eremopterix | Eremopteryx spelling |
| Excel 977 | Rüppell’s Weaver omitted from checklist | Workbook includes it; PDF p42 rejects the Kenyan record |

Additional differences include Quailplover and Wren-Warbler/Crimsonwing hyphenation, a missing Burhinidae heading in Excel, inconsistent stone-curlew and skua family allocation, and misplaced species notes. The PDF values are retained even where the workbook might look more familiar. Full individual differences and original numbering remain available in the audit CSVs.

## Scope and remaining decisions

Names and taxonomy are transcribed, not modernized. The hybrid is intentionally retained; omitted-species discussion is not counted as checklist membership. Source threat categories and qualifications remain in `entry_checklist_of_kenya`; the shared CSV schema cannot represent all of them as separate flags.

Avibase coverage is reported separately in `../avibase/`. There are 1,051 supported assignments and 49 unresolved concepts. The automated source audit does not certify those historical taxon interpretations. Read the mapping status and evidence before treating an ID as an exact historical global concept.

The maintained v2019.1 CSV has only schema cleanup; its identifiers remain unchanged. The three approved identifier corrections are published separately as v2019.2; see `../../2019.2/corrections.csv`. Published older bundles remain immutable.

The source has three front-matter pages. Printed checklist pages 1–39 are PDF pages 4–42. The extractor and coordinate audit skip those front-matter pages explicitly. Only the combined source PDF is retained.
