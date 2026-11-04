"""Attestation bridge — records each verdict as proof.

Two modes:

- **simulated** (default, no key needed): the attestation UID is a
  deterministic SHA-256 of the canonical payload, so the same screening always
  yields the same UID and the demo never depends on a faucet or RPC being up.
  The dashboard labels these SIMULATED.
- **onchain**: when ``chain/.env`` exists with ATTESTER_PK + SCHEMA_UID (and
  HAKI_ATTEST_MODE != "simulated"), the payload is handed to
  ``chain/attest.mjs`` — the official EAS SDK on Base Sepolia (TESTNET ONLY).

The payload hashes over exactly the six fields in the registered EAS schema:
assetId, wallet, verdict, timestamp, rulesProfile, runId.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from .schemas import Attestation, ScreeningResult

REPO_ROOT = Path(__file__).resolve().parents[1]
CHAIN_DIR = REPO_ROOT / "chain"
EASSCAN_ATTESTATION = "https://base-sepolia.easscan.org/attestation/"

SIMULATED_NOTE = (
    "SIMULATED proof — deterministic hash of the attestation payload. "
    "Configure chain/.env (faucet-funded testnet key) to write it to Base Sepolia."
)


def _payload(screening: ScreeningResult, run_id: str) -> dict[str, str]:
    return {
        "assetId": screening.asset_id,
        "wallet": screening.wallet_address,
        "verdict": screening.verdict.value,
        "timestamp": screening.evaluated_at,
        "rulesProfile": screening.rules_profile,
        "runId": run_id,
    }


def _canonical(payload: dict[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _chain_env_ready() -> bool:
    if os.environ.get("HAKI_ATTEST_MODE", "").lower() == "simulated":
        return False
    env_file = CHAIN_DIR / ".env"
    if not env_file.exists():
        return False
    text = env_file.read_text(encoding="utf-8")
    return "ATTESTER_PK=" in text and "SCHEMA_UID=" in text


def _simulated(screening: ScreeningResult, run_id: str) -> Attestation:
    # Deterministic content hash: same (asset, wallet, verdict, profile) always
    # yields the same UID, so repeated demo runs are stable. The onchain UID
    # differs per tx by design; this one is the verdict's content identity.
    stable = _canonical({
        "assetId": screening.asset_id,
        "wallet": screening.wallet_address,
        "verdict": screening.verdict.value,
        "rulesProfile": screening.rules_profile,
    })
    uid = "0x" + hashlib.sha256(stable.encode("utf-8")).hexdigest()
    return Attestation(
        mode="simulated",
        run_id=run_id,
        asset_id=screening.asset_id,
        wallet_label=screening.wallet_label,
        wallet_address=screening.wallet_address,
        verdict=screening.verdict,
        uid=uid,
        easscan_url=EASSCAN_ATTESTATION + uid,
        note=SIMULATED_NOTE,
    )


def _onchain(screening: ScreeningResult, run_id: str) -> Attestation:
    payload = _payload(screening, run_id)
    proc = subprocess.run(
        ["node", "attest.mjs", _canonical(payload)],
        cwd=CHAIN_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        # Demo-safe: fall back to the simulated proof, but say so loudly.
        fallback = _simulated(screening, run_id)
        fallback.note = (
            f"onchain attestation FAILED — fell back to simulated. "
            f"node stderr: {proc.stderr.strip()[-400:]}"
        )
        return fallback

    tx_hash, uid = "", ""
    for line in proc.stdout.splitlines():
        if line.startswith("tx hash  :"):
            tx_hash = line.split(":", 1)[1].strip()
        elif line.startswith("UID      :"):
            uid = line.split(":", 1)[1].strip()
    return Attestation(
        mode="onchain",
        run_id=run_id,
        asset_id=screening.asset_id,
        wallet_label=screening.wallet_label,
        wallet_address=screening.wallet_address,
        verdict=screening.verdict,
        uid=uid or "0x" + hashlib.sha256(_canonical(payload).encode()).hexdigest(),
        explorer_url=("https://sepolia.basescan.org/tx/" + tx_hash) if tx_hash else "",
        easscan_url=EASSCAN_ATTESTATION + uid if uid else "",
        note="Recorded on Base Sepolia via EAS (testnet).",
    )


def attest(screening: ScreeningResult, run_id: str) -> Attestation:
    if _chain_env_ready():
        return _onchain(screening, run_id)
    return _simulated(screening, run_id)
