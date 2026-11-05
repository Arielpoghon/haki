# STATUS — handoff & resume point

> **Read this first when resuming work on Haki.**
> Last updated: 2026-11-05, after commit 7a4cc20 (verify command).

## 1. What Haki is (30 seconds)

Compliance agent for tokenized real-world assets (RWAs). YAML jurisdiction
rule packs → deterministic verdicts (ALLOW / RESTRICT / DENY) → verifiable
EAS attestation on Base Sepolia (testnet). Solo build by Ariel Poghon for
the Node Engine Hackathon (Real-World Assets track), Nov 12–14 2026.
Pitch (M4) is Nov 11.

Design principle: the rules engine decides; the agent explains; the chain
proves. An LLM is never the final authority on a verdict.

## 2. Environments

- Real repo (source of truth): `~/Projects/haki/haki` → github.com/Arielpoghon/haki
- Attester wallet: `0x7aA2be809FB87A50eAb032747b100128DCfd4bF9` (throwaway, TESTNET key only, chain/.env gitignored)
- API server: `uvicorn api.main:app --port 8000` (FastAPI, from repo root)

## 3. Milestones

- M0 (Nov 5) DONE — repo, fixtures, 4 rule packs, rules engine, 30-cell verdict matrix green (pytest -q)
- M1 DONE — wallet screening tool + API surface (api/main.py, FastAPI)
- M2 DONE — agent pipeline + audit trail + plain-HTML dashboard; deterministic mode, no LLM key
- M3 DONE, verified onchain — live attestation end-to-end; tag `m3-onchain-live`; verify command in 7a4cc20

## 4. Onchain artifacts (verified 2026-11-05 by direct eth_call)

- Schema UID: `0x174675172679983535d90fb64f2be4788ab053d402eefe17abae69c35fd90355` (deterministic; resolver 0x0, revocable)
- Schema: `string assetId, string wallet, string verdict, string timestamp, string rulesProfile, string runId`
- Attestation UID: `0xcc907f0d9320889f7a129150da653cd0df86eaa3591db8b17a48ee7eac3a4421`
- Attest tx: `0x4e704a135eaca2d8d3dd17a56e9bd4666afbde30de86faf6f1a144a318270a5f` (block 54788625, SUCCESS)
  https://sepolia.basescan.org/tx/0x4e704a135eaca2d8d3dd17a56e9bd4666afbde30de86faf6f1a144a318270a5f
- Payload: `KE-TB-2030` × `0xa11ce00000000000000000000000000000000001` → DENY (profile KE, run drill-1)

Judge verification: `cd chain && npm run verify` (read-only, no key), or the
Basescan tx link, or Basescan Read-Contract `getAttestation` on
`0x4200000000000000000000000000000000000021` with the UID.

## 5. Gotchas already paid for — do not re-learn

1. `npm scripts` live in `chain/`, not repo root. `cd chain` first.
2. easscan frontend shows "Page not found!" for attestations it HAS indexed
   (React crash, leaked raw time `1793879593n`). Chain is the source of truth.
3. eas-sdk v2: `tx.wait()` broadcasts + confirms; hash hides at `tx.data.hash`.
   Printed undefined hash is cosmetic; the returned UID is the proof.
4. `SchemaRegistry.getSchema()` THROWS when schema not registered — expected.
5. Live Base Sepolia EAS `attest()` selector is `0xf17325e7` (struct includes
   refUID + value). Stale ABIs disagree — don't panic.
6. uvicorn `[Errno 98] address already in use` = previous instance still
   running; only restart after Python-side changes.
7. `chain/.env` must hold the real SCHEMA_UID (see section 4). A pasted
   placeholder makes ethers throw "invalid BytesLike value".

## 6. Where to resume (priority order)

1. M4 — pitch, Nov 11. Fill every `[RESEARCH]` slot in BUSINESS.md: pricing
   anchors (2–3 comparable compliance-API pricing pages), CMA Kenya
   sandbox/digital-assets page, FSCA CASP guidance, one reputable RWA
   market-size citation. No invented numbers.
2. Track question with judges: one written escalation (project, current
   track, requested track, one-line reason + repo link), screenshot it,
   24–48h; ask an organizer in person on day 1 (Nov 12); check the
   submission form for multi-track prize checkboxes; prepare a dual-framing
   15-second opener. Time-box it — the pitch is the leverage, not the label.
3. Pre-attest demo-day runs early; cache tx/UID links.
4. Root README status checkboxes: mark M1–M3 done if not already.

## 7. Change log

- 2026-11-05: M3 verified onchain; tx hash recovered by block-scan; verify
  command added (7a4cc20); STATUS.md created.
