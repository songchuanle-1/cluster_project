import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:/project/cluster_project")
WORK = ROOT / "pipeline/research_work.json"
ARTIFACTS = (
    ROOT / "pipeline/reports/due_capture_readiness_20260918-1812.json",
    ROOT / "scripts/record_due_capture_readiness_20260918-1812.py",
    ROOT / "pipeline/reports/referent_control_pairing_20260918-1812.json",
    ROOT / "scripts/referent_control_pairing_20260918.py",
    ROOT / "scripts/test_referent_control_pairing_20260918.py",
    ROOT / "pipeline/decisions/20260918-181201_other.md",
)
IDS = {
    "referent-causality-audit",
    "modality-identity-preservation",
    "referent-discrimination",
    "instance-identity-representation",
    "referent-query-selection",
    "input-modality-distinguishability",
    "same-target-description-grounding",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


hashes = {path: sha(path) for path in ARTIFACTS}
pairing_path = ROOT / "pipeline/reports/referent_control_pairing_20260918-1812.json"
pairing = json.loads(pairing_path.read_text(encoding="utf-8"))
summary = pairing["summary"]
document = json.loads(WORK.read_text(encoding="utf-8"))
seen = {candidate["id"] for candidate in document["candidates"]}
if not IDS.issubset(seen):
    raise ValueError("Expected due candidate missing from research_work.json")

progress = {
    "timestamp": "2026-09-18T18:13:00+08:00",
    "report": "pipeline/reports/referent_control_pairing_20260918-1812.json",
    "report_sha256": hashes[pairing_path],
    "native_execution_completed": False,
    "primary_same_class_pairs": summary["same_class_primary_pairs"],
    "scenes": summary["scenes"],
    "same_target_repeated_among_primary": (
        summary["same_target_repeated_among_primary"]
    ),
    "direct_connected_primary_pairs": (
        summary["direct_connected_primary_pairs"]
    ),
    "finding": (
        "The frozen pairing registry has 31 primary exact same-class pairs "
        "across 17 scenes; 30/31 are in the repeated-description sensitivity "
        "subset and only 2/31 support the directly connected same-class "
        "subgroup. Scene weights sum to one per scene (total pair weight 17)."
    ),
}

for candidate in document["candidates"]:
    if candidate["id"] not in IDS:
        continue
    candidate["stage"] = "blocked"
    candidate["blocker"] = (
        "GPU7 remains at the two-process cap with M197-PIRS plus one foreign "
        "process; the frozen static pairing contract cannot substitute for the "
        "missing native candidate-support capture."
    )
    candidate["retry_after"] = "2026-09-18T19:00:00+08:00"
    candidate["unblock_condition"] = (
        "M197-PIRS reaches terminal state or GPU7 has fewer than two processes "
        "with sufficient measured free memory."
    )
    candidate["latest_progress"] = (
        "2026-09-18T18:12:31+08:00: the due retry still found M197 pid1134192 "
        "(19956 MiB) plus foreign pid3827570 (42488 MiB) on GPU7, 19076 MiB "
        "free, 100 percent utilization; M197 remained alive at epoch 18, "
        "iteration 1750/4686, and the preflight best improved to 0.4845. A new "
        "CPU-only registry froze 31 primary exact same-class pairs across 17 "
        "scenes, with 30 repeated-description pairs and only 2 direct-connected "
        "pairs. Fresh evidence: "
        "pipeline/reports/referent_control_pairing_20260918-1812.json "
        f"sha256={hashes[pairing_path]}."
    )
    candidate["next_action"] = (
        "Retry after 2026-09-18T19:00:00+08:00. If GPU7 is below the "
        "two-process cap, execute the frozen native TRAIN/control capture using "
        "the 31 primary same-class pairs and the recorded scene weights. Report "
        "the 30 repeated-description pairs as sensitivity and the two "
        "direct-connected pairs as exploratory only. Require exact model/config "
        "identity, distinct checkpoints, native candidate/mask coverage, and "
        "identical transformed-input and hierarchical-partition hashes; do not "
        "impute missing pairs or claim a relation-context effect."
    )
    candidate["pairing_contract_progress"] = progress
    evidence = candidate.setdefault("evidence", [])
    for path in ARTIFACTS:
        relative = path.relative_to(ROOT).as_posix()
        if not any(item.get("path") == relative for item in evidence):
            evidence.append({"path": relative, "sha256": hashes[path]})

WORK.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
loaded = json.loads(WORK.read_text(encoding="utf-8"))
updated = [candidate for candidate in loaded["candidates"] if candidate["id"] in IDS]
if len(updated) != len(IDS):
    raise ValueError("Post-write candidate count differs")
print(json.dumps({
    "updated": len(updated),
    "artifacts": {
        path.relative_to(ROOT).as_posix(): digest
        for path, digest in hashes.items()
    },
}, indent=2))
