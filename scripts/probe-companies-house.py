#!/usr/bin/env python3
"""Phase 0 live probe of the Companies House Public Data API.

Reproduces the measurements recorded in PHASE0-FINDINGS.md. Each probe answers one design
question and prints a verdict, so a re-run after an upstream change shows immediately whether a
conclusion still holds.

    export CH_API_KEY=...      # API Key application from developer.company-information.service.gov.uk
    python3 scripts/probe-companies-house.py

The API allows 600 requests / 5 minutes per application and Companies House bans persistent
over-users, so this paces itself, reports the budget headers, and never retries a 429.

It prints only aggregate shape facts and company numbers (public register identifiers, not
personal data). Officer ids, person numbers and names are counted, never printed.
"""

import argparse
import base64
import collections
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.company-information.service.gov.uk"
MIN_INTERVAL = 0.35  # ~2.8/s ceiling is 600/5min; stay clearly under it

# Long-lived companies with large, old officer lists — chosen for shape variety (pre-1992
# appointments, corporate officers, many resignations), not for who is on them.
SAMPLE_COMPANIES = [
    "00000006", "00445790", "02627406", "03977902", "00102498", "00234106", "00542515",
    "04951416", "11700098", "08274009", "00432981", "00651878", "01094398", "00041424",
    "00095411", "00227458", "01471587", "00617987", "02065704", "00214436",
]

# Categories the vendored swagger enum declares. Live responses exceed this — see probe 6.
SPEC_FILING_CATEGORIES = {
    "accounts", "address", "annual-return", "capital", "change-of-name", "incorporation",
    "liquidation", "miscellaneous", "mortgage", "officers", "resolution",
}


class RateLimited(Exception):
    """A 429. Never retried — it is a finding, not a transient error."""


class Client:
    def __init__(self, key):
        self.auth = base64.b64encode(f"{key}:".encode()).decode()
        self.last = 0.0
        self.calls = 0
        self.budget = None

    def get(self, path, **params):
        gap = time.monotonic() - self.last
        if gap < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - gap)
        url = API + path
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        req = urllib.request.Request(url, headers={"Authorization": "Basic " + self.auth})
        self.last = time.monotonic()
        self.calls += 1
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                hdrs = {k.lower(): v for k, v in r.headers.items() if "ratelimit" in k.lower()}
                if hdrs:
                    self.budget = hdrs
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise RateLimited(dict(e.headers)) from e
            if e.code == 404:
                return None
            raise


def officer_id_of(item):
    """The officer id lives only inside links — no endpoint exposes it as a field."""
    link = ((item.get("links") or {}).get("officer") or {}).get("appointments") or ""
    parts = [p for p in link.split("/") if p]
    return parts[1] if len(parts) > 1 and parts[0] == "officers" else None


def verdict(label, ok, detail):
    print(f"  [{'HOLDS' if ok else 'CHANGED'}] {label}: {detail}")


def probe_person_number(client, companies):
    """What is person_number, and does it add linking power over officer_id?

    person_number is <8-digit prefix><4-digit suffix>. The measured model is:
      prefix  = the natural person
      suffix  = one underlying register record for that person
      officer_id = Companies House's own aggregation of every record sharing a prefix

    Two consequences, both load-bearing:
      1. prefix <-> officer_id is 1:1, so person_number adds NOTHING for duplicate detection.
      2. an officer_id spanning several person_numbers is a merge CH already performed --
         which means officer_id is not the raw, unmerged atom the product spec assumes.
    """
    print("\n1. person_number — structure, and does it link anything officer_id does not?")
    by_prefix = collections.defaultdict(set)   # person prefix -> officer ids
    by_officer = collections.defaultdict(set)  # officer id -> full person numbers
    suffixes = collections.Counter()
    entries = 0
    for cn in companies:
        d = client.get(f"/company/{cn}/officers", items_per_page=100)
        for it in (d or {}).get("items", []):
            pn, oid = it.get("person_number"), officer_id_of(it)
            if not (pn and oid):
                continue
            entries += 1
            suffixes[pn[-4:]] += 1
            by_prefix[pn[:-4]].add(oid)
            by_officer[oid].add(pn)

    split_person = {k: v for k, v in by_prefix.items() if len(v) > 1}
    merged_officers = [o for o, v in by_officer.items() if len(v) > 1]
    one_prefix_each = sum(1 for v in by_officer.values() if len({x[:-4] for x in v}) == 1)

    print(f"   {entries} officer entries, {len(by_officer)} distinct officer ids")
    print(f"   suffix distribution: {dict(suffixes.most_common(6))}")
    verdict("prefix <-> officer_id is 1:1 (person_number adds no linking power)",
            not split_person and one_prefix_each == len(by_officer),
            f"{len(split_person)} prefixes span >1 officer id; "
            f"{one_prefix_each}/{len(by_officer)} officer ids sit under exactly one prefix")
    verdict("officer_id is already an upstream MERGE of register records",
            bool(merged_officers),
            f"{len(merged_officers)}/{len(by_officer)} officer ids span >1 person_number "
            f"({100.0 * len(merged_officers) / max(len(by_officer), 1):.1f}%) — "
            "the product's 'raw record' atom is itself a CH judgment")
    return by_officer


def probe_person_number_stability(client):
    """Confirm the merge on a single officer: one prefix, possibly several suffixes."""
    print("\n2. One officer across their companies — one prefix, how many records?")
    d = client.get("/company/00102498/officers", items_per_page=100)
    # A single-appointment officer proves nothing here — find one who sits on several boards.
    oid, appts = None, None
    for cand in [officer_id_of(o) for o in (d or {}).get("items", []) if officer_id_of(o)][:12]:
        a = client.get(f"/officers/{cand}/appointments", items_per_page=50)
        if (a or {}).get("total_results", 0) > 5:
            oid, appts = cand, a
            break
    if not oid:
        print("   no multi-appointment officer in sample; inconclusive")
        return None
    seen = {}
    for a in (appts or {}).get("items", [])[:8]:
        cn = (a.get("appointed_to") or {}).get("company_number")
        if not cn:
            continue
        co = client.get(f"/company/{cn}/officers", items_per_page=100)
        for it in (co or {}).get("items", []):
            if officer_id_of(it) == oid:
                seen[cn] = it.get("person_number")
    values = {v for v in seen.values() if v}
    prefixes = {v[:-4] for v in values}
    verdict("one officer sits under exactly one person prefix", len(prefixes) == 1,
            f"{len(prefixes)} prefix(es), {len(values)} person_number record(s) "
            f"across {len(seen)} companies")
    return prefixes


def probe_appointment_identity(client):
    """Does an appointment carry an id? The answer differs by which side you approach from."""
    print("\n3. Appointment identity — officer-anchored vs company-anchored")
    co = client.get("/company/00000006/officers", items_per_page=1)
    self_link = (((co or {}).get("items") or [{}])[0].get("links") or {}).get("self", "")
    has_company_side_id = "/appointments/" in self_link
    resolved = client.get(self_link) if has_company_side_id else None

    oid = officer_id_of(((co or {}).get("items") or [{}])[0])
    ap = client.get(f"/officers/{oid}/appointments", items_per_page=1) if oid else None
    item = ((ap or {}).get("items") or [{}])[0]
    officer_side_links = sorted((item.get("links") or {}).keys())
    has_officer_side_id = any("appointment" in k for k in officer_side_links)

    verdict("company-anchored appointments HAVE an id", has_company_side_id,
            f"links.self {'resolves' if resolved else 'missing'}")
    verdict("officer-anchored appointments have NO id", not has_officer_side_id,
            f"links keys = {officer_side_links} — composite key required for the passport")
    return has_company_side_id and not has_officer_side_id


def probe_passport_cost(client):
    """Does the appointments call alone carry company name, number and status?"""
    print("\n4. Passport cost — is company detail inline with appointments?")
    co = client.get("/company/00102498/officers", items_per_page=100)
    oid = next((officer_id_of(o) for o in (co or {}).get("items", []) if officer_id_of(o)), None)
    ap = client.get(f"/officers/{oid}/appointments", items_per_page=50)
    items = (ap or {}).get("items", [])
    inline = sum(
        1 for a in items
        if all((a.get("appointed_to") or {}).get(k) for k in ("company_name", "company_number", "company_status"))
    )
    verdict("appointed_to carries name+number+status inline", inline == len(items) and items,
            f"{inline}/{len(items)} appointments — passport is ONE paged call")
    return inline == len(items)


def probe_dates(client, companies):
    """Pre-1992 appointments give a bound, not a date. Is that an edge case or common?"""
    print("\n5. Date states — exact / bounded / absent")
    states = collections.Counter()
    for cn in companies[:6]:
        d = client.get(f"/company/{cn}/officers", items_per_page=100)
        for it in (d or {}).get("items", []):
            if it.get("appointed_on"):
                states["exact"] += 1
            elif it.get("appointed_before"):
                states["bounded (pre-1992)"] += 1
            else:
                states["absent"] += 1
    total = sum(states.values()) or 1
    bounded = states["bounded (pre-1992)"]
    print(f"   {dict(states)}")
    verdict("bounded dates are common enough to design for", bounded > 0,
            f"{bounded} of {total} ({100.0 * bounded / total:.0f}%) — overlap must return 'unknown', never impute")
    return bounded


def probe_filing_history(client):
    """Strike-off wording, the category filter, and the paging field name."""
    print("\n6. Filing history — strike-off distinction, filter, paging")
    live_categories = set()
    manner = collections.Counter()
    for cn in ["11686010", "OC446750", "10432398", "00102498", "00000006"]:
        d = client.get(f"/company/{cn}/filing-history", items_per_page=100)
        if not d:
            continue
        for i in d.get("items", []):
            if i.get("category"):
                live_categories.add(i["category"])
            desc = i.get("description") or ""
            if "gazette-dissolved" in desc:
                manner[desc] += 1

    fh = client.get("/company/11686010/filing-history", items_per_page=100)
    uses_total_count = "total_count" in (fh or {}) and "total_results" not in (fh or {})
    filtered = client.get("/company/11686010/filing-history", category="gazette", items_per_page=50)
    only_gazette = all(i.get("category") == "gazette" for i in (filtered or {}).get("items", []))

    print(f"   manner-of-dissolution descriptions seen: {dict(manner)}")
    verdict("voluntary vs compulsory strike-off is retrievable", bool(manner),
            "only from gazette filing descriptions — never from company_status")
    verdict("category filter narrows at source", only_gazette, "one call per dissolved company")
    verdict("filing history pages on total_count, NOT total_results", uses_total_count,
            f"keys = {sorted((fh or {}).keys())}")
    undocumented = sorted(live_categories - SPEC_FILING_CATEGORIES)
    verdict("the vendored category enum is complete", not undocumented,
            f"live-only categories: {undocumented}")
    return undocumented


def probe_paging(client):
    """items_per_page ceilings differ per endpoint."""
    print("\n7. Paging ceilings")
    d = client.get("/company/00102498/officers", items_per_page=500)
    co_echo = (d or {}).get("items_per_page")
    oid = next((officer_id_of(o) for o in (d or {}).get("items", []) if officer_id_of(o)), None)
    a = client.get(f"/officers/{oid}/appointments", items_per_page=500)
    ap_echo = (a or {}).get("items_per_page")
    print(f"   company officers: asked 500, echoed {co_echo}")
    print(f"   officer appointments: asked 500, echoed {ap_echo}")
    verdict("officer appointments cap at 50 per page", ap_echo == 50,
            f"echoed {ap_echo} — a 200-appointment officer costs 4 calls")
    return ap_echo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--companies", default=",".join(SAMPLE_COMPANIES))
    args = ap.parse_args()

    key = os.environ.get("CH_API_KEY")
    if not key:
        sys.exit(
            "CH_API_KEY is not set.\n"
            "Register an API Key application at "
            "https://developer.company-information.service.gov.uk/ and export the key."
        )

    client = Client(key)
    companies = [c.strip() for c in args.companies.split(",") if c.strip()]
    print("Companies House Phase 0 probe — verdicts against PHASE0-FINDINGS.md\n" + "=" * 66)
    try:
        probe_person_number(client, companies)
        probe_person_number_stability(client)
        probe_appointment_identity(client)
        probe_passport_cost(client)
        probe_dates(client, companies)
        probe_filing_history(client)
        probe_paging(client)
    except RateLimited as e:
        print(f"\n429 Too Many Requests — stopping, not retrying. Headers: {e}")
    print("\n" + "=" * 66)
    print(f"API calls: {client.calls} | budget headers: {client.budget}")


if __name__ == "__main__":
    main()
