# Kenya checklist, fourth edition

`checklist.csv` contains the 1,100 entries on printed pages 1–39 (PDF pages 4–42) of `source.pdf`: the September 2009 edition **with minor corrections dated 13 December 2017**. This is not an untouched 2009 printing. The printed Hybrid Lovebird is retained; omitted taxa on pages 41–42 are excluded.

The CSV has 33 columns, matching `../2019.1/checklist.csv` with a single edition-local `note` column. Cross-edition sort and note columns have been removed from both canonical CSVs. Original numbering is preserved separately in `audit/numbering_crosswalk.csv` and `../2019.1/numbering_crosswalk.csv`.

`source.pdf` is the combined 51-page source, with cover, abbreviation key and map followed by the 48-page main document recovered from the local ngulia-dataset archive. The original Excel workbook was downloaded from the logged-in A Rocha Kenya Science SharePoint library, Documents → 02 Birds → 02. Bird Species lists, info & taxonomy → zChecklist_of_Kenya_2009. The PDF governs transcription when these sources disagree.

## Reproduce

Run from the repository root with Python 3, Poppler, pdfplumber and openpyxl installed:

```sh
python3 scripts/extract_2009_checklist.py
python3 scripts/audit_2009_checklist.py
```

The extractor uses the PDF’s embedded text; OCR is unnecessary. It also reapplies the recorded Avibase decisions through `scripts/map_2009_avibase.py`. Run that script separately after editing `avibase/reviewed_matches.csv`. `source_text.txt` preserves all 51 PDF pages, including commentary and omitted taxa.

## Transcription

- `sort` is the contiguous printed-entry position, 1–1100. The PDF prints no species numbers. Excel has 1101 entries, including Rüppell’s Weaver at number 977, which the PDF explicitly omits. Therefore Excel numbering exceeds `sort` by one from position 977 onward.
- Names, families and order follow the PDF, including historical names and printed spellings. `entry_checklist_of_kenya` retains the whole entry line with status codes, threat categories and inline corrections.
- `note` contains species notes, subspecies annotations and inline corrections. Wrapped lines are joined; printed hyphens are retained. Group commentary is preserved separately in `audit/group_commentary.csv` and the full text.
- Status flags follow the existing TRUE/blank convention. Lowercase am and pm map to AMR and PMR; Ex maps to EX and VS to VSO. Lowercase mm, io and om map to MM, IO and OM because the schema has no separate lowercase columns. Parentheses do not change the flags. The unmapped NM code remains in the original entry. Endemic subspecies do not set the species-level E flag.
- Waterbird classifications and other fields absent from the PDF remain blank. No 2019 status or note values are copied into the 2009 data.

## Audit and Avibase

See `audit/REVIEW.md` for the independent PDF audit and the Excel disagreements. All 1,100 entries pass the coordinate-based and second-text-engine checks; `audit/pdf_failures.csv` contains its header only. These checks establish transcription consistency, not infallibility of the published taxonomy.

`avibase/matches.csv` records an evidence trail for every entry. There are 1,051 populated identifiers and 49 unresolved entries, listed in `avibase/unresolved.csv`. Ambiguous global taxon boundaries are left blank rather than guessed. Most matches are unique historical or consistent exact-name matches in the consulted Avibase tables; these are distinguished from individually reviewed matches. A unique name match is evidence, not proof that every unprinted global species boundary matches the Kenyan authors’ intention.

The PDF p40 describes a conservative revision of the 1996 list using Birds of Africa and Howard & Moore 3. Historical concepts therefore matter: a broad 2009 species may legitimately have a different Avibase ID from its 2019 counterpart. The 2019 IDs and old numbering were considered as leads, not used as automatic matching rules. See `avibase/README.md` for the source tables and method.

This transcription is archived as v2009.0. The corrected 2019 transcription is v2019.2; its identifier changes are recorded in `../2019.2/corrections.csv`. Published v2019.0 and v2019.1 bundles remain unchanged.

Only the combined `source.pdf` is retained. Its original working filename was `sdsd.pdf`. Before removing the separate PDFs, all 48 main-source pages were verified to have identical extracted text to the standalone main document (`Kenya list 4th edition.pdf`). `source.xlsx` was originally `2009 Kenya list FINAL spp list_CJ-GCB.xlsx`. Audit page references use printed page numbers; add three for the PDF page number.
