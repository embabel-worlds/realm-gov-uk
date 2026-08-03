# Phase 0 — evidence spike findings

**Measured:** 2026-08-03, against the live Companies House developer specs, the download service
and the live API.
**Status:** COMPLETE. Both halves measured. Reproduce with
`CH_API_KEY=... python3 scripts/probe-companies-house.py` (~45 calls, prints a verdict per
finding).

Everything below is a measured fact with the probe that produced it, in the `realm-gov-au` house
style. Facts that contradict an assumption in [DIRECTOR-WEB.md](DIRECTOR-WEB.md) or
[ARCHITECTURE.md](ARCHITECTURE.md) are marked **CONTRADICTS** and carry the consequence.

## 1. The API requires a key; the docs do not

```
$ curl -s https://api.company-information.service.gov.uk/company/00000006
401 {"error":"Empty Authorization header","type":"ch:service"}
```

- **Auth:** HTTP Basic, **API key as the username, password blank** (`curl -u my_api_key:`).
  Not a bearer token, not a query parameter.
- **Where to get one:** register a Companies House user account, then create an *API Key
  application* in the Developer Hub at <https://developer.company-information.service.gov.uk/>.
  The reference pages under `developer-specs.company-information.service.gov.uk` are
  documentation only and need no key — they are not the source of one.
- **Credential handling:** the key goes in the credential store and is referenced from
  `apis/`. It never enters this repo.

Every remaining TO MEASURE in ARCHITECTURE.md needs live responses, so it needs this key.

## 2. Rate limit confirmed at 600 requests / 5 minutes, per application

From the official rate-limiting guide, verbatim: *"You can make up to 600 requests within a
five-minute period. If you exceed this limit, you will receive a 429 Too Many Requests HTTP
status code for each request made within the remainder of the five-minute window."* The guide
also reserves the right to **ban without notice** applications that regularly exceed it.

This confirms the architecture's premise that the request budget, not compute, is the scarce
resource — and that a 429 must surface as a partial-result warning and never be retried.

## 3. The full API specification is published and now vendored

Swagger 2.0, 34 paths, split across 22 `$ref`-linked files (the root `swagger.json` is a 9 KB
skeleton whose refs point at `127.0.0.1:10000` — an internal authoring host — but each file is
independently fetchable at its public URL). All of them, plus the enumeration mappings, are
vendored under `apis/companies-house/` so no build step reaches the network.

The enumeration mappings come from the official `companieshouse/api-enumerations` repo and are
the source of the register's own human wording for statuses, filing types and PSC natures of
control. They are what makes "the register's words, never ours" implementable.

## 4. Endpoint facts that change the design

### `GET /officers/{officer_id}/appointments`

Params: `officer_id` (path), `filter=active`, `items_per_page`, `start_index`.
List-level fields include `total_results`, `items_per_page`, `start_index`, `date_of_birth`,
`is_corporate_officer`, `name`.

Each appointment item carries **`appointed_to` inline** — `company_name`, `company_number` and
`company_status`.

> **Consequence — the passport gets much cheaper than the architecture assumed.**
> ARCHITECTURE.md costed a passport at `1 + N` calls (appointments, then one profile per
> company). Company name, number and status arrive *with the appointments*, so the headline
> passport — appointment counts, date range, companies-by-status — is **one paged call**.
> Per-company profile calls become an expansion cost, not a passport cost. Update the cost model
> and the caching strategy accordingly.

**No appointment identifier is present on the item.** The only identity available is
`officer_id` + `appointed_to.company_number` + `appointed_on`. This resolves open question 2 in
favour of the composite key — subject to a live check that a single officer never holds two
appointments at the same company on the same date (re-appointment after resignation is the risk
case, and it is exactly what the 20-person probe set must include).

### Pre-1992 appointments break the date model

Items carry `is_pre_1992_appointment` (boolean) and `appointed_before` (a date the officer was
appointed *before*), present only when that flag is true.

> **Consequence — temporal precision needs a third state at the data layer, not just the UI.**
> The product spec already promises to distinguish "was a director when this happened" from
> "cannot be determined". This is the concrete mechanism: an appointment start is either
> `appointed_on` (exact), `appointed_before` (an upper bound), or absent. Overlap arithmetic in
> `RecurringCoDirectors` must return `overlap: unknown` for bounded dates rather than treating
> the bound as the date. Imputing `appointed_before` as a start date would silently manufacture
> overlaps that the register does not support.

### `officer_role` is a 23-value enum

Including `director`, `secretary`, `llp-member`, `nominee-director`, `corporate-director`,
`judicial-factor` and `receiver-and-manager`. "Director Web" is therefore a product name, not a
filter: the passport must state which roles it counts. Corporate officers are a distinct kind
(`is_corporate_officer` at list level) and are not natural persons — the identity ladder needs a
sixth case, or corporate officers must be excluded from person-shaped observations.

### `GET /company/{n}/officers` exposes `person_number`

Documented as *"Unique person identifier as displayed in bulk products 195, 198, 208, 209 and
216."*

> **Consequence — a possible real identity key, worth a dedicated live probe.** If
> `person_number` is stable and shared across a person's separate officer records, it is a
> materially stronger basis for the level-4 "possible same person" view than name-and-attribute
> comparison. If it is per-appointment, it is worthless for that purpose. This single
> measurement could change the duplicate-detection design, so it is the highest-value item on
> the live-probe list. It is exposed on the company-officers endpoint but **not** on the
> officer-appointments endpoint, which is itself a routing consequence.

Also on this endpoint: `register_type` (`directors`/`secretaries`/`llp_members`),
`register_view`, and `order_by` (`appointed_on`/`resigned_on`/`surname`).

### `GET /search/officers` returns no officer id directly

Items carry `address`, `appointment_count`, `date_of_birth` (month + year only),
`description_identifiers`, `kind`, plus the common `title`, `address_snippet`, `snippet`,
`matches` and `links`. The officer identifier must be parsed out of the `links` URL. Search is
display-only anyway, so this is a producer-projection detail, not a design change — but it means
the search producer cannot claim an `officerId` field without a URL-parsing step.

`date_of_birth` is month + year only, which is the register's own privacy posture and the exact
granularity the product spec wants for disambiguation. No extra minimisation work is needed.

### `GET /company/{n}/filing-history` filters by category at source

Enum: `accounts`, `address`, `annual-return`, `capital`, `change-of-name`, `incorporation`,
`liquidation`, `miscellaneous`, `mortgage`, `officers`, `resolution`. Comma-separated and
inclusive. This resolves the architecture's TO MEASURE on category filtering: timeline events
can be fetched narrowly rather than paging a whole filing history.

Note the enum has no `gazette` category despite gazette filings existing as *types* — see the
strike-off finding below.

## 5. CONTRADICTS: "voluntarily struck off" is not a company status

The product spec insists — three separate times, including in a release gate — that the app must
display "voluntarily struck off" rather than collapsing it into "dissolved". **The API has no
such status.**

`company_status` is a closed 12-value enum: `active`, `dissolved`, `liquidation`,
`receivership`, `administration`, `voluntary-arrangement`, `converted-closed`,
`insolvency-proceedings`, `registered`, `removed`, `closed`, `open`.

`company_status_detail` is a separate 10-value enum containing `active-proposal-to-strike-off`
— a company *heading toward* strike-off — but nothing recording that a dissolution *was* by
voluntary strike-off.

The voluntary-versus-compulsory distinction exists only in **filing history entries**:

```
gazette-notice-voluntary        "First Gazette notice for voluntary strike-off"
gazette-dissolved-voluntary     "Final Gazette dissolved via voluntary strike-off"
gazette-notice-compulsary       "First Gazette notice for compulsory strike-off"
gazette-dissolved-compulsary    "Final Gazette dissolved via compulsory strike-off"
dissolution-application-strike-off-company
                                "Application to strike the company off the register"
dissolution-voluntary-strike-off-discontinued
                                "Voluntary strike-off action has been discontinued"
```

> **Consequence — the promise costs one extra call per dissolved company, or it must be
> reworded.** Honouring it requires a filing-history fetch per dissolved company and a derived
> reading of gazette entries. Two options, and this is a product decision, not an engineering
> one:
>
> - **(a) Keep the promise, pay for it.** Fetch filing history for dissolved companies only,
>   and present the manner of dissolution as a *filing-derived* statement with the gazette entry
>   as its evidence — never as a status. Cost is bounded because it applies only to dissolved
>   companies, and the observation "nine connected companies are dissolved" is exactly where a
>   user will want it.
> - **(b) Reword the spec.** Report `company_status` plus `company_status_detail` verbatim and
>   drop the strike-off distinction from the release gate.
>
> Recommendation is (a), scoped to the `StatusConcentration` drill-down rather than the passport,
> because the distinction is genuinely meaningful to the product's audience and the spec's own
> release gate is written around it. Either way ARCHITECTURE.md and the gate need editing —
> today they promise something the status field cannot deliver.

There is also a `cessation_label_for_status` mapping (`dissolved` → "Dissolved on",
`converted-closed` → "Closed on", `removed` → "Removed on") which is how the official service
words a cessation date. Reuse it rather than inventing phrasing.

## 6. CONTRADICTS: the free bulk products cannot serve this product

The architecture left open whether bulk snapshots might back recurrence queries. They cannot,
for two independent reasons:

1. **No officer data.** The Free Company Data Product (`BasicCompanyDataAsOneFile-2026-08-01.zip`,
   493 MB, monthly, keyless) contains company records only — the product page mentions no
   officer, director, appointment or PSC field anywhere. Officer and appointment bulk data are
   the **paid** Companies House bulk products (195, 198, 208, 209, 216 — the same list cited in
   the `person_number` documentation), ordered separately, not free downloads.
2. **Live companies only.** The product is *"a downloadable data snapshot containing basic
   company data of **live** companies on the register"*. Dissolved companies are excluded — and
   dissolved companies are central to Director Web, whose flagship observation is a
   concentration of dissolved connected companies.

The PSC snapshot (`psc-snapshot-2026-08-02`, 32 parts, near-daily) *is* free and complete, and
remains a plausible future mirror for PSC-side recurrence questions — but it is PSC data keyed
by company, not an officer spine.

> **Consequence — v1 live-per-key is confirmed as the only viable architecture, and it is now a
> measured conclusion rather than a preference.** Record it in `sources.yml` with this reasoning
> so nobody revisits bulk as an optimisation later.

## 7. Deep links work and need no key

```
200  https://find-and-update.company-information.service.gov.uk/company/00000006
200  .../company/00000006/officers
200  .../company/00000006/filing-history
```

The public service resolves company-scoped paths cleanly, so the evidence drawer's "official
link" is a template, not a lookup. Officer-scoped deep links follow `/officers/{officer_id}/appointments`
on the same host and must be confirmed with a real officer id once a key exists.

## 8. LIVE: `officer_id` is already a merge — and `person_number` adds nothing

This was the highest-value question, and the answer inverts the assumption behind it.

`person_number` is a 12-digit value with internal structure: an 8-digit **prefix** and a 4-digit
**suffix**. Measured over 854 officer entries across 20 companies (713 distinct officer records):

| Relationship | Result |
|---|---|
| prefix → officer_id | **1:1** — 0 prefixes span more than one officer id |
| officer_id → prefix | **1:1** — all 713 officer ids sit under exactly one prefix |
| officer_id → person_number | **1:many** — 9 of 713 (1.3%) span two or more, differing only in suffix |

Confirmed on a single officer directly: 24 appointments across 8 sampled companies returned one
prefix but **two** person_numbers (`…0001` and `…0002`), with the officer-appointments endpoint
returning all of them under one officer id.

The model is therefore: **prefix = the natural person, suffix = one underlying register record,
`officer_id` = Companies House's own aggregation of every record sharing a prefix.**

> **Consequence 1 — duplicate detection stays attribute-based.** Since prefix and `officer_id`
> are 1:1, `person_number` carries no information `officer_id` does not already carry. It cannot
> upgrade the level-4 "possible same person" view. Design that view as originally specified
> (attribute comparison, candidates listed, never merged, never counted), and keep
> `person_number` only as the join key to the paid bulk products.
>
> **Consequence 2 — the product's identity honesty needs restating, and this matters more.**
> DIRECTOR-WEB.md and ARCHITECTURE.md both treat a Companies House officer record as the raw,
> unmerged atom: *"`UkOfficerRecord` — one Companies House officer identifier, not automatically
> a natural person"*, with the product promising never to merge. But `officer_id` **is itself a
> merge**, performed upstream by Companies House, of several underlying register records — in
> 1.3% of records observed here. The product cannot claim to present unmerged raw records while
> its atom is a supplied judgment.
>
> The fix is honesty, not avoidance: keep `officer_id` as the identity key (there is no
> finer-grained alternative exposed on the officer-anchored path anyway), and state plainly in
> the methodology and the passport that the officer record is Companies House's own grouping of
> register entries. Where an officer record spans multiple `person_number`s, that is disclosable
> provenance — the record's own composition — and it belongs in the evidence drawer. This
> *strengthens* the product's honesty claim rather than weakening it, because it stops the app
> asserting a purity it does not have.

## 9. LIVE: appointment identity is asymmetric by approach path

The same appointment has an id when reached from the company, and none when reached from the
officer:

- **Company-anchored** (`GET /company/{n}/officers`) — each item's `links.self` is
  `/company/{n}/appointments/{appointment_id}`, and that URL resolves to a single appointment
  resource.
- **Officer-anchored** (`GET /officers/{id}/appointments`) — each item's `links` contains only
  `company`. There is no appointment id anywhere on the item.

> **Consequence — the composite key stands, because the passport is officer-anchored.**
> `UkAppointment` identity remains `officerId + companyNumber + appointedOn`. The company-side
> `appointment_id` is still worth projecting when a company expansion supplies it, because it
> gives the evidence drawer an exact single-record deep link. No collisions were observed in the
> sampled data, but same-date re-appointment remains the theoretical collision case.

## 10. LIVE: confirmations and paging gotchas

- **Passport cost confirmed.** Every appointment's `appointed_to` carried company name, number
  and status. The passport headline really is one paged call.
- **Bounded dates are common, not an edge case.** Of 318 sampled appointments, **47 (15%)** had
  no `appointed_on` and instead carried `appointed_before` with `is_pre_1992_appointment: true`.
  On one long-lived company, 10 of 52 officers were pre-1992. The three-state date model is
  mandatory, and imputing the bound would corrupt a sixth of the overlap arithmetic.
- **Strike-off wording confirmed retrievable.** Dissolved companies carry
  `gazette-dissolved-voluntary` or `gazette-dissolved-compulsory` filing descriptions (plus
  `DS01` / `dissolution-application-strike-off-company` on the voluntary path). `company_status`
  was `dissolved` with `company_status_detail: null` in every case — confirming §5: the
  distinction exists *only* in filing history.
- **`category=gazette` filters at source**, returning only gazette items. The manner of
  dissolution therefore costs exactly one narrow call per dissolved company.
- **Filing history pages on `total_count`, not `total_results`.** Every other endpoint uses
  `total_results`; filing history uses `total_count` and omits `total_results` entirely. A
  producer that reads `total_results` here will silently see "unknown total" and mis-page.
- **`items_per_page` ceilings differ.** Company officers honoured 500. Officer appointments
  **cap at 50** regardless of what is requested — so a 200-appointment professional director
  costs 4 calls, not 1. Fan-out budgeting must use 50 as the page size on the passport path.
- **Rate-limit headers are returned on every response**: `x-ratelimit-limit: 600`,
  `x-ratelimit-remain`, `x-ratelimit-reset` (epoch seconds), `x-ratelimit-window: 5m`. The
  producer can therefore track its own budget precisely rather than inferring it, and shed load
  before hitting a 429. No 429 was deliberately provoked.

## 11. LIVE: the published filing-history category enum is stale

The vendored swagger declares 11 categories. Live responses returned five more:
`auditors`, `confirmation-statement`, `dissolution`, `gazette`,
`persons-with-significant-control`.

> **Consequence — never validate against the spec enum.** `gazette` and `dissolution` are
> precisely the categories the strike-off feature depends on, and both are absent from the
> published enum. Treat category as an open vocabulary, project it verbatim, and resolve labels
> through the vendored enumerations (which *are* current) rather than the swagger.

## Remaining live probes (lower value, deferred to implementation)

Ordered by how much each could still change the design:

Answered above: `person_number` (§8), appointment identity (§9), paging ceilings, date states,
strike-off retrieval, rate-limit headers (§10), category vocabulary (§11).

Still worth measuring, but none blocks writing YAML:

1. **Composite appointment key collisions** — the sampled data showed none, but a deliberate
   hunt for same-company re-appointment on the same date would close it. Cheap safeguard: assert
   uniqueness at MERGE time and log a warning rather than silently overwriting.
2. **High-degree officers** — the largest `appointment_count` reachable, and what paging a
   formation-agent director actually costs at 50 per page. Sizes the passport cap.
3. **Field presence rates** for `occupation`, `nationality`, `former_names` and
   `country_of_residence`, over a probe set spanning common names, apparent duplicates,
   professional directors, purely historical appointments, corporate officers and
   dissolved-heavy networks. Determines which attributes the disambiguation cards can rely on.
4. **429 behaviour in practice** — whether a `Retry-After` accompanies it. Not provoked
   deliberately; the `x-ratelimit-*` headers make pre-emptive shedding the better design anyway.
5. **Corporate officer shape** — how `is_corporate_officer` records differ, to size the
   exclusion rule for person-shaped observations.
6. **Officer-scoped public deep-link** confirmation on `find-and-update…`.
