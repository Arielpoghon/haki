"""Haki rules engine — the deterministic source of truth for verdicts.

Design contract (defend this in Q&A):
- Verdicts come ONLY from here: YAML rule packs + the fixture facts in data/.
- The LLM agent never decides; it orchestrates tools and explains results.
- Anything unknown fails LOUD (ValueError) — a compliance engine must never
  silently guess.

Severity: ALLOW < RESTRICT < DENY. Every applicable rule is evaluated; the
final verdict is the most severe contribution. Full per-rule results are
always returned so the agent and the audit trail can show the reasoning.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .schemas import (
    Asset,
    Rule,
    RulePack,
    RuleResult,
    ScreeningResult,
    Verdict,
    Wallet,
    severity,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = REPO_ROOT / "rules"
DATA_DIR = REPO_ROOT / "data"
GLOBAL_PACK = "GLOBAL"


# ------------------------------------------------------------------ loading

def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_assets(data_dir: Path = DATA_DIR) -> dict[str, Asset]:
    assets = [Asset(**row) for row in _read_json(data_dir / "assets.json")["assets"]]
    if len({a.id for a in assets}) != len(assets):
        raise ValueError("duplicate asset ids in data/assets.json")
    return {a.id: a for a in assets}


def load_wallets(data_dir: Path = DATA_DIR) -> dict[str, Wallet]:
    wallets = [Wallet(**row) for row in _read_json(data_dir / "wallets.json")["wallets"]]
    if len({w.label for w in wallets}) != len(wallets):
        raise ValueError("duplicate wallet labels in data/wallets.json")
    return {w.label: w for w in wallets}


def load_rule_packs(rules_dir: Path = RULES_DIR) -> dict[str, RulePack]:
    """Load every rules/*.yaml. The GLOBAL pack is mandatory."""
    packs: dict[str, RulePack] = {}
    for path in sorted(rules_dir.glob("*.yaml")):
        pack = RulePack(**yaml.safe_load(path.read_text(encoding="utf-8")))
        if pack.jurisdiction in packs:
            raise ValueError(f"duplicate rule pack jurisdiction {pack.jurisdiction!r}")
        packs[pack.jurisdiction] = pack
    if GLOBAL_PACK not in packs:
        raise ValueError("missing GLOBAL rule pack (rules/global.yaml)")
    return packs


# --------------------------------------------------------- rule evaluation

def _check(condition: str, expected: Any, asset: Asset, wallet: Wallet) -> bool:
    """Evaluate a single condition. Explicit dispatch — unknown keys raise."""
    if condition == "always":
        return bool(expected)
    if condition == "asset_type":
        return asset.asset_type.value in expected
    if condition == "accreditation_required":
        return asset.accreditation_required == expected
    if condition == "us_persons_excluded":
        return asset.us_persons_excluded == expected
    if condition == "issuer_eu_authorized":
        return asset.issuer_eu_authorized == expected
    if condition == "us_person":
        return wallet.us_person == expected
    if condition == "sanctioned":
        return wallet.sanctioned == expected
    if condition == "risk_flags_present":
        return any(flag in expected for flag in wallet.risk_flags)
    if condition == "wallet_age_days_lt":
        return wallet.wallet_age_days < expected
    if condition == "holder_jurisdictions":
        return wallet.jurisdiction in expected
    if condition == "not_sanctioned":
        return (not wallet.sanctioned) == expected
    if condition == "accredited":
        return wallet.accredited == expected
    raise ValueError(f"unknown rule condition {condition!r} — refusing to guess")


def _evaluate_conditions(
    conditions: dict[str, Any], asset: Asset, wallet: Wallet
) -> tuple[bool, list[str]]:
    """Return (all_matched, failed_keys). Empty conditions match everything."""
    if not conditions:
        return True, []
    outcomes = {key: _check(key, value, asset, wallet) for key, value in conditions.items()}
    return all(outcomes.values()), [key for key, ok in outcomes.items() if not ok]


def _describe(failed: list[str], require: dict[str, Any], wallet: Wallet) -> str:
    """Human-readable detail for failed require conditions."""
    parts: list[str] = []
    for key in failed:
        expected = require[key]
        if key == "holder_jurisdictions":
            parts.append(f"holder jurisdiction {wallet.jurisdiction} not in {expected}")
        elif key == "not_sanctioned":
            parts.append("wallet is on the sanctions list")
        elif key == "accredited":
            parts.append("wallet is not accredited")
        elif key == "issuer_eu_authorized":
            parts.append("issuer is not EU-authorized")
        else:
            parts.append(f"{key} failed (expected {expected})")
    return "; ".join(parts)


def evaluate_rule(rule: Rule, pack: str, asset: Asset, wallet: Wallet) -> RuleResult:
    matched, _ = _evaluate_conditions(rule.when, asset, wallet)
    if not matched:
        return RuleResult(rule_id=rule.id, pack=pack, matched=False)

    if rule.action is not None:  # flag rule — `when` matching IS the outcome
        return RuleResult(
            rule_id=rule.id,
            pack=pack,
            matched=True,
            outcome=rule.action,
            detail="flag condition met",
            note=rule.note,
        )

    passed, failed = _evaluate_conditions(rule.require, asset, wallet)
    if passed:
        return RuleResult(rule_id=rule.id, pack=pack, matched=True, passed=True)
    return RuleResult(
        rule_id=rule.id,
        pack=pack,
        matched=True,
        passed=False,
        outcome=rule.on_fail,
        detail=_describe(failed, rule.require, wallet),
        note=rule.note,
    )


# ---------------------------------------------------------------- screening

def screen(
    asset: Asset,
    wallet: Wallet,
    packs: dict[str, RulePack] | None = None,
) -> ScreeningResult:
    """Screen one (asset, wallet) pair against GLOBAL + the asset's pack."""
    if packs is None:
        packs = load_rule_packs()
    if asset.rules_profile == GLOBAL_PACK:
        raise ValueError("asset rules_profile cannot be GLOBAL")
    if asset.rules_profile not in packs:
        raise ValueError(
            f"asset {asset.id!r}: unknown rules_profile {asset.rules_profile!r} "
            f"(no rules/{asset.rules_profile.lower()}*.yaml pack found)"
        )

    applicable = [packs[GLOBAL_PACK], packs[asset.rules_profile]]
    rule_results = [
        evaluate_rule(rule, pack.jurisdiction, asset, wallet)
        for pack in applicable
        for rule in pack.rules
    ]

    verdict = Verdict.ALLOW
    deny_reasons: list[str] = []
    restrict_reasons: list[str] = []
    for result in rule_results:
        if result.outcome is None:
            continue
        if severity(result.outcome) > severity(verdict):
            verdict = result.outcome
        reason = f"{result.rule_id} [{result.pack}]"
        if result.detail:
            reason += f" — {result.detail}"
        if result.note:
            reason += f" ({result.note})"
        if result.outcome is Verdict.DENY:
            deny_reasons.append(reason)
        else:
            restrict_reasons.append(reason)

    return ScreeningResult(
        asset_id=asset.id,
        wallet_label=wallet.label,
        wallet_address=wallet.address,
        rules_profile=asset.rules_profile,
        verdict=verdict,
        rule_results=rule_results,
        deny_reasons=deny_reasons,
        restrict_reasons=restrict_reasons,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


def screen_by_id(
    asset_id: str,
    wallet_label: str,
    packs: dict[str, RulePack] | None = None,
    assets: dict[str, Asset] | None = None,
    wallets: dict[str, Wallet] | None = None,
) -> ScreeningResult:
    """Convenience path used by tests and (in M2) the API layer."""
    assets = assets if assets is not None else load_assets()
    wallets = wallets if wallets is not None else load_wallets()
    for kind, key, table in (
        ("asset", asset_id, assets),
        ("wallet", wallet_label, wallets),
    ):
        if key not in table:
            raise KeyError(f"unknown {kind} {key!r}")
    return screen(assets[asset_id], wallets[wallet_label], packs=packs)
