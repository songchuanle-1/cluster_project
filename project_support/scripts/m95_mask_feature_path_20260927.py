"""Audit M95's final native mask-loss path on frozen TRAIN features."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from m95_native_mask_population_20260927 import cohorts
from m95_positive_coverage_20260927 import choose
from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

POPULATION_SHA = "71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea"
POSITIVE_SHA = "a81b30f58c039cf52bc26c00e345408113c96a935fd0290a7502e799f5a0c7ce"
LOSS_SHA = "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"
LOGIT_ATOL = 1e-4


def evaluate(row, artifact, norm_weight, norm_bias, criterion):
    import torch
    import torch.nn.functional as F

    if (artifact["artifact_contract"] != "m95_manifest_native_query_artifact_v1"
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["manifest_index"] != row["manifest_index"]
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
        raise ValueError("Frozen artifact identity differs")
    q = artifact["identity_query"]["query_states"].detach().float().requires_grad_(True)
    f = artifact["features"]["final"].detach().float().requires_grad_(True)
    saved = artifact["query_mask_logits"].float()
    if q.shape != (128, 256) or f.ndim != 2 or f.shape[1] != 256:
        raise ValueError("Query/feature shape differs")
    logits = F.layer_norm(q, (256,), norm_weight, norm_bias) @ f.T
    max_error = float((logits.detach() - saved).abs().max())
    if not torch.allclose(logits.detach(), saved, atol=LOGIT_ATOL, rtol=0):
        raise ValueError(f"Frozen final mask logits mismatch: {max_error}")
    positive = [i for i, v in enumerate(row["native_positive"]) if v]
    if not positive or any(
        bool(artifact["native_positive"][i]) != (i in positive)
        for i in range(128)
    ):
        raise ValueError("Matcher-positive binding differs")
    selected = choose(row)
    if selected not in positive:
        raise ValueError("Best matched-positive query differs")
    target = artifact["target_union"].bool()
    if target.shape != (f.shape[0],):
        raise ValueError("Target support differs")
    idx = torch.tensor(positive, dtype=torch.long)
    targets = target.float().unsqueeze(0).repeat(len(positive), 1)
    scores = artifact["query_scores"].detach().float().view(-1, 1)
    bce, dice, _ = criterion.loss_masks(
        [logits], [scores], [{"masks": targets}],
        [(idx, torch.arange(len(positive)))],
        torch.tensor([len(positive)], dtype=torch.float),
    )
    (bce + dice).backward()
    if q.grad is None or f.grad is None:
        raise ValueError("Native loss did not reach source")
    return {
        "manifest_index": row["manifest_index"],
        "scene": row["scene"],
        "selected_query": selected,
        "matched_queries": len(positive),
        "logit_max_abs_error": max_error,
        "query_grad_norm": float(q.grad[selected].norm()),
        "feature_grad_norm": float(f.grad.norm()),
        "target_feature_grad_norm": float(f.grad[target].norm()),
        "query_finite": bool(torch.isfinite(q.grad).all()),
        "feature_finite": bool(torch.isfinite(f.grad).all()),
        "loss": float((bce + dice).detach()),
    }


def analyze(capture_path, artifact_root, checkpoint_path, loss_path,
            population_path, positive_path):
    import torch

    for path, expected in (
        (capture_path, CAPTURE_SHA), (checkpoint_path, CHECKPOINT_SHA),
        (loss_path, LOSS_SHA), (population_path, POPULATION_SHA),
        (positive_path, POSITIVE_SHA),
    ):
        if sha(path) != expected:
            raise ValueError(f"Frozen source SHA256 differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256):
        raise ValueError("Frozen capture provenance differs")
    limited, controls = cohorts(capture["rows"])
    if len(limited) != 16 or len(controls) != 16:
        raise ValueError("Frozen cohort size differs")
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)["model"]
    prefix = "dec.decoder_layers.5.out_norm."
    weight, bias = state[prefix + "weight"].detach().float(), state[prefix + "bias"].detach().float()
    if weight.shape != (256,) or bias.shape != (256,):
        raise ValueError("M95 learned final out_norm differs")
    norm_sha = hashlib.sha256(weight.numpy().tobytes() + bias.numpy().tobytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("m95_native_loss", loss_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    criterion = module.Criterion.__new__(module.Criterion)
    pending = limited | controls
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    result = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen artifact SHA256 differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in pending:
                result[index] = evaluate(rows[index], artifact, weight, bias, criterion)
                pending.remove(index)
    if pending:
        raise ValueError(f"Missing {len(pending)} cohort artifacts")
    def summarize(ids):
        group = [result[i] for i in sorted(ids)]
        return {
            "expressions": len(group), "scenes": len({r["scene"] for r in group}),
            "finite_nonzero_query": sum(r["query_finite"] and r["query_grad_norm"] > 0 for r in group),
            "finite_nonzero_feature": sum(r["feature_finite"] and r["feature_grad_norm"] > 0 for r in group),
            "max_logit_error": max(r["logit_max_abs_error"] for r in group),
            "rows": group,
        }
    return {
        "contract": "m95_mask_feature_path_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "checkpoint_sha256": CHECKPOINT_SHA,
        "out_norm_state_sha256": norm_sha, "out_norm_key_prefix": prefix,
        "logit_atol": LOGIT_ATOL, "limited": summarize(limited),
        "size_matched_controls": summarize(controls),
        "limits": "Frozen M95 final-mask subgraph only; source gradients do not establish causal representation deficit, full candidate backward or training benefit.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "checkpoint", "loss", "population", "positive", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root, args.checkpoint,
                     args.loss, args.population, args.positive)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {j: v for j, v in report[k].items() if j != "rows"}
                      for k in ("limited", "size_matched_controls")}))


if __name__ == "__main__":
    main()
