#!/usr/bin/env python
"""Persist M197 terminal state and server-4 migration blockers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_PATH = ROOT / "pipeline" / "research_work.json"
EXP_PATH = ROOT / "pipeline" / "experiments" / "M197-PIRS.json"
EVIDENCE_PATH = (
    ROOT / "pipeline" / "reports" / "m197_terminal_evidence_20260920-0952.json"
)
ANALYSIS_PATH = (
    ROOT
    / "pipeline"
    / "analyses"
    / "M197-PIRS_stopped_unknown_20260920-0952.md"
)

ACTIVE_DIAGNOSTICS = {
    "referent-causality-audit",
    "modality-identity-preservation",
    "referent-discrimination",
    "instance-identity-representation",
    "referent-query-selection",
    "input-modality-distinguishability",
    "same-target-description-grounding",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evidence(path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
    }


def append_unique(items: list[dict[str, str]], item: dict[str, str]) -> None:
    if item not in items:
        items.append(item)


def main() -> None:
    terminal_evidence = evidence(EVIDENCE_PATH)
    terminal_analysis = evidence(ANALYSIS_PATH)
    payload = json.loads(WORK_PATH.read_text(encoding="utf-8"))

    shared_blocker = (
        "New GPU execution is allocated only to server-4 GPU0/1, one slot each. "
        "server-4 answers ping but refuses SSH port22, so GPU occupancy, code root, "
        "environment and data paths are unverified and no sync or launch is allowed. "
        "server-6 is dispatch-disabled. M197-PIRS is no longer running there; its "
        "remote last.pth and best.pth are preserved."
    )
    shared_unblock = (
        "server-4 SSH succeeds and GPU0/1 occupancy, memory, code root, conda "
        "environment and dataset paths are verified. Any M197 resume also requires "
        "verified checkpoint transfer and path adaptation."
    )
    shared_next = (
        "Continue executable CPU collation/prepare_replay for saved groups3040/3893 "
        "and export original indices3921/4278 while preserving each full31 "
        "denominator. Retry read-only server-4 SSH at/after "
        "2026-09-20T10:07:00+08:00. Before any GPU forward, sync or launch, verify "
        "GPU0/1 occupancy and memory, /data/songcl/Project/Cluster_project/Cluster, "
        "the project_cluster environment and dataset paths. Never dispatch to "
        "server-6 and never use legacy sync.sh."
    )

    updated = []
    for candidate in payload.get("candidates", []):
        candidate_id = candidate.get("id")
        if candidate_id == "referent-supervision-axis":
            candidate["stage"] = "blocked"
            candidate["blocker"] = (
                "M197-PIRS stopped without a completion marker at epoch27 step3241. "
                "Its checkpoints remain on dispatch-disabled server-6, while "
                "server-4 SSH port22 refuses connections."
            )
            candidate["retry_after"] = "2026-09-20T10:07:00+08:00"
            candidate["unblock_condition"] = (
                "server-4 SSH and runtime paths verify successfully, and the "
                "server-6 last.pth can be transferred with checkpoint/path "
                "compatibility established."
            )
            candidate["latest_progress"] = (
                "2026-09-20T09:52:26+08:00: M197-PIRS classified "
                "stopped_unknown after three missing-process observations. Last "
                "log progress is Train27 step3241/4686; no traceback, OOM, early-stop "
                "or completion marker. Remote last.pth and best.pth are preserved."
            )
            candidate["next_action"] = (
                "Do not restart on server-6. After server-4 verification, transfer "
                "and validate last.pth, then resume M197 on one server-4 GPU only if "
                "checkpoint and path adaptation checks pass. Keep the second slot "
                "for an independently admitted task or native diagnostic."
            )
            evidence_list = candidate.setdefault("evidence", [])
            append_unique(evidence_list, terminal_evidence)
            append_unique(evidence_list, terminal_analysis)
            updated.append(candidate_id)
        elif candidate_id in ACTIVE_DIAGNOSTICS:
            candidate["blocker"] = shared_blocker
            candidate["retry_after"] = "2026-09-20T10:07:00+08:00"
            candidate["unblock_condition"] = shared_unblock
            candidate["next_action"] = shared_next
            candidate["latest_progress"] = (
                "2026-09-20T09:52:26+08:00: server-4 remains unreachable over "
                "SSH; M197-PIRS was reconciled stopped_unknown on server-6. Physical "
                "coverage remains9/31 and model captures0/31."
            )
            append_unique(candidate.setdefault("evidence", []), terminal_evidence)
            updated.append(candidate_id)

    payload["next_action"] = shared_next
    payload["last_terminal_event"] = {
        "experiment_id": "M197-PIRS",
        "state": "stopped_unknown",
        "timestamp": "2026-09-20T09:52:26+08:00",
        "evidence": terminal_evidence,
        "analysis": terminal_analysis,
    }
    WORK_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    experiment = json.loads(EXP_PATH.read_text(encoding="utf-8"))
    experiment["terminal_evidence"] = terminal_evidence["path"]
    experiment["terminal_analysis"] = terminal_analysis["path"]
    experiment["resume_checkpoint"] = (
        "/data3/songcl/Project/Cluster_project/Cluster_checkpoints/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pirs/"
        "20260916_042843/last.pth"
    )
    experiment["resume_policy"] = (
        "server-4 GPU0/1 only after SSH/runtime/checkpoint-transfer verification"
    )
    EXP_PATH.write_text(
        json.dumps(experiment, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    verified = json.loads(WORK_PATH.read_text(encoding="utf-8"))
    pirs = next(
        item
        for item in verified["candidates"]
        if item.get("id") == "referent-supervision-axis"
    )
    if pirs.get("stage") != "blocked":
        raise RuntimeError("PIRS terminal disposition did not persist")
    print(
        json.dumps(
            {
                "updated": updated,
                "terminal_evidence": terminal_evidence,
                "terminal_analysis": terminal_analysis,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
