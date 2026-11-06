"""Haki agent — the orchestrator, NOT the decision-maker.

Contract (defend this in Q&A):
- The rules engine decides the verdict. Always.
- The agent runs the tool pipeline: load asset -> load rules -> screen wallet
  -> verdict is known -> write rationale -> record every step -> attest.
- With HAKI_LLM_KEY set, an OpenAI-compatible endpoint rewrites the rationale
  in prose. Any failure (no key, network, timeout, bad shape) falls back to
  the deterministic template — the demo survives a dead API on stage.

Every run produces a full audit trail, persisted to audit/trail.jsonl.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone

import httpx

from . import attestation, tools
from .schemas import ComplianceRun, Verdict

LLM_TIMEOUT_S = 12.0


def new_run_id(asset_id: str, wallet_label: str) -> str:
    """Readable, collision-safe run id: run-<date>-<short hash>."""
    seed = f"{asset_id}:{wallet_label}:{datetime.now(timezone.utc).isoformat()}"
    digest = hashlib.sha256(seed.encode()).hexdigest()[:8]
    return f"run-{datetime.now(timezone.utc):%Y%m%d}-{digest}"


# ------------------------------------------------------------- rationale

def template_rationale(screening) -> str:
    """Deterministic rationale — cites rule ids, the same way the engine does."""
    verdict = screening.verdict.value
    lines: list[str] = []

    if verdict == "ALLOW":
        passed = [r.rule_id for r in screening.rule_results if r.matched and r.passed]
        lines.append(
            f"Wallet {screening.wallet_label} ({screening.wallet_address}) may hold "
            f"{screening.asset_id} under the {screening.rules_profile} profile: "
            f"verdict ALLOW."
        )
        lines.append(
            f"All applicable rules passed ({', '.join(passed) if passed else 'none triggered'}); "
            f"no deny or restrict conditions fired."
        )
    else:
        opener = {
            "DENY": f"Wallet {screening.wallet_label} is NOT permitted to hold "
                    f"{screening.asset_id} — verdict DENY.",
            "RESTRICT": f"Wallet {screening.wallet_label} may hold {screening.asset_id} "
                        f"only after enhanced due diligence — verdict RESTRICT.",
        }[verdict]
        lines.append(opener)
        if screening.deny_reasons:
            lines.append("Blocking reasons: " + "; ".join(screening.deny_reasons) + ".")
        if screening.restrict_reasons:
            lines.append("Restrictions: " + "; ".join(screening.restrict_reasons) + ".")

    lines.append(
        "Verdict produced by the deterministic rules engine; "
        "this rationale only explains it."
    )
    return " ".join(lines)


def llm_rationale(screening) -> tuple[str, str]:
    """Optional prose polish via an OpenAI-compatible endpoint.

    Returns (rationale, mode). Never raises — any problem returns the
    deterministic template, because a compliance demo must not die on stage.
    """
    key = os.environ.get("HAKI_LLM_KEY", "").strip()
    if not key:
        return template_rationale(screening), "deterministic"

    base_url = os.environ.get("HAKI_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("HAKI_LLM_MODEL", "gpt-4o-mini")
    system = (
        "You are the rationale writer inside a RegTech compliance agent. "
        "You NEVER decide verdicts; the rules engine already decided. Rewrite "
        "the given deterministic rationale as 3-4 clear sentences for a "
        "compliance officer. Keep every rule id, verdict and fact exactly as "
        "given. Do not add assumptions."
    )
    user = template_rationale(screening)
    try:
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "temperature": 0,
            },
            timeout=LLM_TIMEOUT_S,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("empty LLM rationale")
        return text, "llm"
    except Exception:
        # key set but endpoint failed -> deterministic fallback, demo-safe
        return template_rationale(screening), "deterministic"


# ------------------------------------------------------------- orchestration

def run_compliance(asset_id: str, wallet_label: str) -> ComplianceRun:
    """The full pipeline for one screening. Raises KeyError for unknown ids —
    fail loud, never guess."""
    run_id = new_run_id(asset_id, wallet_label)
    seq = 0
    trail: list = []

    def step(tool: str, detail: str, data: dict | None = None):
        nonlocal seq
        seq += 1
        recorded = tools.record_audit_step(run_id, seq, tool, detail, data)
        trail.append(recorded)

    step("run_started", f"compliance run opened for {asset_id} x {wallet_label}")

    asset = tools.load_asset(asset_id)
    step("load_asset", f"loaded asset {asset.id} ({asset.name})", asset.model_dump())

    packs = tools.load_rules()
    profile = packs[asset.rules_profile]
    step(
        "load_rules",
        f"applied packs: GLOBAL + {profile.jurisdiction} ({len(packs)} packs loaded)",
        {"global_rules": len(packs["GLOBAL"].rules),
         "profile_rules": len(profile.rules),
         "regulator": profile.regulator},
    )

    wallet = tools.load_wallet(wallet_label)
    step("load_wallet", f"loaded wallet {wallet.label} ({wallet.jurisdiction})", wallet.model_dump())

    screening = tools.screen_wallet(asset, wallet)
    step(
        "screen_wallet",
        f"rules engine verdict: {screening.verdict.value}",
        {"verdict": screening.verdict.value,
         "deny_reasons": screening.deny_reasons,
         "restrict_reasons": screening.restrict_reasons},
    )

    rationale, mode = llm_rationale(screening)
    step("write_rationale", f"rationale written ({mode} mode)")

    record = attestation.attest(screening, run_id)
    step(
        "record_attestation",
        f"proof recorded ({record.mode}): {record.uid[:18]}…",
        {"uid": record.uid, "mode": record.mode},
    )

    step(
        "run_closed",
        f"run complete — {asset_id} x {wallet_label} = {screening.verdict.value}",
        # run summary — the /audit regulator view renders one row per run from this
        {
            "asset_id": asset.id,
            "wallet_label": wallet.label,
            "verdict": screening.verdict.value,
            "rules_profile": asset.rules_profile,
            "agent_mode": mode,
            "rule_ids": [r.rule_id for r in screening.rule_results if r.matched],
            "attestation": {
                "uid": record.uid,
                "mode": record.mode,
                "easscan_url": record.easscan_url,
                "explorer_url": record.explorer_url,
            },
        },
    )

    return ComplianceRun(
        run_id=run_id,
        agent_mode=mode,
        asset=asset,
        wallet=wallet,
        screening=screening,
        rationale=rationale,
        audit_trail=trail,
        attestation=record,
    )
