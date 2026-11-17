import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:/project/cluster_project")
WORK = ROOT / "pipeline/research_work.json"
ARTIFACTS = (
    ROOT / "pipeline/reports/referent_selection_admissibility_20260918-2116.json",
    ROOT / "scripts/referent_selection_admissibility_20260918.py",
    ROOT / "scripts/test_referent_selection_admissibility_20260918.py",
    ROOT / "pipeline/decisions/20260918-211544_route_change.md",
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
report_path = ARTIFACTS[0]
report = json.loads(report_path.read_text(encoding="utf-8"))
gate = report["selection_gate"]
if gate["population_effect_admissible"]:
    raise ValueError("Selection audit unexpectedly admits a population effect")
if not gate["failure_local_diagnostic_admissible"]:
    raise ValueError("Selection audit rejects failure-local diagnostics")

document = json.loads(WORK.read_text(encoding="utf-8"))
seen = {candidate["id"] for candidate in document["candidates"]}
if not IDS.issubset(seen):
    raise ValueError("Expected due candidate missing from research_work.json")

progress = {
    "timestamp": "2026-09-18T21:16:00+08:00",
    "report": "pipeline/reports/referent_selection_admissibility_20260918-2116.json",
    "report_sha256": hashes[report_path],
    "native_execution_completed": False,
    "primary_pairs": gate["primary_pairs"],
    "outcome_independent_expressions": gate["outcome_independent_expressions"],
    "population_effect_admissible": gate["population_effect_admissible"],
    "failure_local_diagnostic_admissible": (
        gate["failure_local_diagnostic_admissible"]
    ),
    "finding": (
        "All 31 primary pairs are selected from observed failures and use the "
        "observed wrong instance as control. The failure sample has same-class "
        "peers in 33/33 expressions versus 21656/36665 train expressions; the "
        "selection audit therefore rejects promotion to a primary population "
        "effect and retains the registry as failure-local diagnostic evidence."
    ),
}

for candidate in document["candidates"]:
    if candidate["id"] not in IDS:
        continue
    candidate["stage"] = "blocked"
    candidate["blocker"] = (
        "GPU7 remains at the two-process cap with M197-PIRS plus one foreign "
        "process. The observed-failure registry also fails the primary "
        "outcome-independence gate."
    )
    candidate["retry_after"] = "2026-09-18T21:45:00+08:00"
    candidate["unblock_condition"] = (
        "M197-PIRS reaches terminal state or GPU7 has fewer than two processes "
        "with sufficient measured free memory. Before capture, an "
        "outcome-independent registry must be frozen."
    )
    candidate["latest_progress"] = (
        "2026-09-18T21:16:00+08:00: GPU7 still had M197 pid1134192 (19956 MiB) "
        "and foreign pid3827570 (42488 MiB). The M197 log advanced from "
        "iteration 1750/4686 to validation after iteration 4680/4686 at epoch "
        "18, with preflight best 0.4845. A CPU-only selection audit found that "
        "all 31 primary pairs are observed-failure selected and use the observed "
        "wrong instance as control; 33/33 failures had same-class peers versus "
        "21656/36665 train expressions (RR 1.693064, Fisher p 5.85e-08). Fresh "
        "evidence: "
        "pipeline/reports/referent_selection_admissibility_20260918-2116.json "
        f"sha256={hashes[report_path]}."
    )
    candidate["next_action"] = (
        "Retry after 2026-09-18T21:45:00+08:00. Before native GPU capture, "
        "construct and freeze an outcome-independent registry from the archived "
        "123-expression cohort with complete same-class candidate pools. If GPU7 "
        "has capacity, capture native scores and masks for the target and every "
        "predeclared same-class candidate; use scene-balanced target rank among "
        "the full candidate pool as the primary diagnostic. Retain the 31 "
        "observed failures only as failure-local tracing, not a population "
        "effect. Require exact model/config identity, distinct checkpoints, "
        "native candidate/mask coverage, and identical transformed-input and "
        "hierarchical-partition hashes; do not impute missing pairs."
    )
    candidate["selection_admissibility_progress"] = progress
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
