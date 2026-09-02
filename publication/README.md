# Publication profiles

`publication.toml` holds the canonical publication metadata for a release. It continues to point to the full release evidence, category definitions, and EARC review material.

Public-facing variants belong in `profiles/`. A profile overlays only the editorial fields that differ from the canonical metadata, such as the title-page wording, introduction, PDF filename, and visible status definitions.

For the 2026 draft:

```sh
python3 tests/validate_publication.py publication/publication.toml --profile publication/profiles/2026-draft.toml
python3 scripts/render_checklist_pdf.py publication/publication.toml --profile publication/profiles/2026-draft.toml
```

The profile does not change checklist data or EARC provenance. It replaces the policy pages with the reader introduction and hides the `PE` (Pending EARC) badge from the PDF.
