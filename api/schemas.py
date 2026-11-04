"""Pydantic models — the typed core of Haki.

Everything the rules engine consumes or emits is modeled here, so malformed
data fails loudly at load time instead of silently misfiring at verdict time.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class AssetType(str, Enum):
    DEBT_SECURITY = "debt_security"
    LAND_TITLE = "land_title"
    CARBON_CREDIT = "carbon_credit"
    AGRI_INVOICE = "agri_invoice"
    COMMODITY_RECEIPT = "commodity_receipt"
    INFRA_BOND = "infra_bond"


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    RESTRICT = "RESTRICT"
    DENY = "DENY"


_SEVERITY = {Verdict.ALLOW: 0, Verdict.RESTRICT: 1, Verdict.DENY: 2}


def severity(verdict: Verdict) -> int:
    """DENY (2) > RESTRICT (1) > ALLOW (0)."""
    return _SEVERITY[verdict]


class Asset(BaseModel):
    id: str
    name: str
    asset_type: AssetType
    issuer: str
    rules_profile: str  # jurisdiction pack to apply: KE, ZA, EU, ...
    accreditation_required: bool = False
    us_persons_excluded: bool = False
    issuer_eu_authorized: bool = False
    summary: str = ""


class Wallet(BaseModel):
    label: str
    address: str
    jurisdiction: str
    accredited: bool = False
    sanctioned: bool = False
    risk_flags: list[str] = Field(default_factory=list)
    wallet_age_days: int = 0
    us_person: bool = False


class Rule(BaseModel):
    """One compliance rule. Exactly one of two shapes must be used:

    - gate rule: ``when`` + ``require`` + ``on_fail``
      If ``when`` matches and ``require`` fails, the rule contributes
      ``on_fail`` (DENY or RESTRICT) to the verdict.

    - flag rule: ``when`` + ``action``
      If ``when`` matches, the rule contributes ``action`` (usually RESTRICT).

    An empty ``when`` means "always matches".
    """

    id: str
    when: dict[str, Any] = Field(default_factory=dict)
    require: dict[str, Any] = Field(default_factory=dict)
    on_fail: Optional[Verdict] = None
    action: Optional[Verdict] = None
    note: str = ""

    @model_validator(mode="after")
    def _check_shape(self) -> "Rule":
        if (self.on_fail is None) == (self.action is None):
            raise ValueError(
                f"rule {self.id!r}: set exactly one of on_fail (gate rule) "
                f"or action (flag rule)"
            )
        if self.on_fail is not None and not self.require:
            raise ValueError(
                f"rule {self.id!r}: gate rule needs at least one require condition"
            )
        if self.action is not None and self.require:
            raise ValueError(
                f"rule {self.id!r}: flag rule cannot have require conditions"
            )
        return self


class RulePack(BaseModel):
    jurisdiction: str
    regulator: str
    rules: list[Rule]


class RuleResult(BaseModel):
    rule_id: str
    pack: str
    matched: bool  # did `when` fire?
    passed: Optional[bool] = None  # gate rules: outcome of `require`
    outcome: Optional[Verdict] = None  # verdict contribution; None = no effect
    detail: str = ""
    note: str = ""


class ScreeningResult(BaseModel):
    """Full, auditable output of one (asset, wallet) screening."""

    asset_id: str
    wallet_label: str
    wallet_address: str
    rules_profile: str
    verdict: Verdict
    rule_results: list[RuleResult]
    deny_reasons: list[str] = Field(default_factory=list)
    restrict_reasons: list[str] = Field(default_factory=list)
    evaluated_at: str  # ISO-8601 UTC
