# Phase 0 — evidence spike findings

**Measured:** 2026-08-03, against the live Companies House developer specs, the download service
and the API host itself.
**Status:** desk-measurable half COMPLETE. Live-response half BLOCKED on an API key.

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

## Live-probe list (blocked on the key)

Ordered by how much each could still change the design:

1. **`person_number` stability** across a person's separate officer records — could replace
   attribute matching for level-4 duplicate leads entirely.
2. **Composite appointment key collisions** — any officer with two appointments at one company
   sharing `appointed_on` (re-appointment cases).
3. **`items_per_page` real maximum** and whether `total_results` is exact or capped, per
   endpoint — determines paging cost and whether "+37 others" counts are trustworthy.
4. **429 behaviour in practice** — headers returned, whether a `Retry-After` is supplied.
5. **Field presence rates** over the 20-person probe set: `occupation`, `nationality`,
   `former_names`, `country_of_residence`, `date_of_birth` on appointments.
6. **High-degree officers** — the largest `appointment_count` reachable, and what paging a
   formation-agent director actually costs.
7. **Officer-scoped deep-link format** confirmation.
8. **Corporate officer shape** — how `is_corporate_officer` records differ, to size the
   exclusion rule.

The 20-person probe set itself must span: common names, apparent duplicates, professional
directors, large networks, purely historical appointments, corporate officers, pre-1992
appointments, dissolved-heavy networks, and redacted or partial records.
