"""Summarize exact-input native captures and advance the existing research ID."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "pipeline/reports"
INPUTS = (
    "m95_seed_exact_input_prereg_20260927.md",
    "m95_seed_exact_1999_20260927.json",
    "m95_seed_exact_2000_20260927.json",
    "m95_seed_role_controls_1999_20260927.json",
)
OUTPUT = REPORTS / "m95_seed_exact_input_summary_20260927.json"
LEDGER = ROOT / "pipeline/research_work.json"
NEXT = (
    "Preregister a structural instance-role seed-supervision unit distinct from "
    "selector/ranking and scalar loss tuning. The native same-instance zero-target "
    "placebo is impossible in the captured cohort (0/2140), so specify an alternative "
    "causal control with its unmatched confounders and predeclared rejection criterion; "
    "do not describe the old count/logit placebo as instance matched. Implement the "
    "candidate and run paired same-forward native loss/parameter backward with unchanged "
    "matcher, indicator and masks on server-6 GPU7. If diagnostic/control gates pass, "
    "measure baseline/champion/candidate resources on one protocol, independence, "
    "constraints and efficacy; otherwise reject with disconfirming evidence. No "
    "admission or launch until six hard gates pass."
)


def bound(name):
    rel = "pipeline/reports/" + name
    return {"path": rel, "sha256": hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()}


def indexed(rows):
    result = {(r["scene"], int(r["ann_id"])): r for r in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate scene/annotation key")
    return result


def main():
    if OUTPUT.exists():
        raise ValueError("Summary already exists")
    first, second, repeat = [
        json.loads((REPORTS / name).read_text(encoding="utf-8"))
        for name in INPUTS[1:]
    ]
    if [d["transform_seed"] for d in (first, second, repeat)] != [1999, 2000, 1999]:
        raise ValueError("Transform seed identity changed")
    a, b, c = (indexed(d["rows"]) for d in (first, second, repeat))
    if set(a) != set(b) or set(a) != set(c) or len(a) != 128:
        raise ValueError("Native population keys differ")
    cohort = {(r["scene"], int(r["ann_id"])) for r in first["population_selected"]}
    if len(cohort) != 32 or any(key not in a for key in cohort):
        raise ValueError("Preregistered cohort incomplete")
    same = sum(a[key]["batch_input_sha256"] == c[key]["batch_input_sha256"] for key in a)
    changed = sum(a[key]["batch_input_sha256"] != b[key]["batch_input_sha256"] for key in a)
    if same != 128 or changed != 128:
        raise ValueError("Same/independent transform fingerprint expectation changed")
    exposed = {
        str(seed): sorted(f"{scene}:{ann}" for scene, ann in cohort
                          if group[(scene, ann)]["selected_seed_is_context"])
        for seed, group in ((1999, a), (2000, b))
    }
    eligible = sum(r["unmatched_non_target_context"] for r in c.values())
    same_instance = sum(r["same_instance_zero_control_eligible"] for r in c.values())
    if eligible != 2140 or same_instance:
        raise ValueError("Instance-matched control feasibility changed")
    output = {
        "contract": "m95_seed_exact_input_summary_v1",
        "admission": False,
        "input_evidence": [bound(name) for name in INPUTS],
        "all_native_rows": 128,
        "prespecified_cohort": len(cohort),
        "same_seed_exact_input_hashes": same,
        "independent_seed_changed_input_hashes": changed,
        "selected_context_keys": exposed,
        "selected_context_failures": {
            str(seed): sum(group[(scene, ann)]["selected_seed_is_context"]
                           and group[(scene, ann)]["selected_mask_iou"] <= .5
                           for scene, ann in cohort)
            for seed, group in ((1999, a), (2000, b))
        },
        "context_exposure_changed_keys": sorted(
            f"{scene}:{ann}" for scene, ann in cohort
            if a[(scene, ann)]["selected_seed_is_context"]
            != b[(scene, ann)]["selected_seed_is_context"]),
        "outcome_changed_keys": sorted(
            f"{scene}:{ann}" for scene, ann in cohort
            if (a[(scene, ann)]["selected_mask_iou"] > .5)
            != (b[(scene, ann)]["selected_mask_iou"] > .5)),
        "unmatched_non_target_context_seeds": eligible,
        "same_instance_zero_target_control_seeds": same_instance,
        "limitations": (
            "Fingerprint covers recorded collated tensors, not hidden runtime state. "
            "Transform-repeat outcomes are observational; no trained intervention or "
            "native new-mechanism backward. Native class-context labels leave no "
            "same-physical-instance zero-target controls, so count/logit placebo "
            "cannot identify an instance-role mechanism."
        ),
    }
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    row = next(r for r in data["candidates"] if r["id"] == "m95-sample-context-support")
    if row["stage"] != "diagnosis":
        raise ValueError("Candidate stage changed")
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    row["latest_progress"] = (
        stamp + ": Frozen 32-key native TRAIN cohort replayed with input fingerprints "
        "and physical-instance binding. Same-seed 128/128 input hashes and outcomes "
        "stable; independent seed 128/128 hashes changed. Selected context exposure "
        "4/32 in each draw, all four IoU<=0.5; exposed-key overlap 3/5, with two "
        "exposure and four success-status changes across draws. Across all 128 "
        "expressions, 2140 eligible context seeds have zero same-instance zero-target "
        "placebos. This is observational and makes the proposed exact instance-matched "
        "placebo impossible; no candidate mechanism, resources or admission."
    )
    row["next_action"] = NEXT
    new_evidence = [bound(name) for name in INPUTS] + [bound(OUTPUT.name)]
    paths = {item["path"] for item in row["evidence"]}
    row["evidence"].extend(item for item in new_evidence if item["path"] not in paths)
    data["next_action"] = NEXT
    data["updated_at"] = stamp
    data["design_cycle"] = {
        "timestamp": stamp,
        "stop_reason": "No candidate passed admission; one evidence-backed route remains at diagnosis after its proposed exact placebo proved infeasible.",
        "attempted_ids": [row["id"]],
        "evidence": new_evidence,
        "blocker": "Internal control design and new mechanism implementation, not an external GPU blocker.",
        "resume_condition": NEXT,
        "admissions": 0,
    }
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({key: output[key] for key in
                      ("prespecified_cohort", "selected_context_keys",
                       "same_instance_zero_target_control_seeds")}))


if __name__ == "__main__":
    main()
