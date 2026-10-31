# Birds of Kenya checklist policy

The *Checklist of the Birds of Kenya* is a public, living account of birds represented in Kenya. This version uses AviList for taxonomic identity, sequence, family placement, and default English and scientific names.

## Taxonomy and species names

This checklist follows AviList v2025b. It supplies the taxon identity, order, family, scientific name, and the English name displayed in this version. AviList v2025 adopted the IOC World Bird List v15.1 English names as its default where taxonomy aligned.

From AviList v2026 onward, AviList's English Names Committee will recommend the global-standard English names. Future versions of this checklist will adopt those AviList names by default. See AviList's [English Names Committee terms of reference](https://www.avilist.org/tor/).

## Taxonomic resolution

The public checklist is species-level for the current release, following AviList.
Using [eBird taxonomic definitions](https://support.ebird.org/en/support/solutions/articles/48000837816-the-ebird-taxonomy#anchorISSF), subspecies (ISSF) are rolled up to species level, as are intergrades and forms when possible (as defined by the eBird `REPORT_AS` code). Slashes and unidentified taxa are not included. Hybrids and domestic forms are retained in a separate local supplementary table.

Following [eBird exotic status](https://support.ebird.org/en/support/solutions/articles/48001218430-exotic-and-introduced-species-in-ebird), the main checklist retains native and naturalized species. Escapee records, hybrids, domestic taxa, and other retained non-species entities are retained separately in local supplementary taxa tables; those tables are not part of the website downloads or GBIF export.

Taita Falcon and Saker Falcon are classified as sensitive-species in eBird and their records are withheld from the EBD.

## Geographic scope

The geographic scope is the Kenya coverage used to obtain the EBD, which closely follows Kenya's Exclusive Economic Zone (EEZ) for marine records.

## Categories

The public checklist distinguishes categories derived for each release from external statuses and editorial review flags. They describe different things and must not be treated as interchangeable.

**Release-derived categories.** `HIST` identifies a species whose latest qualifying Kenyan eBird record is more than 50 years before the release reference date. `RAR` identifies a species with fewer than five release observations; one observation clusters eBird reports within three calendar months and 3 km, with travelling checklists allowed an additional radius of half their reported distance (capped at 5 km). A species admitted solely through an accepted [East African Rarities Committee (EARC)](https://www.eararities.org/) decision has `0` eBird observations and is marked `RAR`. `RAR` is only a review aid: it is not an EARC decision or threshold, and it is not a conservation assessment. `W` identifies a waterbird from AviList family placement using the 33-family scope of the Ramsar Convention's [Waterbird Population Estimates](https://www.ramsar.org/sites/default/files/2024-03/SC63_20_waterbird_population_estimates_e.pdf).

**External statuses and review flags.** The Status column uses `NAT` for naturalized species; native species are unlabelled, while escapee-only species are outside the main checklist. `S` marks sensitive species whose observation evidence is withheld. `PE` marks Pending EARC: a species added since 2019 and not represented in the curated EARC decision list. It is a review flag, not an EARC decision. The separate Conservation column displays the global IUCN Red List category supplied by AviList.

## Record review

The [East African Rarities Committee (EARC)](https://www.eararities.org/) is the defining authority for the acceptance of new, very rare, or disputed national records. Its remit includes new species and up to the fifth national record, and it may also assess records of species considered extinct or possibly extinct, long-unrecorded residents, and major range extensions.

EARC decisions concern the acceptance of national occurrence evidence, not the taxonomic validity of a species. Accepted decisions can establish checklist membership where EBD evidence is absent. Rejected decisions remain as annotations and do not remove the species or its source records from this version. A rejection can concern a particular record; it does not establish that all evidence for the species is invalid. A refereed publication or other documented evidence may support an EARC submission or help interpret a record, but it does not replace an EARC decision where the record falls within EARC's remit.

A species surfaced by the evidence pipeline before a matching EARC decision is recorded may remain visible pending review. When it appears as an addition to or removal from the 2019.1 checklist, the website marks it `PE`. This flag means that the repository has no mapped EARC decision for the change; it does not itself confirm that a submission is active, and it must not be read as acceptance.

## Changes

Version v2026.0 is a released snapshot with unresolved record review retained for a later version. Draft category definitions and assignments remain available in the repository and are not exported to GBIF.

Each new release should explain what changed: source coverage, taxonomy, names, categories, EARC decisions, and unresolved records. An added or removed row is a question for interpretation, not automatically an arrival, disappearance, split, or lump. The comparison distinguishes taxonomic concept changes from additions and removals and exposes the applicable EARC decision or `Pending EARC` flag.
