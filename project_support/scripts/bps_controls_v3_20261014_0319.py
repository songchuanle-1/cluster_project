"""Independent candidate matched controls on identical native forwards."""
import argparse
import copy
from datetime import datetime, timezone
import gc
import itertools
import json
import sys

from bps_native_v2_20261014_0319 import (
    PIPE, TOKEN, fingerprint, get_batch, parameters, setup, sha)


def disjoint_supports(torch, batch, supports, catalog, readout):
    import numpy as np
    sp = batch["superpoints"].cpu().numpy()
    xyz = batch["coords_float"].cpu().numpy().astype(np.float64)
    offsets = batch["batch_offsets"].tolist()
    alternatives, eligibility = [], []
    expression = 0
    for scene_index, (scene, length) in enumerate(zip(batch["scan_ids"], batch["scenes_len"])):
        start, end = offsets[scene_index:scene_index + 2]
        selected = (sp >= start) & (sp < end)
        local_sp, points = sp[selected] - start, xyz[selected]
        labels = batch["sp_ins_labels"][scene_index].cpu().numpy()
        point_labels = labels[local_sp]
        geometry = {int(oid): points[point_labels == oid]
                    for oid in np.unique(labels) if oid >= 0 and oid != 199}
        for _ in range(int(length)):
            support = supports[expression]
            alternative = {**support, "costs": [], "pairs": []}
            aid = int(batch["ann_ids"][expression])
            record = catalog["records"].get(str(scene) + "/" + str(aid))
            target_ids = set(map(int, batch["object_idss"][expression]))
            reference_ids = set()
            if record:
                categories = {ref["category"] for event in record["events"]
                              for ref in event["references"] if ref["category"] is not None}
                reference_ids = {int(oid) for oid, category in catalog["instances"][str(scene)].items()
                                 if category in categories}
            pool = sorted(set(geometry) - target_ids - reference_ids)
            fields, pairs = [], []
            needed = max([c.shape[-1] for c in support["costs"]], default=0)
            centers = support["centers"].numpy()
            if needed:
                for a, b in itertools.combinations(pool, 2):
                    pa, pb = geometry[a], geometry[b]
                    delta = pb.mean(0) - pa.mean(0)
                    norm = float(np.linalg.norm(delta))
                    if norm == 0:
                        continue
                    axis = delta / norm
                    lower, upper = float((pa @ axis).max()), float((pb @ axis).min())
                    if lower >= upper:
                        continue
                    projection = centers @ axis
                    fields.append(((np.maximum(lower - projection, 0) +
                                    np.maximum(projection - upper, 0)) / (upper - lower)) ** 2)
                    pairs.append([a, b])
                    if len(fields) == needed:
                        break
            eligible = needed > 0 and len(fields) >= needed
            if eligible:
                alternative["costs"] = [torch.as_tensor(np.stack(fields[:c.shape[-1]], -1),
                                                        dtype=torch.float64)
                                         for c in support["costs"]]
                alternative["pairs"] = [pairs[:c.shape[-1]] for c in support["costs"]]
            alternatives.append(alternative)
            eligibility.append({"expression": expression, "needed_pairs": needed,
                                "available_disjoint_pairs": len(fields),
                                "matched": eligible, **readout[expression]})
            expression += 1
    return alternatives, eligibility


def radial_loss(torch, masks, targets, indices, num_boxes, supports):
    total = sum(m.sum().double() * 0 for m in masks)
    missing = []
    for bi, (mask, target, (src, tgt), support) in enumerate(zip(masks, targets, indices, supports)):
        if not support["costs"] or not len(src):
            continue
        counts = support["counts"].to(mask.device)
        centers = support["centers"].to(mask.device)
        gt = target["masks"][tgt].double() * counts
        gt = gt / gt.sum(-1, keepdim=True)
        center = gt @ centers
        square = (centers.unsqueeze(0) - center.unsqueeze(1)).square().sum(-1)
        variance = (gt * square).sum(-1, keepdim=True)
        if bool((variance == 0).any()):
            missing.append(bi)
            continue
        cost = square / variance
        prediction = mask[src].sigmoid().double() * counts
        prediction = prediction / prediction.sum(-1, keepdim=True).clamp_min(1e-12)
        total = total + torch.relu((prediction * cost).sum(-1) - (gt * cost).sum(-1)).sum()
    return total / num_boxes, missing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    torch, gorilla, dataset, model, state, frozen, sources, full_name = setup(args.token)
    model.eval()
    loss_module = sys.modules[full_name + ".loss"]
    operator = loss_module.support_excess
    held = {}
    def capture(*values):
        value = operator(*values)
        held["args"] = values
        held["component"] = value
        return value
    loss_module.support_excess = capture
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs, kwargs: held.update(pred=inputs[0]), with_kwargs=True)
    rows = []
    progress = PIPE / ("bps_controls_v3_" + args.token + ".progress.jsonl")
    torch.cuda.reset_peak_memory_stats()
    try:
        with progress.open("x") as stream:
            for item in frozen:
                batch = get_batch(torch, gorilla, dataset, [item["native_group"]])
                gorilla.set_random_seed(1999)
                held.clear()
                model.zero_grad(set_to_none=True)
                total, parts = model(batch, mode="loss")
                masks, targets, indices, num_boxes, supports = held["args"]
                unpadded = [m.detach().clone().requires_grad_() for m in masks]
                readout = model.between_support.last_readout
                reverse = [{**s, "costs": [cost.flip(-1) for cost in s["costs"]]}
                           for s in supports]
                disjoint, eligibility = disjoint_supports(
                    torch, batch, supports, model.between_support.catalog, readout)
                subset = [{**s, "costs": s["costs"] if e["matched"] else []}
                          for s, e in zip(supports, eligibility)]
                empty = [{**s, "costs": []} for s in supports]
                conditions, gradients = {}, {}
                for name, override, fragmented in (
                        ("coherent", supports, False), ("identity", supports, False),
                        ("reversed_pair_order", reverse, False),
                        ("fragmented_witness", supports, True),
                        ("matched_reference_subset", subset, False),
                        ("disjoint_reference", disjoint, False),
                        ("no_event_bypass", empty, False)):
                    values, derivatives = [], []
                    for repeat in (0, 1):
                        loss = operator(unpadded, targets, indices, num_boxes, override,
                                        fragmented=fragmented)
                        gradient = torch.autograd.grad(loss, unpadded, retain_graph=True)
                        assert bool(torch.isfinite(loss).all())
                        assert all(bool(torch.isfinite(g).all()) for g in gradient)
                        values.append(float(loss.detach()))
                        derivatives.append([g.detach().clone() for g in gradient])
                    assert values[0] == values[1]
                    assert all(torch.equal(a, b) for a, b in zip(*derivatives))
                    gradients[name] = derivatives[0]
                    conditions[name] = {"loss": values[0],
                                        "gradient_l2": sum(float(g.double().square().sum())
                                                           for g in derivatives[0]) ** .5,
                                        "repeat_exact": True}
                assert conditions["coherent"] == conditions["identity"]
                assert conditions["coherent"] == conditions["reversed_pair_order"]
                assert all(torch.equal(a, b) for a, b in
                           zip(gradients["coherent"], gradients["reversed_pair_order"]))
                assert conditions["no_event_bypass"]["loss"] == 0
                assert conditions["no_event_bypass"]["gradient_l2"] == 0
                assert abs(conditions["coherent"]["loss"] - float(parts["between_support_loss"])) <= 1e-6
                # Binary GT is a measure, not an infinite-logit native prediction.
                gt_terms = []
                for target, (src, tgt), support in zip(targets, indices, supports):
                    if not support["costs"] or not len(src):
                        continue
                    counts = support["counts"].to(target["masks"].device)
                    teacher = target["masks"][tgt].double() * counts
                    teacher = teacher / teacher.sum(-1, keepdim=True)
                    for field in support["costs"]:
                        field = field.to(teacher.device)
                        readout_gt = teacher @ field
                        gt_terms.append(torch.relu(readout_gt - readout_gt).min(-1).values)
                gt_self = max([float(term.abs().max()) for term in gt_terms], default=0.)
                assert gt_self == 0
                radial, radial_missing = radial_loss(torch, unpadded, targets, indices, num_boxes, supports)
                radial_grads = torch.autograd.grad(radial, unpadded, retain_graph=True)
                assert all(bool(torch.isfinite(g).all()) for g in radial_grads)
                dot = sum(float((a.double() * b.double()).sum())
                          for a, b in zip(gradients["coherent"], radial_grads))
                radial_norm = sum(float(g.double().square().sum()) for g in radial_grads) ** .5
                denom = conditions["coherent"]["gradient_l2"] * radial_norm
                cosine = dot / denom if denom else None
                wrong_objects = [[199] for _ in batch["object_idss"]]
                wrong = model.between_support.prepare(
                    batch["ann_ids"], batch["scan_ids"], batch["scenes_len"], wrong_objects,
                    batch["superpoints"], batch["coords_float"], batch["batch_offsets"],
                    batch["sp_ins_labels"])
                wrong_loss = float(operator(unpadded, targets, indices, num_boxes, wrong))
                assert wrong_loss == 0
                row = {"group": item["native_group"], "scene": item["scene"],
                       "input_sha256": fingerprint(batch), "expressions": len(batch["ann_ids"]),
                       "conditions": conditions, "gt_self_operator_loss": gt_self,
                       "wrong_target_bypass_loss": wrong_loss,
                       "disjoint_eligibility": eligibility, "readout": readout,
                       "radial_loss": float(radial.detach()), "radial_missing": radial_missing,
                       "radial_gradient_norm": radial_norm, "relational_radial_gradient_cosine": cosine}
                rows.append(row)
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(json.dumps({"group": row["group"], "component": conditions["coherent"]["loss"],
                                  "fragmented": conditions["fragmented_witness"]["loss"],
                                  "disjoint_matched": sum(e["matched"] for e in eligibility)}), flush=True)
                held.clear()
                del total, parts, masks, targets, indices, supports, unpadded, gt_terms
                del gradients, derivatives, gradient, radial, radial_grads, loss
                gc.collect()
                torch.cuda.empty_cache()
    finally:
        hook.remove()
        loss_module.support_excess = operator
    # Prediction and no-event loss checks use the same candidate weights/operator.
    model.load_state_dict(state, strict=True)
    model.eval()
    batch = get_batch(torch, gorilla, dataset, [frozen[0]["native_group"]])
    catalog = model.between_support.catalog
    with torch.no_grad():
        gorilla.set_random_seed(1999)
        before_calls = model.between_support.prepare_calls
        prediction_full = model(batch, mode="predict")
        calls_full = model.between_support.prepare_calls
        gorilla.set_random_seed(1999)
        full_loss, full_parts = model(batch, mode="loss")
        model.between_support.catalog = {"schema_version": 1, "records": {}, "instances": {}}
        gorilla.set_random_seed(1999)
        prediction_empty = model(batch, mode="predict")
        calls_empty = model.between_support.prepare_calls
        gorilla.set_random_seed(1999)
        empty_loss, empty_parts = model(batch, mode="loss")
    model.between_support.catalog = catalog
    prediction_equal = fingerprint(prediction_full) == fingerprint(prediction_empty)
    assert prediction_equal and calls_full == before_calls and calls_empty == calls_full + 1
    original_part_delta = {key: float((value - empty_parts[key]).abs().max())
                           for key, value in full_parts.items()
                           if key not in ("loss", "between_support_loss")}
    assert all(value == 0 for value in original_part_delta.values())
    result = {"tick_token": args.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(__import__("pathlib").Path(__file__)),
              "source_manifest": sources, "rows": rows, "native_forward_count": 12,
              "optimizer_steps": 0, "prediction_catalog_free_exact": prediction_equal,
              "prediction_fingerprint": fingerprint(prediction_full),
              "original_loss_parts_catalog_delta": original_part_delta,
              "empty_catalog_component_loss": float(empty_parts["between_support_loss"]),
              "full_minus_empty_loss": float(full_loss - empty_loss),
              "full_catalog_component_loss": float(full_parts["between_support_loss"]),
              "allocator_peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
              "allocator_peak_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
              "scope": "Matched operator/native controls and prediction bypass; not task benefit or exclusive efficiency."}
    output = PIPE / ("bps_controls_v3_" + args.token + ".json")
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "groups": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
