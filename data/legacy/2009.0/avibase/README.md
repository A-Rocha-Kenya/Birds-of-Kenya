# Avibase evidence and unresolved concepts

Research date: 6 November 2026. These files preserve factual name/identifier associations from Avibase, not a claim that modern nomenclature should replace the PDF’s names.

- `source_taxa.csv`: 5,556 distinct taxonomy/name/identifier records from the Avibase Kenya checklists for Clements 5 including 2005 revisions, Howard & Moore 4 including corrigenda, and Clements 2025, plus the changed rows in its Kenya comparisons of Howard & Moore 3 vs Clements 2009, Howard & Moore 3 vs Clements 2025, and Clements 2009 vs Clements 2025. Comparison tables contain changes only; absence from one does not mean a taxon is absent from that taxonomy. Each record includes its original species-profile URL.
- `profile_evidence.csv`: 193 distinct profile headings recovered through indexed Avibase pages for potential concept conflicts and aliases. Twenty-one important concepts were additionally read directly in logged-in Chrome. The evidence contains names and concept labels, not entire web pages.
- `reviewed_matches.csv`: explicit decisions supported by PDF notes, separate PDF entries, and Avibase profiles, including decisions to leave an entry unresolved.
- `matches.csv`: generated coverage of every PDF entry, including assigned ID, status, candidates, rationale, source taxonomies and links.
- `unresolved.csv`: all entries with blank IDs. This is an editorial work queue, not a list of absent Kenyan birds.

Sources: [Avibase Kenya checklist](https://avibase.bsc-eoc.org/checklist.jsp?region=KE&lang=EN) and [Compare taxonomies](https://avibase.bsc-eoc.org/compare.jsp?lang=EN), with the editions above selected in the website. Retrieved tables are preserved as `source_taxa.csv`, so mapping does not require a live web request. Source snapshots are research inputs; current website results may change.

The mapping prefers a unique exact scientific-name ID in Howard & Moore 3/Clements 2009 changed-row records. If neither has a record, it requires agreement among all available exact-name records. Competing IDs remain blank unless there is a recorded manual decision. Separately printed species cannot receive the same ID. This provides reproducible source-supported matches; it does not demonstrate every global taxon boundary independently. `historical_name_match` and `consistent_name_match` deliberately differ from `reviewed`.

Examples of reviewed historical aggregates include Tropical Boubou (the PDF p41 explicitly retains the Kenyan forms together), Grey-headed Sparrow (the note retains gongonensis, suahelicus and swainsonii), and Yellow Wagtail (the note does not adopt the Eastern split). Conversely, the historical Olive Thrush ID includes Taita Thrush, which the PDF lists separately, so it is rejected and left unresolved. Eastern Double-collared Sunbird and Winding Cisticola also need a more exact historical boundary. Northern Black Tit and the reichardi/gularis seedeaters require distinguishing an old broad concept from a misapplied regional name.

No 2019 ID is copied merely because the spelling or old checklist number agrees. Keep uncertain IDs blank until the historical concept can be established; edit `reviewed_matches.csv` with an evidence-based reason and rerun `python3 scripts/map_2009_avibase.py`.
