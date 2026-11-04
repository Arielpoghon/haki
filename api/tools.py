"""Agent tools — the small, file-backed operations the orchestrator calls.

Each function is a "tool" in the agent's vocabulary (load_asset, load_rules,
screen_wallet, record_audit_step). They are plain, deterministic functions so
the whole pipeline stays testable. The LLM, when enabled, only picks the
wording of the rationale — never a verdict, never a data read.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from .rules_engine import (
    DATA_DIR,
    REPO_ROOT,
    load_assets,
    load_rule_packs,
    load_wallets,
    screen,
)
from .schemas import (
    Asset,
    AuditStep,
    RulePack,
    ScreeningResult,
    Wallet,
)

AUDIT_DIR = REPO_ROOT / "audit"
AUDIT_FILE = AUDIT_DIR / "trail.jsonl"

_lock = threading.Lock()  # trail.jsonl is append-only; one writer at a time


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------- read tools

def load_asset(asset_id: str) -> Asset:
    assets = load_assets()
    if asset_id not in assets:
        raise KeyError(f"unknown asset {asset_id!r}")
    return assets[asset_id]


def load_wallet(wallet_label: str) -> Wallet:
    wallets = load_wallets()
    if wallet_label not in wallets:
        raise KeyError(f"unknown wallet {wallet_label!r}")
    return wallets[wallet_label]


def load_rules() -> dict[str, RulePack]:
    return load_rule_packs()


def screen_wallet(asset: Asset, wallet: Wallet) -> ScreeningResult:
    return screen(asset, wallet)


# --------------------------------------------------------------- audit trail

def record_audit_step(run_id: str, seq: int, tool: str, detail: str, data: dict | None = None) -> AuditStep:
    """Append one step to the run's audit trail and persist it to trail.jsonl."""
    step = AuditStep(seq=seq, tool=tool, at=utc_now(), detail=detail, data=data or {})
    record = {"run_id": run_id, **step.model_dump()}
    with _lock:
        AUDIT_DIR.mkdir(exist_ok=True)
        with AUDIT_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    return step


def read_run(run_id: str) -> dict | None:
    """Return the persisted steps for one run, or None if unknown."""
    if not AUDIT_FILE.exists():
        return None
    steps: list[dict] = []
    with AUDIT_FILE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue  # a torn trailing line must never take the API down
            if record.get("run_id") == run_id:
                steps.append(record)
    if not steps:
        return None
    return {"run_id": run_id, "steps": steps}
