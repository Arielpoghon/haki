# Haki — one-pager

> Compliance infrastructure for tokenized real-world assets. Built for the
> Node Engine Hackathon (Real-World Assets track), Nov 2026. All numbers
> sourced — see [BUSINESS.md](../BUSINESS.md) for full citations.

## 1. Problem

Tokenized real-world assets are already a $39.95B onchain category with
**5.62M holders** (rwa.xyz, Nov 2026) — but the #1 adoption blocker is
compliance: **who is allowed to hold which asset, in which jurisdiction,
with what status.** Issuers can't verify holders at scale. Regulators can't
audit who held what. That gap is why a tokenized T-bill still can't sit in
an ordinary Kenyan investment wallet.

## 2. Solution

Haki is a compliance agent that screens (asset, wallet) pairs and issues a
verifiable proof for every verdict:

1. **Rules engine decides** — YAML jurisdiction packs (GLOBAL + KE / ZA /
   EU-MiCA-lite), deterministic ALLOW / RESTRICT / DENY, worst outcome wins,
   every rule result recorded. An LLM never decides.
2. **Agent explains** — orchestration + a written rationale in plain
   language, with a deterministic no-key fallback.
3. **Chain proves** — an EAS attestation on Base Sepolia records every
   verdict, independently verifiable by anyone (`cd chain && npm run verify`).

## 3. Customers

| Who | What they get |
|---|---|
| **Tokenized-asset issuers** | Per-holder eligibility screening they can show their regulator |
| **Platforms / exchanges listing RWAs** | A compliance gate at listing and at transfer |
| **Regulators / auditors** | Read-only audit view (`/audit`) — every run, the rule ids behind each verdict, onchain proof; exports to CSV any compliance officer can open in Excel |

## 4. Pricing

**$0.50–$1.00 per screening** at launch — anchored below every published
comparable: Sumsub charges **$1.85/verification** with AML screening
($299/mo minimum); Veriff charges **$0.80–$1.89/verification** plus
**$0.64** for AML screening as an add-on (veriff.com/pricing,
sumsub.com/pricing — retrieved Nov 2026).

## 5. Africa-first go-to-market

- **Kenya — CMA**: enter the CMA Regulatory Sandbox (sandbox.cma.or.ke;
  framework: Regulatory Sandbox Policy Guidance Note 2019; CMA is a GFIN
  cross-border testing member).
- **South Africa — FSCA**: the CASP regime under FAIS — FSCA has approved
  **75 crypto asset service providers** to date; each is a potential
  integration partner for transfer-time screening.
- **Expansion is the product**: each new jurisdiction = one YAML rule pack
  = one sales conversation.

## 6. Why Base

Haki attests where the assets already settle: Base ranks **#10 by RWA
value** — **1,351 tokenized assets, $616.2M** (rwa.xyz, Nov 2026). The
demo's attestation registry (EAS) is a Base mainnet predeploy, so the same
architecture runs on mainnet without redeployment.

## 7. Roadmap (90 days)

1. Replace the mock wallet screening with a real KYC/AML data source.
2. Live sanctions feed replacing the fixture list.
3. More jurisdiction packs (the YAML format is the product).
4. Mainnet attestations after a security review.
5. CMA Regulatory Sandbox application, dated after Nov 14 results.
