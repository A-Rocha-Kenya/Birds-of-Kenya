# Checklist of the Birds of Kenya - draft policy

**Status:** Working draft. This document is a starting point for Bird Committee review and is not yet an approved policy.

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

The checklist does not force a disputed species/subspecies conclusion. It handles this by using AviList as the required taxonomic frame. Every checklist row must have an `AvibaseID`; there are no free-floating unresolved names in the core checklist.

When a Kenyan record is discussed under a disputed species or subspecies treatment, or concerns a hybrid, the curator links it to the appropriate AviList concept where one exists and records the discussion, alternative treatment, evidence, and uncertainty in the Kenya-specific note column. The note preserves the editorial context without creating a parallel taxonomy.

If no appropriate AviList concept exists for the record, it remains in the evidence and review records until the Committee can associate it with an AviList concept. It is not added to the core checklist without an `AvibaseID`.

## 5. Inclusion and exclusion

### Inclusion principle

A taxon is included when the Bird Committee accepts that it has occurred in Kenya under this policy and the decision has supporting evidence.

Two routes are recognised for a new inclusion:

1. the East African Rarities Committee (EARC) has vetted and accepted the record; or
2. a refereed publication documents the validity of including the taxon.

The Committee may record additional evidence types if it defines how they are assessed and approved.

**UNSET - Phase 0 decision:** Define the minimum evidence and approval route for additions, removals, and status changes, including whether EARC acceptance alone is sufficient.

### Exclusion principle

A claimed record may be excluded when the evidence is materially doubtful, has not undergone appropriate scrutiny, or cannot be reliably separated from similar taxa. Exclusion from the public checklist is a precautionary editorial decision, not deletion of the historical claim.

An excluded or unconfirmed claim should remain in the curator's evidence and decision records with its reason. Exclusion from the public checklist is not deletion of the historical claim.

### Introduced and escaped birds

**UNSET - Phase 0 decision:** Define how the checklist treats introduced populations, established feral populations, escapees, and uncertain provenance.

## 6. Kenyan status classifications

The following codes apply to Kenyan checklist interpretation, not to global taxonomy.

| Code | Meaning |
| --- | --- |
| `AM` | Afrotropical migrant. |
| `AMR` | Afrotropical migrant and resident. |
| `E` | Endemic species or subspecies. |
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

Lower-case migrant notation indicates that migrants may occur alongside resident, non-migratory, or other migrant individuals. Parentheses indicate that some Kenyan individuals might be migrants or wanderers from the stated region. The data design must preserve this distinction where it remains relevant.

### Rarity

The EARC considers species with fewer than five records across Kenya, Uganda, Tanzania, Rwanda, and Burundi. `RAR` identifies a taxon included on the Kenya list with fewer than five EARC-list records at the relevant assessment date.

The vagrant category applies to taxa with more than four and fewer than ten records at publication. Vagrancy is separate from `RAR`; both may therefore apply to a taxon with five to nine records.

### Historical and not-recently-recorded taxa

`HIST` indicates no Kenyan record for 50 years. `NRR` indicates no record during the preceding 20 years.

`HIST` and `NRR` are rolling statuses. They must be reassessed for every new Kenya release using the latest accepted Kenyan record date available at the editorial cutoff. The status is a Committee-reviewed classification for that release; it is not silently changed by an automated calculation alone.

The project must therefore maintain a reliable latest-record date, or an explicitly documented reason why no later accepted record is available, for taxa carrying these statuses.

### Waterbirds

The checklist uses the Ramsar functional concept of waterbirds: birds that are ecologically dependent on wetlands. For the operational checklist classification, the initial family set is the one used in *Waterfowl Population Estimates, Second Edition* (Rose & Scott, 1997):

`Gaviidae`, `Podicipedidae`, `Pelecanidae`, `Phalacrocoracidae`, `Anhingidae`, `Ardeidae`, `Balaenicipitidae`, `Scopidae`, `Ciconiidae`, `Threskiornithidae`, `Phoenicopteridae`, `Anhimidae`, `Anatidae`, `Pedionomidae`, `Gruidae`, `Aramidae`, `Rallidae`, `Heliornithidae`, `Eurypygidae`, `Jacanidae`, `Rostratulidae`, `Dromadidae`, `Haematopodidae`, `Ibidorhynchidae`, `Recurvirostridae`, `Burhinidae`, `Glareolidae`, `Charadriidae`, `Scolopacidae`, `Thinocoridae`, `Laridae`, `Sternidae`, and `Rynchopidae`.

The `water_bird` field is generated automatically from this rule and the AviList taxonomic hierarchy. It is not manually entered for individual rows. The build must maintain a versioned mapping from the operational family list to AviList families, because family treatment and names may change between AviList releases. Species and subspecies inherit the classification from their AviList family.


## 7. Kenya-specific names and conservation information

### Kenya English name

AviList provides the default English name for each taxon. The Kenya checklist may provide a Kenya-specific English name when the Bird Committee considers a different name to be the appropriate name used in Kenya.

The core checklist should store a Kenya-specific name only when it intentionally differs from the AviList name. When there is no difference, the generated checklist uses the AviList name and leaves the Kenya-specific override blank. This avoids duplicating names while preserving the Committee's local nomenclature where it matters.

The Kenya-specific name field represents the Committee's preferred English name, not an alternative taxonomic concept. The row must still use the relevant AviList `AvibaseID`, and any taxonomic or naming discussion is recorded in the Kenya-specific note field.

eBird/Clements supports multiple regional and taxonomic English name sets ([eBird naming guidance](https://support.ebird.org/en/support/solutions/articles/48000804865-bird-names-in-ebird)), so a difference between the Kenya name and the AviList name is valid and should be documented rather than treated as an error. The project should maintain a machine-readable list of approved Kenya-name overrides that can be shared with eBird/Clements for consideration in future Kenya name-set updates.

**UNSET - Phase 0 decision:** Define the scope and approval process for Kenya English names: which taxa are eligible, what evidence or usage supports a proposed name, who approves it, how conflicts are resolved, and how approved names are submitted to external maintainers.

### Kenya vulnerability

Regional BirdLife/IUCN threat categories are not Kenyan threat assessments. AviList-supplied global conservation fields may be displayed, but must remain clearly labelled as global source information.

Any Kenya conservation watchlist is a separate national classification. It must not be silently replaced by global IUCN/BirdLife categories.

**UNSET - Phase 0 decision:** Decide whether the watchlist is republished unchanged, updated as a Kenyan assessment, or retained only as historical information. Define the authority and method for any new Kenya vulnerability assessment.

## 8. Evidence and decision records

Each accepted or rejected editorial assertion should be traceable to:

- a source citation, record, or Committee decision;
- the date or year of the evidence;
- the date of the Committee decision;
- the decision outcome;
- a short rationale where the outcome is not self-evident.

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
- [ ] publish the approved policy with the first AviList-based release.
