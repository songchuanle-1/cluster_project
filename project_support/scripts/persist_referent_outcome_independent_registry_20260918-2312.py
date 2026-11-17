import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:/project/cluster_project")
WORK = ROOT / "pipeline/research_work.json"
REPORT = (
    ROOT
    / "pipeline/reports/"
    "referent_outcome_independent_registry_20260918-2311.json"
)
PRODUCER = ROOT / "scripts/referent_outcome_independent_registry_20260918.py"
TESTS = (
    ROOT
    / "scripts/test_referent_outcome_independent_registry_20260918.py"
)
DECISION = ROOT / "pipeline/decisions/20260918-231223_route_change.md"
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


artifacts = [
    (REPORT, sha(REPORT)),
    (PRODUCER, sha(PRODUCER)),
    (TESTS, sha(TESTS)),
    (DECISION, sha(DECISION)),
]
document = json.loads(WORK.read_text(encoding="utf-8"))
seen = {candidate["id"] for candidate in document["candidates"]}
if not IDS.issubset(seen):
    raise ValueError("Expected due candidate missing from research_work.json")

for candidate in document["candidates"]:
    if candidate["id"] not in IDS:
        continue
    candidate["stage"] = "blocked"
    candidate["blocker"] = (
        "GPU7 remains at the two-process cap with M197-PIRS plus one foreign "
        "process. The outcome-independent registry is now frozen; native "
        "candidate scoring remains unavailable."
    )
    candidate["retry_after"] = "2026-09-19T00:15:00+08:00"
    candidate["unblock_condition"] = (
        "M197-PIRS reaches terminal state or GPU7 has fewer than two processes "
        "with sufficient measured free memory."
    )
    candidate["latest_progress"] = (
        "2026-09-18T23:11:00+08:00: the due retry still found M197 pid1134192 "
        "(19956 MiB) plus foreign pid3827570 (42488 MiB), with 18597 MiB free. "
        "Completed the CPU-only next validation stage: reproduced the archived "
        "seed-1999 16-batch TRAIN cohort, froze all 123 expressions before "
        "native scoring, enumerated 312 same-class candidates for 73 "
        "rank-eligible expressions, and retained 50 expressions with no "
        "same-class candidate without outcome-based exclusion. The registry "
        "contains no score, rank, prediction, or observed-error field. Fresh "
        "evidence: "
        f"pipeline/reports/{REPORT.name} sha256={sha(REPORT)}."
    )
    candidate["next_action"] = (
        "Retry after 2026-09-19T00:15:00+08:00. If GPU7 has capacity, run the "
        "frozen native capture for every target plus all 312 predeclared "
        "same-class candidates on the 73 eligible expressions; bind exact "
        "config/model/checkpoint identities and identical transformed-input and "
        "hierarchical-partition hashes; compute scene-balanced target rank "
        "among the complete candidate pool and reject any expression with "
        "missing native coverage instead of imputing it. Keep the 31 "
        "observed-failure pairs separate as failure-local diagnostics. If "
        "capacity remains unavailable, continue only CPU-only registry and "
        "admission checks that do not duplicate this validation."
    )
    evidence = candidate.setdefault("evidence", [])
    for path, digest in artifacts:
        relative = path.relative_to(ROOT).as_posix()
        item = {"path": relative, "sha256": digest}
        if item not in evidence:
            evidence.append(item)

WORK.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
loaded = json.loads(WORK.read_text(encoding="utf-8"))
updated = [candidate for candidate in loaded["candidates"] if candidate["id"] in IDS]
if len(updated) != len(IDS):
    raise ValueError("Post-write candidate count differs")
if any(candidate["stage"] != "blocked" for candidate in updated):
    raise ValueError("Unexpected post-write stage")
print(json.dumps({
    "updated": len(updated),
    "report_sha256": sha(REPORT),
    "producer_sha256": sha(PRODUCER),
    "tests_sha256": sha(TESTS),
    "decision_sha256": sha(DECISION),
}, indent=2))
