# Vendored Companies House specifications

Fetched 2026-08-03 from the official developer-specs host and the official enumerations repo.
Vendored so no build or test step reaches the network.

| Path | Origin |
|---|---|
| `spec/swagger.json` | the Swagger 2.0 root — a skeleton whose `$ref`s point at an internal authoring host (`127.0.0.1:10000`), so the referenced files are resolved by name from `spec/` and `models/` here, not by URL |
| `spec/*.json` | the 15 referenced operation/definition files (`officerAppointmentList`, `companyOfficerList`, `companyProfile`, `psc`, `pscModels`, `filingHistory`, `search`, …) |
| `models/*.json` | shared models the specs reference (`errors`, `filings`, `insolvency`, `officerChanges`, `registeredOfficeAddress`) |
| `enumerations/*.yml` | `companieshouse/api-enumerations` — the register's own human wording for statuses, filing types and PSC natures of control |

The enumerations are the source for every user-facing label. Never hand-write phrasing that
exists in `constants.yml`, `psc_descriptions.yml` or `filing_history_descriptions.yml` — the
product promise is the register's words, and these files are those words.

Re-fetch and diff on any upstream change; the paths are stable and the whole set is under 1 MB.
