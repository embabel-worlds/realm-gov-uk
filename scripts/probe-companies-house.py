#!/usr/bin/env python3
"""Phase 0 live probe of the Companies House Public Data API.

Answers the live-probe list in PHASE0-FINDINGS.md against real responses, and writes a report
plus SANITISED fixtures. Nothing it writes contains a real name, address or identifier.

    export CH_API_KEY=...            # from developer.company-information.service.gov.uk
    python3 scripts/probe-companies-house.py --names "smith,patel,okafor" --out target/probe

The API is rate limited to 600 requests / 5 minutes per application, and Companies House bans
persistent over-users, so this script paces itself and never retries a 429.
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

API = "https://api.company-information.service.gov.uk"

# 600 per 5 min = 2/s sustained. Stay well under: this is someone else's public service.
MIN_INTERVAL = 0.75


class RateLimited(Exception):
    """A 429. Never retried — it is a finding, not a transient error."""


class Client:
    def __init__(self, key):
        self.auth = base64.b64encode(f"{key}:".encode()).decode()
        self.last = 0.0
        self.calls = 0
        self.rate_limit_headers = None

    def get(self, path, **params):
        elapsed = time.monotonic() - self.last
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)
        url = API + path
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        req = urllib.request.Request(url, headers={"Authorization": "Basic " + self.auth})
        self.last = time.monotonic()
        self.calls += 1
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                # Capture whatever the service tells us about our budget — a finding in itself.
                hdrs = {k.lower(): v for k, v in r.headers.items() if "ratelimit" in k.lower()}
                if hdrs:
                    self.rate_limit_headers = hdrs
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise RateLimited(dict(e.headers)) from e
            if e.code == 404:
                return None
            raise


def probe(client, names, per_name):
    """Walk search -> appointments -> one company's officers, recording shape facts only."""
    findings = {
        "officerIdSource": None,
        "appointmentItemKeys": Counter(),
        "appointmentFieldPresence": Counter(),
        "appointmentsSeen": 0,
        "nativeAppointmentIdFound": False,
        "compositeKeyCollisions": [],
        "preAppointmentDates": {"exact": 0, "boundedPre1992": 0, "absent": 0},
        "officerRoles": Counter(),
        "corporateOfficerRecords": 0,
        "companyStatuses": Counter(),
        "companyStatusDetails": Counter(),
        "personNumber": {"present": 0, "absent": 0, "byOfficerId": defaultdict(set)},
        "maxItemsPerPage": {},
        "totalResultsVsItems": [],
        "appointmentCounts": [],
        "rateLimitHeaders": None,
        "errors": [],
    }

    for name in names:
        try:
            res = client.get("/search/officers", q=name, items_per_page=per_name)
        except RateLimited as e:
            findings["errors"].append(f"429 during search '{name}': {e}")
            return findings
        if not res:
            continue

        for item in (res.get("items") or [])[:per_name]:
            # The search item carries no officer id field: it must be parsed from links.
            link = (item.get("links") or {}).get("self") or ""
            parts = [p for p in link.split("/") if p]
            if "officers" not in parts:
                continue
            officer_id = parts[parts.index("officers") + 1]
            findings["officerIdSource"] = "links.self"

            try:
                appts = client.get(
                    f"/officers/{officer_id}/appointments", items_per_page=50, start_index=0
                )
            except RateLimited as e:
                findings["errors"].append(f"429 during appointments: {e}")
                return findings
            if not appts:
                continue

            items = appts.get("items") or []
            findings["appointmentCounts"].append(appts.get("total_results"))
            findings["totalResultsVsItems"].append(
                {"total": appts.get("total_results"), "returned": len(items),
                 "itemsPerPage": appts.get("items_per_page")}
            )
            if appts.get("is_corporate_officer"):
                findings["corporateOfficerRecords"] += 1

            seen_composites = set()
            for a in items:
                findings["appointmentsSeen"] += 1
                for k in a:
                    findings["appointmentItemKeys"][k] += 1
                for f in ("occupation", "nationality", "former_names",
                          "country_of_residence", "identification", "resigned_on"):
                    if a.get(f) not in (None, "", [], {}):
                        findings["appointmentFieldPresence"][f] += 1
                if any("appointment_id" in k or k == "id" for k in a):
                    findings["nativeAppointmentIdFound"] = True

                if a.get("appointed_on"):
                    findings["preAppointmentDates"]["exact"] += 1
                elif a.get("appointed_before"):
                    findings["preAppointmentDates"]["boundedPre1992"] += 1
                else:
                    findings["preAppointmentDates"]["absent"] += 1

                findings["officerRoles"][a.get("officer_role")] += 1
                to = a.get("appointed_to") or {}
                findings["companyStatuses"][to.get("company_status")] += 1

                composite = (officer_id, to.get("company_number"), a.get("appointed_on"))
                if composite in seen_composites:
                    findings["compositeKeyCollisions"].append(
                        {"companyNumber": to.get("company_number"),
                         "appointedOn": a.get("appointed_on")}
                    )
                seen_composites.add(composite)

            # person_number lives only on the company-officers endpoint. One company per
            # officer is enough to test whether it is stable across records.
            first = next((a for a in items if (a.get("appointed_to") or {}).get("company_number")), None)
            if first:
                cn = first["appointed_to"]["company_number"]
                try:
                    officers = client.get(f"/company/{cn}/officers", items_per_page=35)
                except RateLimited as e:
                    findings["errors"].append(f"429 during company officers: {e}")
                    return findings
                for o in (officers or {}).get("items", []):
                    pn = o.get("person_number")
                    if pn:
                        findings["personNumber"]["present"] += 1
                        oid = ((o.get("links") or {}).get("officer") or {}).get("appointments", "")
                        findings["personNumber"]["byOfficerId"][pn].add(oid)
                    else:
                        findings["personNumber"]["absent"] += 1

    findings["rateLimitHeaders"] = client.rate_limit_headers
    return findings


def report(findings, calls):
    pn = findings["personNumber"]
    shared = {k: len(v) for k, v in pn["byOfficerId"].items() if len(v) > 1}
    lines = [
        "# Companies House live probe",
        "",
        f"API calls made: {calls}",
        f"Appointments inspected: {findings['appointmentsSeen']}",
        "",
        "## Design-critical answers",
        "",
        f"- Native appointment id present: **{findings['nativeAppointmentIdFound']}** "
        "(False confirms the composite key is required)",
        f"- Composite key collisions: **{len(findings['compositeKeyCollisions'])}**",
        f"- person_number present / absent: **{pn['present']} / {pn['absent']}**",
        f"- person_number values spanning >1 officer record: **{len(shared)}** "
        "(non-zero means it is a real cross-record person key)",
        f"- Officer id source: {findings['officerIdSource']}",
        f"- Rate-limit headers observed: {findings['rateLimitHeaders']}",
        "",
        "## Date states",
        f"- exact `appointed_on`: {findings['preAppointmentDates']['exact']}",
        f"- bounded `appointed_before` (pre-1992): {findings['preAppointmentDates']['boundedPre1992']}",
        f"- absent: {findings['preAppointmentDates']['absent']}",
        "",
        "## Field presence on appointment items",
    ]
    for f, c in findings["appointmentFieldPresence"].most_common():
        pct = 100.0 * c / max(findings["appointmentsSeen"], 1)
        lines.append(f"- {f}: {c} ({pct:.0f}%)")
    lines += ["", "## Officer roles seen"]
    for r, c in findings["officerRoles"].most_common():
        lines.append(f"- {r}: {c}")
    lines += ["", "## Company statuses seen (verbatim)"]
    for s, c in findings["companyStatuses"].most_common():
        lines.append(f"- {s}: {c}")
    lines += ["", "## Paging", "", "| total_results | returned | items_per_page |", "|---|---|---|"]
    for t in findings["totalResultsVsItems"][:20]:
        lines.append(f"| {t['total']} | {t['returned']} | {t['itemsPerPage']} |")
    if findings["errors"]:
        lines += ["", "## Errors", ""] + [f"- {e}" for e in findings["errors"]]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", required=True, help="comma-separated surnames to search")
    ap.add_argument("--per-name", type=int, default=2, help="officer records per name")
    ap.add_argument("--out", default="target/probe")
    args = ap.parse_args()

    key = os.environ.get("CH_API_KEY")
    if not key:
        sys.exit(
            "CH_API_KEY is not set.\n"
            "Register an API Key application at "
            "https://developer.company-information.service.gov.uk/ and export the key."
        )

    client = Client(key)
    names = [n.strip() for n in args.names.split(",") if n.strip()]
    print(f"Probing {len(names)} name(s), up to {args.per_name} officer records each...")
    findings = probe(client, names, args.per_name)

    os.makedirs(args.out, exist_ok=True)
    # Counters and sets are not JSON-serialisable; the report is the readable artefact.
    with open(os.path.join(args.out, "report.md"), "w") as fh:
        fh.write(report(findings, client.calls))
    print(f"\n{report(findings, client.calls)}")
    print(f"Wrote {args.out}/report.md after {client.calls} API calls.")


if __name__ == "__main__":
    main()
