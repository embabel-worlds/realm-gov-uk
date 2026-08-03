# Director Web — realm architecture

**Status:** proposal. **Phase 0 is COMPLETE** — see [PHASE0-FINDINGS.md](PHASE0-FINDINGS.md),
which is measured against the live API and supersedes this document wherever the two disagree.
**Product spec:** [DIRECTOR-WEB.md](DIRECTOR-WEB.md) — the product contract this realm implements.
**Sibling precedent:** `realm-gov-au` — its `sources.yml` shape declarations, measured-producer
comments and views-first reporting are the house style this document follows.

This document is the engineering half the product spec deliberately omits: how the Companies
House registers become a governed graph, which access paths are live versus mirrored, where the
fan-out bounds sit, how the identity-confidence ladder maps onto graph mechanics, and how every
edge stays evidence-linked.

## Design posture

1. **Views, not lenses, wherever possible.** Every read the app or chat needs — passport,
   timeline, recurring co-directors, shared addresses, observations — is a named, parameterised
   view in `views/`. Views are inspectable, testable, and cost-declared. A lens is reserved for
   a genuine focus-binding need that a view cannot express; none is currently anticipated.
2. **Measured, not assumed.** Companies House endpoint behaviour (pagination, field presence,
   identifier stability, deep-link patterns, rate-limit enforcement) is asserted in producer
   comments only after probing the live service, gov-au style. This document marks every such
   fact TO MEASURE.
3. **Live per-key first; mirror only when a question forces it.** The product is person-anchored:
   one officer record, its appointments, the companies around them. That is per-key fetching over
   a handful of endpoints — the shape live producers serve well. The bulk data products (company
   snapshot, PSC snapshot) become a mirror only if recurrence queries (shared address across the
   whole register, cross-register duplicate-officer leads) prove infeasible over live calls.
4. **The register's words, never ours.** Statuses ("voluntarily struck off", "liquidation"),
   role names and PSC natures-of-control are projected verbatim. No derived judgment, score or
   collapsed category is ever written into the graph.
5. **No real people anywhere in this repo.** Fixtures, tests, examples and doc snippets use
   invented names and placeholder identifiers (`abc123`, `01234567`). The register is public;
   our test assets still are not the place for real identities.

## Graph schema

### Labels and identity keys

| Label | Identity key | MERGE semantics |
|---|---|---|
| `UkOfficerRecord` | `officerId` (Companies House officer identifier) | `identity: true` — one node per register identifier. **MEASURED**: this identifier is itself an upstream Companies House grouping of underlying register records (1.3% span more than one `person_number`), so it is a supplied judgment, not a raw atom — disclose, do not hide |
| `UkCompany` | `companyNumber` | `identity: true` |
| `UkAppointment` | `appointmentId` — composite `officerId + companyNumber + appointedOn`. **MEASURED**: an appointment id exists on the *company*-anchored path (`links.self`) but not on the officer-anchored path the passport uses, so the composite is required; project the company-side id as a bonus deep link when an expansion supplies it | `identity: true` |
| `UkPscRecord` | `pscId` (per-company PSC link id; TO MEASURE stability) | `identity: true` |
| `UkAddress` | `normalizedAddress` (deterministic normalization; original rendering kept as a property) | `identity: true` — a navigation node, not a claim of shared occupation |
| `UkCompanyEvent` | `eventId` (composite `companyNumber + type + date`) | `identity: true` |
| `PressQuery` / `PressResult` | query hash / result URL | separate subgraph, never joined to identity |

Two register identifiers are **never** merged into one node. "Possible same person" is a derived
query result (see the ladder below), not a graph fact.

### Edges

```text
(UkOfficerRecord)-[:HELD_APPOINTMENT]->(UkAppointment)-[:AT_COMPANY]->(UkCompany)
(UkCompany)-[:HAS_PSC_RECORD]->(UkPscRecord)
(UkCompany)-[:USED_REGISTERED_OFFICE]->(UkAddress)
(UkCompany)-[:HAS_EVENT]->(UkCompanyEvent)
(UkOfficerRecord)-[:HAS_PRESS_QUERY]->(PressQuery)-[:RETURNED]->(PressResult)
```

`CO_DIRECTOR_OF`, `RECURS_WITH` and every other recurrence relationship is a **view result**,
never a materialised edge. The evidence for a recurrence is the set of overlapping appointment
nodes, which the view returns alongside the aggregate — materialising the summary edge would
detach the count from its evidence and go stale against the register.

### The identity-confidence ladder as graph mechanics

The product spec's five levels map onto three distinct mechanisms:

| Level | Product meaning | Realm mechanism |
|---|---|---|
| 1–2. Exact company / exact officer record | same register identifier | `identity: true` MERGE key — the node **is** the identifier |
| 3. Exact register traversal | the API connects the records | producer-created edge, carrying the fetch provenance |
| 4. Possible same person | compatible attributes, different identifiers | a **view** (`PossibleDuplicateOfficers`) returning candidate pairs with the matching attributes listed; no edge, no merged count |
| 5. Same name only | search lead | search producer output, displayed and discarded; never persisted as a relationship |

**`person_number` does NOT upgrade level 4 — measured and settled.** Its 8-digit prefix is 1:1
with `officerId` across 713 sampled officer records, so it carries no information `officerId`
does not. Duplicate detection stays attribute-based, exactly as originally specified. Project
`person_number` only as the join key to the paid bulk products.

**Level 2 needs a disclosure, not just a key.** Because `officerId` is Companies House's own
grouping of underlying register records, "exact officer record" means "the grouping Companies
House publishes", not "one raw filing". The passport and methodology must say so, and where a
record demonstrably spans several underlying entries that composition belongs in its evidence
drawer. Claiming an unmerged purity the data does not have would be the one dishonesty this
product cannot afford.

**Corporate officers are a sixth case.** `officer_role` spans 23 values and the appointments list
carries `is_corporate_officer`. A corporate director is not a natural person, so it must be
excluded from person-shaped observations (recurring co-director, possible duplicate) rather than
silently counted as one.

The hard invariant, enforced by the row-shape of every aggregate view: levels 4–5 never
contribute to any count anchored on a selected officer record.

## Provenance and the evidence drawer

The product requires every relationship to open an evidence drawer (source, identifiers, dates,
retrieval time, match method, official link). The realm supplies this **without a per-edge
evidence node**:

- Every producer projects the provenance fields onto the node it creates: source identifiers,
  the register dates, `retrievedAt`, and the official deep link (`sourceUrl`, pattern TO MEASURE
  in Phase 0 — the spike must prove which record types have stable public URLs and which need
  the narrowest reproducible page instead).
- Structural edges (`HELD_APPOINTMENT`, `AT_COMPANY`, …) are exact register traversals by
  construction; their evidence *is* the endpoint that returned them, which the connected nodes'
  provenance fields identify. The app renders the drawer from those fields.
- Derived findings (observations, recurrences, duplicate leads) return their constituent record
  identifiers as view columns — the drawer for an aggregate is the list of rows it aggregates.

A dedicated `UkEvidenceRecord` node is introduced only if Phase 3 cross-register joins
(donations, contracts) need provenance that belongs to the *join* rather than to either joined
record. Do not build it speculatively.

## Data source and producers

### The source

**Companies House Public Data API** — key-authenticated (HTTP Basic, **key as username, blank
password**), rate limited to **600 requests per 5 minutes per application** (confirmed from the
official guide, which also reserves the right to ban persistent over-users; 429 headers and any
`Retry-After` still TO MEASURE). Unlike gov-au's feeds, the axes users ask on and the axes the
source serves are **well aligned**: name search, per-officer appointments, per-company
profile/officers/PSCs/filing-history are all first-class endpoints.

**v1 is live-per-key with no mirror, and that is now a measured conclusion.** The free bulk
products cannot serve this product at all: the Free Company Data Product carries no officer,
appointment or PSC-to-officer data (officer bulk data is a *paid* product) and covers **live
companies only**, excluding the dissolved companies this product is largely about. The free PSC
snapshot is complete and remains a candidate future mirror for PSC-side questions only. See
PHASE0-FINDINGS.md §6 — do not revisit bulk as an optimisation.

Access paths, one producer each:

| Producer | Endpoint | Shape | Creates |
|---|---|---|---|
| `officerSearch` | `GET /search/officers?q=` | bounded, paged (`items_per_page`, `start_index`) | search candidates — **display-only**. Returns no officer id field; it must be parsed from the item's `links` URL. DOB is month+year only |
| `officerAppointments` | `GET /officers/{officer_id}/appointments` (`filter=active`, paged) | per-key, paged | `UkOfficerRecord`, `UkAppointment`, and a **fully-named** `UkCompany` — `appointed_to` carries company name, number and status inline |
| `companyProfile` | `GET /company/{companyNumber}` | per-key | `UkCompany` (status verbatim), `UkCompanyEvent` (incorporation, status) |
| `companyOfficers` | `GET /company/{companyNumber}/officers` | per-key, paged | co-director `UkOfficerRecord` + `UkAppointment` |
| `companyPscs` | `GET /company/{companyNumber}/persons-with-significant-control` | per-key, paged | `UkPscRecord` |
| `filingHistory` | `GET /company/{companyNumber}/filing-history` | per-key, paged on `total_count`, **category-filtered at source** | selected `UkCompanyEvent`s, incl. manner of dissolution via `category=gazette` |

Phase 0 must additionally measure, per gov-au practice, before any `project:` block is written:
field presence rates (month/year of birth, occupation, former names, address granularity),
identifier stability across responses, pagination parameters and their real maxima, and what a
resigned-officer record looks like versus a current one.

### Rate-limit and retry policy

The 600/5min budget is the realm's scarcest resource and shapes everything:

- **The passport is one paged call, not `1 + N`.** Because `appointed_to` carries company name,
  number and status inline, every passport headline — appointment counts, date range, companies
  grouped by status — comes from the appointments call alone. Per-company profile, officers, PSC
  and filing-history calls are **expansion** costs the user triggers explicitly, roughly 2–4 per
  expanded company. Producer TTL caching makes the second viewer of a shared page nearly free,
  which is exactly the product's share model.
- **Manner of dissolution costs one filing-history call per dissolved company.** See "Status
  wording" below — this is the one place the product's promises exceed what a single call
  returns.
- `realm.yml` retry policy mirrors gov-au's: retry transport failures only, never HTTP errors —
  and specifically **never 429**, which must instead surface as a partial-result warning
  ("register busy, N of M companies loaded") so a rate-limited page renders as partial, not
  complete. This is the product spec's partial-rendering requirement landing in the realm layer.
- **MEASURED: every response carries `x-ratelimit-limit`, `x-ratelimit-remain`,
  `x-ratelimit-reset` (epoch seconds) and `x-ratelimit-window`.** The producer should track the
  remaining budget from these headers and shed load *before* a 429 rather than discovering the
  limit by hitting it — which also keeps us clear of the documented ban policy.
- **MEASURED: the officer-appointments endpoint caps at 50 items per page** regardless of the
  requested `items_per_page` (company officers honoured 500). Passport paging must assume 50, so
  a 200-appointment professional director costs 4 calls.
- **MEASURED: filing history reports `total_count`, not `total_results`.** A producer reading
  `total_results` on that endpoint sees nothing and mis-pages. Every other endpoint uses
  `total_results`.
- The per-key API credential lives in the credential store, referenced from `apis/`; never in
  this repo.

### Status wording — the register does not say "voluntarily struck off"

`company_status` is a closed 12-value enum and **contains no strike-off value**;
`company_status_detail` offers `active-proposal-to-strike-off` only. The voluntary-versus-
compulsory distinction the product spec demands exists solely in **filing-history gazette
entries** (`gazette-dissolved-voluntary`, `gazette-dissolved-compulsary`, and the
`dissolution-application-strike-off-*` types).

The realm's position: `UkCompany.status` and `.statusDetail` are projected verbatim from the
enum, and the **manner of dissolution is a separate, filing-derived statement** carrying its
gazette entry as evidence — never presented as a status. It is fetched only for dissolved
companies, and only inside the `StatusConcentration` drill-down where a user is asking the
question. Human wording for every code comes from the vendored enumeration mappings, including
`cessation_label_for_status` for cessation dates, so the app never invents phrasing.

**MEASURED and confirmed live**: dissolved companies return `company_status: dissolved` with
`company_status_detail: null`, while their filing history carries `gazette-dissolved-voluntary`
or `gazette-dissolved-compulsory` (plus `DS01` on the voluntary path). `category=gazette` filters
at source, so the manner of dissolution costs exactly one narrow call per dissolved company.

**Do not validate `category` against the vendored swagger enum** — it is stale. Live responses
return `gazette`, `dissolution`, `auditors`, `confirmation-statement` and
`persons-with-significant-control`, none of which the published enum lists, and the first two are
exactly what this feature depends on. Treat category as an open vocabulary and resolve labels
through the vendored enumerations, which are current.

This needs a matching edit to the product spec's release gate, which currently reads as though
the status field itself distinguishes strike-off. See PHASE0-FINDINGS.md §5.

### Dates have three states, not two

Appointments carry `is_pre_1992_appointment` and `appointed_before` (an upper bound, not a
date). Every temporal calculation therefore resolves to exact, bounded, or unknown — and
`RecurringCoDirectors` must return `overlap: unknown` for bounded dates rather than treating the
bound as a start. Imputing a bound as a date would manufacture overlaps the register does not
support, which is precisely the inference the product forbids.

**MEASURED: this is 15% of appointments, not an edge case** (47 of 318 sampled; 10 of 52
officers on one long-lived company). Getting it wrong would corrupt a sixth of the overlap
arithmetic on exactly the historical networks the product exists to explain.

### `sources.yml` sketch

```yaml
sources:
  - name: ch-officer-appointments
    producer: officerAppointments
    label: UkAppointment
    identityProperty: appointmentId
    anchor:
      label: UkOfficerRecord
      keyProperty: officerId
      edge: HELD_APPOINTMENT
    shape: per-key
    filterableAtSource: [officerId]
    updates: business-days
    sync:
      strategy: live
    visibility: public
```

Company profile, officers, PSC and filing-history sources follow the same per-key pattern
anchored on `UkCompany.companyNumber`. `cardinality`/`ordering` are filled from Phase 0
measurements, not guessed.

## Views

Every read path in the product spec's "suggested realm implementation" list becomes a view. The
staged-query discipline (resolve → appointments → companies → expansions → observations) is
enforced by giving each stage its own view rather than one enormous traversal.

### Core views

| View | Params | Returns | Bound |
|---|---|---|---|
| `OfficerPassport` | `officerId` | header counts: current/former appointments, date range, companies by verbatim status | one officer's appointment set |
| `OfficerTimeline` | `officerId`, optional `companyNumber`, `eventTypes` | ordered events with dates-or-explicitly-unknown | one officer's companies |
| `RecurringCoDirectors` | `officerId`, `minShared` | co-officer, shared-company list, **dated overlap intervals per company** | capped, ordered by shared count |
| `SharedAddresses` | `officerId`, `minCompanies` | normalized address, company list, original renderings | one hop from the officer's companies |
| `StatusConcentration` | `officerId` | verbatim status → companies, count | one officer's companies |
| `FormationBurst` | `officerId`, `windowDays` | incorporation clusters with member companies | one officer's companies |
| `SynchronousRoleChanges` | `officerId`, `windowDays` | role-change clusters with the underlying appointments | one officer's appointments |
| `PossibleDuplicateOfficers` | `officerId` | candidate officer records with the compatible attributes enumerated | leads only; never counted |

### View rules

- **Every aggregate row carries its constituent identifiers** (`collect(...)` of appointment /
  company keys) so the drill-down contract — sentence to records to official source in two
  interactions — is satisfied by the row itself, with no second query design.
- **Temporal precision is computed in the view**, not the app: `RecurringCoDirectors` returns
  per-company overlap intervals (or `null` where the register lacks the dates), so "was a
  director *at the same time*" versus "at some other time" versus "cannot be determined" is a
  data column, not front-end arithmetic.
- **Observation thresholds are view params with defaults** (`minShared: 3`, `windowDays: 120`…),
  making the methodology page's "configurable, visible editorial thresholds" literally true —
  the params *are* the published methodology.
- **Fan-out caps live in the views.** The known trap (learned on gov-au's expander): a
  formation-agent address or professional director touches thousands of companies. Every
  expansion view takes an explicit `limit` with a modest default and returns a total alongside
  the capped rows, so the UI can render "+37 other companies" honestly. `maxAnchors` in the view
  declarations is the realm's cost statement for multi-anchor asks.
- **No suspicion arithmetic.** No view computes a score, a ratio presented as risk, or an
  ordering by "unusualness". Ordering columns are counts and dates the drawer can prove.

## Scope and tenancy

All `Uk*` labels are **public-reference data** — the same register facts for every user — and
must be registered with public scope explicitly. (Unregistered labels default to PRIVATE scope,
which would silently partition the register per user and multiply upstream calls by the number
of users.) `PressQuery`/`PressResult` are the exception: they are user-initiated queries and stay
private to the requesting user.

Watches, notebooks and correction requests (Phase 4) are user-scoped by nature and get
non-`Uk*`-prefixed private labels when they arrive.

## App

`apps/director-web.html` — a vibe app over the views above, one view call per screen stage:

1. search box → `officerSearch` producer (display-only candidates);
2. selection → `OfficerPassport` + observation views;
3. explicit expansion → per-company views;
4. every edge/aggregate click → evidence drawer rendered from provenance columns already in the
   row.

The app never issues a raw traversal the views don't provide — the views are the product's
governed-calculation guarantee. Graph rendering follows the spec's rules (type-coded colour
only, labelled-count sizing only, list equivalent always present).

## Phase mapping

Engineering exit gates alongside the product spec's:

| Product phase | Realm deliverable | Engineering exit gate |
|---|---|---|
| 0 — evidence spike ✅ | `scripts/probe-companies-house.py`; vendored specs + enumerations; PHASE0-FINDINGS.md | **DONE** — every design-critical question answered against the live API, each probe printing a HOLDS/CHANGED verdict that re-runs on demand |
| 1 — passport | `types/uk-corporate.yml`, producers, `sources.yml`, passport + timeline + first three observation views, app skeleton | passport views return correct counts against recorded fixtures; 429 renders as partial |
| 2 — the web | expansion views with caps, `PossibleDuplicateOfficers`, methodology page fed from view params | every graph edge dated or explicitly undated; capped expansions report their cap; duplicate leads excluded from every count (asserted by test) |
| 3 — public-interest layer | contract/donation producers joining on `companyNumber` only; possible-match sections as separate views | exact joins and name-leads structurally separate views — inconfusable by construction |
| 4 — retention | watches/notebooks (private scope), change emails | public views unchanged and still free-path |

## Testing

- `tests/` mirrors gov-au: suite scripts driving the app plus view-level probes.
- **Fixtures are recorded-then-sanitised**: capture real endpoint shapes in Phase 0, then
  replace every name, address and identifier with invented values before committing. Shape
  fidelity yes, real identities no.
- Standing assertions encoding the product's hard promises:
  - no aggregate view row ever includes a level-4/5 identity candidate;
  - status values pass through verbatim (a fixture with "voluntarily struck off" must surface
    exactly that string);
  - every aggregate row's constituent-identifier column is non-empty;
  - a simulated 429 mid-expansion yields a partial-marked result, not a smaller complete-looking
    one.

## Open engineering questions

Carried from the product spec plus this document's own:

**Resolved by Phase 0:**

- ~~Native appointment id?~~ **Company-anchored yes, officer-anchored no** — composite key stands.
- ~~Bulk snapshots as a mirror?~~ **No** — no free officer data, live companies only.
- ~~Filing history filterable by category at source?~~ **Yes**, and the published enum is stale.
- ~~Does `person_number` upgrade duplicate detection?~~ **No** — its prefix is 1:1 with
  `officerId`. But it revealed that `officerId` is itself an upstream merge.

**Still open:**

1. Public URL key: raw `officerId` or an opaque internal key? (Leaning raw — it *is* the public
   register identifier and the honesty story; no identifier churn observed.)
2. **Does the product disclose that an officer record is Companies House's own grouping?**
   Recommended yes, in the methodology and the evidence drawer — see PHASE0-FINDINGS.md §8.
   This is a product decision with a spec edit attached.
3. Does the product keep the voluntary-strike-off promise at one extra call per dissolved
   company, or reword the release gate? (Product decision — PHASE0-FINDINGS.md §5.)
4. Can the composite appointment key collide via same-date re-appointment? (None observed;
   assert uniqueness at MERGE and warn rather than overwrite.)
5. Can historical registered-office addresses be fetched consistently enough to make address
   overlap temporal? (A question about the `address` filing-history category specifically.)
6. At what officer-degree does the passport need a cap, given 50-per-page paging?
7. Where does address normalization run — producer projection (deterministic, cache-friendly) or
   view-time? (Leaning producer, so `UkAddress` identity is stable.)
