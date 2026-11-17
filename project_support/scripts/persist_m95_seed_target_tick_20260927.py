"""Persist the targeted diagnostic under its existing stable research ID."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
EVIDENCE = (
    "pipeline/reports/m95_final_seed_target_prereg_20260927.md",
    "pipeline/reports/m95_final_seed_target_20260927.json",
    "pipeline/reports/m95_seed_loss_intervention_prereg_20260927.md",
    "pipeline/reports/m95_seed_loss_intervention_20260927.json",
    "pipeline/reports/m95_seed_parameter_backward_20260927.json",
    "pipeline/reports/m95_targeted_seed_replay_prereg_20260927.md",
    "pipeline/reports/m95_targeted_seed_replay_20260927.json",
    "pipeline/reports/m95_targeted_seed_endpoint_20260927.json",
    "pipeline/decisions/20260927-004106_route_change.md",
    "pipeline/reports/m95_seed_population_prereg_20260927.md",
    "pipeline/reports/m95_seed_population_20260927.json",
    "pipeline/reports/m95_seed_population_repeat_20260927.json",
)


def bound(path):
    return {
        "path": path,
        "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
    }


def main():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    row = next(x for x in data["candidates"]
               if x["id"] == "m95-sample-context-support")
    if row["stage"] != "diagnosis" or any(
            item["path"] == EVIDENCE[-1] for item in row["evidence"]):
        raise ValueError("Unexpected candidate stage or duplicate tick")
    passive = json.loads((ROOT / EVIDENCE[1]).read_text(encoding="utf-8"))
    targeted = json.loads((ROOT / EVIDENCE[7]).read_text(encoding="utf-8"))
    population = json.loads((ROOT / EVIDENCE[10]).read_text(encoding="utf-8"))
    repeat = json.loads((ROOT / EVIDENCE[11]).read_text(encoding="utf-8"))
    exposed = [r for r in passive["rows"] if r["unmatched_non_target_context"]]
    ann15 = next(r for r in targeted["rows"]
                 if (r["scene"], r["ann_id"]) == ("scene0588_00", 15))
    if (len(passive["rows"]), len(exposed),
            sum(r["unmatched_non_target_context"] for r in exposed)) != (16, 11, 222):
        raise ValueError("Native final target census changed")
    if not ann15["selected_seed_is_context"] or ann15["selected_seed_final_target"] != .25:
        raise ValueError("Targeted exposure changed")
    if len(population["population_selected"]) != 32 or len(repeat["population_selected"]) != 32:
        raise ValueError("Prediction-blind population incomplete")
    if [(x["scene"], x["ann_id"], x["selected_context"], x["selected_iou"])
            for x in population["population_selected"]] != [
            (x["scene"], x["ann_id"], x["selected_context"], x["selected_iou"])
            for x in repeat["population_selected"]]:
        raise ValueError("Population repeat outcomes differ")
    exposed_population = [x for x in population["population_selected"]
                          if x["selected_context"]]
    if len(exposed_population) != 4 or any(x["selected_iou"] > .5
                                           for x in exposed_population):
        raise ValueError("Population exposure differs")
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    row["latest_progress"] = (
        stamp + ": Native 2-batch/16-expression target census found 222 unmatched "
        "non-target context seeds in 11 expressions with final sample target 0.25; "
        "all target overrides were confined to matched/top-k seeds. Count/logit "
        "placebo changes focal gradients and treated label removal changes existing "
        "sampling parameters (2 tensors, treated gradient delta L1 1.33266, "
        "placebo 0.44668). Fresh transformed TRAIN replay scene0588_00 ann15 "
        "selected a context seed, final target 0.25, selected IoU 0.5. This is "
        "not identical to frozen full-order input. Prediction-blind 32-key "
        "population (16 ambiguous/16 unique) found four selected context seeds, "
        "all IoU 0; 1/28 non-exposed had IoU <=0.5, and same-seed replay had "
        "0/32 selected outcome changes. These are observational associations "
        "without independent augmentation repeats. Matched class/instance control, "
        "new candidate code, efficacy, resources and six-gate receipt are absent."
    )
    row["next_action"] = (
        "On server-6 GPU7, create frozen exact-input native batch fingerprints "
        "for the preregistered 32-key population, with independent transform "
        "repeats and selected-seed label/instance binding. Preregister an "
        "instance-role structural seed-supervision mechanism distinct from "
        "selector/ranking and mere loss-weight tuning. Compare intervention "
        "and matched controls inside the same captured forward, preserving "
        "the matcher/indicator/masks, and report the class/instance-matching "
        "limitations or impossibility explicitly. "
        "Test same-forward native parameter backward and matched mechanisms, then "
        "resource/Pareto, independent package/config and goal constraints. Do not "
        "admit or enqueue from the current association/gradient evidence."
    )
    row["evidence"].extend(bound(p) for p in EVIDENCE)
    data["next_action"] = row["next_action"]
    data["updated_at"] = stamp
    cycle = data["design_cycle"]
    cycle.update(
        timestamp=stamp,
        attempted_ids=["m95-sample-context-support"],
        evidence=[bound(p) for p in EVIDENCE],
        resume_condition=row["next_action"],
        blocker="Actionable native population/control and candidate implementation; no external blocker.",
        deferred_reason="Native final target and gradient tests advanced; strict matched intervention and six-gate candidate still unexecuted.",
    )
    # This is a foreground continuation, not a scheduler deadline disposition.
    cycle.pop("stop_reason", None)
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(row["id"], row["stage"], len(row["evidence"]))


if __name__ == "__main__":
    main()
