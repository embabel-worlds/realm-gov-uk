# realm-gov-uk

UK public-register realm for Embabel Worlds. First product: **Director Web**, a free
evidence-linked navigator over Companies House officer records.

Status: **proposal**. No producers, types or views are implemented yet.

| Document | What it holds |
|---|---|
| [DIRECTOR-WEB.md](DIRECTOR-WEB.md) | Product specification — the problem, prior art, product promise, principles, phased roadmap and launch slice |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Realm engineering — graph schema, identity mechanics, provenance model, producers, views (views-first, no lenses), scope, rate-limit policy, phase gates |

The product spec originated in [`realm-gov-au`](https://github.com/embabel/realm-gov-au) during
cross-jurisdiction work and moved here so UK types, producers and views carry no Australian
assumptions.

Next step is Phase 0 (the evidence spike): measure the Companies House Public Data API and
resolve every TO MEASURE in ARCHITECTURE.md before writing any YAML.
