#!/usr/bin/env python
"""Persist the server-4-only dispatch allocation into durable research state."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_PATH = ROOT / "pipeline" / "research_work.json"
EVIDENCE_PATH = ROOT / "pipeline" / "reports" / "allocation_change_20260920-0937.json"

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


def main() -> None:
    payload = json.loads(WORK_PATH.read_text(encoding="utf-8"))
    evidence = {
        "path": EVIDENCE_PATH.relative_to(ROOT).as_posix(),
        "sha256": sha256(EVIDENCE_PATH),
    }
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    retry_after = "2026-09-20T10:07:00+08:00"
    blocker = (
        "New GPU execution is allocated only to server-4 GPU0/1, one slot each. "
        "server-4 answers ping but SSH port22 is refusing connections, so GPU "
        "occupancy, code root, environment and data paths are not verified and "
        "no sync or launch is allowed. server-6 GPU7 is dispatch-disabled; only "
        "the grandfathered M197-PIRS may continue there. CPU preparation remains "
        "executable. Candidate-specific scientific gates remain unresolved."
    )
    unblock = (
        "server-4 SSH succeeds and GPU0/1 occupancy, memory, code root, conda "
        "environment and data paths are verified; then use only server-4 GPU0/1. "
        "Candidate-specific scientific gates must also pass."
    )
    next_action = (
        "Do not repeat recovered0815 replay or the 0915 exports. First continue "
        "CPU exact collation/prepare_replay for3040/3893 and export original "
        "indices3921/4278 while preserving each full31 denominator. In parallel, "
        "retry read-only server-4 SSH after2026-09-20T10:07:00+08:00. Before any "
        "GPU model forward, sync or training launch, verify GPU0/1 occupancy and "
        "memory, /data/songcl/Project/Cluster_project/Cluster, the project_cluster "
        "environment and dataset paths. Use one task per GPU. Never dispatch new "
        "work to server-6; monitor M197 there to terminal only. No promotion until "
        "mechanism, controls, novelty, independence, backward, resource and "
        "admission gates pass; never run legacy sync.sh."
    )

    updated = []
    for candidate in payload.get("candidates", []):
        candidate_id = candidate.get("id")
        evidence_list = candidate.setdefault("evidence", [])
        if evidence not in evidence_list:
            evidence_list.append(evidence)
        if candidate_id in ACTIVE_DIAGNOSTICS:
            candidate["blocker"] = blocker
            candidate["retry_after"] = retry_after
            candidate["unblock_condition"] = unblock
            candidate["next_action"] = next_action
            candidate["latest_progress"] = (
                f"{now}: Allocation changed to server-4 GPU0/1 only; "
                "server-4 SSH port22 refused, so no GPU execution or sync occurred. "
                "Physical coverage remains9/31 and model captures0/31."
            )
            updated.append(candidate_id)
        elif candidate_id == "referent-supervision-axis":
            candidate["next_action"] = (
                "Monitor grandfathered M197-PIRS on server-6 GPU7 to terminal, "
                "then run the pre-registered design1150 section7 analysis. Do not "
                "restart or launch a successor on server-6. New work uses only "
                "verified server-4 GPU0/1."
            )
            updated.append(candidate_id)

    payload["next_action"] = next_action
    payload["allocation_updated_at"] = now
    payload["allocation_evidence"] = evidence

    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    WORK_PATH.write_text(serialized, encoding="utf-8")

    verified = json.loads(WORK_PATH.read_text(encoding="utf-8"))
    ids = {item.get("id") for item in verified.get("candidates", [])}
    missing = ACTIVE_DIAGNOSTICS - ids
    if missing:
        raise RuntimeError(f"Missing candidates after write: {sorted(missing)}")
    if verified.get("allocation_evidence") != evidence:
        raise RuntimeError("Allocation evidence did not persist")
    print(
        json.dumps(
            {
                "updated": updated,
                "candidate_count": len(verified.get("candidates", [])),
                "evidence": evidence,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
