"""Haki — a compliance agent for tokenized real-world assets (RWA).

M0 package layout:
- schemas.py      — pydantic models (assets, wallets, rules, screening results)
- rules_engine.py — deterministic verdict engine (the source of truth)

Coming in M1-M3: agent.py (tool pipeline), tools.py, attestation.py, main.py
(FastAPI + static dashboard).
"""
