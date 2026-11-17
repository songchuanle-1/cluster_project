"""Standalone native geometry-loss prototype on unchanged M95 masks."""
import ast
import hashlib
import itertools
import json
from pathlib import Path

PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")
SOURCE = PIPE / "native_role_direction_v2_20261014_0010.py"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "c5a9c1157421bd9cc386a2da160ac1cf0ae376948ddff5b7f0c6808be690d749")
META = {}


def native_cohort(dataset, original):
    inventory_path = PIPE / "between_pair_typed_inventory_66fa1e81aec94d5eb10265ea533669ac.json"
    assert hashlib.sha256(inventory_path.read_bytes()).hexdigest() == (
        "93ad4419a9eaa06e1fdeb24929b06bf099f9126b5a7fe4f9b67564c62521995d")
    inventory = json.loads(inventory_path.read_text())
    manifest_path = PIPE / "between_pair_typed_66fa1e81aec94d5eb10265ea533669ac.manifest.json"
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == inventory["frozen_manifest_sha256"]
    frozen = json.loads(manifest_path.read_text())["frozen"]
    graphs_path = Path("/data3/songcl/data/data_cluster/scanrefer/scene_graphs_new_train.json")
    assert hashlib.sha256(graphs_path.read_bytes()).hexdigest() == inventory["source_hashes"]["graphs"]
    graphs = json.loads(graphs_path.read_text())
    selections = {}
    for row in frozen:
        case = next(c for c in inventory["geometry"]
                    if c["scene"] == row["scene"] and c["ann_id"] == row["ann_id"])
        graph = graphs[row["scene"]][str(row["ann_id"])]
        tokens = graph["utterance"].split()
        events = {}
        for edge in graph["graph_edge"]:
            if 0 not in (edge["obj_idx"], edge["sub_idx"]) or "between" not in edge["relation"].lower():
                continue
            positions = tuple(i for i in edge.get("relation_idx", [])
                              if 0 <= i < len(tokens) and tokens[i].lower() == "between")
            other = edge["sub_idx"] if edge["obj_idx"] == 0 else edge["obj_idx"]
            if not positions or other == 0:
                continue
            events.setdefault(positions, set()).add(other)
        META[(row["scene"], row["ann_id"])] = {
            "references": {r["node_id"]: r for r in case["references"]},
            "events": [{"between_token_positions": list(key), "reference_nodes": sorted(value)}
                       for key, value in sorted(events.items())],
            "target_ids": row["target_ids"]}
        group = row["native_group"]
        assert [int(a["ann_id"]) for a in dataset.scene_inputs[group]] == row["group_ann_ids"]
        selections[group] = {"group": group, "scene": row["scene"],
                             "ann_ids": row["group_ann_ids"], "families": ["typed_between"],
                             "trigger_ann_ids": [row["ann_id"]]}
    assert len(selections) == 8
    return selections


def prototype(model, native, held, batch, selection, torch):
    import numpy as np
    pred = held["pred"]
    masks = pred["masks"]
    assert isinstance(masks, torch.Tensor)
    device = masks.device
    sp = batch["superpoints"].detach().cpu().numpy().astype(np.int64)
    xyz = batch["coords_float"].detach().cpu().numpy().astype(np.float64)
    labels = batch["sp_ins_labels"][0].detach().cpu().numpy().astype(np.int64)
    counts = np.bincount(sp, minlength=len(labels))
    centers = np.stack([np.bincount(sp, weights=xyz[:, d], minlength=len(labels))
                        for d in range(3)], axis=1) / counts[:, None]
    assert bool(np.isfinite(centers).all()) and bool((counts > 0).all())
    constants = torch.as_tensor(centers, dtype=torch.float64, device=device)
    masses = torch.as_tensor(counts, dtype=torch.float64, device=device)
    point_labels = labels[sp]
    targets, indices, num_boxes = native[3], native[4], float(native[5])
    cases = []
    structures = {}
    for bi, aid in enumerate(map(int, batch["ann_ids"])):
        key = (selection["scene"], aid)
        if key not in META:
            cases.append({"batch": bi, "ann_id": aid, "status": "companion_exact_bypass"})
            continue
        metadata = META[key]
        events = []
        schema = []
        for event in metadata["events"]:
            pairs = []
            missing = []
            for left, right in itertools.combinations(event["reference_nodes"], 2):
                a_ids = metadata["references"].get(left, {}).get("candidate_ids", [])
                b_ids = metadata["references"].get(right, {}).get("candidate_ids", [])
                for a, b in itertools.product(a_ids, b_ids):
                    if a == b:
                        continue
                    pa, pb = xyz[point_labels == a], xyz[point_labels == b]
                    if not len(pa) or not len(pb):
                        missing.append({"a": a, "b": b, "status": "native_support_missing"})
                        continue
                    delta = pb.mean(0) - pa.mean(0)
                    norm = float(np.linalg.norm(delta))
                    if norm == 0:
                        continue
                    axis = delta / norm
                    lower, upper = float((pa @ axis).max()), float((pb @ axis).min())
                    if lower >= upper:
                        missing.append({"a": a, "b": b, "status": "overlap_gap"})
                        continue
                    pairs.append((torch.as_tensor(axis, dtype=torch.float64, device=device),
                                  lower, upper))
            schema.append({**event, "valid_candidate_pairs": len(pairs), "unavailable": missing})
            if pairs:
                events.append(pairs)
        cases.append({"batch": bi, "ann_id": aid, "events": schema,
                      "unknown_event_count": len(schema) - len(events),
                      "status": "proxy_events_available" if events else "no_resolved_proxy_event"})
        if events:
            structures[bi] = events

    def center(weights):
        weighted = weights.double() * masses
        return weighted @ constants / weighted.sum(-1, keepdim=True).clamp_min(1e-12)

    def values(c, events, flat=False):
        event_values = []
        all_values = []
        for pairs in events:
            candidate = torch.stack([
                ((torch.relu(lower - c @ axis) + torch.relu(c @ axis - upper))
                 / (upper - lower)).square() for axis, lower, upper in pairs], dim=-1)
            event_values.append(candidate.min(-1).values)
            all_values.append(candidate)
        return (torch.cat(all_values, dim=-1).min(-1).values if flat else
                torch.stack(event_values, dim=-1).mean(-1))

    def objective(tensor, flat=False):
        total = tensor.sum().double() * 0
        for bi, events in structures.items():
            src = indices[bi][0]
            unpadded = tensor[bi].masked_select((~pred["batch_mask"][bi]).unsqueeze(0)).view(
                tensor.shape[1], -1)
            assert unpadded.shape[-1] == len(labels)
            total = total + values(center(unpadded[src].sigmoid()), events, flat).sum()
        return total / num_boxes

    conditions = {}
    derivatives = {}
    for name, flat in (("event_grouped", False), ("identity", False), ("flat_union", True)):
        observed, grads = [], []
        for repeat in (0, 1):
            leaf = masks.detach().clone().requires_grad_()
            loss = objective(leaf, flat)
            gradient, = torch.autograd.grad(loss, leaf)
            assert bool(torch.isfinite(loss)) and bool(torch.isfinite(gradient).all())
            observed.append(float(loss.detach()))
            grads.append(gradient.detach())
        assert observed[0] == observed[1] and torch.equal(grads[0], grads[1])
        derivatives[name] = grads[0]
        conditions[name] = {"loss": observed[0], "mask_gradient_norm": float(grads[0].double().norm()),
                            "same_capture_repeat_exact": True}
    assert conditions["event_grouped"] == conditions["identity"]
    assert torch.equal(derivatives["event_grouped"], derivatives["identity"])
    attached = objective(masks)
    assert abs(float(attached.detach()) - conditions["event_grouped"]["loss"]) <= 1e-6
    query_gradient, = torch.autograd.grad(attached, held["decoder_query"], retain_graph=True)
    assert bool(torch.isfinite(query_gradient).all())
    for case in cases:
        bi = case["batch"]
        if bi not in structures:
            continue
        target = targets[bi]["masks"]
        assert torch.equal(target, target[:1].expand_as(target))
        events = structures[bi]
        with torch.no_grad():
            gt_center = center(target[0].double())
            case["gt_mask_proxy_loss"] = float(values(gt_center, events))
            case["native_positive_query_proxy_losses"] = values(
                center(masks[bi, indices[bi][0], :len(labels)].sigmoid()), events).tolist()
            wrong = []
            for oid in np.unique(labels):
                if oid < 0 or oid == 199 or int(oid) in META[(selection["scene"], case["ann_id"])]["target_ids"]:
                    continue
                weights = torch.as_tensor(labels == oid, dtype=torch.float64, device=device)
                wrong.append({"instance_id": int(oid), "proxy_loss": float(values(center(weights), events))})
            case["other_native_instance_mask_proxy_losses"] = wrong
    return {
        "conditions": conditions, "final_query_gradient_norm": float(query_gradient.double().norm()),
        "final_query_gradient_finite": True, "cases": cases, "optimizer_steps": 0,
        "scope": "Standalone prototype on original native masks/parameters; partial unknown events and SP-majority reference approximation are not true witness labels, independent candidate backward, efficacy or admission."}


module = ast.parse(SOURCE.read_text())
main = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "main")
for index, node in reversed(list(enumerate(main.body))):
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "dataset" for target in node.targets):
        main.body[index + 1:index + 1] = ast.parse("cohort = native_cohort(dataset, cohort)").body
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "held" for target in node.targets):
        main.body[index + 1:index + 1] = ast.parse(
            "query_hook = model.dec.decoder_layers[-1].register_forward_hook(lambda module, inputs, output: held.update(decoder_query=output[0]))").body
for node in ast.walk(main):
    if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "name":
        if isinstance(node.iter, ast.Tuple) and any(
                isinstance(value, ast.Constant) and value.value == "remove_other_disjoint"
                for value in node.iter.elts):
            node.iter.elts = [ast.Constant(value="original"), ast.Constant(value="identity")]
    if isinstance(node, ast.With):
        for loop in node.body:
            if not isinstance(loop, ast.For):
                continue
            for index, statement in enumerate(loop.body):
                if isinstance(statement, ast.Assign) and any(
                        isinstance(target, ast.Name) and target.id == "row" for target in statement.targets):
                    loop.body[index:index] = ast.parse(
                        "between_readout = prototype(model, native, held, batch, selection, torch)").body
                    break
    if isinstance(node, ast.Dict) and any(
            isinstance(key, ast.Constant) and key.value == "injected_original_loss_delta"
            for key in node.keys if key is not None):
        node.keys.append(ast.Constant(value="between_readout"))
        node.values.append(ast.Name(id="between_readout", ctx=ast.Load()))
    if isinstance(node, ast.Try) and node.finalbody:
        node.finalbody += ast.parse("query_hook.remove()").body
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        node.value = node.value.replace("native_role_direction_v2_", "between_pair_native_")
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__,
      "native_cohort": native_cohort, "prototype": prototype})
