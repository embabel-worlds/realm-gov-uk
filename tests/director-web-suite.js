// Offline browser regression for the Director Web app.
//
// The app runtime (`/api/v1/apps-runtime/v1/embabel.js`) is STUBBED with representative envelopes,
// so this needs no running world and no Companies House key — it drives the REAL app HTML in a
// REAL browser and checks what a user would actually see.
//
// The stub's row shapes are copied from what the realm's views RETURN and from live API responses
// measured on 2026-08-03, so a view whose columns change breaks this suite rather than silently
// rendering blanks. Names and numbers below are invented; no real person appears in a fixture.
//
//   (cd apps && python3 -m http.server 8765 &)
//   cd ../../assistant/uit && node ../../realm-gov-uk/tests/director-web-suite.js

const { chromium } = require('playwright');

const BASE = 'http://localhost:8765/director-web.html';
let pass = 0, fail = 0;
const failures = [];
function check(name, cond, detail) {
  if (cond) { pass++; console.log('  ok   ' + name); }
  else { fail++; failures.push(name + (detail ? ' — ' + detail : '')); console.log('  FAIL ' + name + (detail ? ' — ' + detail : '')); }
}

// Envelopes exactly as the view invoke endpoint returns them: rows under `data`, plus `warnings`.
const FIXTURES = {
  OfficerSearchCandidates: [
    { officerId: 'OFFICER_A', name: 'AVERY, Dana Kim', appointmentCount: 26, birthMonth: 4, birthYear: 1968,
      addressSnippet: '11 Example Street, Sampleton', registerDescription: 'Total number of appointments 26',
      officialUrl: 'https://find-and-update.company-information.service.gov.uk/officers/OFFICER_A/appointments' },
    { officerId: 'OFFICER_B', name: 'AVERY, Dana', appointmentCount: 1, birthMonth: null, birthYear: null,
      addressSnippet: '2 Placeholder Road, Sampleton', registerDescription: 'Total number of appointments 1',
      officialUrl: 'https://find-and-update.company-information.service.gov.uk/officers/OFFICER_B/appointments' }
  ],
  OfficerPassport: [
    { appointmentsRead: 50, currentAppointments: 7, formerAppointments: 43, distinctCompanies: 26,
      earliestAppointedOn: '2012-03-14', latestAppointedOn: '2026-01-09', boundedStartDates: 4,
      recordedNames: ['AVERY, Dana Kim'], recordedRoles: ['director', 'secretary'],
      possiblyTruncated: true,
      officialUrl: 'https://find-and-update.company-information.service.gov.uk/officers/OFFICER_A/appointments' }
  ],
  ManyAppointments: [
    { companies: 26, appointmentsRead: 50, currentAppointments: 7, formerAppointments: 43,
      firstAppointedOn: '2012-03-14', lastAppointedOn: '2026-01-09',
      roles: ['director', 'secretary'], companyNumbers: ['01234567', '02345678'], countIsAFloor: true }
  ],
  SynchronousRoleChanges: [
    { windowAnchorDate: '2024-09-10', resignationsInWindow: 6, earliestInWindow: '2024-09-02',
      latestInWindow: '2024-09-14', companies: ['Alpha Holdings Ltd', 'Beta Trading Ltd', 'Gamma Services Ltd'],
      companyNumbers: ['01234567', '02345678', '03456789'] }
  ],
  FormationBurst: [
    { windowAnchorDate: '2019-11-04', companiesIncorporatedInWindow: 8, earliestInWindow: '2019-09-30',
      latestInWindow: '2020-01-22',
      companies: ['Delta Estates Ltd', 'Epsilon Estates Ltd'], companyNumbers: ['04567890', '05678901'],
      companyStatuses: ['active', 'dissolved'] }
  ],
  OfficerDissolutionManner: [
    { companyName: 'Beta Trading Ltd', companyNumber: '02345678', mannerOfDissolution: 'voluntary strike-off',
      registerFilingDescriptions: ['gazette-dissolved-voluntary'], registerFilingTypes: ['GAZ2(A)'],
      latestFilingDate: '2024-11-05',
      filingHistoryUrl: 'https://find-and-update.company-information.service.gov.uk/company/02345678/filing-history' },
    { companyName: 'Gamma Services Ltd', companyNumber: '03456789', mannerOfDissolution: 'compulsory strike-off',
      registerFilingDescriptions: ['gazette-dissolved-compulsory'], registerFilingTypes: ['GAZ2'],
      latestFilingDate: '2023-06-19',
      filingHistoryUrl: 'https://find-and-update.company-information.service.gov.uk/company/03456789/filing-history' }
  ],
  OfficerAppointments: [
    { companyName: 'Alpha Holdings Ltd', companyNumber: '01234567', companyStatus: 'active',
      officerRole: 'director', appointedOn: '2021-03-14', appointedBefore: null, startDateBasis: 'exact',
      resignedOn: null, currentlyRecorded: true, nameOnRecord: 'AVERY, Dana Kim',
      companyUrl: 'https://find-and-update.company-information.service.gov.uk/company/01234567' },
    { companyName: 'Historic Works Ltd', companyNumber: '00098765', companyStatus: 'dissolved',
      officerRole: 'secretary', appointedOn: null, appointedBefore: '1992-04-30', startDateBasis: 'before',
      resignedOn: '1998-02-01', currentlyRecorded: false, nameOnRecord: 'AVERY, Dana',
      companyUrl: 'https://find-and-update.company-information.service.gov.uk/company/00098765' }
  ],
  OfficerCompaniesByStatus: [
    { status: 'dissolved', companies: 9, companyNames: ['Beta Trading Ltd', 'Gamma Services Ltd'],
      companyNumbers: ['02345678', '03456789'] },
    { status: 'active', companies: 7, companyNames: ['Alpha Holdings Ltd'], companyNumbers: ['01234567'] }
  ],
  OfficerTimeline: [
    { eventDate: '2024-09-10', eventType: 'resigned', dateBasis: 'exact', companyName: 'Beta Trading Ltd',
      companyNumber: '02345678', companyStatus: 'dissolved', officerRole: 'director' },
    { eventDate: '1992-04-30', eventType: 'appointed', dateBasis: 'before', companyName: 'Historic Works Ltd',
      companyNumber: '00098765', companyStatus: 'dissolved', officerRole: 'secretary' }
  ]
};

// `EMPTY_FOR` and `WARN_FOR` are set per-scenario from the test to exercise the honesty paths.
const STUB = `
window.__dwCalls = [];
window.__dwEmpty = window.__dwEmpty || [];
window.__dwWarn = window.__dwWarn || [];
window.__dwFail = window.__dwFail || [];
(function () {
  var FIX = __FIXTURES__;
  function envelope(id) {
    if (window.__dwFail.indexOf(id) >= 0) { throw new Error('the register is unavailable'); }
    return {
      outcome: 'SUCCEEDED', outputType: 'rows',
      data: window.__dwEmpty.indexOf(id) >= 0 ? [] : (FIX[id] || []),
      warnings: window.__dwWarn.indexOf(id) >= 0
        ? [{ code: 'PARTIAL', message: 'One company did not answer in time.' }] : []
    };
  }
  async function invoke(kind, id, args) {
    window.__dwCalls.push({ id: id, args: args });
    await new Promise(function (r) { setTimeout(r, 5); });
    return envelope(id);
  }
  window.embabel = {
    views: { invoke: function (id, args, o) { return invoke('view', id, args, o); } },
    lenses: { invoke: function (id, args, o) { return invoke('lens', id, args, o); } },
    createRunner: function () {
      return {
        view: function (id, args, o) { return invoke('view', id, args, o); },
        lens: function (id, args, o) { return invoke('lens', id, args, o); },
        cancel: function () {}
      };
    },
    manifest: { ready: Promise.resolve({ ok: true, missing: {} }) },
    progress: { subscribe: function () { return function () {}; }, label: function () {}, text: function () {} }
  };
})();
`.replace('__FIXTURES__', JSON.stringify(FIXTURES));

async function newPage(browser, opts) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 1400 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => {
    if (m.type() === 'error' && !m.text().includes('404') && !m.text().includes('Failed to load resource')) {
      errors.push('console: ' + m.text().slice(0, 160));
    }
  });
  await page.addInitScript(`window.__dwEmpty = ${JSON.stringify((opts && opts.empty) || [])};
                            window.__dwWarn  = ${JSON.stringify((opts && opts.warn) || [])};
                            window.__dwFail  = ${JSON.stringify((opts && opts.fail) || [])};`);
  await page.addInitScript(STUB);
  return { page, errors, ctx };
}

async function searchAndSelect(page, which) {
  await page.fill('#q', 'avery');
  await page.click('#search-form button[type=submit]');
  await page.waitForSelector('.dw-candidate');
  await page.locator('.dw-candidate').nth(which === undefined ? 0 : which).click();
  await page.waitForSelector('#passport-tiles .dw-tile');
}

(async () => {
  const browser = await chromium.launch();

  // ── happy path ──────────────────────────────────────────────────────────────────────────
  console.log('\n== search and disambiguation ==');
  let { page, errors, ctx } = await newPage(browser);
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  check('passport hidden before a search', await page.locator('#passport-card').isHidden());
  await page.fill('#q', 'avery');
  await page.click('#search-form button[type=submit]');
  await page.waitForSelector('.dw-candidate');
  check('both candidates offered, never merged', (await page.locator('.dw-candidate').count()) === 2);
  const firstCard = await page.locator('.dw-candidate').first().innerText();
  check('candidate shows appointment count', /26 appointments/.test(firstCard));
  check('candidate shows birth month and year', /Born 04\/1968/.test(firstCard));
  const secondCard = await page.locator('.dw-candidate').nth(1).innerText();
  check('a record without a birth date says so rather than blank',
    /Birth date not published/.test(secondCard), secondCard);

  console.log('\n== passport ==');
  await page.locator('.dw-candidate').first().click();
  await page.waitForSelector('#passport-tiles .dw-tile');
  const tiles = await page.locator('#passport-tiles').innerText();
  check('companies count shown', /26/.test(tiles));
  // innerText returns the RENDERED text, and the tile labels are uppercased by CSS — match
  // case-insensitively so this asserts what the user sees rather than what the source says.
  check('current and former split out', /current roles/i.test(tiles) && /former roles/i.test(tiles), tiles);
  check('recorded span shown', /2012-03-14 – 2026-01-09/.test(tiles));
  check('bounded dates surfaced as their own tile', /before/i.test(tiles), tiles);
  const caution = await page.locator('#passport-caution').innerText();
  check('the 50-appointment cap is disclosed as a floor', /floor/i.test(caution), caution);
  check('official officer link present',
    (await page.locator('#passport-link a[href*="/officers/OFFICER_A/appointments"]').count()) === 1);

  console.log('\n== observations ==');
  await page.waitForSelector('.dw-obs');
  const obs = await page.locator('#observations').innerText();
  check('appearance count observation', /appears in 26 companies/.test(obs), obs.slice(0, 120));
  check('synchronous resignations observation', /6 recorded directorships ended within 30 days/.test(obs));
  check('every observation states what it does NOT establish', /does not establish/i.test(obs));
  check('ordinary explanation offered for many appointments', /not evidence of wrongdoing/i.test(obs));
  check('no risk or suspicion language anywhere',
    !/risk|suspicious|fraud|shell company/i.test(await page.locator('body').innerText()));

  console.log('\n== expensive checks are opt-in ==');
  let calls = await page.evaluate(() => window.__dwCalls.map(c => c.id));
  check('FormationBurst NOT called on render', calls.indexOf('FormationBurst') === -1, calls.join(','));
  check('OfficerDissolutionManner NOT called on render', calls.indexOf('OfficerDissolutionManner') === -1);
  await page.click('#btn-formation');
  await page.waitForSelector('#deep-results .dw-obs');
  check('formation cluster renders on request',
    /8 connected companies were incorporated within 120 days/.test(await page.locator('#deep-results').innerText()));
  await page.click('#btn-dissolution');
  await page.waitForSelector('#deep-results table');
  const diss = await page.locator('#deep-results').innerText();
  check('voluntary strike-off distinguished', /voluntary strike-off/.test(diss));
  check('compulsory strike-off distinguished', /compulsory strike-off/.test(diss));
  check('dissolution is explained as lawful, not a finding', /normal, lawful way/i.test(diss));

  console.log('\n== detail tabs ==');
  const appts = await page.locator('#appointments').innerText();
  check('appointments table rendered', /Alpha Holdings Ltd/.test(appts));
  check('a pre-1992 start shows as "before", never as a date', /before 1992-04-30/.test(appts), appts);
  check('an unresigned role reads as still recorded', /still recorded/.test(appts));
  await page.click('#tab-statuses');
  await page.waitForTimeout(150);
  const statuses = await page.locator('#statuses').innerText();
  check('statuses grouped verbatim', /dissolved/.test(statuses) && /active/.test(statuses));
  check('status panel warns the status field has no strike-off value', /no strike-off value/.test(statuses));
  await page.click('#tab-timeline');
  await page.waitForTimeout(150);
  const timeline = await page.locator('#timeline').innerText();
  check('timeline rendered', /resigned/.test(timeline) && /appointed/.test(timeline));
  check('timeline marks a bounded date', /before/.test(timeline));
  check('timeline refuses to imply causation', /states no common reason/.test(timeline));

  console.log('\n== quality invariants ==');
  const body = await page.locator('body').innerText();
  check('no [object Object] anywhere', !body.includes('[object Object]'));
  check('no undefined leaked into the page', !/\bundefined\b/.test(body), body.slice(0, 200));
  const blankTargets = await page.locator('a[target="_blank"]:not([rel*="noopener"])').count();
  check('every new-tab link carries rel=noopener', blankTargets === 0);
  const links = await page.locator('#appointments a[href^="https://find-and-update"]').count();
  check('company names are links to the official register', links > 0);
  check('no console or page errors', errors.length === 0, errors.join(' | '));
  await ctx.close();

  // ── empty is not failure ────────────────────────────────────────────────────────────────
  console.log('\n== an empty answer reads as an answer ==');
  ({ page, errors, ctx } = await newPage(browser, { empty: ['OfficerSearchCandidates'] }));
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.fill('#q', 'nobody');
  await page.click('#search-form button[type=submit]');
  await page.waitForSelector('#candidates .dw-empty');
  const emptyText = await page.locator('#candidates').innerText();
  check('empty search states it is the register answering', /not a failure/.test(emptyText), emptyText);
  check('empty search is not worded as an error', !/did not answer/.test(emptyText));
  await ctx.close();

  console.log('\n== a failure reads as a failure, not as emptiness ==');
  ({ page, errors, ctx } = await newPage(browser, { fail: ['OfficerSearchCandidates'] }));
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.fill('#q', 'avery');
  await page.click('#search-form button[type=submit]');
  await page.waitForSelector('#candidates .dw-empty');
  const failText = await page.locator('#candidates').innerText();
  check('a failed search says the register did not answer', /did not answer/.test(failText), failText);
  check('a failed search does not claim there is nothing', !/No officer records matched/.test(failText));
  await ctx.close();

  console.log('\n== a partial answer is never presented as a total ==');
  ({ page, errors, ctx } = await newPage(browser, { warn: ['OfficerPassport'] }));
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await searchAndSelect(page, 0);
  const warned = await page.locator('#passport-caution').innerText();
  check('engine warning surfaces as a partial answer', /Partial answer/.test(warned), warned);
  check('partial answer explains figures are a floor', /floor rather than a total/.test(warned));
  await ctx.close();

  // ── capability preflight ────────────────────────────────────────────────────────────────
  console.log('\n== missing realm is explained, not silently broken ==');
  const ctx3 = await browser.newContext();
  const page3 = await ctx3.newPage();
  await page3.addInitScript(STUB);
  await page3.addInitScript(`window.embabel.manifest = { ready: Promise.resolve(
      { ok: false, missing: { realms: ['gov-uk'], views: [] } }) };`);
  await page3.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page3.waitForSelector('#unavailable:not(.dw-hidden)');
  check('missing realm named to the user',
    /gov-uk/.test(await page3.locator('#unavailable').innerText()));
  check('search hidden when the realm is absent', await page3.locator('#search-card').isHidden());
  await ctx3.close();

  await browser.close();
  console.log('\n' + '='.repeat(60));
  console.log(`${pass} passed, ${fail} failed`);
  if (fail) { failures.forEach(f => console.log('  - ' + f)); process.exit(1); }
})();
