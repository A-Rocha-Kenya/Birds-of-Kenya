# eBird source inputs

`ebd_KE_relJun-2026.zip` is the local Kenya eBird Basic Dataset used for the first EBD-based build. `eBird_taxonomy_v2025-4.csv` is the matching Clements/eBird taxonomy snapshot used to join `TAXON_CONCEPT_ID` and resolve `REPORT_AS` species codes. Both are ignored by Git and must not be redistributed from this repository.

`derived/` holds the checksum-controlled compact summaries, exotic-code correction audit, and five-newest-record extracts used as a local development cache. The release configuration and manifest record the source versions, filenames, and SHA-256 checksums. See [`docs/release-pipeline.md`](../../docs/release-pipeline.md) for the source fields, exotic-status routing, ISSF treatment, and taxonomy mapping used by the build.
