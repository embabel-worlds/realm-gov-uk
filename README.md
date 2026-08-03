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

**Phase 0 is complete.** The API specification and official enumerations are vendored under
`apis/companies-house/`, and every design-critical question is answered against the live API.
Five assumptions changed — read PHASE0-FINDINGS.md before writing any YAML.

The headline finding: a Companies House `officer_id` is **already a merge** of underlying
register records that Companies House performed, not the raw atom the product spec assumes. That
does not break anything, but it does mean the product must disclose it rather than claim an
unmerged purity it does not have.

Re-run the measurements any time (~45 API calls, one HOLDS/CHANGED verdict per finding):

```bash
export CH_API_KEY=...   # API Key application from developer.company-information.service.gov.uk
python3 scripts/probe-companies-house.py
```

Next: Phase 1 — types, producers and `sources.yml`, then the passport and timeline views.
