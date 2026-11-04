"""Haki API — the only backend. FastAPI serves the plain-HTML dashboard and
the /api/v1 endpoints. No build step, no second stack.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from . import agent, tools
from .schemas import ComplianceRun, ScreenRequest

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = REPO_ROOT / "static"

app = FastAPI(
    title="Haki",
    description="Compliance agent for tokenized real-world assets — "
                "rules engine decides, agent explains, chain proves.",
    version="0.2.0",
)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "haki"}


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
    try:
        return agent.run_compliance(request.asset_id, request.wallet_label)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc


@app.get("/api/v1/runs/{run_id}")
def get_run(run_id: str) -> dict:
    stored = tools.read_run(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id!r}")
    return stored


# static assets (css/js if split out later) served from /static
if STATIC_DIR.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
