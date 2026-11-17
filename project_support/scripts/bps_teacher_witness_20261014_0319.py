"""Actual native teacher-pair slack and a preregistered coupled contrast."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import sys

from bps_native_20261014_0319 import (
    PIPE, fingerprint, get_batch, parameters, setup, sha)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    torch, gorilla, dataset, model, state, frozen, sources, full_name = setup(args.token)
    stress = json.loads((PIPE / ("bps_stress_" + args.token + ".json")).read_text())
    manifest_path = PIPE / ("bps_stress_" + args.token + ".manifest.json")
    assert sha(manifest_path) == stress["frozen_manifest_sha256"]
    assert sha(PIPE / ("bps_stress_" + args.token + ".json")) == "62c482431273e48e91e405c7c682e9a9901cfed43b57b8e52984dfa6fa230e5e"
    selections = frozen + stress["frozen"]
    assert len({row["native_group"] for row in selections}) == 10
    model.eval()
    loss_module = sys.modules[full_name + ".loss"]
    original = loss_module.support_excess
    held = {}
    def capture(*values):
        value = original(*values)
        held["args"] = values
        return value
    loss_module.support_excess = capture
    # Fixture costs come from two actual 1D support-gap slabs, not label edits.
    points = torch.tensor([-1., 1.], dtype=torch.float64, device="cuda")
    costs = torch.stack([
        ((torch.relu(lower - points) + torch.relu(points - upper)) / (upper - lower)).square()
        for lower, upper in ((-2., .5), (-.5, 2.))], -1)
    gt_fixture, wrong_fixture = costs[0], costs[1]
    fixture_old = float(torch.relu(wrong_fixture - gt_fixture).min())
    fixture_joint = float(torch.relu((wrong_fixture + gt_fixture).min() - 2 * gt_fixture.min()))
    assert fixture_old == 0 and fixture_joint > 0
    rows, counts = [], Counter()
    progress = PIPE / ("bps_teacher_witness_" + args.token + ".progress.jsonl")
    try:
        with progress.open("x") as stream:
            for selection in selections:
                batch = get_batch(torch, gorilla, dataset, [selection["native_group"]])
                gorilla.set_random_seed(1999)
                model.zero_grad(set_to_none=True)
                held.clear()
                total, parts = model(batch, mode="loss")
                masks, targets, indices, num_boxes, supports = held["args"]
                details = []
                def objective(joint=False, record=False):
                    value = sum(mask.sum().double() * 0 for mask in masks)
                    for bi, (mask, target, (src, tgt), support) in enumerate(
                            zip(masks, targets, indices, supports)):
                        if not support["costs"] or not len(src):
                            continue
                        masses = support["counts"].to(mask.device)
                        prediction = mask[src].sigmoid().double() * masses
                        prediction = prediction / prediction.sum(-1, keepdim=True).clamp_min(1e-12)
                        gt = target["masks"][tgt].double() * masses
                        gt = gt / gt.sum(-1, keepdim=True)
                        terms = []
                        for event_index, cost in enumerate(support["costs"]):
                            cost = cost.to(mask.device)
                            eq, egt = prediction @ cost, gt @ cost
                            minimum_gt = egt.min(-1).values
                            original_excess, selected = torch.relu(eq - egt).min(-1)
                            coupled = torch.relu((eq + egt).min(-1).values - 2 * minimum_gt)
                            best = egt == minimum_gt.unsqueeze(-1)
                            restricted = torch.relu(eq - egt).masked_fill(~best, float("inf")).min(-1).values
                            if record:
                                selected_gt = egt.gather(-1, selected.unsqueeze(-1)).squeeze(-1)
                                for qi, query in enumerate(src.tolist()):
                                    details.append({
                                        "batch": bi, "ann_id": int(batch["ann_ids"][bi]),
                                        "query": query, "event_index": event_index,
                                        "pair_count": cost.shape[-1],
                                        "minimum_gt_cost": float(minimum_gt[qi].detach()),
                                        "selected_pair_gt_cost": float(selected_gt[qi].detach()),
                                        "original_excess": float(original_excess[qi].detach()),
                                        "best_gt_proxy_set_excess": float(restricted[qi].detach()),
                                        "coupled_contrast": float(coupled[qi].detach()),
                                        "gt_self_contrast": float(torch.relu(
                                            (egt[qi] + egt[qi]).min() - 2 * egt[qi].min()).detach())})
                            terms.append(coupled if joint else original_excess)
                        value = value + torch.stack(terms, -1).mean(-1).sum()
                    return value / num_boxes
                original_loss = objective(record=True)
                assert abs(float(original_loss.detach()) - float(parts["between_support_loss"].detach())) <= 1e-6
                derivatives = []
                losses = []
                for repeat in (0, 1):
                    coupled = objective(joint=True)
                    gradients = torch.autograd.grad(coupled, masks, retain_graph=True)
                    assert bool(torch.isfinite(coupled).all())
                    assert all(bool(torch.isfinite(g).all()) for g in gradients)
                    losses.append(float(coupled.detach()))
                    derivatives.append([g.detach().clone() for g in gradients])
                assert losses[0] == losses[1]
                assert all(torch.equal(a, b) for a, b in zip(*derivatives))
                named = parameters(model)
                reached = torch.autograd.grad(coupled, [p for _, p in named],
                                              retain_graph=True, allow_unused=True)
                assert all(g is None or bool(torch.isfinite(g).all()) for g in reached)
                nonzero = sum(g is not None and bool((g != 0).any()) for g in reached)
                for detail in details:
                    counts["matched_query_events"] += 1
                    counts["old_zero_best_gt_positive_exact"] += (
                        detail["original_excess"] == 0 and detail["best_gt_proxy_set_excess"] > 0)
                    counts["old_zero_best_gt_positive_over_noise"] += (
                        detail["original_excess"] == 0 and detail["best_gt_proxy_set_excess"] > 1e-6)
                    counts["old_zero_joint_positive_exact"] += (
                        detail["original_excess"] == 0 and detail["coupled_contrast"] > 0)
                    counts["old_zero_joint_positive_over_noise"] += (
                        detail["original_excess"] == 0 and detail["coupled_contrast"] > 1e-6)
                    assert detail["gt_self_contrast"] == 0
                row = {"group": selection["native_group"], "scene": selection["scene"],
                       "input_sha256": fingerprint(batch), "details": details,
                       "old_loss": float(original_loss.detach()), "joint_contrast_loss": losses[0],
                       "joint_same_capture_repeat_exact": True,
                       "joint_mask_gradient_norm": sum(float(g.double().square().sum())
                                                       for g in derivatives[0]) ** .5,
                       "joint_original_parameter_nonzero_tensors": nonzero}
                rows.append(row)
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(json.dumps({"group": row["group"], "query_events": len(details),
                                  "old": row["old_loss"], "joint": losses[0],
                                  "nonzero_original_tensors": nonzero}), flush=True)
                held.clear()
                del total, parts, original_loss, coupled, gradients, derivatives, reached, masks, targets
                del indices, supports, named, batch
                gc.collect()
                torch.cuda.empty_cache()
    finally:
        loss_module.support_excess = original
    result = {"tick_token": args.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "source_manifest": sources,
              "rows": rows, "counts": dict(counts), "native_forward_count": len(rows),
              "fixture": {"old_loss": fixture_old, "joint_contrast": fixture_joint},
              "optimizer_steps": 0,
              "scope": "Native component-only GT-proxy witness slack, not physical-witness truth, an independent revised model, efficacy or admission."}
    output = PIPE / ("bps_teacher_witness_" + args.token + ".json")
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "counts": dict(counts)}), flush=True)


if __name__ == "__main__":
    main()
