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

## Notes

- Contract addresses verified against https://docs.base.org/specifications/reference/base-contracts
- SDK API verified against the official type definitions in the installed
  package (EAS.attest / SchemaRegistry.register / SchemaEncoder.encodeData).
- `lib.mjs` loads the SDK via `createRequire`: the SDK's ESM build has a
  lodash named-export interop bug on Node >= 22; the CommonJS build is stable.
- If faucets are flaky: pre-attest the demo runs early, cache the links, and
  fall back to a plain `AttestationRegistry.sol` (M3 fallback plan).
