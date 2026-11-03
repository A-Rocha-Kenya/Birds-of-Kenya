# Checklist PDF publication

`publication.toml` defines the canonical checklist PDF for the editable candidate. Each archived release has exactly one PDF and its own frozen metadata. The renderer records its checklist, metadata, pending-review table, policy, category definitions and renderer hashes; staging rejects a stale PDF.

```sh
uv run python scripts/render_checklist_pdf.py publication/publication.toml --keep-typ
uv run python scripts/stage_release_assets.py
```

Editorial profiles are local review tools, not separate downloadable PDFs for the same archived version. Only the canonical `render.output_filename` is staged. Comparison PDF generation is retired. See [release architecture](../docs/release-architecture.md) for historical PDF labels, immutability, version-specific curation and website activation.
