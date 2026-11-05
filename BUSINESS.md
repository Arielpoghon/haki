# Haki — BUSINESS

> The hackathon's Business criterion is worth 30 pts. This file contains
> **only facts with sources** — all `[RESEARCH]` slots filled 2026-11-05
> with stable public sources. No invented numbers.

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
  - Pricing anchors (public pages, retrieved 2026-11-05):
    - **Sumsub** (sumsub.com/pricing): Compliance plan **$1.85/verification** with AML
      screening + ongoing monitoring, $299/mo minimum; Basic **$1.35/verification**,
      $149/mo minimum.
    - **Veriff** (veriff.com/pricing): identity plans $0.80–$1.89/verification
      ($49–$209/mo minimums); **AML screening (PEP & sanctions)
      +$0.64/verification** as an add-on, ongoing monitoring +$0.09.
  - Implication: a compliance verdict (rules + sanctions screening + onchain
    attestation) priced at **$0.50–$1.00 per screening** at launch sits below
    every published comparable — anchored, not invented.
- **Regulators/auditors: read-only audit view** — no direct charge in the
  first 90 days; the audit trail being publicly verifiable is the adoption
  wedge.

## 3. Regulators we design around (facts only)

- **Kenya — CMA** (Capital Markets Authority, cma.or.ke): capital-markets
  regulator; the demo's KE pack is framed around CMA-style investor
  protections (accreditation, jurisdiction limits).
  - Regulatory Sandbox live page: https://www.cma.or.ke/regulatory-sandbox/
    — governed by the **Regulatory Sandbox Policy Guidance Note (PGN), 2019**
    (eligibility, application, safeguard, testing requirements); dedicated
    sandbox portal: https://sandbox.cma.or.ke/
  - CMA participates in the **Global Financial Innovation Network (GFIN)**
    cross-border testing platform (linked from cma.or.ke online services):
    https://www.thegfin.com/crossborder-testing
- **South Africa — FSCA** (Financial Sector Conduct Authority, fsca.co.za):
  market-conduct regulator; the ZA pack follows the same framing.
  - CASP licensing: crypto asset service providers are licensed under the
    **FAIS Act (Act 37 of 2002)**; FSCA's own newsroom confirms it has
    approved **75 CASPs to date** ("FSCA confirms list of currently approved
    crypto asset service providers", fsca.co.za/Latest-News/) with the
    approved list published on the FSCA website.
  - Licensing entry point (FAIS): https://www.fsca.co.za/Regulated-Entities?collapse=collapseLicensing&subCollapse=subCollapseTwoLicensing
  - FSCA innovation channel: **Intergovernmental Fintech Working Group
    (IFWG)** — Regulatory Guidance Unit + Regulatory Sandbox:
    https://www.ifwg.co.za/ (linked from fsca.co.za innovations page:
    https://www.fsca.co.za/Innovator-Or-Product-Developer)
  - FSCA research holdings incl. Crypto Market Study and DeFi Market Study
    (publications & resources: https://www.fsca.co.za/Publications-and-Resources/)
- **EU — MiCA / ESMA framing** in the research pack (`rules/eu_mica_lite.yaml`),
  deliberately simplified and labeled as such.

## 4. 90-day roadmap (post-hackathon)

Only commitments that follow from what exists today:

1. Replace mock wallet screening with a real KYC/AML data source
   (paid API — today's mock is a local file, by design).
2. Real sanctions feed instead of `data/sanctions.json`.
3. More jurisdiction packs (the YAML format is the product).
4. Mainnet attestations after a security review — today: Base Sepolia only.
5. Engagement path with CMA: apply to the CMA Regulatory Sandbox (portal:
    https://sandbox.cma.or.ke/; framework: Regulatory Sandbox PGN 2019, which
    sets out eligibility and testing requirements). Date the application after
    the Nov 14 hackathon results — no invented dates.

## 5. Sources

- Base / EAS contract addresses: https://docs.base.org/specifications/reference/base-contracts
- EAS SDK: https://github.com/ethereum-attestation-service/eas-sdk
- CMA Kenya: https://www.cma.or.ke
- FSCA South Africa: https://www.fsca.co.za
- **RWA market size — rwa.xyz (retrieved 2026-11-05):** tokenized RWA
  distributed asset value **$39.95B** (+1.22% over 30d), represented asset
  value $366.32B, 5.62M RWA holders, $283.22B total stablecoin value.
  Chain-relevant: **Base ranks #10 by RWA value — 1,351 tokenized assets,
  $616.2M** — i.e. real RWA activity already settles on the exact chain the
  demo attests to. Source: https://www.rwa.xyz (homepage dashboard,
  figures as of 05 Nov 2026).
- Pricing anchors: https://www.sumsub.com/pricing/ · https://veriff.com/pricing
- CMA Regulatory Sandbox: https://www.cma.or.ke/regulatory-sandbox/ ·
  sandbox portal https://sandbox.cma.or.ke/ · Sandbox PGN 2019 (framework)
- CMA GFIN cross-border testing: https://www.thegfin.com/crossborder-testing
- FSCA CASP licensing (FAIS): https://www.fsca.co.za/Regulated-Entities?collapse=collapseLicensing&subCollapse=subCollapseTwoLicensing ·
  75 approved CASPs (FSCA newsroom): https://www.fsca.co.za/Latest-News/
- FSCA innovation/sandbox channel: https://www.ifwg.co.za/ ·
  https://www.fsca.co.za/Innovator-Or-Product-Developer
- Not yet cited: a forward-looking BCG/Ripple tokenization forecast — the
  exact report page was not retrievable at write time; pull the landing page
  (and numbers) before quoting any projection. Current-size facts above are
  already sufficient for the pitch.
