"""The verdict matrix is the spec — if this table changes, the demo changes.

30 cells: 6 assets x 5 wallets. Every cell is a contract between the rules
packs, the fixtures and the pitch demo. The rules engine is the only thing
allowed to produce verdicts.
"""
import json
import re
from pathlib import Path

import pytest

from api.rules_engine import (
    load_assets,
    load_rule_packs,
    load_wallets,
    screen,
)
from api.schemas import Asset, AssetType, Rule, RulePack, Verdict

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    "KE-TB-2030":        {"CLEAN": "ALLOW",    "SANCT": "DENY", "MIXER": "RESTRICT", "FRESH": "RESTRICT", "US": "DENY"},
    "NBO-LAND-0042":     {"CLEAN": "ALLOW",    "SANCT": "DENY", "MIXER": "DENY",     "FRESH": "DENY",     "US": "DENY"},
    "CHY-CC-2027":       {"CLEAN": "ALLOW",    "SANCT": "DENY", "MIXER": "RESTRICT", "FRESH": "ALLOW",    "US": "RESTRICT"},
    "KE-AGRI-INV-011":   {"CLEAN": "ALLOW",    "SANCT": "DENY", "MIXER": "RESTRICT", "FRESH": "RESTRICT", "US": "DENY"},
    "ZA-GOLD-003":       {"CLEAN": "ALLOW",    "SANCT": "DENY", "MIXER": "DENY",     "FRESH": "DENY",     "US": "DENY"},
    "KE-INFRA-BND-2041": {"CLEAN": "ALLOW",    "SANCT": "DENY", "MIXER": "RESTRICT", "FRESH": "RESTRICT", "US": "DENY"},
}


@pytest.fixture(scope="module")
def packs():
    return load_rule_packs()


@pytest.fixture(scope="module")
def assets():
    return load_assets()


@pytest.fixture(scope="module")
def wallets():
    return load_wallets()


@pytest.mark.parametrize("asset_id", sorted(EXPECTED))
def test_verdict_matrix(asset_id, packs, assets, wallets):
    for wallet_label, expected in EXPECTED[asset_id].items():
        result = screen(assets[asset_id], wallets[wallet_label], packs=packs)
        assert result.verdict.value == expected, (
            f"{asset_id} x {wallet_label}: expected {expected}, "
            f"got {result.verdict.value}; "
            f"rule_results={[r.model_dump() for r in result.rule_results]}"
        )


def test_fixtures_match_demo_plan(assets, wallets):
    assert len(assets) == 6
    assert set(wallets) == {"CLEAN", "SANCT", "MIXER", "FRESH", "US"}


def test_global_pack_applies_to_every_screening(packs, assets, wallets):
    for asset in assets.values():
        result = screen(asset, wallets["CLEAN"], packs=packs)
        ids = {r.rule_id for r in result.rule_results}
        assert "GLOBAL-SANCTIONS" in ids


def test_sanctioned_wallet_denied_on_every_asset(packs, assets, wallets):
    for asset in assets.values():
        result = screen(asset, wallets["SANCT"], packs=packs)
        assert result.verdict is Verdict.DENY
        assert any("GLOBAL-SANCTIONS" in reason for reason in result.deny_reasons)


def test_wallet_addresses_wellformed(wallets):
    pattern = re.compile(r"^0x[0-9a-fA-F]{40}$")
    for wallet in wallets.values():
        assert pattern.match(wallet.address), f"malformed address for {wallet.label}"


def test_mock_sanctions_list_consistency(wallets):
    entries = json.loads((REPO_ROOT / "data" / "sanctions.json").read_text(encoding="utf-8"))["entries"]
    listed = {entry["address"].lower() for entry in entries}
    assert wallets["SANCT"].address.lower() in listed
    for label in ("CLEAN", "MIXER", "FRESH", "US"):
        assert wallets[label].address.lower() not in listed


def test_unknown_rules_profile_fails_loud(packs, wallets):
    ghost = Asset(
        id="XX-1", name="Ghost", asset_type=AssetType.DEBT_SECURITY,
        issuer="Nobody", rules_profile="XX",
    )
    with pytest.raises(ValueError, match="unknown rules_profile"):
        screen(ghost, wallets["CLEAN"], packs=packs)


def test_unknown_condition_fails_loud(packs, assets, wallets):
    bad_global = RulePack(
        jurisdiction="GLOBAL",
        regulator="test",
        rules=[
            Rule(
                id="BAD-1",
                when={"no_such_condition": True},
                require={"accredited": True},
                on_fail=Verdict.DENY,
            )
        ],
    )
    broken = dict(packs)
    broken["GLOBAL"] = bad_global
    with pytest.raises(ValueError, match="unknown rule condition"):
        screen(assets["KE-TB-2030"], wallets["CLEAN"], packs=broken)


def test_new_jurisdiction_is_one_yaml_pack(packs, wallets):
    """EU-MiCA-lite demo: a synthetic EU-profile debt asset gets RESTRICT
    because the issuer is not EU-authorized (MiCA Title III framing)."""
    eu_asset = Asset(
        id="EU-BND-TEST", name="EU Test Bond", asset_type=AssetType.DEBT_SECURITY,
        issuer="Test Issuer", rules_profile="EU", issuer_eu_authorized=False,
    )
    result = screen(eu_asset, wallets["CLEAN"], packs=packs)
    assert result.verdict is Verdict.RESTRICT
    assert any("EU-MICA-T3" in reason for reason in result.restrict_reasons)


def test_deny_beats_restrict(packs, assets, wallets):
    """MIXER on the land title: unaccredited (DENY) plus mixer exposure
    (RESTRICT) — the DENY contribution wins."""
    result = screen(assets["NBO-LAND-0042"], wallets["MIXER"], packs=packs)
    assert result.verdict is Verdict.DENY
    assert result.deny_reasons
    assert result.restrict_reasons
