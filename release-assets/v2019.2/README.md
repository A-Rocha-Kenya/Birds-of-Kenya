# Kenya checklist v2019.2

This is a corrected digital transcription of the 2019 fifth edition, released on 6 November 2026. It contains the same 1,181 printed entries as v2019.1, including group headings and subspecies rows. The PDF remains the original printed edition; it does not incorporate the CSV corrections.

`corrections.csv` records the three changed identifier cells and their Avibase references:

- Sort 775, Grey-headed Sparrow parent: E10D0809 → 2F9F81C9, the broad group containing the four printed children.
- Sort 775.1, Northern Grey-headed Sparrow: 2F9F81C9 → E10D0809, the narrow Northern species concept. The printed ugandae name is retained; the identifier follows the existing species-level matching convention rather than asserting a subspecies-specific ID.
- Sort 943, Eurasian Reed Warbler: 3F0EE474 → 5C17300B, the scirpaceus/fuscus concept, excluding separately listed African Reed Warbler. This is an explicit narrower interpretation. The printed account does not establish the extralimital avicenniae boundary; the alternative historical 2D3FC761 includes avicenniae. No claim is made that the PDF itself spells out that distinction.

No names, entry lines, membership, status flags or note values are changed. The notes column is now simply `note`. Cross-edition fields `sort_1996`, `sort_2009` and `note_2009` are removed. The old numbering remains in `../2019.1/numbering_crosswalk.csv`. Published v2019.0/v2019.1 bundles, Git tags and GitHub assets remain unchanged and retain their original schemas.

The source PDF is `../2019.1/source.pdf`. Rebuild the CSV and stage a new historical bundle with `python3 scripts/build_legacy_releases.py`. Existing sealed bundles are verified rather than overwritten. A further data edit requires another revision ID.

The v2019.2 archive records both its correction relationship to v2019.1 and its reviewed mappings to v2025.0 in `transitions.json`. In particular, the broad Grey-headed Sparrow parent connects to all four modern species, and the narrower Eurasian Reed Warbler joins the broader modern Reed Warbler concept. These links preserve concept lineage; they do not transfer observation data or represent newly observed Kenyan species.
