# JUDGING_READINESS.md — close every gap against the official criteria

> Written for the coding agent. Execute top to bottom. Priority tags:
> **[P0] = must be done before Nov 12 · [P1] = strong value · [P2] = if time.**
> Constraints that NEVER change: testnet-only, no real personal data, mock
> fixtures stay clearly fictional, the 31 tests must stay green after every
> change (`pytest -q`), and the rules engine remains the ONLY decision-maker.

## The official criteria (from BuilderBase, verbatim)

1. **Product design — 33%** — user experience design, interface quality,
   usability, user flow, accessibility, overall product polish.
2. **Technical UX — 34%** — code quality, architecture, functionality,
   deployment status, technical implementation, performance, reliability.
3. **Business/Market Fit — 33%** — African market problem identification,
   solution-market fit, target user understanding, commercial viability,
   go-to-market potential, integration with local infrastructure.

## Step 0 — Audit first (do not skip)

The agent must READ before writing. Report the findings, then fix:

```bash
.venv/bin/python -m pytest -q                 # baseline: expect 31 passed
ls api/ tests/                                # list actual modules
grep -n "route\|@app" api/main.py | head -30  # real endpoint list
wc -l api/main.py                             # size of the API
ls audit/ 2>/dev/null | head                  # audit trail exists?
```

Answer these in the report: What endpoints exist? How is the dashboard
served (static HTML? template?)? What does a screening result look like in
the API response? Is there an /health endpoint? Is there error handling for
bad input?

---

## Criterion 1 — Product design (33%) — WEAKEST, spend the most here

### Task 1.1 [P0] Dashboard polish pass
The dashboard is currently "plain-HTML" — judges score interface quality.
Upgrade IN PLACE (no frameworks, no build tools, no npm for the frontend —
hand-written CSS in a single `<style>` block or one `static/style.css`):

- **Design tokens**: pick 3 colors + neutrals. Verdict semantics:
  ALLOW = green (#15803d), RESTRICT = amber (#b45309), DENY = red (#b91c1c).
  Body text ≥ 4.5:1 contrast ratio against background (WCAG AA).
- **Type scale**: system font stack, one heading size hierarchy, max text
  width ~72ch, generous whitespace. No raw default browser styling.
- **Verdict cards**: each screening result renders as a card showing
  asset id + name, wallet (monospace, truncated with full value in `title`),
  a big verdict badge (icon + text, never color-only), the per-rule
  rationale list (rule id, label, outcome), and — if attested — the
  attestation UID with two links: Basescan tx and easscan page.
- **Landing flow**: page must make sense cold. One sentence at top:
  *"Haki screens wallets against jurisdiction rules and attests every
  verdict onchain."* Then: asset selector, wallet selector, RUN button.
- **States**: loading (disable button + "Screening…"), empty ("no runs yet"),
  error (invalid wallet → readable message, not a stack trace).

### Task 1.2 [P0] Accessibility (explicitly judged)
- Semantic HTML: `h1` once, `h2` sections, `<label for=…>` on every input,
  `<button>` for actions, `<a>` for links. No `<div onclick>`.
- Keyboard: every interactive element reachable + operable by Tab/Enter;
  visible focus outline (`:focus-visible { outline: 2px solid …; }`).
- Alt text on the logo; `lang="en"`; `<meta name="viewport">` for mobile;
  test at 375px width — nothing may overflow horizontally.
- Verdict is never communicated by color alone: badge has text + symbol
  (✓ / ! / ✕).

### Task 1.3 [P1] The regulator view (one new page, big wow factor)
`GET /audit` (HTML): a read-only table of every run — timestamp, asset,
wallet, verdict, rules profile, rule ids hit, attestation link. This IS the
"regulators can audit who held what" pitch made visible. Add export buttons:
"Download JSON" and "Download CSV" (generate client- or server-side, trivial).
This single page demonstrates user-flow thinking for all three user types.

### Task 1.4 [P2] Small polish details
- `<title>Haki — RWA compliance rail</title>`, favicon (link the logo),
  footer: "Demo software · Base Sepolia testnet · fictional data · not legal
  advice".

**Done when**: a stranger can load the dashboard, run a screening in < 30
seconds with zero instruction, read the verdict + rationale, and find the
attestation link. Tab through the whole page with eyes closed except for
reading.

---

## Criterion 2 — Technical UX (34%) — strongest, protect and extend it

### Task 2.1 [P0] One-command demo
`./demo.sh` (chmod +x) at repo root: creates venv if missing, installs
requirements, runs pytest, starts uvicorn, prints "Dashboard: http://
127.0.0.1:8000". README Quick Start becomes one line. Judges (and you,
sleep-deprived on stage) never assemble the demo by hand.

### Task 2.2 [P0] Reliability surface
- `GET /health` → `{"status":"ok","version":"0.1.0"}` (if missing).
- Every endpoint returns proper JSON 4xx for bad input (unknown asset id,
  malformed wallet, wrong rules profile) with a helpful message — never a
  bare 500. Add tests for each error path (pytest count will grow — fine).
- Log each screening run (one line: time, asset, wallet, verdict, ms).

### Task 2.3 [P0] Deployment status — the only real gap in this criterion
"Onchain deployment" is proven (tag m3-onchain-live, verify command). But a
live HTTP URL scores "deployment status" harder. Deploy the read-only demo:

- Recommended: **Render free tier** (or Fly.io) — it runs FastAPI natively.
- Deployed instance runs WITHOUT any chain keys: attestation UI shows the
  recorded drill-1 links (schema UID, tx, easscan) as "verified onchain"
  evidence; live attesting stays local-only. This is honest and secure.
- Add the URL to README top + BuilderBase submission.
- Fallback if hosting flaky: Dockerfile + docker-compose.yml + "deployment
  instructions" in README still counts as deployment readiness.

### Task 2.4 [P1] Code quality pass
- Type hints on all public functions; docstrings on modules.
- requirements.txt: everything pinned (`pip freeze` into it).
- Remove dead code, TODOs, commented-out blocks. `grep -rn "TODO\|XXX"`.
- README: add an endpoint table (method, path, purpose) after the diagram.
- If the agent pipeline module lacks tests: add at least a deterministic-
  mode test (no LLM key → rationale still produced).

### Task 2.5 [P2] Performance
Add `/health` latency + simple `time.perf_counter()` around screening;
print p50 in the README ("single screening: ~Xms"). Trivial but "performance"
is a judged word.

**Done when**: fresh clone → `./demo.sh` → green tests + dashboard up in
under 2 minutes on a clean machine, plus a public URL in the README.

---

## Criterion 3 — Business/Market Fit (33%) — fueled, now make it VISIBLE

Research is done (BUSINESS.md, commit 5db3497). Judges won't excavate a
research file. Surface it:

### Task 3.1 [P0] One-pager: `docs/ONEPAGER.md`
Compress BUSINESS.md to one page, sections exactly:
1. **Problem** — RWA adoption is blocked by compliance; $39.95B already
   tokenized onchain, 5.6M holders (rwa.xyz, Nov 2026); issuers can't verify
   holders at scale, regulators can't audit who held what.
2. **Solution** — deterministic rules engine (YAML jurisdiction packs) →
   verdict + written rationale → EAS attestation on Base. Trustless proof
   for every screening.
3. **Customers** — (a) tokenized-asset issuers (per-holder eligibility),
   (b) platforms listing RWAs (listing/transfer gate), (c) regulators/
   auditors (read-only audit view — link the /audit page).
4. **Pricing** — $0.50–$1.00 per screening at launch, vs Sumsub $1.85/verif
   (incl. AML) and Veriff $0.80–$1.89 + $0.64 AML add-on. Below every
   published comparable.
5. **Africa-first go-to-market** — Kenya: CMA regulatory sandbox (PGN 2019,
   sandbox.cma.or.ke, GFIN member). South Africa: FSCA CASP regime, 75
   licensed CASPs. The YAML pack format means each new jurisdiction = one
   file, one sales conversation.
6. **Why Base** — Base ranks #10 for RWA activity: 1,351 assets / $616.2M
   (rwa.xyz). Haki attests where the assets already settle.
7. **Roadmap** — real KYC/AML data source → live sanctions feed → more
   packs → mainnet after security review.

### Task 3.2 [P0] African-market framing in the README
First paragraph under the title: add two sentences — who in Africa this is
for (KE/ZA issuers and regulators) and that the demo jurisdictions are the
builder's actual regulators (CMA, FSCA). "Integration with local
infrastructure" (a judged phrase) → name it: the YAML packs encode each
regulator's actual rules; audit export works offline as a CSV any
compliance officer can open in Excel.

### Task 3.3 [P1] Target-user empathy in the UI
Dashboard footer or an "About" block, 3 lines: "For issuers: prove every
holder was screened. For platforms: gate listings and transfers. For
regulators: verify any verdict independently onchain."

**Done when**: a judge who reads ONLY the README + one-pager + dashboard
could answer "African problem? target user? viable pricing? GTM? local
integration?" — with sourced numbers.

---

## Execution order (time-boxed for the agent)

1. Step 0 audit → report
2. 1.1 + 1.2 (dashboard + accessibility) — biggest point swing
3. 2.1 + 2.2 (demo script + reliability)
4. 3.1 + 3.2 (one-pager + README framing)
5. 2.3 (deployment — needs human decisions: hosting account)
6. 1.3 (audit/regulator page)
7. 2.4 (code quality) → 1.4 / 3.3 / 2.5 as time allows
8. FINAL: `pytest -q` green · `./demo.sh` works · commit per task, push

## After each task

Commit message convention: `feat(design): …`, `feat(tech): …`,
`docs(business): …` — so the commit log itself reads as organized work
(judges do look).
