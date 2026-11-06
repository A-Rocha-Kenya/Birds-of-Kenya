# Kenya checklist, fourth edition

`source.pdf` is the combined 51-page September 2009 checklist with minor corrections dated 13 December 2017. Its three front-matter pages precede the 48-page main document. The 1,100 entries in `checklist.csv` come from printed pages 1–39 (PDF pages 4–42), including the printed hybrid entry. The `entry_checklist_of_kenya` field preserves the printed entry text and codes, with the checkbox glyph removed. The `note` field holds following species notes and inline corrections.

Run `python3 scripts/extract_2009_checklist.py` to reproduce the CSV from the embedded PDF text using Poppler. The script retains the historical Avibase assignments from the sealed v2009.0 checklist. The fourth edition used the 1996 list, Birds of Africa and Howard & Moore 3. The mapping prioritized contemporary Avibase concepts, then used consistent names and reviewed aliases where supported. There are 1,051 assigned IDs and 49 unresolved historical concepts. The unresolved entries remain in the CSV and are listed in the release assets.

The independent audit used PDF coordinates and Poppler raw text to verify every entry, family, status and note. It found zero transcription failures and compared all five sheets of the original A Rocha Kenya Science SharePoint workbook. The PDF governs disagreements. The workbook included Rüppell’s Weaver at position 977, which the PDF explicitly omits.

Run `python3 scripts/audit_2009_checklist.py` with Poppler, pdfplumber and openpyxl. It reads the frozen workbook from the v2009.0 Git tag and writes regenerated reports to `tmp/audit-2009/`. Fetch the v2009.0 tag if your checkout lacks it.

The original workbook, detailed PDF/Excel audit, numbering crosswalk and Avibase lookup evidence are preserved together in the [v2009.0 source snapshot](https://github.com/A-Rocha-Kenya/Birds-of-Kenya/tree/v2009.0/data/legacy/2009.0). The [release assets](https://github.com/A-Rocha-Kenya/Birds-of-Kenya/releases/tag/v2009.0) include the checklist, PDF and unresolved concepts.
