# Day-1 testnet drill — EAS attestations on Base Sepolia

**Testnet only.** The scripts hard-refuse any chain other than Base Sepolia
(chainId 84532). Never put a mainnet key in `.env`.

## Setup (once)

```bash
cd chain
npm install                 # @ethereum-attestation-service/eas-sdk 2.10.0 + ethers 6.17.0 (pinned)
cp .env.example .env
npm run wallet              # generates a throwaway wallet — put the key in chain/.env as ATTESTER_PK
```

Fund the address with Base Sepolia ETH from a faucet (e.g. the Superchain
faucet linked from https://base-sepolia.easscan.org or Google Cloud's Base
faucet). A little testnet ETH is plenty — each attestation costs gas.

## Register the schema (once, deterministic)

```bash
npm run schema
# prints: SCHEMA_UID=0x...
# -> paste that line into chain/.env
```

Schema: `string assetId, string wallet, string verdict, string timestamp, string rulesProfile, string runId`
Registered on the EAS SchemaRegistry at `0x4200000000000000000000000000000000000020`
(address from the official Base docs; EAS itself is at `0x4200000000000000000000000000000000000021`).

## Attest a screening result

```bash
npm run attest -- '{"assetId":"KE-TB-2030","wallet":"0xa11ce00000000000000000000000000000000001","verdict":"ALLOW","timestamp":"2026-11-05T12:00:00Z","rulesProfile":"KE","runId":"run-001"}'
# prints: tx hash + Basescan link, attestation UID + easscan link
```

## Verify an attestation (read-only, no key)

```bash
cd chain                                # npm scripts live here, NOT the repo root
npm run verify                          # verifies the recorded drill-1 attestation
npm run verify -- 0x<attestation-uid>   # verifies any attestation
```

This matters because easscan's web frontend sometimes shows "Page not found!"
for attestations it has already indexed (its React page crashes and leaks raw
fields — e.g. time rendered as `1793879593n`). The chain is the source of
truth: `verify.mjs` calls `EAS.getAttestation()` directly via `eth_call` and
decodes the full payload. A judge can also verify manually on Basescan:
Contract → `0x4200000000000000000000000000000000000021` → Contract → Read
Contract → `getAttestation` → paste the UID.

## Live drill artifacts (tag `m3-onchain-live`, 2026-11-05)

- Schema UID: `0x174675172679983535d90fb64f2be4788ab053d402eefe17abae69c35fd90355`
  (deterministic — `npm run schema` recomputes the same UID)
- Attestation UID: `0xcc907f0d9320889f7a129150da653cd0df86eaa3591db8b17a48ee7eac3a4421`
- Attest tx: https://sepolia.basescan.org/tx/0x4e704a135eaca2d8d3dd17a56e9bd4666afbde30de86faf6f1a144a318270a5f
  (block 54788625, `attest()` selector `0xf17325e7`, status success)
- Payload: `KE-TB-2030` × `0xa11ce00000000000000000000000000000000001` → **DENY**
  (profile KE, run `drill-1`), attester `0x7aA2be809FB87A50eAb032747b100128DCfd4bF9`

## Notes

- Contract addresses verified against https://docs.base.org/specifications/reference/base-contracts
- SDK API verified against the official type definitions in the installed
  package (`EAS.attest` / `SchemaRegistry.register` / `SchemaEncoder.encodeData`).
- `lib.mjs` loads the SDK via `createRequire`: the SDK's ESM build has a
  lodash named-export interop bug on Node >= 22; the CommonJS build is stable.
- eas-sdk v2 quirk: `tx.wait()` broadcasts AND confirms; the tx hash hides at
  `tx.data.hash` in the SDK wrapper. A printed `undefined` hash is cosmetic.
- If faucets are flaky: pre-attest the demo runs early, cache the links, and
  fall back to a plain `AttestationRegistry.sol` (M3 fallback plan).
