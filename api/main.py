"""Haki API — the only backend. FastAPI serves the plain-HTML dashboard and
the /api/v1 endpoints. No build step, no second stack.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from . import agent, tools
from .schemas import ComplianceRun, ScreenRequest

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = REPO_ROOT / "static"

logger = logging.getLogger("haki.api")

app = FastAPI(
    title="Haki",
    description="Compliance agent for tokenized real-world assets — "
                "rules engine decides, agent explains, chain proves.",
    version="0.2.0",
)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "haki", "version": app.version}


@app.get("/api/v1/assets")
def list_assets() -> dict:
    return {"assets": list(tools.load_assets().values())}


@app.get("/api/v1/wallets")
def list_wallets() -> dict:
    # never expose full fixture internals the demo doesn't need
    return {
        "wallets": [
            {"label": w.label, "address": w.address, "jurisdiction": w.jurisdiction}
            for w in tools.load_wallets().values()
        ]
    }


@app.get("/api/v1/rules")
def list_rules() -> dict:
    return {
        "packs": [
            pack.model_dump() for pack in tools.load_rules().values()
        ]
    }


@app.post("/api/v1/screen", response_model=ComplianceRun)
def screen(request: ScreenRequest) -> ComplianceRun:
    started = time.perf_counter()
    try:
        run = agent.run_compliance(request.asset_id, request.wallet_label)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "screening asset=%s wallet=%s verdict=%s mode=%s %.1fms",
        request.asset_id, request.wallet_label,
        run.screening.verdict.value, run.agent_mode, elapsed_ms,
    )
    return run


@app.get("/api/v1/runs/{run_id}")
def get_run(run_id: str) -> dict:
    stored = tools.read_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id!r}")
    return stored


@app.get("/audit", include_in_schema=False)
def audit_view() -> HTMLResponse:
    """Read-only regulator view: every recorded run, one row each."""
    return HTMLResponse(render_audit_page())


@app.get("/audit/export.json", include_in_schema=False)
def audit_export_json() -> JSONResponse:
    return JSONResponse(content={"runs": _audit_rows()})


@app.get("/audit/export.csv", include_in_schema=False)
def audit_export_csv() -> FileResponse:
    csv_path = STATIC_DIR / ".audit-export.csv"  # transient; regenerated per request
    rows = _audit_rows()
    lines = ["timestamp,run_id,asset_id,wallet_label,verdict,rules_profile,mode,attestation_uid,attestation_mode"]
    for r in rows:
        lines.append(",".join(
            '"' + str(r[k]).replace('"', '""') + '"'
            for k in ("timestamp", "run_id", "asset_id", "wallet_label",
                      "verdict", "rules_profile", "mode",
                      "attestation_uid", "attestation_mode")
        ))
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename="haki-audit-trail.csv",
    )


def _audit_rows() -> list[dict]:
    """One row per completed run, newest last. Only runs with a structured
    run summary (the run_closed step) are rendered — legacy or torn records
    without one are skipped, never shown as blank rows."""
    latest: dict[str, dict] = {}
    for record in tools.read_all_runs():
        rid = record.get("run_id", "")
        if not rid:
            continue
        data = record.get("data") or {}
        if not data.get("verdict"):  # not a run summary — skip
            continue
        latest[rid] = record
    rows = []
    for rid, rec in sorted(latest.items(), key=lambda kv: kv[1].get("at", "")):
        data = rec.get("data") or {}
        attestation = data.get("attestation") or {}
        rows.append({
            "timestamp": rec.get("at", ""),
            "run_id": rid,
            "asset_id": data.get("asset_id", ""),
            "wallet_label": data.get("wallet_label", ""),
            "verdict": data.get("verdict", ""),
            "rules_profile": data.get("rules_profile", ""),
            "mode": data.get("agent_mode", ""),
            "attestation_uid": attestation.get("uid", ""),
            "attestation_mode": attestation.get("mode", ""),
            "rule_ids": data.get("rule_ids", []),
            "easscan_url": attestation.get("easscan_url", ""),
            "explorer_url": attestation.get("explorer_url", ""),
        })
    return rows


def render_audit_page() -> str:
    """Server-rendered audit table — plain HTML, no JS required to read it."""
    rows = _audit_rows()
    body_rows = "\n".join(
        "<tr>"
        f"<td>{r['timestamp'][:19].replace('T', ' ')}</td>"
        f"<td><code>{r['asset_id']}</code></td>"
        f"<td><code>{r['wallet_label']}</code></td>"
        f"<td><span class=\"v {r['verdict'].lower()}\">{r['verdict']}</span></td>"
        f"<td>{r['rules_profile']}</td>"
        f"<td>{', '.join(r['rule_ids']) or '—'}</td>"
        f"<td>{r['attestation_mode']}</td>"
        f"<td><code>{r['attestation_uid'][:18]}…</code>"
        + (f' <a href="{r["explorer_url"]}">tx</a>' if r["explorer_url"] else "")
        + "</td>"
        "</tr>"
        for r in rows
    ) or '<tr><td colspan="8">No runs recorded yet — run a screening on the <a href="/">dashboard</a>.</td></tr>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Haki — audit view</title>
<link rel="icon" type="image/png" href="/static/haki-logo.png">
<style>
  body {{ margin:0; background:#0d1117; color:#e6edf3;
        font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
  :focus-visible {{ outline:3px solid #58a6ff; outline-offset:2px; }}
  header {{ display:flex; align-items:center; gap:12px; padding:16px 24px;
           border-bottom:1px solid #30363d; }}
  header img {{ width:36px; height:36px; border-radius:8px; }}
  h1 {{ font-size:1.2rem; margin:0; }}
  header .sub {{ color:#9da7b3; font-size:.85rem; }}
  main {{ max-width:1180px; margin:0 auto; padding:20px 24px; }}
  p {{ color:#9da7b3; max-width:72ch; }}
  table {{ width:100%; border-collapse:collapse; font-size:.85rem; margin-top:16px; }}
  th,td {{ text-align:left; padding:8px 10px; border-bottom:1px solid #30363d; }}
  th {{ color:#9da7b3; font-weight:500; }}
  code {{ color:#58a6ff; font-family:ui-monospace,Menlo,monospace; font-size:.8rem; }}
  .v {{ font-weight:700; padding:1px 10px; border-radius:999px; font-size:.75rem; }}
  .v.allow {{ background:#12351c; color:#7ee787; }}
  .v.restrict {{ background:#3b2e0a; color:#e3b341; }}
  .v.deny {{ background:#4a1216; color:#ff7b72; }}
  a {{ color:#58a6ff; }}
  .exports {{ margin-top:14px; }}
  .exports a {{ display:inline-block; padding:6px 14px; margin-right:8px;
               border:1px solid #30363d; border-radius:8px; text-decoration:none; }}
</style>
</head>
<body>
<header>
  <img src="/static/haki-logo.png" alt="Haki logo">
  <h1>Audit view</h1>
  <span class="sub">read-only · every screening recorded · Base Sepolia testnet</span>
</header>
<main>
  <p>What regulators see: every run Haki has screened, with the rule ids that
  produced each verdict and the attestation proving it was recorded. This table
  is generated straight from the append-only audit trail.</p>
  <div class="exports">
    <a href="/audit/export.json">Download JSON</a>
    <a href="/audit/export.csv">Download CSV</a>
    <a href="/">Back to dashboard</a>
  </div>
  <table>
    <thead><tr>
      <th scope="col">Time (UTC)</th><th scope="col">Asset</th><th scope="col">Wallet</th>
      <th scope="col">Verdict</th><th scope="col">Profile</th><th scope="col">Rules hit</th>
      <th scope="col">Proof</th><th scope="col">Attestation</th>
    </tr></thead>
    <tbody>{body_rows}</tbody>
  </table>
</main>
</body>
</html>"""


# static assets (css/js if split out later) served from /static
if STATIC_DIR.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
