# Phylogeny

Dated evolutionary tree of the active checklist's species, used by the website's Tree page. It is
pruned from the Cornell Lab of Ornithology / Open Tree of Life Aves tree with the R package
[clootl](https://github.com/eliotmiller/clootl).

| File | Content |
| --- | --- |
| `kenya.tre` | Newick tree; branch lengths in millions of years; tips are eBird species codes |
| `tips.csv` | Tip code → Avibase ID, and whether it matched by eBird code or scientific name |
| `citations.csv` | Published studies supporting the pruned tree (`clootl::getCitations`) |
| `source.json` | clootl package, tree version, eBird taxonomy year, root age and citations |

Regenerate after the active release changes its species:

```sh
Rscript scripts/build_phylogeny.R
```

clootl uses an eBird taxonomy year (currently 2025), so checklist codes renamed since then are
matched by scientific name. The script stops if a species has no match. `scripts/build_site.py`
refuses to build if the tree's tips differ from the active release's species.
