#!/usr/bin/env python
"""Bounded design-tick audit for the 2026-09-19 05:07 candidate slot."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pipeline" / "reports" / "design_admissibility_audit_20260919-0510.json"

EVIDENCE_PATHS = [
    "pipeline/headless/.tick_context.json",
    "pipeline/goal.json",
    "pipeline/queue.json",
    "pipeline/research_work.json",
    "pipeline/reports/positive_membership_intervention_20260916.json",
    "pipeline/reports/referent_selection_admissibility_20260918-2116.json",
    "pipeline/decisions/20260917-131234_route_change.md",
    "pipeline/designs/exp_design_20260918-0517.md",
    "pipeline/designs/exp_design_20260916-1150.md",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    context = load("pipeline/headless/.tick_context.json")
    queue = load("pipeline/queue.json")
    research = load("pipeline/research_work.json")

    if context["mode"] != "design":
        raise SystemExit("expected design mode")
    if context["queue"]["candidate_budget"] != 1:
        raise SystemExit("expected candidate_budget=1")
    if context["queue"]["active_count"] != 1 or context["queue"]["capacity"] != 2:
        raise SystemExit("unexpected queue capacity state")
    if context["research_work"]["due_ids"]:
        raise SystemExit("due research work must be resumed before new design")

    pirs = [task for task in queue["gpu_queues"]["server-6"] if task["id"] == "M197-PIRS"]
    if len(pirs) != 1 or pirs[0]["status"] != "running":
        raise SystemExit("PIRS must still be running for the preterminal gate")

    rejected = {
        candidate["id"]: candidate
        for candidate in research["candidates"]
        if candidate.get("stage") == "rejected"
    }
    required = {
        "decision-aligned-referent-supervision",
        "referent-exclusivity-supervision",
        "same-target-description-consistency",
        "language-guided-query-selection",
        "relation-conditioned-identity-transport",
        "same-forward-coverage-diagnosis",
    }
    missing = sorted(required - rejected.keys())
    if missing:
        raise SystemExit(f"missing rejected-route evidence: {missing}")

    candidates = [
        {
            "id": "preterminal-mask-quality-successor",
            "decision": "reject",
            "reason": (
                "PIRS is still running and its branch-stop gate is preterminal. "
                "A score-target successor would both preempt that gate and duplicate "
                "the closed PIRS/listwise/hard-negative families."
            ),
            "evidence_ids": [
                "decision-aligned-referent-supervision",
                "referent-exclusivity-supervision",
            ],
        },
        {
            "id": "same-forward-mask-coverage",
            "decision": "reject",
            "reason": (
                "118/123 fixed TRAIN expressions already contain an acceptable query; "
                "only 5 are mask-limited and fixed sampling loses 0/117 covered targets."
            ),
            "evidence_ids": ["same-forward-coverage-diagnosis"],
        },
        {
            "id": "relation-or-modality-identity-fusion",
            "decision": "reject",
            "reason": (
                "The same-forward 2D identity signal is not aligned to referent language "
                "(top-5 6.1%; prefers-target 51.5%-57.6%), and RefMask3D already covers "
                "language/geometric-group mask identification."
            ),
            "evidence_ids": ["relation-conditioned-identity-transport"],
        },
        {
            "id": "same-target-consistency-or-listwise-ranking",
            "decision": "reject",
            "reason": (
                "Both are established closed routes and would only rename multi-positive "
                "or rank-and-sort supervision."
            ),
            "evidence_ids": [
                "same-target-description-consistency",
                "decision-aligned-referent-supervision",
            ],
        },
    ]

    evidence = []
    for rel in EVIDENCE_PATHS:
        path = ROOT / rel
        evidence.append(
            {
                "path": rel,
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )

    report = {
        "schema_version": 1,
        "created": "2026-09-19T05:10:00+08:00",
        "scope": (
            "CPU-only bounded design audit. No model forward, GPU execution, queue "
            "mutation, admission receipt, or efficacy claim."
        ),
        "tick_snapshot": {
            "mode": context["mode"],
            "candidate_budget": context["queue"]["candidate_budget"],
            "active_count": context["queue"]["active_count"],
            "capacity": context["queue"]["capacity"],
            "pirs_status": pirs[0]["status"],
            "pirs_config": pirs[0]["config"],
            "due_ids": context["research_work"]["due_ids"],
        },
        "decision": {
            "admitted_candidates": [],
            "slot_action": "keep_empty",
            "reason": (
                "All structurally distinct alternatives fail a measured diagnosis, "
                "constraint, primary-source, or closed-branch gate. Filling the slot "
                "would require a renamed duplicate or an unsupported placeholder."
            ),
        },
        "rejected_candidates": candidates,
        "next_executable_work": [
            "At/after 2026-09-19T05:25:00+08:00, retry the seven due native "
            "referent diagnostics only if GPU7 has fewer than two processes and "
            "sufficient measured free memory.",
            "Monitor M197-PIRS to terminal before evaluating or replacing the "
            "referent-supervision branch.",
        ],
        "evidence": evidence,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
