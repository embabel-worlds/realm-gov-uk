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

Phase 0's desk-measurable half is **done**: the API specification and enumerations are vendored
under `apis/companies-house/`, and three design assumptions changed (see PHASE0-FINDINGS.md).
The live half is **blocked on an API key**.

To unblock it: register an *API Key application* at
<https://developer.company-information.service.gov.uk/>, then

```bash
export CH_API_KEY=...
python3 scripts/probe-companies-house.py --names "smith,patel,okafor" --out target/probe
```

The probe answers the remaining live questions — chiefly whether `person_number` is a stable
cross-record person identifier, which would change how duplicate officer records are detected.
No YAML gets written until it has run.
