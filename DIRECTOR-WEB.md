# Director Web — product specification

**Status:** proposal  
**Date:** 2026-08-03  
**Market:** United Kingdom  
**Audience:** concerned citizens first; journalists, researchers and civil-society investigators
second  
**Business model:** the public search, evidence pages and core graph remain free  

## Product decision

Build a free, evidence-linked Companies House person web that answers:

> Who is this person, where do they keep appearing, and why might that be worth understanding?

The first release begins with a person rather than a company. It reconstructs that person's public
Companies House appointments, shows the companies and people around them, detects a small number
of understandable recurrence patterns, and explains each pattern without implying wrongdoing.

The graph is the navigation. **The explanation, provenance and ability to drill into every claim
are the product.**

This is deliberately not another generic company-information search or an opaque fraud score.
Products including OC Intelligence, UKGovScan and chgraph already cover substantial parts of
company and officer exploration. Director Web must distinguish itself through free citizen access,
plain-language findings, temporal reasoning, explicit identity confidence and an official source
behind every factual edge.

## The problem

Companies House makes individual records public, but it does not help a non-expert understand a
person's wider pattern:

- the same person may have many current and former appointments;
- names may vary between filings or belong to different people;
- recurring co-directors and addresses are scattered across company pages;
- appointments, resignations, incorporations, dissolutions and name changes are hard to read as
  one sequence;
- a large network can be entirely legitimate, but a bare graph encourages users to infer more than
  the evidence says; and
- connections to public contracts, political donations and regulatory events sit in different
  registers with different identifiers and different levels of certainty.

Existing tools often assume that users already know corporate terminology, know what to search
for, and can interpret a dense network. Director Web should instead take a citizen from a name to
an intelligible public-record account, with every step open to inspection.

## Prior art and competition

**Market review date:** 2026-08-03. Product features and prices change; the linked product pages
are the source of truth.

Director Web enters an active market. Free Companies House access, officer search, appointment
history, PSC lookup and company-network visualisation already exist. Cross-register products also
connect some companies to contracts and political donations. The opportunity is therefore not
"put Companies House in a graph" or "make company data free". It is to make one person's public
record unusually understandable, temporally precise and verifiable for a non-expert.

### Direct and adjacent products

| Product | Model and existing strength | Overlap with Director Web | Remaining opening |
|---|---|---|---|
| [Companies House: Find and update company information](https://www.gov.uk/guidance/searching-the-companies-house-register) | The authoritative free register. It provides company and officer search, current and resigned officers, filing documents, insolvency information and free company-follow alerts. | It is the source and the baseline experience. A citizen can already open a company, inspect its officers and follow later filings. | It presents register records principally company by company. It does not build a guided person-centred account across appointments, explain recurrence patterns or join the wider public-interest context. Director Web must always defer to and deep-link back to it. |
| [chgraph](https://chgraph.co.uk/) | UK company-intelligence product with a free tier and a Pro tier advertised at £12/month. It presents officer cross-referencing, PSCs, filing links, network graphs, shared-address analysis, exports and automated risk indicators. | This is the closest direct prior art for recurring directors, connected companies, addresses and graph navigation. It demonstrates that a visual Companies House network alone is not novel. | Director Web should not imitate risk scoring. Its opening is the citizen explanation contract: what the record says, why the pattern helps, what it does not establish, and the evidence for each edge. Public-money and political-finance context can later extend that account. |
| [UKGovScan](https://ukgovscan.com/) | Free independent beta spanning contracts, government payments, companies and officers, political donations, lobbying, grants, charities, councils, schools and parliamentary interests. It already publishes donation-to-contract examples and company/officer search. | It substantially overlaps the proposed free cross-register transparency destination and already competes for citizen attention. | Its breadth leaves room for a much deeper person workflow: careful officer disambiguation, appointment-overlap reasoning, recurrence explanations, exact-versus-possible identity labels and a complete evidence ledger. Director Web should integrate depth rather than attempt to out-menu it. |
| [OC Intelligence](https://ocintelligence.co.uk/) | The strongest commercial overlap. OC Corporate advertises company and people search across directors and PSCs, filings, land, charities, contracts and political donations at £24.99/month. OC Political adds MPs' interests, donation analysis, contracts, a Network Explorer and an investigator notebook at £49.99/month. | It already implements much of the eventual data breadth, including people search and connections between companies, contracts and political finance. | Director Web cannot claim novelty from those joins. It can compete through permanent free public pages, no-login evidence access, citizen-level explanations, reproducible per-edge provenance, precise uncertainty labels and an openly documented methodology. Paid workflow can come later without paywalling the public evidence. |
| [OpenCorporates](https://knowledge.opencorporates.com/knowledge-base/gb/) | A global legal-entity database containing UK companies, officers and source-registry links. Its website remains free with registration for personal and public-benefit use, while commercial and API access support its business model. | It establishes cross-jurisdiction company/officer search and source-linked legal-entity data at far greater geographic scale. | It is primarily an entity-data platform. Director Web can specialise in UK temporal narratives, citizen explanations and public-money questions rather than attempt to reproduce OpenCorporates' global coverage. |
| [Endole](https://www.endole.co.uk/pricing/) | Commercial UK business intelligence aimed at company research, credit, sales and monitoring. It advertises company and director research, ownership insights, financial history, property and alerts at £39/month, or £25/month billed annually. | It competes for searches about companies, directors, ownership and changes and shows that professional users will pay for monitoring and enriched company profiles. | Its principal jobs are B2B prospecting and credit/commercial intelligence. Director Web should remain public-interest and evidence-first, avoiding sales contacts, opaque credit judgments and a generic business-information feature race. |
| [Givers and Takers](https://autonomy.work/portfolio/givers-and-takers-uncovering-the-donor-contractor-nexus-at-the-heart-of-government/) | Autonomy Institute research cross-referencing corporate political donors with public contractors. It demonstrated that the donation–contract intersection can produce a consequential public story. | It validates one of Director Web's proposed later joins and means that "companies both donated and contracted" is already established research territory. | It is a bounded research project rather than a continuously updated, person-centred navigator. Director Web can let a citizen reproduce an exact company-number join, place it against dated officer roles and continue through the evidence without claiming influence. |

### What prior art has already solved

The following are necessary features, but they are not defensible product differentiation:

- free company and officer lookup;
- current and historical appointment lists;
- PSC and filing-history display;
- a force-directed company/director graph;
- shared-address and recurring-director discovery;
- generic "risk flags" over Companies House fields;
- connecting at least some suppliers to contracts;
- connecting company donors to political donations; and
- professional alerts, reports and exports.

Marketing Director Web as any one of these would overstate its novelty.

### The underserved job

The narrower job that appears less well served is:

> Starting with an ambiguous person's name, help a non-expert choose the right officer record,
> understand the few patterns that matter, distinguish historical coincidence from dated overlap,
> and verify every sentence without learning corporate-investigation software.

Director Web should combine five qualities in one free public experience:

1. **Identity honesty** — exact officer record, possible duplicate and same-name lead never look
   equivalent.
2. **Temporal precision** — appointments are compared with events only for the periods in which
   the records overlap.
3. **Citizen explanation** — every surfaced pattern includes meaning, limitations and plausible
   ordinary context.
4. **Evidence depth** — every aggregate expands to its constituent records and then to the
   official source in at most two interactions.
5. **Public-interest extension** — contracts, corporate political donations and regulatory events
   are later added to the same evidence discipline rather than displayed as insinuating badges.

No identified competitor proves that this combination is unavailable somewhere in every detail.
The defensible claim is more modest: it is not the centre of their published product proposition,
and it can be tested as a focused citizen experience.

### Competitive posture

Director Web should not try to beat established products on breadth in its first release:

- **Against Companies House:** provide comprehension and cross-record navigation, while treating
  Companies House as the authority.
- **Against chgraph:** provide explanation and temporal evidence rather than more graph controls or
  stronger risk labels.
- **Against UKGovScan:** go deeper on one person-centred investigation instead of adding more
  government-data categories.
- **Against OC Intelligence:** make the public evidence permanently free and exceptionally
  reproducible; reserve paid value for monitoring and professional workflow.
- **Against broad business databases:** serve public understanding rather than credit, sales or
  compliance decisions.

The product should interoperate rather than pretend these tools do not exist. Official links are
mandatory; links to useful third-party research may be offered as clearly labelled external
resources.

### Competitive validation before build-out

Before Phase 2, run the same five citizen tasks through Companies House, chgraph, UKGovScan, OC
Intelligence and the Director Web prototype:

1. Find the correct officer among several people with the same name.
2. Identify the companies on which two officer records repeatedly co-occur.
3. Determine whether the appointments actually overlapped.
4. Explain the precise status of each connected company, including voluntary strike-off.
5. Open the official evidence supporting a generated summary.

Measure successful completion, time, identity mistakes, comprehension and the number of clicks to
official evidence. If an existing free product performs these tasks as clearly as Director Web,
the specification should narrow further rather than ship a redundant explorer.

## Product promise

Search for a UK director and receive:

1. a defensible identity selection rather than a silent name match;
2. a dated account of the person's recorded company roles;
3. a small set of plain-language observations about recurrence and change;
4. an explorable web of companies, co-directors, PSCs and addresses;
5. a direct official link and evidence explanation for every connection; and
6. an honest statement of what the records do **not** establish.

A useful result should be understandable without knowing what an officer, PSC, filing-history item
or company status means.

## Target users

### Primary: a concerned citizen

They have encountered a director's or company officer's name in a local story, planning matter,
charity, failed business, political donation or public contract. They want to know whether the
person appears elsewhere and do not know how to conduct corporate research.

They need guided questions, explanations and source links. They do not need a compliance dashboard.

### Secondary users

- A local or national journalist doing initial research.
- A campaigner following companies active in one sector or locality.
- A researcher studying corporate and public-money networks.
- A public servant performing open-source context gathering.

The product may help these users generate leads. It must not represent a lead as a finding of
fraud, corruption, control, collusion or personal responsibility.

## Jobs to be done

- "I have a person's name. Help me find the right public record."
- "Show me every company role Companies House associates with this officer record."
- "Which people and addresses recur around these companies?"
- "What changed, in what order, and where is the filing that supports it?"
- "Explain why a pattern may be worth a question and what innocent explanations may exist."
- "Let me expand one connection without losing my place."
- "Give me a link I can share that another person can independently verify."
- Later: "Did these companies receive public contracts, make political donations or appear in
  regulatory records?"

## Product principles

### 1. Evidence before interpretation

Every factual relationship opens an evidence drawer containing the source register, record date,
identifiers, relevant fields, retrieval date and official link. A generated explanation must
reference only relationships already present in the evidence model.

### 2. Explain both meaning and limits

Every observation contains four parts:

- **What the public record says** — the reproducible fact.
- **Why someone might ask a question** — why the pattern aids navigation.
- **What it does not mean** — the important non-inference.
- **Open the evidence** — the records and dates needed to verify it.

### 3. No suspicion score

There is no red/amber/green person rating, fraud probability, integrity score or "most suspicious
directors" league. Counts and timing patterns help users navigate; they do not characterise a
person.

### 4. Identity uncertainty is part of the interface

The product never silently merges people merely because their names match. Exact officer-record
traversals, probable duplicate records and same-name search results are visibly distinct.

### 5. Time is first-class

Roles and relationships have dates. The interface distinguishes "was a director when this event
occurred" from "was a director at some other time" and from "the register does not provide enough
information to determine overlap".

### 6. Progressive disclosure

The first screen provides three to five useful observations, not the entire graph. Detail opens on
demand: observation, timeline, web, company, filing, then official source.

### 7. Public by default

No account is required for search, person pages, company pages or evidence. Pages have stable URLs,
are indexable where lawful, and work well when shared. Monitoring and private notebooks can be
added later without putting the core public record behind a subscription.

## Scope

### MVP scope

- Search Companies House officers by name.
- Help the user disambiguate results.
- Traverse all appointments exposed for the selected officer identifier.
- Resolve the connected companies and their current public status.
- Retrieve the officers and PSC records attached to those companies.
- Present a person passport, timeline and bounded one-hop web.
- Detect and explain a defined set of deterministic patterns.
- Provide official Companies House links on people, companies, appointments, PSC statements and
  filing-history entries where available.
- Create a stable, shareable page for the selected officer record.

### Explicitly outside the MVP

- Declaring two Companies House officer identifiers to be the same natural person.
- Assigning beneficial ownership not stated in the PSC record.
- Background checks or suitability decisions.
- A general-purpose whole-register graph workbench.
- Political-donation, procurement, sanctions, insolvency and press joins.
- Automated allegations or personality summaries.
- Ranking named people by inferred risk.

Those external joins are roadmap enrichments after the core identity, evidence and explanation
experience works.

## Core experience

### 1. Landing and search

The page leads with one search box:

> Search a UK director or company

Supporting copy:

> See recorded company roles, recurring people and addresses, important changes, and the official
> evidence behind every connection.

If a company is entered, its officers become starting points. The user should never reach a dead
end merely because they began with the company rather than the person's name.

### 2. Identity selection

Name search returns candidate officer records as cards, not an undifferentiated list. Each card
shows only public attributes useful for disambiguation:

- recorded name and former names where available;
- month and year of birth where lawfully returned by the public API;
- nationality and occupation where present;
- current and historical appointment counts;
- a small sample of company names;
- locality from the public service-address representation, avoiding unnecessary address exposure;
- whether the candidate is an exact officer record or a possible related record; and
- a direct Companies House link.

Copy above the results explains:

> Companies House can hold several officer records with the same name, including separate records
> that may refer to the same person. Choose using the recorded companies and public details. We do
> not merge candidates automatically.

### 3. Person passport

The passport is the default result page. It contains:

- recorded identity and Companies House officer identifier;
- number of current and historical appointments;
- date range covered by those appointments;
- active, dissolved and other company-status counts;
- a concise "What stands out?" section;
- a chronological role timeline;
- company cards with current/historical role labels; and
- entry points to the web and evidence ledger.

The passport describes a **Companies House officer record**, not a complete biography of a natural
person.

### 4. What stands out?

Show no more than five observation cards initially, ordered by usefulness rather than by a hidden
risk score. In the MVP, all triggering facts are deterministic. Natural-language rendering may be
templated or model-assisted, but the numbers, dates and relationships come from governed data.

Each card must answer:

```text
Headline
What the public record says
Why a citizen might ask a question
What this does not establish
[Explore] [Open records]
```

Initial observation types:

#### Many appointments

Trigger: the officer record has at least a configurable number of appointments.

> **This officer record appears in 26 companies**  
> Companies House lists 7 current and 19 former appointments between 2012 and 2026.  
> A citizen may want to understand whether the companies share a business purpose or professional
> service. Holding many appointments is common for accountants, company-formation agents and group
> directors and is not evidence of wrongdoing.

#### Formation burst

Trigger: several connected companies were incorporated within a defined rolling window.

> **Eight connected companies were incorporated within four months**  
> The dates form a useful cluster for exploring shared directors, addresses or business activity.
> Companies in a legitimate group are often formed together; timing alone does not show coordination
> for an improper purpose.

#### Synchronous role changes

Trigger: several appointments or resignations occur within a short period.

> **Six recorded directorships ended within 12 days**  
> The timeline makes it possible to check whether the companies were restructured, sold or closing.
> The records do not state a common reason, and proximity does not establish one.

#### Recurring co-director

Trigger: another exact officer record co-occurs with the selected record on multiple companies.

> **The same co-director appears with this officer on five companies**  
> Open the five overlapping appointments and their dates. Repeated co-appointments may reflect an
> ordinary business partnership, professional service or corporate group.

#### Shared registered or service address

Trigger: multiple connected companies use the same normalized public address.

> **Eleven connected companies use the same registered-office address**  
> The address may help explain how the companies are related. It may also be an accountant, solicitor,
> virtual office or company-formation address and does not establish common ownership.

#### Status concentration

Trigger: a substantial count or proportion of connected companies has the same status, such as
dissolved, liquidation or voluntarily struck off.

> **Nine connected companies are recorded as dissolved**  
> Open each company's status history and filing record. Dissolution is a legal company status, not a
> finding of misconduct. The app must display the precise status, including "voluntarily struck
> off" where that is what the source records, rather than collapsing every closure into "dissolved".

#### Possible duplicate officer records

Trigger: a separate officer identifier shares a sufficiently unusual combination of normalized
name and compatible public attributes. This is always a lead, never an automatic merge.

> **Companies House may hold another record for a similarly described officer**  
> The name and public details overlap, but the identifiers differ. Compare the two records. The app
> cannot confirm they belong to the same person.

Thresholds must be configurable and visible in the methodology. They are editorial display rules,
not population-level claims that a count is statistically unusual.

### 5. Timeline

The timeline provides one ordered sequence of:

- company incorporation;
- officer appointment and resignation;
- company name change;
- company status change;
- PSC notification or cessation where the register supplies it; and
- later roadmap events such as awards, donations and regulatory actions.

The user can filter by company or event type. Events at the same date are grouped but not described
as causally related. Unknown and partial dates remain unknown rather than being imputed.

### 6. Person web

The graph initially displays only:

```text
selected officer -> appointment -> company
company -> appointment -> co-director
company -> PSC statement -> recorded PSC
company -> registered office -> address
```

Interaction rules:

- The selected person remains visually anchored.
- Current and historical roles use different line styles and include date labels.
- Director and PSC are different node/edge types; neither is silently treated as "owner".
- The initial graph is bounded to one hop from the selected person.
- The user explicitly expands a company, co-director, PSC or address.
- High-degree nodes collapse into a count such as "+37 other companies" until requested.
- Selecting an edge opens its evidence drawer.
- A readable list/table alternative contains all graph information.
- The current expansion state is encoded in a shareable URL where practical.

Graph layout must never encode a risk score through colour, size or proximity. Size may represent a
labelled count only. Colour represents entity or relationship type.

### 7. Evidence drawer

Every relationship and event opens a consistent evidence drawer:

- plain-English relationship;
- source register and publisher;
- exact source identifier(s);
- source fields used;
- effective dates and whether they are complete;
- retrieval or snapshot date;
- match method: exact identifier, exact register traversal, normalized field, or possible match;
- current-source link; and
- "What this proves / What this does not prove" copy.

Example:

> **Recorded appointment**  
> Companies House officer record `abc123` is listed as a director of company `01234567`, appointed
> 14 March 2021 and resigned 9 September 2024. This supports a recorded role during that interval.
> It does not establish share ownership, operational involvement throughout the period or
> responsibility for every company decision.

If a deep link to an individual source record is not possible, link to the narrowest official page
that lets the user reproduce the lookup and say why.

## Drill-down contract

No name, number, count, relationship or observation is decorative. Each must drill down:

| User sees | First click | Second click |
|---|---|---|
| Person name | Person passport | Official officer/appointments record |
| Company name or number | Company passport | Official Companies House company page |
| Appointment edge | Evidence drawer with role and dates | Official appointments/company record |
| PSC edge | Nature-of-control and dates | Official PSC/company page |
| "Appears in 26 companies" | Complete appointment list | Selected appointment evidence |
| "Five recurring co-directorships" | Five-company overlap | Individual appointment evidence |
| "Six resignations in 12 days" | Filtered timeline | Filing or appointment record |
| Company status count | Companies grouped by precise status | Company filing/status evidence |
| Possible identity match | Side-by-side candidate comparison | Both official records |

A user must be able to answer "where did that sentence come from?" in at most two interactions.

## Information and evidence model

### Core entities

- `UkOfficerRecord` — one Companies House officer identifier, not automatically a natural person.
- `UkCompany` — identified by Companies House company number.
- `UkAppointment` — the dated role between an officer record and company.
- `UkPscRecord` — a PSC statement or PSC identity exactly as recorded.
- `UkAddress` — a normalized navigation node retaining the original rendered address on evidence.
- `UkCompanyEvent` — incorporation, name, status and selected filing-history events.
- `UkEvidenceRecord` — source-specific provenance for an entity, relationship or event.
- `UkObservation` — a reproducible calculation plus citizen-facing explanation.

Future entities include `UkContractAward`, `UkPoliticalDonation`, `UkRegulatoryAction`,
`UkInsolvencyEvent` and `PressResult`.

### Core relationships

```text
(UkOfficerRecord)-[:HELD_APPOINTMENT]->(UkAppointment)-[:AT_COMPANY]->(UkCompany)
(UkCompany)-[:HAS_PSC_RECORD]->(UkPscRecord)
(UkCompany)-[:USED_REGISTERED_OFFICE]->(UkAddress)
(UkCompany)-[:HAS_EVENT]->(UkCompanyEvent)
(entity or relationship)-[:SUPPORTED_BY]->(UkEvidenceRecord)
(UkOfficerRecord)-[:HAS_OBSERVATION]->(UkObservation)
```

`CO_DIRECTOR_OF`, `RECURS_WITH` and similar connections should normally be derived query results,
not unsupported primary facts. Their evidence is the set of overlapping appointments.

### Identity confidence

Use these labels consistently:

1. **Exact company** — same Companies House company number.
2. **Exact officer record** — same Companies House officer identifier.
3. **Exact register traversal** — the source API directly connects the records.
4. **Possible same person** — separate identifiers with compatible public attributes.
5. **Same name only** — a search lead with no corroborating identifier.

Levels 4 and 5 are never merged into aggregate counts shown for the selected officer record.

Address normalization similarly creates a navigation relationship, not proof of shared occupation,
control or business activity.

## Data sources

### MVP

- [Companies House Public Data API](https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference)
  for company profiles, company officers, officer appointments, PSCs and filing history.
- [Companies House free company data product](https://download.companieshouse.gov.uk/en_output.html)
  if a local searchable company spine is needed.
- [Companies House PSC data product](https://download.companieshouse.gov.uk/en_pscdata.html)
  if the API alone cannot support the intended recurrence queries efficiently.

Source licensing, rate limits, returned-field policy, update cadence and retention must be recorded
before implementation. The UI displays the age of its cached record and always links to the live
official page.

### Roadmap enrichments

- Find a Tender and Contracts Finder/OCDS for awarded suppliers and contract events.
- Electoral Commission political-finance disclosures for exact company-number donation joins.
- The Insolvency Service, Gazette and relevant regulator publications.
- UK Sanctions List and public debarment information where identifiers permit a responsible join.
- Press search as a **separate, explicitly requested query**, visually isolated from official
  register findings.

External enrichment must not delay or contaminate the initial Companies House result. A press
failure renders "press search unavailable", never "no press coverage".

## Political donations and public contracts

These are important post-MVP paths, with distinct language:

### Exact company donation

The Electoral Commission records a company donation with the same Companies House number.

> Company `01234567` made a disclosed donation of £X to Y on date D.

This is an exact legal-entity join. If a person held a role at the company, the app may say that the
company associated with their recorded role donated. It must not say the director personally made,
authorised or influenced the donation.

### Possible personal donor

Individual donation records do not carry a Companies House officer identifier. A matching name is
therefore shown only as a possible lead in a separate section and excluded from totals until
corroborated.

### Public supplier

Where an award record contains the same company number, show the award against the exact company.
Where historical procurement provides only a supplier name, label the link as a possible entity
match and keep it out of exact totals.

Contracts are reported commitments or awards according to the source, not proof of expenditure or
favour. Donation and contract dates may share a timeline; temporal proximity is not evidence that
one caused the other.

## AI behaviour

AI is an explanation and document-reading layer, not the source of graph facts.

### Allowed

- Turn governed observations into concise citizen-facing language.
- Explain Companies House terms using approved definitions.
- Compare selected filings and state factual changes with page or record citations.
- Suggest neutral follow-up questions such as "Were these companies part of the same group?"
- Summarize separately retrieved press results with a link to each publication.
- Answer open questions over the currently loaded evidence set.

### Not allowed

- Invent, infer or merge a person identity.
- Label a person or company suspicious, fraudulent, corrupt, a shell or a front.
- Infer control from a directorship or address.
- Infer responsibility for a company action from a recorded role.
- Treat absence from a retrieved result set as proof of absence from the world.
- State causal conclusions from event order.
- Cite an observation without a source-backed calculation.

### Answer format

Open questions should produce:

1. a short answer;
2. numbered factual claims;
3. evidence links for each claim;
4. identity and coverage caveats; and
5. useful unanswered questions.

If the evidence is insufficient, the answer says so and identifies what would be needed.

## Suggested realm implementation

The product is specified here because it emerged from the cross-jurisdiction work in this realm.
The production implementation may ultimately belong in a dedicated `realm-gov-uk`; its UK types,
producers and lenses should therefore avoid Australian assumptions.

Suggested assets:

```text
apps/director-web.html
types/uk-corporate.yml
producers/uk-companies-house.yml
lenses/uk-officer-passport.yml
lenses/uk-officer-web.yml
lenses/uk-officer-observations.yml
views/uk-director-web.yml
```

The app should use separate virtual queries for bounded tasks rather than one enormous traversal:

1. resolve/search candidates;
2. load the exact officer appointment set;
3. load company profiles and status events;
4. load co-directors and PSCs for explicitly expanded companies;
5. calculate governed observations;
6. run optional public-money, political-finance or press enrichments only when selected.

Conceptual query shapes:

```cypher
// Exact Companies House officer record and its appointment history
MATCH (p:UkOfficerRecord {officerId: $officerId})
      -[:HELD_APPOINTMENT]->(a:UkAppointment)
      -[:AT_COMPANY]->(c:UkCompany)
RETURN p, a, c
```

```cypher
// Recurring co-directors, derived through overlapping company appointments
MATCH (p:UkOfficerRecord {officerId: $officerId})
      -[:HELD_APPOINTMENT]->(:UkAppointment)-[:AT_COMPANY]->(c:UkCompany)
      <-[:AT_COMPANY]-(otherAppointment:UkAppointment)
      <-[:HELD_APPOINTMENT]-(other:UkOfficerRecord)
WHERE other.officerId <> p.officerId
RETURN other, collect(DISTINCT c) AS sharedCompanies
ORDER BY size(sharedCompanies) DESC
```

```cypher
// Separate, opt-in press query; results are not graph identity evidence
MATCH (p:UkOfficerRecord {officerId: $officerId})
      -[:HAS_PRESS_QUERY]->(q:PressQuery)
      -[:RETURNED]->(r:PressResult)
RETURN q, r
```

The exact YAML and schema should follow measured API behaviour rather than assuming the conceptual
model maps one-to-one to Companies House responses.

## Non-functional requirements

### Performance and boundedness

- A normal exact-officer passport should become useful within three seconds from cache and ten
  seconds on a cold upstream traversal.
- Initial graph rendering is capped and reports the cap.
- Expansions are lazy and cancellable.
- High-degree professional-service addresses and directors do not trigger unbounded fan-out.
- Partial upstream results render as partial, not complete.

### Accessibility

- All graph content is available as structured lists or tables.
- The graph is keyboard navigable where feasible, but no required task depends on it.
- Meaning never relies on colour alone.
- Explanatory copy targets an ordinary reading level and defines PSC, appointment and company
  status at first use.
- Mobile users can complete search, read observations and open evidence without interacting with
  the graph canvas.

### Privacy and fairness

- Display only information necessary to understand the public corporate record.
- Avoid exposing full residential-looking addresses when a locality or official link is sufficient
  for identity selection; retain precise registered-office evidence only where publication and use
  are justified.
- Provide a correction/contact route for mistaken identity or stale-source concerns.
- Preserve the source record and retrieval date when correcting the app's derived representation.
- Do not generate pages for search-engine bait based on weak same-name matches.

### Reproducibility

- Observation cards store their rule version, input identifiers and calculation timestamp.
- Counts can be expanded to the records that comprise them.
- Cached and live states are visibly distinguished.
- Changes in upstream records do not erase the provenance of an earlier shared observation, subject
  to lawful retention policy.

## Delivery roadmap

### Phase 0 — evidence spike (one week)

- Measure Companies House endpoints, pagination, identifiers, rate limits and deep-link behaviour.
- Test 20 deliberately varied people: common names, duplicate-looking records, professional
  directors, large networks, historical appointments, corporate officers and redacted/partial data.
- Prove that every intended passport statement can open official evidence.
- Decide which address fields are necessary and proportionate.

**Exit gate:** the team can render one exact officer record and all of its reported appointments
without accidental cross-person merging.

### Phase 1 — free person passport (weeks 2–4)

- Name/company search and candidate disambiguation.
- Exact officer appointment traversal.
- Person passport, company cards and timeline.
- Precise company statuses, including voluntary strike-off states where supplied.
- Evidence drawer and stable share URLs.
- Three deterministic observations: appointment count, formation burst and synchronous role
  changes.

**Exit gate:** five representative citizens can find the correct candidate, explain one observation
and reach its official evidence without assistance.

### Phase 2 — the web (weeks 5–7)

- Bounded co-director, PSC and address expansion.
- Recurring co-director and shared-address observations.
- Accessible list equivalent.
- Possible duplicate-record comparison without merging.
- Methodology and correction pages.

**Exit gate:** every graph edge is dated or explicitly undated, typed, evidence-linked and readable
outside the graph.

### Phase 3 — public-interest layer (weeks 8–12)

- Exact company-number joins to procurement and political donations.
- One timeline with roles, awards and company donations.
- Separate exact, possible and same-name match sections.
- Opt-in press query with publication links and no identity merge.

**Exit gate:** exact joins and name-based leads cannot be confused visually, in exports or in
generated answers.

### Phase 4 — attention and retention

- Watch a person, company or public supplier.
- Weekly "what changed" emails.
- Embeddable evidence cards for newsrooms and civil-society sites.
- Saved private notebooks and cited exports.
- Carefully editorialised public examples based only on reproducible records.

The free public passport, graph and evidence links remain free. Potential paid products are
high-volume monitoring, team workspaces, bulk export and APIs—not basic access to the public record.

## Launch slice

The smallest valuable launch is narrower than the full MVP:

1. one search box;
2. careful officer-record selection;
3. every exact appointment on a timeline;
4. recurring co-directors across those companies;
5. three "What stands out?" explanations;
6. a direct official link for every relationship; and
7. a shareable person URL.

Do not delay this slice for procurement, donations, press or an elaborate graph layout. Those
features become valuable only after a user trusts the identity and evidence model.

## Success measures

### Trust and comprehension

- At least 90% of test users correctly describe what one observation does and does not establish.
- At least 95% can reach supporting evidence in two interactions or fewer.
- Zero known cases where a same-name record is presented as an exact identity.
- Correction requests and upheld correction rate are measured publicly.

### Usefulness

- Search-to-valid-person-passport completion rate.
- Observation-to-evidence open rate.
- Percentage of sessions that deliberately expand one relationship.
- Shared person pages that lead to an evidence interaction, not merely a page view.
- Citations by journalists, researchers and civil-society organisations.
- Watch subscriptions driven by a useful record rather than a generic signup wall.

Raw graph size, alarming headlines and time-on-site are not success measures.

## Editorial and legal release gates

Before public launch:

- Review UK Companies House data licensing and public-register terms for the intended caching,
  republication and search-engine behaviour.
- Conduct a privacy and misuse review, especially for addresses and weak identity matches.
- Test correction, stale-data and source-outage handling.
- Establish forbidden generated-language tests for allegations and unsupported identity claims.
- Verify company-status labels against source values; do not lose distinctions such as voluntary
  strike-off, liquidation and dissolution.
- Red-team common-name searches and deliberately misleading user questions.
- Display a clear service description: this is a navigator over public records, not a background
  check and not an assessment of a person's conduct.

## Open product questions

- Should stable public URLs use the Companies House officer identifier directly, or an internal
  opaque key that allows source evolution?
- What minimum public attributes are sufficient for disambiguation without unnecessarily
  republishing personal data?
- Should high-degree professional directors receive a different default layout so their networks
  remain useful rather than spectacular?
- Which official filing-history items reliably explain changes in company status across company
  types?
- Can historical registered-office changes be obtained consistently enough to make address overlap
  temporal rather than merely current?
- Which population baselines, if any, justify calling a pattern "unusual" rather than simply
  reporting its exact count?
- At what point should this product move from `realm-gov-au` into a dedicated UK realm while
  retaining cross-jurisdiction comparison?

## One-sentence launch definition

> Director Web is a free public-interest navigator that starts with a Companies House officer
> record, shows where that record recurs, explains the useful questions raised by the pattern, and
> lets a citizen verify every statement at its official source.
