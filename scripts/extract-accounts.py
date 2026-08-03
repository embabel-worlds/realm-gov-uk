#!/usr/bin/env python3
"""Extract filed accounts figures for a company, from Companies House iXBRL.

This is a PROVEN PROTOTYPE, not the shipped path. It exists because the realm cannot yet fetch
these documents itself (see the blocker below), and because the numbers it produces settle two
design questions that were otherwise guesswork:

  1. The figures are STRUCTURALLY TAGGED, not prose. An accounts document filed as iXBRL carries
     `ix:nonFraction` facts whose name is a standard UK GAAP tag (`core:Equity`,
     `core:CashBankOnHand`, `core:NetAssetsLiabilities`) and whose period comes from the
     `xbrli:context` it points at. No LLM is needed for a balance sheet, which matters for a
     product whose whole claim is sourced numbers. An LLM is for the narrative notes, not these.

  2. COVERAGE IS THE REAL CONSTRAINT, and it is worse than the format suggests. Measured on
     company 06294226 (2026-08-03): of 15 accounts filings, ONE was iXBRL and FOURTEEN were
     PDF-only. Older accounts are scanned images. So a figures-over-time feature must render
     "filed as a PDF — figures not machine-readable" for most historic years, and must never let
     a missing year read as a zero or as a gap in the company's trading.

Three transport details that cost an hour each if rediscovered:

  · The document lives on a DIFFERENT host (document-api…) from the data API, reached through the
    `document_metadata` link on a filing-history item.
  · Ask the metadata endpoint for `resources` FIRST. Requesting xhtml from a PDF-only document
    returns 406, not an empty result.
  · `/content` 302s to signed S3 storage. The Authorization header must NOT be resent on that
    redirect — S3 rejects it with 400. Python's urllib follows redirects WITH the header by
    default, which is exactly the trap.

Values need `scale` (a power of ten) and `sign` applied before they mean anything: a raw "1,095"
with scale="3" is £1,095,000.

    export CH_API_KEY=...
    python3 scripts/extract-accounts.py 06294226
"""

import base64
import collections
import json
import os
import re
import sys
import urllib.error
import urllib.request

API = "https://api.company-information.service.gov.uk"

# Balance-sheet tags worth reporting first. The full set is whatever the filing tagged.
HEADLINE_TAGS = [
    "core:Equity", "core:NetAssetsLiabilities", "core:CashBankOnHand",
    "core:FinancialAssets", "core:Creditors", "core:NetCurrentAssetsLiabilities",
]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Stop urllib following the 302 so the auth header is never resent to storage."""

    def redirect_request(self, *_args, **_kwargs):
        return None


def _client(key):
    auth = base64.b64encode(f"{key}:".encode()).decode()
    opener = urllib.request.build_opener(_NoRedirect)

    def get_json(url):
        req = urllib.request.Request(url, headers={"Authorization": "Basic " + auth})
        return json.loads(urllib.request.urlopen(req, timeout=30).read())

    def get_content(url, content_type):
        req = urllib.request.Request(
            url, headers={"Authorization": "Basic " + auth, "Accept": content_type}
        )
        try:
            return opener.open(req, timeout=40).read()
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307):
                # Follow WITHOUT the Authorization header — the signed URL carries its own auth.
                return urllib.request.urlopen(e.headers["Location"], timeout=60).read()
            raise

    return get_json, get_content


def facts_from_ixbrl(body):
    """Every tagged numeric fact, keyed by (tag, period end), with scale and sign applied."""
    contexts = {}
    for m in re.finditer(r'<xbrli:context id="([^"]+)".*?</xbrli:context>', body, re.S):
        when = re.search(r"<xbrli:(?:instant|endDate)>([^<]+)<", m.group(0))
        if when:
            contexts[m.group(1)] = when.group(1)

    out = {}
    for m in re.finditer(r"<ix:nonFraction([^>]*)>([^<]*)</ix:nonFraction>", body):
        attrs, raw = m.group(1), m.group(2).strip()
        name = re.search(r'name="([^"]+)"', attrs)
        ctx = re.search(r'contextRef="([^"]+)"', attrs)
        if not (name and ctx and raw):
            continue
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        scale = re.search(r'scale="(-?\d+)"', attrs)
        if scale:
            value *= 10 ** int(scale.group(1))
        sign = re.search(r'sign="([^"]+)"', attrs)
        if sign and sign.group(1) == "-":
            value = -value
        out[(name.group(1), contexts.get(ctx.group(1)))] = value
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: extract-accounts.py <companyNumber>")
    key = os.environ.get("CH_API_KEY")
    if not key:
        sys.exit("CH_API_KEY is not set.")
    company = sys.argv[1]
    get_json, get_content = _client(key)

    history = get_json(f"{API}/company/{company}/filing-history?category=accounts&items_per_page=50")
    series, formats = collections.defaultdict(dict), collections.Counter()

    for item in history.get("items", []):
        metadata_url = (item.get("links") or {}).get("document_metadata")
        if not metadata_url:
            formats["no document"] += 1
            continue
        resources = get_json(metadata_url).get("resources", {})
        if "application/xhtml+xml" not in resources:
            # Filed on paper or as a scanned image: real, and NOT machine-readable.
            formats["PDF only"] += 1
            continue
        formats["iXBRL"] += 1
        body = get_content(metadata_url + "/content", "application/xhtml+xml").decode("utf-8", "ignore")
        for (tag, period), value in facts_from_ixbrl(body).items():
            if period:
                series[tag][period] = value

    print(f"company {company}: accounts filings by format = {dict(formats)}")
    print(f"{len(series)} distinct tagged facts\n")
    if formats["PDF only"]:
        print(f"NOTE: {formats['PDF only']} filing(s) are PDF-only — their figures are NOT in this")
        print("      series. A missing year here means 'not machine-readable', never 'nothing'.\n")

    ordered = [t for t in HEADLINE_TAGS if t in series] + \
              [t for t in sorted(series) if t not in HEADLINE_TAGS]
    for tag in ordered:
        points = sorted(series[tag].items())
        print(f"  {tag:<34} " + "   ".join(f"{d}: {v:,.0f}" for d, v in points))


if __name__ == "__main__":
    main()
