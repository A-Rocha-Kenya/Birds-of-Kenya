# Checklist of the Birds of Kenya - draft policy

**Status:** Working draft. This document is a starting point for Bird Committee review and is not yet an approved policy.

**Basis:** The *Checklist of the Birds of Kenya, Fifth Edition* (2019), especially its abbreviation key and “Some considerations in regard to this list” section. The 2019 edition remains the historical source and is preserved in `data/sources/`.

## 1. Purpose

The Checklist of the Birds of Kenya records bird taxa that have been accepted as having occurred in Kenya. It is a country checklist, not a prediction of current presence, a range map, or a global taxonomic authority.

The checklist includes both species and subspecies recognised by the AviList version used for a release. Every checklist row corresponds to one AviList taxonomic concept and is joined by `AvibaseID`.

The policy has two roles:

- define which Kenyan records and classifications belong in the checklist;
- define how those decisions are documented, reviewed, and changed.

## 2. Authorities and responsibilities

### Taxonomic authority

AviList is the taxonomic authority for each release. AviList supplies the scientific name, rank, hierarchy, family, sequence, and other taxonomic fields. The Kenyan Committee does not create a competing taxonomy in the checklist.

### Kenyan editorial authority

The Bird Committee is the editorial authority for Kenyan occurrence and Kenya-specific classifications. The curator records Committee decisions, maintains the working data, resolves AviList identifiers, prepares releases, and preserves the evidence and decision history.

### External information

Information from AviList, eBird/Clements, BirdLife, GBIF, and other sources is added through the project's reproducible enrichment process. Such information must be labelled with its source and version. It must not be presented as a Kenyan Committee assessment unless the Committee has made that assessment.

## 3. Geographic scope

**UNSET - Phase 0 decision:** Define whether “Kenya” includes mainland Kenya only, territorial waters, offshore islands, the Exclusive Economic Zone, or another boundary.

Until this is decided, no new geographic interpretation should be inferred. Records whose treatment depends on the boundary should be flagged for Committee review.

## 4. Taxonomic units and species limits

### Species and subspecies

Both species and subspecies are eligible checklist rows. A species record and a subspecies record are separate assertions.

If evidence demonstrates that a bird occurred in Kenya but does not support assignment to a particular subspecies, record the species and do not infer a subspecies. If a subspecies is accepted, its parent species is displayed as the taxonomic parent or grouping row; this does not create an additional species-level occurrence assertion.

Only subspecies individually supported as occurring in Kenya are included. The presence of a species does not imply that all of its AviList subspecies occur in Kenya.

### Unresolved taxonomy

The 2019 checklist retained some observations without forcing a disputed species/subspecies conclusion. The new checklist retains this principle through an evidence or editorial note linked to the nearest accepted AviList concept.

**UNSET - Phase 0 decision:** Decide whether unresolved species complexes and hybrids appear in the main checklist, a separate appendix, or only in the internal evidence register.

## 5. Inclusion and exclusion

### Inclusion principle

A taxon is included when the Bird Committee accepts that it has occurred in Kenya under this policy and the decision has supporting evidence.

The 2019 checklist identifies two routes for a new inclusion:

1. the East African Rarities Committee (EARC) has vetted and accepted the record; or
2. a refereed publication documents the validity of including the taxon.

The Committee may record additional evidence types if it defines how they are assessed and approved.

**UNSET - Phase 0 decision:** Define the minimum evidence and approval route for additions, removals, and status changes, including whether EARC acceptance alone is sufficient.

### Exclusion principle

A claimed record may be excluded when the evidence is materially doubtful, has not undergone appropriate scrutiny, or cannot be reliably separated from similar taxa. The 2019 decision to omit Matsudaira's Storm-petrel illustrates this precautionary approach.

An excluded or unconfirmed claim should remain in the curator's evidence and decision records with its reason. Exclusion from the public checklist is not deletion of the historical claim.

### Introduced and escaped birds

The 2019 checklist marks some taxa as introduced but does not provide a complete admission rule.

**UNSET - Phase 0 decision:** Define how the checklist treats introduced populations, established feral populations, escapees, and uncertain provenance.

## 6. Kenyan status classifications

The following codes are retained from the 2019 checklist for the first AviList-based migration. Their meanings apply to Kenyan checklist interpretation, not to global taxonomy.

| Code | Meaning |
| --- | --- |
| `AM` | Afrotropical migrant. |
| `AMR` | Afrotropical migrant and resident. |
| `E` | Endemic species or race. |
| `EX` | Species thought to have become extinct in Kenya. |
| `HIST` | No record for 50 years. |
| `IO` / `VIO` | Visitor / vagrant from northwest Indian Ocean islands. |
| `MM` / `VM` | Migrant / vagrant from the Malagasy region. |
| `N` / `NR` | Nomadic or wanderer / nomadic or wanderer and resident. |
| `NRR` | Not recently recorded. |
| `OM` / `VO` | Migrant / vagrant from the Oriental region. |
| `PM` / `PMR` / `VP` | Palaearctic migrant / Palaearctic migrant and resident / Palaearctic vagrant. |
| `RAR` | Fewer than five EARC-list records at the assessment date. |
| `RS` | Visitor from the Red Sea. |
| `SO` / `VSO` | Visitor / vagrant from the Southern Ocean or Antarctica. |
| `VN` | Vagrant from the Nearctic region. |
| `VSA` | Vagrant from southern Africa. |

Lower-case migrant notation in the 2019 policy indicates that migrants may occur alongside resident, non-migratory, or other migrant individuals. Parentheses indicate that some Kenyan individuals might be migrants or wanderers from the stated region. The data design must preserve this distinction where it remains relevant.

### Rarity

The EARC considers species with fewer than five records across Kenya, Uganda, Tanzania, Rwanda, and Burundi. `RAR` identifies a taxon included on the Kenya list with fewer than five EARC-list records at the relevant assessment date.

The 2019 convention applies a vagrant category to taxa with more than four and fewer than ten records at publication. Vagrancy is separate from `RAR`; both may therefore apply to a taxon with five to nine records.

### Historical and not-recently-recorded taxa

`HIST` indicates no Kenyan record for 50 years. `NRR` was introduced for no record during the preceding 20 years. The 2019 abbreviation key expresses that period as 1969-1999, reflecting the publication date.

**UNSET - Phase 0 decision:** Decide whether `HIST` and `NRR` are rolling statuses and whether the Committee reassesses them at every release.

### Endemicity

The initial migration retains the 2019 meaning of `E`, “endemic species or race.”

**UNSET - Phase 0 decision:** Confirm whether this definition is retained unchanged and how it applies to AviList subspecies.

### Waterbirds

**UNSET - Phase 0 decision:** Define the waterbird and strict-waterbird classifications and identify the authoritative source for each.

## 7. Kenya-specific names and conservation information

### Kenya English name

**UNSET - Phase 0 decision:** Decide when a Kenya English name is required, who approves it, and when it may differ from the AviList English name.

### Kenya vulnerability

The 2019 edition intentionally did not present regional BirdLife/IUCN threat categories as Kenyan threat assessments. AviList-supplied global conservation fields may be displayed, but must remain clearly labelled as global source information.

Appendix 2 of the 2019 edition is retained as a separate “2019 Kenya conservation watchlist.” It must not be silently replaced by global IUCN/BirdLife categories.

**UNSET - Phase 0 decision:** Decide whether the watchlist is republished unchanged, updated as a Kenyan assessment, or retained only as historical information. Define the authority and method for any new Kenya vulnerability assessment.

## 8. Evidence and decision records

Each accepted or rejected editorial assertion should be traceable to:

- a source citation, record, or Committee decision;
- the date or year of the evidence;
- the date of the Committee decision;
- the decision outcome;
- a short rationale where the outcome is not self-evident.

**UNSET - Phase 0 decision:** Confirm the minimum evidence fields and the Committee's practical approval workflow.

## 9. Changes to the checklist

Changes may result from:

- a new accepted Kenyan record;
- a new or corrected Committee classification;
- a correction to an existing note or evidence record;
- an AviList taxonomic change;
- a corrected or expanded external mapping.

The curator records the change, updates the core checklist or source mapping, rebuilds the generated outputs, and publishes a new Kenya release. Published releases are not overwritten.

An AviList upgrade requires a comparison of all affected `AvibaseID` records, including splits, lumps, rank changes, removed concepts, and changed parent relationships. Kenyan decisions must be reviewed when their taxonomic concept changes.

## 10. Publication and provenance

Each release must state:

- the Kenya release version;
- the AviList version and source citation;
- the source and enrichment versions used;
- the release date and editorial cutoff date;
- the curator and approving Committee;
- a change summary and recommended citation.

The proposed version format is `KE-<AviList-version>.<Kenya-release-number>`, for example `KE-v2025b.1`. This remains subject to the project versioning task in [the to-do list](todo.md).

## 11. Policy approval checklist

Before this policy becomes version 1.0, the curator should:

- [ ] obtain Bird Committee decisions for every item marked `UNSET`;
- [ ] record those decisions in the relevant sections;
- [ ] test the rules against ordinary species, subspecies, historical taxa, rarities, introduced taxa, and ambiguous records;
- [ ] publish the approved policy with the first AviList-based release;
- [ ] preserve this draft and the 2019 source as part of the project history.
