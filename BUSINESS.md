# Haki — BUSINESS

> The hackathon's Business criterion is worth 30 pts. This file contains
> **only facts with sources**, plus clearly-marked `[RESEARCH]` slots to fill
> before the pitch (M4, Nov 11). No invented numbers.

## 1. Problem & customers

Tokenized treasuries and RWAs are the fastest-growing institutional crypto
category, but the #1 adoption blocker is compliance: **who is allowed to hold
which asset, in which jurisdiction, with what status.** Issuers cannot verify
holders at scale; regulators cannot audit who held what.

Customers (post-hackathon, in order):

1. **Tokenized-asset issuers** — need per-holder eligibility screening they
   can show to their regulator.
2. **Platforms / exchanges listing RWAs** — need a gate at listing and at
   transfer.
3. **Regulators / auditors** — need a read-only, verifiable audit view
   (onchain attestations + the rule ids that produced each verdict).

## 2. Who pays

- **Issuers/platforms pay per attestation** (every screening that ends in an
  onchain proof) or via a monthly tier.
  - `[RESEARCH]` pull 2–3 public pricing pages for comparable compliance-API
    vendors (e.g. KYC/AML API pricing pages) to anchor a defensible number.
    Do NOT invent one.
- **Regulators/auditors: read-only audit view** — no direct charge in the
  first 90 days; the audit trail being publicly verifiable is the adoption
  wedge.

## 3. Regulators we design around (facts only)

- **Kenya — CMA** (Capital Markets Authority, cma.or.ke): capital-markets
  regulator; the demo's KE pack is framed around CMA-style investor
  protections (accreditation, jurisdiction limits).
  - `[RESEARCH]` link the CMA regulatory-sandbox / digital-assets page and
    any public statement on tokenized securities.
- **South Africa — FSCA** (Financial Sector Conduct Authority, fsca.co.za):
  market-conduct regulator; the ZA pack follows the same framing.
  - `[RESEARCH]` link FSCA's crypto-asset licensing (CASP) guidance.
- **EU — MiCA / ESMA framing** in the research pack (`rules/eu_mica_lite.yaml`),
  deliberately simplified and labeled as such.

## 4. 90-day roadmap (post-hackathon)

Only commitments that follow from what exists today:

1. Replace mock wallet screening with a real KYC/AML data source
   (paid API — today's mock is a local file, by design).
2. Real sanctions feed instead of `data/sanctions.json`.
3. More jurisdiction packs (the YAML format is the product).
4. Mainnet attestations after a security review — today: Base Sepolia only.
5. `[RESEARCH]` engagement path with CMA (sandbox application?) — needs the
   sourced facts from section 3 before we can commit to dates.

## 5. Sources

- Base / EAS contract addresses: https://docs.base.org/specifications/reference/base-contracts
- EAS SDK: https://github.com/ethereum-attestation-service/eas-sdk
- CMA Kenya: https://www.cma.or.ke
- FSCA South Africa: https://www.fsca.co.za
- `[RESEARCH]` add: RWA market-size citation (pick one reputable source,
  e.g. a BCG/Ripple report — cite the exact page), CMA + FSCA pages above.
