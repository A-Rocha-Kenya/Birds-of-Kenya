# Kenya checklist v2019.3

This revision corrects two Avibase IDs from v2019.2. The printed names, entry text, notes, status flags, and checklist membership are preserved. The PDF is the original printed 2019 edition.

- **Lesser Sand Plover**, sort 182, changes from `66DA1FB3` (Siberian) to `828D3D5A` (Tibetan). The 2019 Kenyan records all refer to the Tibetan concept.
- **Woolly-necked Stork**, sort 293, changes from `F76E7B80` (Asian) to `5157C558` (African). The printed account explicitly names the African form, *Ciconia microscelis*.

The Avibase sources are in `corrections.csv`. Run `uv run python scripts/build_legacy_releases.py` from the repository root to regenerate the checklist and verify the sealed bundle.
