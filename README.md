# Haki — a compliance agent for tokenized real-world assets

Haki (Swahili for *justice*) screens tokenized real-world assets (RWAs) and
the wallets that want to hold them against a jurisdiction rules pack, and
issues a **verifiable onchain attestation** (Ethereum Attestation Service on
Base Sepolia) for every verdict: **ALLOW / RESTRICT / DENY**, with a written
rationale and a full audit trail.

**Who this is for in Africa:** tokenized-asset issuers in Kenya and South
Africa who must prove every holder was screened, and the regulators who audit
them — the demo's jurisdiction packs are framed around the builder's actual
regulators (Kenya's **CMA**, South Africa's **FSCA**). Local integration is
the design: each regulator's rules live in one YAML pack, and the audit view
exports to CSV any compliance officer can open offline in Excel.

Built for the Node Engine Hackathon (Real-World Assets track), Nov 12–14 2026,
by Ariel Poghon (solo). The business case, with sourced numbers, is in
[docs/ONEPAGER.md](docs/ONEPAGER.md).

> ⚠️ **Demo software.** Testnet only. Mock data, fictional issuers, simplified
> rule profiles. Not legal advice, not production-ready.

## Prior-art disclosure

The hackathon forbids pre-existing work, so in the interest of full
transparency: the builder previously worked on a separate compliance-agent
project ("BLI RegTech"). **Haki is a new project** — this repository was
created fresh for this hackathon (first commit Nov 5, 2026) and shares **zero
code** with that earlier work: different stack, different architecture,
different scope. Disclosed up front so judges hear it from the builder first.

## How it works

```
asset (data/assets.json) + wallet (data/wallets.json)
        │
        ▼
┌─────────────────────────────────────────────┐
│ RULES ENGINE — api/rules_engine.py          │
│ YAML rule packs (rules/*.yaml) + facts      │
│ => ALLOW / RESTRICT / DENY                  │
│ THE source of truth for every verdict       │
└──────────────────┬──────────────────────────┘
                   │ structured result (per-rule outcomes)
┌──────────────────▼──────────────────────────┐
│ AGENT (M2) — orchestrates tools, writes     │
│ the human-readable rationale. NEVER decides.│
│ Deterministic mode with no LLM key.         │
└──────────────────┬──────────────────────────┘
                   │ attests (assetId, wallet, verdict, ...)
┌──────────────────▼──────────────────────────┐
│ EAS on Base Sepolia — chain/                │
│ onchain proof, verifiable on easscan        │
└─────────────────────────────────────────────┘
```

**Design principle:** the rules engine decides; the agent explains; the chain
proves. An LLM is never the final authority on a compliance verdict — and the
demo still runs end-to-end with no LLM key at all (deterministic mode).

## Status

- [x] **M0 (Nov 5):** fresh repo, fixtures, rules packs (GLOBAL / KE / ZA /
      EU-MiCA-lite), deterministic rules engine, full 6×5 verdict matrix green
- [x] EAS attestation scripts for Base Sepolia, API verified against the
      official SDK types (day-1 drill ready — see `chain/README.md`)
- [x] **M2 (Nov 4):** agent pipeline (deterministic mode + optional LLM
      rationale), audit trail persisted to `audit/trail.jsonl`, FastAPI API,
      plain-HTML dashboard — **31 tests green**
- [x] **M3 (Nov 5):** live attestation end-to-end, **verified onchain** —
      schema registered, attestation recorded on Base Sepolia and decoded by
      `verify.mjs` (tag `m3-onchain-live`). Judge-proof: `cd chain && npm run verify`,
      or https://sepolia.basescan.org/tx/0x4e704a135eaca2d8d3dd17a56e9bd4666afbde30de86faf6f1a144a318270a5f
      Full handoff: see `STATUS.md`.

## Quick start

```bash
./demo.sh          # venv + deps + tests + dashboard on http://127.0.0.1:8000
```

That single command does everything. By hand, it is:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q     # the verdict matrix is the spec
.venv/bin/uvicorn api.main:app --port 8000
# dashboard: http://localhost:8000 · audit view: http://localhost:8000/audit
# API docs:  http://localhost:8000/docs
```

Docker: `docker compose up` (keyless container; audit trail persisted on a
volume).

**Deployed demo:** a keyless instance runs on Render — the dashboard and
audit view are live, with attestation proofs labeled SIMULATED; the onchain
evidence stays the recorded drill txs (see `chain/README.md`). Deploy your
own in one click: Render → New → Blueprint → this repo (`render.yaml` is
committed; the instance never holds chain keys). Note: free tier sleeps
after ~15 min idle (~30 s cold start). Onchain attestation drill (optional,
testnet only): see `chain/README.md`.

## The verdict matrix (doubles as the test table)

`tests/test_rules_engine.py` encodes this table; all 30 cells are green.

| asset \ wallet | CLEAN | SANCT | MIXER | FRESH | US |
|---|---|---|---|---|---|
| KE-TB-2030 (KE treasury bond) | ALLOW | DENY | RESTRICT | RESTRICT | DENY |
| NBO-LAND-0042 (fractional land) | ALLOW | DENY | DENY | DENY | DENY |
| CHY-CC-2027 (carbon credit) | ALLOW | DENY | RESTRICT | ALLOW | RESTRICT |
| KE-AGRI-INV-011 (agri invoice) | ALLOW | DENY | RESTRICT | RESTRICT | DENY |
| ZA-GOLD-003 (gold receipt) | ALLOW | DENY | DENY | DENY | DENY |
| KE-INFRA-BND-2041 (infra bond) | ALLOW | DENY | RESTRICT | RESTRICT | DENY |

Wallets: CLEAN (2-yr KE retail, accredited) · SANCT (sanctions match) ·
MIXER (mixer exposure) · FRESH (1-day-old, no history) · US (US-person tag).

## Adding a jurisdiction = adding one YAML file

Write `rules/<profile>.yaml`, set `rules_profile: <profile>` on the asset.
See `rules/eu_mica_lite.yaml` and
`tests/test_rules_engine.py::test_new_jurisdiction_is_one_yaml_pack`.
Unknown conditions or profiles **fail loud** — the engine never guesses.

## Repository layout

```
api/
  schemas.py         # pydantic models (assets, wallets, rules, runs, proofs)
  rules_engine.py    # deterministic verdict engine (source of truth)
  tools.py           # agent tools: load_* + audit trail (audit/trail.jsonl)
  agent.py           # orchestrator: tool pipeline + rationale (LLM optional)
  attestation.py     # proof bridge: simulated by default, EAS when configured
  main.py            # FastAPI — the only backend, serves static/
static/
  index.html         # plain HTML dashboard — no framework, no build step
rules/
  global.yaml        # sanctions, accreditation, wallet-risk baseline
  ke.yaml  za.yaml  eu_mica_lite.yaml
data/
  assets.json  wallets.json  sanctions.json   # demo fixtures (fictional)
chain/
  lib.mjs  wallet.mjs  schema.mjs  attest.mjs # EAS on Base Sepolia (testnet)
  package.json  .env.example  README.md
tests/
  test_rules_engine.py    # the verdict matrix is the spec
  test_api.py             # API surface, agent pipeline, audit trail
conftest.py  requirements.txt  .env.example  .gitignore
README.md  BUSINESS.md
audit/               # run log (gitignored) — every screening persists here
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | plain-HTML dashboard (no build step) |
| GET | `/health`, `/api/v1/health` | liveness + version |
| GET | `/api/v1/assets` | demo asset registry |
| GET | `/api/v1/wallets` | demo wallets (no risk internals) |
| GET | `/api/v1/rules` | all rule packs |
| POST | `/api/v1/screen` | `{asset_id, wallet_label}` → verdict + rationale + audit trail + proof |
| GET | `/api/v1/runs/{run_id}` | persisted audit steps for one run |
| GET | `/audit` | read-only regulator view (all runs, rule ids, proofs) |
| GET | `/audit/export.json`, `/audit/export.csv` | audit-trail exports |

Performance: single screening (full rules evaluation, YAML packs loaded) runs
in **~16 ms p50 / ~19 ms p99** (measured locally, 200 runs; the attestation
call is the only network step).

## License

MIT — see LICENSE.
