"""Frozen same-forward logit audit of target support uncovered by all queries."""
import argparse
import json
from pathlib import Path
from statistics import median as sample_median

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, FRAGMENT_SHA, MANIFEST_SHA, POPULATION_SHA,
    PRODUCER_SHA, sha,
)


def analyze(capture_path, artifact_root, fragment_path, population_path):
    import torch

    for path, expected in ((capture_path, CAPTURE_SHA), (fragment_path, FRAGMENT_SHA),
                           (population_path, POPULATION_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Frozen source differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
    population = json.loads(population_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256
            or fragment["capture_sha256"] != CAPTURE_SHA
            or population["capture_sha256"] != CAPTURE_SHA):
        raise ValueError("Frozen capture provenance differs")
    limited = {r["manifest_index"] for r in population["limited_rows"]}
    controls = {r["manifest_index"] for r in population["control_rows"]}
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    if len(limited) != 16 or len(controls) != 16 or len(fragmented) != 4:
        raise ValueError("Frozen cohorts differ")
    source = {r["manifest_index"]: r for r in capture["rows"]}
    pending = limited | controls
    results = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx not in pending:
                continue
            row = source[idx]
            if (artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != row["scene"]
                    or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
                raise ValueError(f"Native identity differs: {idx}")
            logits = artifact["query_mask_logits"]
            masks = artifact["query_masks"].bool()
            target = artifact["target_union"].bool()
            if (logits.shape != masks.shape or logits.shape != (128, target.numel())
                    or not bool(target.any()) or not bool(torch.isfinite(logits).all())
                    or not torch.equal(logits > 0, masks)):
                raise ValueError(f"Native logit/mask contract differs: {idx}")
            maxima = logits.max(dim=0).values
            uncovered = ~masks.any(dim=0)
            missing_target = maxima[uncovered & target]
            missing_background = maxima[uncovered & ~target]
            def median(values):
                return float(values.median()) if values.numel() else None
            results[idx] = {
                "manifest_index": idx, "scene": row["scene"], "ann_id": row["ann_id"],
                "target_size": int(target.sum()),
                "uncovered_target": int(missing_target.numel()),
                "uncovered_background": int(missing_background.numel()),
                "target_max_logit_median": median(missing_target),
                "background_max_logit_median": median(missing_background),
                "target_near_zero": int(((missing_target >= -.5) &
                                         (missing_target <= 0)).sum()),
                "background_near_zero": int(((missing_background >= -.5) &
                                             (missing_background <= 0)).sum()),
            }
            if missing_target.numel() and missing_background.numel():
                results[idx]["paired_median_delta"] = (
                    results[idx]["target_max_logit_median"]
                    - results[idx]["background_max_logit_median"])
            else:
                results[idx]["paired_median_delta"] = None
            pending.remove(idx)
    if pending:
        raise ValueError(f"Missing native rows: {sorted(pending)}")
    groups = {}
    for name, ids in (("fragmented", fragmented),
                      ("other_limited", limited - fragmented),
                      ("covered_controls", controls)):
        rows = [results[i] for i in sorted(ids)]
        paired = [r for r in rows if r["paired_median_delta"] is not None]
        total = sum(r["uncovered_target"] for r in rows)
        background = sum(r["uncovered_background"] for r in rows)
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "paired_expressions": len(paired),
            "uncovered_target": total, "uncovered_background": background,
            "target_near_zero_fraction": (
                sum(r["target_near_zero"] for r in rows) / total if total else None),
            "background_near_zero_fraction": (
                sum(r["background_near_zero"] for r in rows) / background
                if background else None),
            "median_paired_delta": (
                sample_median(r["paired_median_delta"] for r in paired)
                if paired else None),
            "rows": rows,
        }
    return {
        "contract": "m95_uncovered_logit_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "fragment_sha256": FRAGMENT_SHA,
        "population_sha256": POPULATION_SHA, "groups": groups,
        "limits": "TRAIN GT-localized frozen-logit audit, not a causal mechanism, efficacy or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "fragment", "population", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.fragment, args.population)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({key: {k: v for k, v in value.items() if k != "rows"}
                      for key, value in result["groups"].items()}))


if __name__ == "__main__":
    main()
