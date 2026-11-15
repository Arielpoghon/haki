# HAKI EXPLAINED

This is the plain-language guide for the builder (Ariel) — not the judges'
README. By the end you should be able to explain Haki to anyone, answer any
question about it, and point to the exact file that does the job.

---

## 1. The story in one paragraph

Tokenized real-world assets (treasury bonds, land, invoices put on a
blockchain) are growing fast, but nobody can answer one question: **who is
allowed to hold this asset, in which country, under which rules?** Haki
answers it. You give it an asset and a wallet; a rules engine checks them
against written rules and returns **ALLOW / RESTRICT / DENY**; an AI writes a
plain-language explanation of the decision (English and Swahili); and the
decision is recorded on a public blockchain (Base Sepolia) so anyone can
verify it later. That's the whole product.

**The pitch line:** *"Tokenized assets are growing fast — compliance is why
your grandmother can't hold one. Haki is the compliance layer."*

## 2. The one rule to never forget (this wins arguments)

> **The rules engine decides. The agent explains. The chain proves.**

An LLM (chat AI) is never the judge. Why? Because a compliance decision must
be *auditable*: same input → same output, every time, and you can point to
the exact rule that fired. An LLM is a probability machine — it can invent
reasons. So in Haki:

- **Rules engine** = the referee. Deterministic. Same inputs always give the
  same verdict. This is `api/rules_engine.py`.
- **Agent** = the commentator. It only rewrites *why* in plain language, and
  it is forbidden from adding reasons that aren't in the rule results. This
  is `api/agent.py`.
- **Chain** = the record book. The verdict is stamped publicly where nobody
  can quietly change it. This is `chain/`.

If a judge asks *"what if the AI hallucinates?"* — it can't, because it
doesn't decide. It can write a wrong *sentence*; it cannot produce a wrong
*verdict*. That sentence is the single most important thing to remember.

## 3. What actually happens when you press the button

You open the dashboard (`https://haki-kver.onrender.com`), pick an asset
(say the Kenyan treasury bond `KE-TB-2030`) and a wallet (say `CLEAN`), and
press **Run compliance check**. Here is everything that happens, in order:

1. **Load the asset** — `data/assets.json` describes 6 demo assets: type,
   issuer, which rule pack applies (KE / ZA / EU).
2. **Load the rules** — two YAML packs apply to every screening:
   `rules/global.yaml` (sanctions, accreditation, wallet risk — applies to
   everyone) plus the asset's jurisdiction pack (e.g. `rules/ke.yaml`).
3. **Load the wallet** — `data/wallets.json` describes 5 demo wallets
   (CLEAN, SANCT, MIXER, FRESH, US) with KYC, sanctions and risk fields.
4. **Run the rules** — every rule is checked; each one either *passes*,
   *triggers a RESTRICT*, or *triggers a DENY*. The worst outcome wins:
   any DENY → DENY; else any RESTRICT → RESTRICT; else ALLOW.
5. **Write the explanation** — the AI turns the triggered rules into
   sentences (English + Swahili). With no API key, a template does it —
   that's the demo-safe mode.
6. **Record the proof** — the verdict is hashed and attested on Base
   Sepolia through EAS. Every step is logged to `audit/trail.jsonl`.
7. **Show everything** — the dashboard displays the verdict, each rule's
   outcome, the audit trail, and the proof link.

The whole run takes milliseconds. The demo video shows exactly this flow.

## 4. The verdict matrix — the demo's script

The 30-cell table in `tests/test_rules_engine.py` is the spec: 6 assets × 5
wallets. The cells worth memorizing for demos:

| Asset × Wallet | Verdict | Why (the rule that fired) |
|---|---|---|
| KE-TB-2030 × CLEAN | **ALLOW** | no rule triggered — verified party, complete docs |
| KE-TB-2030 × SANCT | **DENY** | `GLOBAL-SANCTIONS` — wallet on the sanctions list |
| KE-TB-2030 × MIXER | **RESTRICT** | `RISK-EDD` — mixer exposure, enhanced due diligence |
| KE-TB-2030 × FRESH | **RESTRICT** | `RISK-NEW-WALLET` — wallet < 30 days old |
| NBO-LAND-0042 × MIXER | **DENY** | unaccredited (DENY) beats mixer (RESTRICT) — **DENY always beats RESTRICT** |
| CHY-CC-2027 × US | **RESTRICT** | `KE-CARBON-US` — US persons excluded pending Reg S review |

The two "wow" contrasts for any demo: **SANCT → DENY** (sanctions enforced)
and **FRESH → RESTRICT** (it's not a binary yes/no — nuance exists).

## 5. Every file, and what it does

```
api/
  rules_engine.py   THE DECIDER. Loads packs, checks every rule, worst wins.
  agent.py          THE EXPLAINER. Builds the explanation; optional LLM polish.
  tools.py          Agent helpers: load asset/wallet/rules, write audit trail.
  schemas.py        The typed shapes of everything (asset, wallet, verdict...).
  main.py           FastAPI: serves the dashboard + the API endpoints.
  attestation.py    Bridges verdicts to the chain (simulated or real EAS).
static/index.html   The whole dashboard — one file, no framework, no build.
chain/              The Base Sepolia part (wallet, schema, attest, verify).
rules/              The policy layer — 4 YAML files. Adding a country = 1 file.
data/               The demo facts: 6 assets, 5 wallets, mock sanctions list.
tests/              39 tests: the verdict matrix + API surface + error paths.
docs/ONEPAGER.md    The business case, with sourced numbers.
BUSINESS.md         Full business research (pricing anchors, regulators).
audit/trail.jsonl   Every screening ever run, appended line by line.
```

## 6. The onchain part, simply

Haki uses **EAS (Ethereum Attestation Service)** — already deployed on Base,
so no contract was written. The flow:

1. A **schema** was registered once: `string assetId, string wallet, string
   verdict, string timestamp, string rulesProfile, string runId` — think of
   it as the official form layout.
2. Every verdict fills that form and is **attested** — a transaction on Base
   Sepolia that anyone can read forever.
3. The recorded proof from the drill:
   - tx: `https://sepolia.basescan.org/tx/0x4e704a135eaca2d8d3dd17a56e9bd4666afbde30de86faf6f1a144a318270a5f`
   - attestation UID: `0xcc907f0d9320889f7a129150da653cd0df86eaa3591db8b17a48ee7eac3a4421`
4. Anyone can verify without a key: `cd chain && npm run verify` — or open
   the Basescan link.

On the hosted demo the proofs are labeled **SIMULATED** (deterministic
hashes of the same payload) because a free-tier host can't hold a wallet
key. The real attestations above were made from the local build.

## 7. Vocabulary cheat-sheet

| Term | Meaning |
|---|---|
| RWA | Real-World Asset — a bond/land/invoice represented on a blockchain |
| Rules pack | One YAML file of a jurisdiction's rules (KE, ZA, EU) |
| Verdict | ALLOW (ok) / RESTRICT (ok after extra checks) / DENY (no) |
| Worst wins | Any DENY in the rules → final verdict is DENY |
| EAS | Ethereum Attestation Service — the public "stamp" system Haki uses |
| Attestation | A signed public record that a verdict happened, on Base |
| KYC | Know Your Customer — identity verified |
| Sanctions list | List of blocked entities (mock data in the demo) |
| Mixer exposure | Wallet passed funds through a privacy mixer → risk flag |
| Deterministic | Same input always gives the same output — no randomness |
| Audit trail | Line-by-line record of every step a run took |
| Base Sepolia | Ethereum L2 testnet — where the proofs live |

## 8. Questions you WILL be asked — and the answers

**"Why should I trust an AI compliance tool?"**
You shouldn't — that's why it isn't one. The AI never decides. The rules
engine is deterministic and testable; the AI only explains the decision, and
the explanation is grounded in the triggered rule ids.

**"Why Base and not Ethereum/Solana?"**
Base is an Ethereum L2 with ~1s, sub-cent transactions where real RWAs
already settle (rwa.xyz ranked it top-10 by RWA value). EAS is a Base
predeploy — no custom contract needed. (The Solana rebuild, Uhakiki,
proves the architecture is chain-agnostic.)

**"What's to stop someone forging an attestation?"**
Attestations are signed by the attester's key on-chain; the schema, payload
and attester are all public. Anyone can re-verify with `npm run verify` —
no key, no permission.

**"Can you add another country?"**
One YAML file. The EU pack in the repo is the proof — 15 lines.

**"Is this production-ready?"**
No — and it says so in the README. The mock sanctions/KYC data is clearly
labeled. Production needs a real sanctions feed and KYC provider; the
architecture is built so those plug in behind the same rule checks.

**"Who pays for this?"**
Issuers and platforms, per screening — priced below published comparables
(Sumsub $1.85/verification, Veriff $0.80–1.89 + $0.64 AML). Regulators get
the read-only audit view. Details in docs/ONEPAGER.md.

**"You built this with AI — did the AI write your hackathon entry?"**
The AI wrote code under my direction; the architecture, rule packs, demo
design and every product decision were mine. The AI is the same kind of
tool Haki itself is about: it does the work, the human decides. (And the
project placed 1st of 7.)

## 9. Numbers worth knowing cold

- Verdict matrix: **30 cells** (6 assets × 5 wallets) — all green
- Tests: **39** (14 engine + 16 API + 9 program-suite; see README)
- Rules: 4 packs (GLOBAL, KE, ZA, EU) — adding a country = 1 YAML file
- Screening latency: ~16 ms p50 (measured, 200 runs)
- Onchain proof: tx `0x4e704a…270a5f`, block 54788625, verified
- Attestation schema: `0x174675172679983535d90fb64f2be4788ab053d402eefe17abae69c35fd90355`
- Score: **63.4/100 — 1st place**, RWA track, Node Engine 2026

## 10. If you only read one section before a demo

Read §2 (the one rule), §4 (the matrix table), and §8 (the first question).
Everything else is reference.
