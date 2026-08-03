# realm-gov-uk

UK public-register realm for Embabel Worlds. First product: **Director Web**, a free
evidence-linked navigator over Companies House officer records.

Status: **proposal**. No producers, types or views are implemented yet.

| Document | What it holds |
|---|---|
| [DIRECTOR-WEB.md](DIRECTOR-WEB.md) | Product specification — the problem, prior art, product promise, principles, phased roadmap and launch slice |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Realm engineering — graph schema, identity mechanics, provenance model, producers, views (views-first, no lenses), scope, rate-limit policy, phase gates |
| [PHASE0-FINDINGS.md](PHASE0-FINDINGS.md) | Measured evidence-spike results. **Supersedes ARCHITECTURE.md wherever they disagree** |

The product spec originated in [`realm-gov-au`](https://github.com/embabel/realm-gov-au) during
cross-jurisdiction work and moved here so UK types, producers and views carry no Australian
assumptions.

## Where things stand

**Phase 0 and Phase 1 are complete.** The realm loads a self-contained API spec, six producers,
six source contracts, six types and nine views. Nothing is stubbed.

| Path | What it holds |
|---|---|
| `apis/companies-house.yaml` | Self-contained OpenAPI 3 spec, six operations. The vendor's own Swagger 2.0 document cannot be used directly — every path in it is a `$ref` to an unreachable internal host. |
| `apis/companies-house/` | The vendored vendor specs and official enumerations, kept as REFERENCE for field names, enums and the register's own wording. |
| `types/uk-corporate.yml` | `UkAppointment`, `UkCompanyProfile`, `UkCompanyOfficer`, `UkPscRecord`, `UkFilingEvent`, `UkOfficerCandidate`. |
| `producers/uk-companies-house.yml` | One producer per access path. None declares paging — see below. |
| `views/` | The passport path (search → passport → appointments → statuses → timeline) and the three Phase 1 observations, plus the manner-of-dissolution drill-down. |

The two findings that shaped the build:

- **A Companies House `officer_id` is already a merge** of underlying register records, not the
  raw atom the product spec assumes. The product must disclose it rather than claim an unmerged
  purity it does not have.
- **The engine cannot express this API's offset paging**, so reads are single-call and officer
  appointments cap at 50. That is surfaced honestly — `OfficerPassport` returns
  `possiblyTruncated`, `ManyAppointments` returns `countIsAFloor` — rather than presented as a
  total. See PHASE0-FINDINGS.md §12.

## Credentials

The API key is an *API Key application* from
<https://developer.company-information.service.gov.uk/>. Auth is HTTP Basic with the **key as the
username and a blank password**, and nothing in the credential path base64-encodes, so the realm
reads a pre-encoded secret:

```bash
UK_COMPANIES_HOUSE_BASIC=$(printf '%s:' "$UK_COMPANIES_HOUSE_API_KEY" | base64)
```

## Verifying

```bash
# Shape, wiring and spec cross-check — no network, no app boot.
cd ../assistant && ./mvnw test -pl . -Dtest=RealmGovUkShapeTest

# The measured API facts, re-checked (~45 calls; HOLDS/CHANGED per finding).
export CH_API_KEY=...
python3 scripts/probe-companies-house.py

# Every producer projection replayed against live responses.
python3 scripts/verify-projections.py
```

Next: Phase 2 — the web. Bounded co-director, PSC and address expansion, and the
possible-duplicate comparison that never merges.
