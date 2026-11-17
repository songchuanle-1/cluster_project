"""Persist executed static audit evidence without changing queue or model code."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "pipeline/research_work.json"
work = json.loads(path.read_text(encoding="utf-8"))
artifacts = [
    "scripts/referent_supervision_contract_20260916.py",
    "pipeline/reports/referent_supervision_contract_20260916.json",
    "pipeline/reports/referent_supervision_admission_20260916-1012.md",
]
evidence = [{"path": p, "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
            for p in artifacts]
actions = {
    "referent-supervision-unit": (
        "Six source checks/eight finite label cases passed; query has scene/language "
        "attention and produces masks. No-extent premise disproven as a general claim; "
        "score and OHRS label supports differ. Root cause and imitation untested.",
        "Capture native all-query seed/mask-positive contingency, score-supervised "
        "support and true query/target/SP axes on fixed123 TRAIN; report85/33/5 strata "
        "and scene uncertainty before learning comparisons. No assignment-successor admission."),
    "referent-query-selection": (
        "Static audit identifies oracle-best-query rank versus best acceptable-mask "
        "rank distinction; fixed readout failure does not establish missing representation information.",
        "Use shared native contingency capture to compute best indis/score rank over "
        "ALL target masks with IoU>.5 alongside oracle-best-query rank and85/33/5 strata; no new scorer."),
    "input-modality-distinguishability": (
        "Persisted seven connected scene/annotation/node IDs and explicit missing "
        "physical support axes in the inspected archive, not native absence.",
        "Capture original SP IDs, sample inverse, expanded expression axes and paired2D/3D "
        "rows for these seven cases from existing native loader; trace cache producer identity."),
    "same-target-description-grounding": (
        "Executed finite owned/endpoint-relocated/predicate-disabled factor control: "
        "[5,4]/[3,5]/[3,3]. Reference-control evidence only, no novelty/native efficacy.",
        "Bind owned/relocated/disabled controls to seven connected native expression/physical "
        "endpoints; retain12 disconnected controls and verify whole-mechanism prior art."),
    "same-forward-coverage-diagnosis": (
        "Shared static audit verifies scene/language-conditioned query drives both "
        "mask and referent heads; corrects no-extent premise. Coverage route remains closed.",
        "Advance via shared referent-selection native contingency capture and best "
        "acceptable-mask rank with exact physical axes; no repeated coverage/cluster audit."),
}
for candidate in work["candidates"]:
    if candidate["id"] not in actions:
        continue
    progress, action = actions[candidate["id"]]
    if candidate["id"] == "referent-supervision-unit":
        candidate["stage"] = "diagnosis"
    candidate["latest_progress"] = "2026-09-16T10:12:00+08:00: " + progress
    candidate["next_action"] = action
    for entry in evidence:
        if not any(e["path"] == entry["path"] for e in candidate["evidence"]):
            candidate["evidence"].append(entry)
path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Persisted five due candidate dispositions and hashed executed evidence.")
