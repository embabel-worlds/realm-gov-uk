#!/bin/sh
# tests/verify.sh — realm-gov-uk's battery against a LIVE appliance, in one command.
#
#   APPLIANCE=http://localhost:11043 AUTH=user:pass [UK_COMPANIES_HOUSE_BASIC=…] sh tests/verify.sh
#
# UK_COMPANIES_HOUSE_BASIC is the same secret the realm's API declaration uses: base64("<api key>:").
# Without it the Companies House reconciliations (L2) and the sector-window size check (L3) are
# skipped and say so; everything else still runs. The sanctions reconciliation needs no key.
#
#   L1  every view answers BY NAME — on its defaults, or with the subject below for a view whose
#       params are required. A refusal or error fails; the passport views must return rows.
#   L2  the realm against the sources read directly: the officer's appointments, the company's
#       officers and status from Companies House; the surname's designations from the published
#       UK Sanctions List CSV.
#   L3  cost: a company profile read cold makes exactly one source call; a sector read with a
#       company type and a dissolution window makes one call and returns the register's own
#       filtered page (pushed down), not the sector's newest 100 filtered afterwards.
#
# Subjects are public register records chosen to be stable: Tesco PLC (00445790) and one of its
# current directors. The last line on success is exactly `ALL CHECKS PASS`; any failure exits 1.
set -eu
cd "$(dirname "$0")/.."
APPLIANCE=${APPLIANCE:-${APPLIANCE_URL:-http://localhost:11043}}
AUTH=${AUTH:-${EMBABEL_AUTH:-}}
[ -n "$AUTH" ] || { echo "set AUTH=user:pass for the target appliance"; exit 2; }
exec python3 - "$APPLIANCE" "$AUTH" <<'PY'
import base64, csv, io, json, os, sys, urllib.request, urllib.parse

base, auth = sys.argv[1], sys.argv[2]
HDR = {"Authorization": "Basic " + base64.b64encode(auth.encode()).decode(), "Content-Type": "application/json"}
CH = os.environ.get("UK_COMPANIES_HOUSE_BASIC", "").strip()
COMPANY, OFFICER, NAME, SURNAME, SIC = "00445790", "mNJapaOxmblQiJZN4Gr-3vxWMHk", "Ken Murphy", "Kim", "56101"
fails = []

def check(what, ok, detail=""):
    print(("ok    " if ok else "FAIL  ") + what + (("  " + detail) if detail else ""))
    if not ok: fails.append(what)

def post(path, body):
    req = urllib.request.Request(base + path, json.dumps(body).encode(), HDR)
    try:
        with urllib.request.urlopen(req, timeout=600) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        return {"status": "HTTP %d" % e.code, "error": e.read().decode()[:300]}

def view(name, args=None):
    return post("/api/v1/views/%s/invoke" % urllib.parse.quote(name), {"args": args or {}})

def ch(path):
    req = urllib.request.Request("https://api.company-information.service.gov.uk" + path, headers={"Authorization": "Basic " + CH})
    with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)

print("== L1: every view by name")
import glob, yaml
ARGS = {"officerId": OFFICER, "companyNumber": COMPANY, "query": NAME, "surname": SURNAME, "companyNumbers": COMPANY}
MUST_ROWS = {"OfficerPassport", "OfficerAppointments", "OfficerTimeline", "OfficerCompaniesByStatus", "OfficerSearchCandidates",
             "CompanyOfficersOf", "CompanyProfileOf", "ManyAppointments", "SanctionsNameCheck", "PhoenixBySector"}
results = {}
for f in sorted(glob.glob("views/*.yml")):
    for v in yaml.safe_load(open(f)) or []:
        params = v.get("params") or {}
        args = {k: ARGS[k] for k, s in params.items() if isinstance(s, dict) and s.get("required") and k in ARGS}
        env = view(v["name"], args); results[v["name"]] = env
        rows = env.get("data") or []
        ok = env.get("status") == "SUCCEEDED" and (rows or v["name"] not in MUST_ROWS)
        check("%-26s %4d rows" % (v["name"], len(rows)), ok, "" if ok else "%s %s" % (env.get("status"), str(env.get("error"))[:200]))

print("== L2: against the sources")
rows = results["SanctionsNameCheck"].get("data") or []
req = urllib.request.Request("https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv", headers={"User-Agent": "realm-gov-uk-battery"})
text = urllib.request.urlopen(req, timeout=300).read().decode("utf-8-sig", "replace")
listed = list(csv.DictReader(io.StringIO(text.split("\n", 1)[1])))
want = {r["Unique ID"] for r in listed if r["Name 6"].strip().lower() == SURNAME.lower()}
got = {r.get("designationId") for r in rows}
check("SanctionsNameCheck(%s): the designations the list holds" % SURNAME, got == want, "got %d, list %d" % (len(got), len(want)))
if CH:
    appts = ch("/officers/%s/appointments?items_per_page=50" % OFFICER)
    n = len(results["OfficerAppointments"].get("data") or [])
    check("OfficerAppointments = Companies House's first page", n == len(appts.get("items", [])), "%d vs %d" % (n, len(appts.get("items", []))))
    off = ch("/company/%s/officers?items_per_page=500" % COMPANY)
    n = len(results["CompanyOfficersOf"].get("data") or [])
    check("CompanyOfficersOf = Companies House total_results", n == off.get("total_results"), "%d vs %s" % (n, off.get("total_results")))
    prof = ch("/company/%s" % COMPANY)
    got = [r.get("companyStatus") or r.get("status") for r in results["CompanyProfileOf"].get("data") or []]
    check("CompanyProfileOf status = the register's", prof.get("company_status") in got, "%s vs %s" % (got, prof.get("company_status")))
else:
    print("SKIP  Companies House reconciliations: UK_COMPANIES_HOUSE_BASIC is not set")

print("== L3: what it costs at the source")
def kg(cypher):
    return post("/api/v1/admin/kg/execute", {"cypher": cypher})
r = kg("MATCH (c:UkCompany {companyNumber: '%s'})-[:HAS_PROFILE {ai: {fresh: true}}]->(p:UkCompanyProfile) RETURN p.companyStatus AS s" % COMPANY)
check("one company profile, cold: 1 source call", r.get("apiCalls") == 1 and len(r.get("rows") or []) == 1, "apiCalls=%s rows=%s" % (r.get("apiCalls"), len(r.get("rows") or [])))
q = ("MATCH (s:UkSectorDissolutions {sicCode: '%s'})-[:FOUND {ai: {fresh: true}}]->(d:UkDissolvedCompany) "
     "WHERE d.companyType = 'ltd' AND d.dateOfCessation >= '2025-01-01' AND d.dateOfCessation <= '2025-01-31' "
     "RETURN count(d) AS n" % SIC)
r = kg(q); n = (r.get("rows") or [{}])[0].get("n")
check("sector window: 1 source call", r.get("apiCalls") == 1, "apiCalls=%s log=%s" % (r.get("apiCalls"), r.get("apiCallLog")))
if CH:
    hits = ch("/advanced-search/companies?sic_codes=%s&company_status=dissolved&company_type=ltd&dissolved_from=2025-01-01&dissolved_to=2025-01-31&size=1" % SIC).get("hits")
    check("sector window pushed: the register's filtered page, not a filtered sector page", n == min(100, hits or 0), "n=%s, register hits=%s" % (n, hits))
else:
    check("sector window pushed: rows inside the window", (n or 0) > 0, "n=%s" % n)

print()
if fails:
    print("%d check(s) failed: %s" % (len(fails), "; ".join(fails))); sys.exit(1)
print("ALL CHECKS PASS")
PY
