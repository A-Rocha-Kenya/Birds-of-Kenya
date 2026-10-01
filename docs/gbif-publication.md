# Update the GBIF checklist

Use the existing IPT resource `birds-of-kenya-checklist` and its registered GBIF
record ([dataset DOI](https://doi.org/10.15468/mehwcx)). Keep the resource shortname,
registration, and existing taxon identifiers when publishing later versions.

1. After building the new release, generate and validate the update:

   ```sh
   release_id=$(python3 -c 'import tomllib; print(tomllib.load(open("publication/publication.toml", "rb"))["release_id"])')
   uv run python tests/validate_publication.py publication/publication.toml
   uv run python scripts/build_ipt_checklist.py publication/publication.toml
   uv run python tests/validate_ipt_checklist.py "dist/$release_id/gbif"
   ```

2. In IPT, replace the existing data source with
   `dist/<release-id>/gbif/checklist.csv`. Preserve the Taxon core mapping and
   `taxonID` record identifier; recheck mappings if the exported columns changed.
3. Update only changed metadata from `dist/<release-id>/gbif/ipt-metadata.json`:
   citation/release label, source versions, methods, geographic and temporal
   coverage, and release notes. Keep approved creator order, publisher, and licence
   unless they changed. The JSON is a worksheet for the editor, not an EML upload.
4. Preview and publish a new IPT version. Check the generated archive's counts and
   hierarchy, then check the updated GBIF record after ingestion. Higher taxa are
   included, so the total Taxon core count exceeds the species count.
5. Record any changed GBIF URL or citation DOI in `publication/publication.toml`
   and rebuild affected publication products. IPT's version number is separate
   from the repository release ID; mention the repository version in its citation
   and version description.

See the [IPT guide to updating and publishing resources](https://ipt.gbif.org/manual/en/ipt/latest/manage-resources).
