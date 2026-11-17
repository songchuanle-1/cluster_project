import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:/project/cluster_project")
WORK = ROOT / "pipeline/research_work.json"
REPORT = ROOT / "pipeline/reports/referent_control_coverage_20260918-1618.json"
PRODUCER = ROOT / "scripts/referent_control_coverage_20260918.py"
TESTS = ROOT / "scripts/test_referent_control_coverage_20260918.py"
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


report_sha = sha(REPORT)
producer_sha = sha(PRODUCER)
tests_sha = sha(TESTS)
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
        "process; the newly audited same-class controls do not remove the native "
        "capture dependency."
    )
    candidate["retry_after"] = "2026-09-18T17:20:00+08:00"
    candidate["unblock_condition"] = (
        "M197-PIRS reaches terminal state or GPU7 has fewer than two processes "
        "with sufficient measured free memory."
    )
    candidate["latest_progress"] = (
        "2026-09-18T16:22:13+08:00: the due retry still found M197 pid1134192 "
        "(19956 MiB) plus foreign pid3827570 (42488 MiB), with 18597 MiB free; "
        "M197 had advanced to native step 4680/4686 and entered validation. A "
        "CPU-only ScanRefer metadata audit reproduced the 123-expression sample "
        "and matched all 33 observed failures. All 33 had a same-class peer and "
        "31/33 were misassigned to a same-class object, but only 2/33 had a "
        "directly relation-connected same-class peer; 30/33 had a target relation "
        "edge and 32/33 had repeated target descriptions. Fresh evidence: "
        f"pipeline/reports/referent_control_coverage_20260918-1618.json "
        f"sha256={report_sha}."
    )
    candidate["next_action"] = (
        "Await terminal PIRS, then retry GPU7 and execute the frozen TRAIN/control "
        "capture. Use the metadata registry to stratify exact same-class controls "
        "and repeated-description controls; do not claim a relation-connected "
        "same-class effect from the 2 failure expressions alone. Require bound "
        "model/config identities, distinct checkpoints, and identical native-input "
        "and hierarchical-partition hashes before scene-balanced paired evaluation."
    )
    evidence = candidate.setdefault("evidence", [])
    for path, digest in (
        (REPORT, report_sha),
        (PRODUCER, producer_sha),
        (TESTS, tests_sha),
    ):
        relative = path.relative_to(ROOT).as_posix()
        if not any(item.get("path") == relative for item in evidence):
            evidence.append({"path": relative, "sha256": digest})

WORK.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
loaded = json.loads(WORK.read_text(encoding="utf-8"))
updated = [candidate for candidate in loaded["candidates"] if candidate["id"] in IDS]
if len(updated) != len(IDS):
    raise ValueError("Post-write candidate count differs")
print(json.dumps({
    "updated": len(updated),
    "report_sha256": report_sha,
    "producer_sha256": producer_sha,
    "tests_sha256": tests_sha,
}, indent=2))
