"""API tests — the endpoint surface and the agent pipeline, deterministic mode.

Same spec as the verdict matrix: the engine decides, the agent explains,
every run leaves a full audit trail, and the attestation is SIMULATED until
chain/.env is configured.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["HAKI_ATTEST_MODE"] = "simulated"  # tests never touch a chain
os.environ.pop("HAKI_LLM_KEY", None)  # tests run in deterministic mode

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_FILE = REPO_ROOT / "audit" / "trail.jsonl"

from api.main import app  # noqa: E402  (after env is pinned)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# ------------------------------------------------------------------ metadata

def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["service"] == "haki"
    assert "version" in body


def test_dashboard_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Haki" in r.text
    assert "<html" in r.text.lower()


def test_assets_endpoint_matches_fixtures(client):
    r = client.get("/api/v1/assets")
    assert r.status_code == 200
    ids = {a["id"] for a in r.json()["assets"]}
    assert ids == {"KE-TB-2030", "NBO-LAND-0042", "CHY-CC-2027",
                   "KE-AGRI-INV-011", "ZA-GOLD-003", "KE-INFRA-BND-2041"}


def test_wallets_endpoint_hides_risk_details(client):
    r = client.get("/api/v1/wallets")
    assert r.status_code == 200
    wallets = r.json()["wallets"]
    assert {w["label"] for w in wallets} == {"CLEAN", "SANCT", "MIXER", "FRESH", "US"}
    assert all("risk_flags" not in w and "sanctioned" not in w for w in wallets)


def test_rules_endpoint_lists_packs(client):
    r = client.get("/api/v1/rules")
    assert r.status_code == 200
    jurisdictions = {p["jurisdiction"] for p in r.json()["packs"]}
    assert {"GLOBAL", "KE", "ZA", "EU"} <= jurisdictions


# ------------------------------------------------------------------ screening

def test_screen_allow_path(client):
    r = client.post("/api/v1/screen",
                    json={"asset_id": "KE-TB-2030", "wallet_label": "CLEAN"})
    assert r.status_code == 200
    body = r.json()
    assert body["screening"]["verdict"] == "ALLOW"
    assert body["agent_mode"] == "deterministic"
    assert "ALLOW" in body["rationale"]
    assert body["attestation"]["mode"] == "simulated"


def test_screen_deny_cites_sanctions_rule(client):
    r = client.post("/api/v1/screen",
                    json={"asset_id": "KE-TB-2030", "wallet_label": "SANCT"})
    body = r.json()
    assert body["screening"]["verdict"] == "DENY"
    assert any("GLOBAL-SANCTIONS" in reason
               for reason in body["screening"]["deny_reasons"])
    assert "DENY" in body["rationale"]


def test_screen_deny_beats_restrict_via_api(client):
    """The invariant holds through the full agent path, not just the engine."""
    r = client.post("/api/v1/screen",
                    json={"asset_id": "NBO-LAND-0042", "wallet_label": "MIXER"})
    body = r.json()
    assert body["screening"]["verdict"] == "DENY"
    assert body["screening"]["deny_reasons"]
    assert body["screening"]["restrict_reasons"]


def test_screen_full_verdict_matrix_via_api(client):
    expected = {
        ("KE-TB-2030", "CLEAN"): "ALLOW", ("KE-TB-2030", "SANCT"): "DENY",
        ("KE-TB-2030", "MIXER"): "RESTRICT", ("KE-TB-2030", "FRESH"): "RESTRICT",
        ("KE-TB-2030", "US"): "DENY",
        ("CHY-CC-2027", "FRESH"): "ALLOW", ("CHY-CC-2027", "US"): "RESTRICT",
        ("ZA-GOLD-003", "CLEAN"): "ALLOW", ("ZA-GOLD-003", "FRESH"): "DENY",
    }
    for (asset_id, wallet), verdict in expected.items():
        r = client.post("/api/v1/screen",
                        json={"asset_id": asset_id, "wallet_label": wallet})
        assert r.status_code == 200, f"{asset_id} x {wallet}"
        assert r.json()["screening"]["verdict"] == verdict, f"{asset_id} x {wallet}"


# ------------------------------------------------------------------ audit + runs

def test_screen_has_complete_audit_trail(client):
    r = client.post("/api/v1/screen",
                    json={"asset_id": "KE-TB-2030", "wallet_label": "SANCT"})
    body = r.json()
    tools_used = [s["tool"] for s in body["audit_trail"]]
    for expected in ("run_started", "load_asset", "load_rules", "load_wallet",
                     "screen_wallet", "write_rationale", "record_attestation",
                     "run_closed"):
        assert expected in tools_used, f"missing audit step {expected}"
    seqs = [s["seq"] for s in body["audit_trail"]]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)


def test_run_retrievable_after_screen(client):
    r = client.post("/api/v1/screen",
                    json={"asset_id": "CHY-CC-2027", "wallet_label": "US"})
    run_id = r.json()["run_id"]
    got = client.get(f"/api/v1/runs/{run_id}")
    assert got.status_code == 200
    assert len(got.json()["steps"]) >= 8


def test_unknown_run_404(client):
    assert client.get("/api/v1/runs/run-does-not-exist").status_code == 404


def test_unknown_asset_404(client):
    r = client.post("/api/v1/screen",
                    json={"asset_id": "NOPE-1", "wallet_label": "CLEAN"})
    assert r.status_code == 404
    assert "unknown asset" in r.json()["detail"]


def test_unknown_wallet_404(client):
    r = client.post("/api/v1/screen",
                    json={"asset_id": "KE-TB-2030", "wallet_label": "GHOST"})
    assert r.status_code == 404


def test_malformed_request_422(client):
    assert client.post("/api/v1/screen", json={"asset_id": "KE-TB-2030"}).status_code == 422


# ------------------------------------------------------------------ attestation

def test_simulated_attestation_is_deterministic(client):
    payload = {"asset_id": "KE-TB-2030", "wallet_label": "CLEAN"}
    uids = []
    for _ in range(2):
        r = client.post("/api/v1/screen", json=payload)
        uids.append(r.json()["attestation"]["uid"])
    assert uids[0] == uids[1]  # same payload -> same simulated proof
    assert uids[0].startswith("0x") and len(uids[0]) == 66


# ------------------------------------------------------------------ reliability (2.2) + audit view (1.3)

def test_health_alias_at_root(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["service"] == "haki"


def test_audit_page_renders_runs(client):
    # generate a run, then the regulator view must show it
    client.post("/api/v1/screen", json={"asset_id": "KE-TB-2030", "wallet_label": "SANCT"})
    r = client.get("/audit")
    assert r.status_code == 200
    assert "Audit view" in r.text
    assert "KE-TB-2030" in r.text and "SANCT" in r.text and "DENY" in r.text


def test_audit_export_json(client):
    client.post("/api/v1/screen", json={"asset_id": "KE-TB-2030", "wallet_label": "CLEAN"})
    r = client.get("/audit/export.json")
    assert r.status_code == 200
    rows = r.json()["runs"]
    assert rows and all({"timestamp", "asset_id", "verdict", "attestation_uid"} <= set(r) for r in rows)


def test_audit_export_csv(client):
    client.post("/api/v1/screen", json={"asset_id": "KE-TB-2030", "wallet_label": "SANCT"})
    r = client.get("/audit/export.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    header = r.text.splitlines()[0]
    assert header.startswith("timestamp,run_id,asset_id,wallet_label,verdict")
    assert "DENY" in r.text


def test_audit_page_empty_is_friendly(client, tmp_path, monkeypatch):
    """No trail file at all -> readable page, not a 500."""
    from api import tools
    monkeypatch.setattr(tools, "AUDIT_FILE", tmp_path / "nope.jsonl")
    r = client.get("/audit")
    assert r.status_code == 200
    assert "No runs recorded yet" in r.text


def test_logo_served(client):
    r = client.get("/static/haki-logo.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_audit_skips_legacy_records_without_summary(client, tmp_path, monkeypatch):
    """Pre-summary trail records must never render as blank rows."""
    import json as _json

    from api import tools

    legacy = {"run_id": "run-legacy-1", "seq": 1, "tool": "load_asset",
              "at": "2026-11-04T00:00:00Z", "detail": "old step without summary", "data": {}}
    fake = tmp_path / "trail.jsonl"
    fake.write_text(_json.dumps(legacy) + "\n", encoding="utf-8")
    monkeypatch.setattr(tools, "AUDIT_FILE", fake)
    r = client.get("/audit")
    assert r.status_code == 200
    assert "No runs recorded yet" in r.text


def test_audit_shows_rules_hit(client):
    client.post("/api/v1/screen", json={"asset_id": "KE-TB-2030", "wallet_label": "SANCT"})
    r = client.get("/audit")
    assert r.status_code == 200
    assert "GLOBAL-SANCTIONS" in r.text  # rule ids now rendered, not "—"
