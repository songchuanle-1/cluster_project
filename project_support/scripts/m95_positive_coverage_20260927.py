"""Native-mask gradient availability for the best matched query."""
import argparse
import importlib.util
import json
from pathlib import Path

from m95_native_mask_backward_20260927 import LOSS_SHA, evaluate
from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)


def choose(row):
    if len(row["native_positive"]) != 128 or len(row["ious"]) != 128:
        raise ValueError("Native query axes differ")
    positives = [q for q, good in enumerate(row["native_positive"]) if good]
    return max(positives, key=lambda q: (row["ious"][q], -q)) if positives else None


def analyze(capture_path, artifact_root, loss_path):
    import torch

    if sha(capture_path) != CAPTURE_SHA or sha(loss_path) != LOSS_SHA:
        raise ValueError("Frozen capture/loss differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    rows = capture["rows"]
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(rows) != 256):
        raise ValueError("Frozen provenance differs")
    limited = {r["manifest_index"]: r for r in rows if max(r["ious"]) <= .5}
    if len(limited) != 16:
        raise ValueError("Limited population differs")
    spec = importlib.util.spec_from_file_location("m95_native_loss_positive", loss_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    criterion = module.Criterion.__new__(module.Criterion)
    pending = set(limited)
    results = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("Native artifact hash differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index not in pending:
                continue
            row = limited[index]
            if artifact["artifact_contract"] != capture["artifact_contract"]:
                raise ValueError("Artifact contract differs")
            q = choose(row)
            if q is None:
                results[index] = {
                    "manifest_index": index, "scene": row["scene"],
                    "selected_positive": bool(row["native_positive"][row["selected_query"]]),
                    "best_positive_query": None,
                }
            else:
                matched_row = {**row, "selected_query": q}
                results[index] = {
                    **evaluate(matched_row, artifact, criterion),
                    "selected_positive": bool(row["native_positive"][row["selected_query"]]),
                    "best_positive_query": q,
                }
            pending.remove(index)
    if pending:
        raise ValueError("Missing limited artifacts")
    output = [results[i] for i in sorted(results)]
    evaluated = [r for r in output if r["best_positive_query"] is not None]
    return {
        "contract": "m95_positive_coverage_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "loss_sha256": LOSS_SHA,
        "limited_expressions": len(output),
        "limited_scenes": len({r["scene"] for r in output}),
        "selected_negative": sum(not r["selected_positive"] for r in output),
        "has_positive": len(evaluated),
        "corrective": sum(r["all_finite"] and r["fn"] == r["fn_correct"]
                          and r["fp"] == r["fp_correct"] for r in evaluated),
        "rows": output,
        "limits": "Oracle readout of existing native matching, no new-model backward/admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--loss", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.loss)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "limited_expressions", "selected_negative", "has_positive", "corrective")}))


if __name__ == "__main__":
    main()
