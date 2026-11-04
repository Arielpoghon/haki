"""Haki — a compliance agent for tokenized real-world assets (RWA).

Package layout:
- schemas.py      — pydantic models (assets, wallets, rules, runs, proofs)
- rules_engine.py — deterministic verdict engine (the source of truth)
- tools.py        — agent tools: data loads + audit trail (audit/trail.jsonl)
- agent.py        — orchestrator: tool pipeline + rationale (LLM optional)
- attestation.py  — proof bridge: simulated by default, EAS when configured
- main.py         — FastAPI app + plain-HTML dashboard (static/)
"""
