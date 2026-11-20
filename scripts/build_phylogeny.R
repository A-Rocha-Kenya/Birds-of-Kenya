#!/usr/bin/env Rscript
# Extract the dated phylogeny of the active checklist's species from clootl (the eBird/Cornell Aves tree).
#
# Usage: Rscript scripts/build_phylogeny.R [release-id]
# Writes data/phylogeny/: kenya.tre (Newick, branch lengths in millions of years), tips.csv (tree tip
# code -> Avibase ID), citations.csv (studies supporting the pruned tree) and source.json (versions).
# Rerun whenever the active release changes its species; the website build checks they match.

suppressMessages({
  library(clootl)
  library(ape)
  library(jsonlite)
})
invisible(Sys.setlocale("LC_CTYPE", "en_US.UTF-8"))

tree_version <- "1.7"
taxonomy_year <- 2025

args <- commandArgs(trailingOnly = TRUE)
release <- if (length(args)) args[1] else {
  line <- grep("^active_release", readLines("publication/releases.toml"), value = TRUE)
  sub('.*"(.*)".*', "\\1", line)
}
checklist <- read.csv(file.path("release-assets", release, "checklist.csv"), stringsAsFactors = FALSE, encoding = "UTF-8")

# clootl uses an eBird taxonomy year; codes renamed since then are matched by scientific name.
taxonomy <- taxonomyGet(taxonomy_year)
species <- taxonomy[taxonomy$CATEGORY == "species", ]
by_code <- checklist$ebird_species_code %in% species$SPECIES_CODE
tip <- ifelse(by_code, checklist$ebird_species_code, species$SPECIES_CODE[match(checklist$scientific_name, species$SCI_NAME)])
if (anyNA(tip)) {
  stop("No clootl taxon for: ", paste(checklist$scientific_name[is.na(tip)], collapse = ", "),
       ". Add a mapping before rebuilding the phylogeny.")
}
if (anyDuplicated(tip)) stop("Several checklist species map to one clootl taxon: ", paste(unique(tip[duplicated(tip)]), collapse = ", "))

tree <- extractTree(species = tip, label_type = "code", taxonomy_year = taxonomy_year, version = tree_version)
stopifnot(Ntip(tree) == nrow(checklist), setequal(tree$tip.label, tip))

out <- "data/phylogeny"
dir.create(out, showWarnings = FALSE, recursive = TRUE)
write.tree(tree, file.path(out, "kenya.tre"))
tips <- data.frame(
  tip = tip, avibase_id = checklist$avibase_id, scientific_name = checklist$scientific_name,
  match = ifelse(by_code, "ebird_code", "scientific_name")
)
write.csv(tips, file.path(out, "tips.csv"), row.names = FALSE, fileEncoding = "UTF-8")
citations <- getCitations(tree, version = tree_version)
write.csv(citations, file.path(out, "citations.csv"), row.names = FALSE, fileEncoding = "UTF-8")
write_json(list(
  release = release,
  source = "clootl",
  clootl_package = as.character(packageVersion("clootl")),
  tree_version = tree_version,
  taxonomy_year = taxonomy_year,
  species = Ntip(tree),
  root_age_mya = round(max(node.depth.edgelength(tree)), 2),
  studies = nrow(citations),
  citations = gsub("\\s+", " ", gsub("[_“”]", "", format(citation("clootl"), style = "text")))
), file.path(out, "source.json"), auto_unbox = TRUE, pretty = TRUE)

cat(sprintf("Wrote %d species (%d matched by name) from clootl tree v%s, %d studies\n",
            Ntip(tree), sum(!by_code), tree_version, nrow(citations)))
