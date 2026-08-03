# Tests

`director-web-suite.js` — an offline browser regression over `apps/director-web.html`. The app
runtime is STUBBED with representative envelopes, so it needs no running world and no Companies
House key: it drives the real app HTML in a real browser and asserts what a user would see.

43 assertions, covering the product's honesty invariants as much as its features:

- both same-name candidates are offered and never merged;
- the 50-appointment read cap is disclosed as a floor, not presented as a total;
- a pre-1992 start renders as "before 1992-04-30" and never as a date;
- voluntary and compulsory strike-off are distinguished, and dissolution is explained as lawful;
- every observation states what it does **not** establish, and no risk/suspicion language appears;
- the two per-company views are not called on render, only on click;
- an empty answer, a failed call and a partial answer are worded as three different things;
- a missing realm is explained by name rather than silently breaking.

The stub's row shapes mirror what the realm's views return, so a view that changes its columns
breaks this suite instead of silently rendering blanks. Every name and number in the fixtures is
invented.

Playwright lives in the `me` repo's `uit/`, and Node resolves modules from the SCRIPT's directory,
so point `NODE_PATH` at it:

```bash
(cd apps && python3 -m http.server 8765 &)
NODE_PATH=../assistant/uit/node_modules node tests/director-web-suite.js
```

What this cannot reach — live view execution, real producer progress, and the register's own
latency — needs the realm installed in a running world. `RealmGovUkAppTest` in the `me` repo
covers the static half: it runs the production app validator over this HTML and cross-checks every
view name and parameter the app calls against the realm's view YAML.
