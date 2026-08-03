#!/usr/bin/env python3
"""Verify every producer projection against LIVE Companies House responses.

A wrong JSONPath is the quietest failure in a realm: the fetch succeeds, the join forms, and the
property is simply absent — so a passport renders with blank dates or a missing status and nothing
anywhere reports an error. This script makes the real call each producer would make and reports,
per projected field, how many records actually carried a value.

    export CH_API_KEY=...
    python3 scripts/verify-projections.py

It mirrors the engine's path semantics (see RemoteRepositoryBackend): a dotted path walks objects,
a NUMERIC segment indexes an array, and a `[*]` segment flattens a list. Bracketed indexes are NOT
supported by the engine and are not supported here either — if one ever appears in a producer, this
script should report it as null, exactly as production would.

Fields legitimately absent from the register (occupation, resignedOn on a current appointment) are
expected to show partial coverage; the failure signal is a field at 0% where the data plainly
exists, or a field this script cannot resolve at all.
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

API = "https://api.company-information.service.gov.uk"
REALM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_INTERVAL = 0.4

# One representative key per producer. Company numbers are public register identifiers, not
# personal data; the officer id is resolved at run time from a name search so no person is pinned
# into this file.
FIXTURES = {
    "companyProfile": {"company_number": "00000006"},
    "companyOfficers": {"company_number": "00102498"},
    "companyPscs": {"company_number": "11700098"},
    "companyDissolutionFilings": {"company_number": "10432398"},
    "officerSearch": {"q": "smith"},
}

# Fields the REGISTER often or always leaves empty. A zero here is the source's answer, not a
# broken path, and flagging it would train the reader to ignore this script — which is how a real
# broken path gets missed. Each was measured on 2026-08-03; the note is why the zero is expected.
EXPECTED_SPARSE = {
    # Measured 0/27 and 0/96 across two unrelated companies: the register carries the field but
    # almost never populates it. Projected anyway so the rare record that has it is not lost —
    # but no disambiguation card may depend on it.
    ("officerAppointments", "occupation"),
    ("companyOfficers", "occupation"),
    # Present on 29% of search candidates (58/200 measured). The register publishes month and year
    # only, and only for some officers.
    ("officerSearch", "dateOfBirthMonth"),
    ("officerSearch", "dateOfBirthYear"),
    # Usually null even on dissolved companies — the manner of dissolution lives in filing history.
    ("companyProfile", "companyStatusDetail"),
    # Only on pre-1992 appointments (15% of appointments overall, but officer-dependent: a modern
    # director has none at all).
    ("officerAppointments", "appointedBefore"),
    ("companyOfficers", "appointedBefore"),
    # Individual PSCs only; a corporate-entity PSC has neither.
    ("companyPscs", "nationality"),
    ("companyPscs", "countryOfResidence"),
    # Absent while an appointment is current.
    ("officerAppointments", "resignedOn"),
    ("companyOfficers", "resignedOn"),
    ("companyPscs", "ceasedOn"),
    ("officerAppointments", "nationality"),
    ("officerAppointments", "countryOfResidence"),
}


def client(key):
    auth = base64.b64encode(f"{key}:".encode()).decode()
    state = {"last": 0.0}

    def get(path, **params):
        gap = time.monotonic() - state["last"]
        if gap < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - gap)
        url = API + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": "Basic " + auth})
        state["last"] = time.monotonic()
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    return get


def walk(node, path):
    """Resolve one projection path with the engine's semantics."""
    if "[*]" in path:
        head, _, tail = path.partition("[*]")
        base = walk(node, head.rstrip(".")) if head.strip(".") else node
        if not isinstance(base, list):
            return None
        tail = tail.lstrip(".")
        if not tail:
            return base or None
        out = [walk(item, tail) for item in base]
        out = [v for v in out if v is not None]
        return out or None
    cur = node
    for seg in path.split("."):
        if cur is None:
            return None
        if seg.isdigit():
            if not isinstance(cur, list) or int(seg) >= len(cur):
                return None
            cur = cur[int(seg)]
        else:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(seg)
    return cur


def records_of(response, records_path):
    if records_path in ("$", "$."):
        return [response]
    inner = records_path.removeprefix("$.")
    got = walk(response, inner)
    if got is None:
        return []
    return got if isinstance(got, list) else [got]


def call_for(get, producer, key_values):
    """Rebuild the request the engine would issue for this producer."""
    op = producer["operation"]
    args = dict(producer.get("args") or {})
    paths = {
        "officerAppointments": "/officers/{officer_id}/appointments",
        "companyProfile": "/company/{company_number}",
        "companyOfficers": "/company/{company_number}/officers",
        "companyPscs": "/company/{company_number}/persons-with-significant-control",
        "companyFilingHistory": "/company/{company_number}/filing-history",
        "searchOfficers": "/search/officers",
    }
    path = paths[op]
    for name in producer.get("keyArgs") or []:
        path = path.replace("{" + name + "}", urllib.parse.quote(str(key_values[name]), safe=""))
    if producer.get("keyArg"):
        args[producer["keyArg"]] = key_values[producer["keyArg"]]
    return get(path, **args)


def main():
    key = os.environ.get("CH_API_KEY")
    if not key:
        sys.exit(
            "CH_API_KEY is not set.\n"
            "  export CH_API_KEY=$(grep '^UK_COMPANIES_HOUSE_API_KEY=' ../assistant/.env | cut -d= -f2-)"
        )
    get = client(key)

    with open(os.path.join(REALM, "producers", "uk-companies-house.yml")) as fh:
        producers = yaml.safe_load(fh)

    # The officer id is never hard-coded: resolve a real one from a search, the same way the
    # product does. Prefer a candidate with several appointments so optional fields get exercised.
    # A one-appointment officer exercises almost nothing, and search is relevance-ranked rather
    # than appointment-ranked, so take the busiest officer off a large long-lived board instead.
    board = get("/company/00102498/officers", items_per_page=100)
    officer_id, best = None, -1
    for item in board.get("items", [])[:15]:
        link = ((item.get("links") or {}).get("officer") or {}).get("appointments") or ""
        parts = [p for p in link.split("/") if p]
        if len(parts) < 2:
            continue
        count = (get(f"/officers/{parts[1]}/appointments", items_per_page=1) or {}).get("total_results", 0)
        if count > best:
            officer_id, best = parts[1], count
    print(f"resolved a probe officer with {best} appointments")
    FIXTURES["officerAppointments"] = {"officer_id": officer_id}

    failures = []
    print("Projection coverage against live responses")
    print("=" * 62)
    for producer in producers:
        name = producer["name"]
        keys = FIXTURES.get(name)
        if not keys or not all(keys.values()):
            print(f"\n{name}: SKIPPED (no fixture key)")
            continue
        try:
            response = call_for(get, producer, keys)
        except urllib.error.HTTPError as e:
            print(f"\n{name}: HTTP {e.code}")
            failures.append(f"{name}: HTTP {e.code}")
            continue

        records = records_of(response, producer.get("records", "$"))
        print(f"\n{name}  ({len(records)} records)")
        if not records:
            failures.append(f"{name}: produced NO records — check `records:` path")
            print("   !! no records extracted — the `records:` path is wrong")
            continue
        for field, path in (producer.get("project") or {}).items():
            hits = sum(1 for r in records if walk(r, path) is not None)
            pct = 100.0 * hits / len(records)
            sparse = (name, field) in EXPECTED_SPARSE
            flag = "   " if hits else ("  ·" if sparse else " !!")
            note = "" if hits or not sparse else "   (sparse in the register — expected)"
            print(f"{flag} {field:<32} {path:<38} {hits}/{len(records)} ({pct:.0f}%){note}")
            if not hits and not sparse:
                failures.append(f"{name}.{field} -> '{path}' resolved on NO record")

    print("\n" + "=" * 62)
    if failures:
        print("PROJECTIONS THAT RESOLVED NOTHING:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("Every projection resolved on at least one live record.")


if __name__ == "__main__":
    main()
