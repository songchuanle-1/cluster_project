"""Frozen native TRAIN prefixes with all three-scale omission readouts."""
import os
os.environ.update(CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES="0", PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="1")
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
import logging
from pathlib import Path
import signal
import socket
import subprocess
import sys
from scale_terms import branch_terms, shapley

signal.alarm(720)
STAGE = Path(__file__).resolve().parent
manifest = json.loads((STAGE / "scale_manifest.json").read_text())
deadline = datetime.fromisoformat(manifest["deadline_at"])
assert (deadline - datetime.now(timezone.utc)).total_seconds() > 840
assert socket.gethostname() == "dl04-MS-7E06"
ROOT = Path(manifest["root"])


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def gpu():
    row = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
    cells = [v.strip() for v in row.split(",")]
    assert cells[:2] == ["0", "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
    contexts = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
    used = 0
    for line in contexts.splitlines():
        pid, memory = [int(v.strip()) for v in line.split(",")]
        assert pid == os.getpid(), "Foreign GPU context: stop without eviction"
        used += memory
    assert int(cells[4]) + used >= int(cells[2]) - 1024
    return {"gpu": row, "contexts": contexts}


before = gpu()
assert not before["contexts"]
locks = []
progress = {"started_at": datetime.now(timezone.utc).isoformat(), "passed_controls": False, "native_forwards": 0, "native_suffix_replays": 0, "optimizer_steps": 0, "val_forwards": 0, "rows": [], "controls": []}
try:
    for kind in ("training", "diagnostic", "exclusive"):
        handle = open("/tmp/cluster_project_gpu0_" + kind + ".lock", "a+b")
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(handle)
    gpu()
    for name, expected in manifest["source_hashes"].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in manifest["producer_hashes"].items():
        assert sha(STAGE / name) == expected, name
    assert sha(manifest["checkpoint"]) == manifest["checkpoint_sha256"]
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    from tools import train as native_train
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader, Subset
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.25, 0)
    cfg = gorilla.Config.fromfile(str(ROOT / manifest["config"]))
    assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
    assert cfg.dataloader.train.batch_size == 2 and cfg.dataloader.train.num_workers == 4
    cfg.model.data_root = cfg.data.train.data_root = "/home/songcl/data/data/"
    gorilla.set_random_seed(1999)
    package = "framework.model.Quard_model." + manifest["model"]
    native = importlib.import_module(package + ".network")
    hierarchy = importlib.import_module(package + ".hier_postprocess")
    readout = importlib.import_module(package + ".hierarchical_readout")
    model = native.Network(**cfg.model)
    state = torch.load(manifest["checkpoint"], map_location="cpu")["model"]
    extra = set(state) - set(model.state_dict())
    assert extra <= {"text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"}
    assert all(torch.equal(state[name], dict(model.named_buffers())[name]) for name in extra)
    model.load_state_dict({name: value for name, value in state.items() if name not in extra}, strict=True)
    del state
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger("scale-diagnostic"))
    gorilla.set_random_seed(1999)
    groups = [0, 60, 101, 124]
    inputs = list(DataLoader(Subset(dataset, groups), batch_size=1, shuffle=False, num_workers=0, collate_fn=dataset.collate_fn))
    assert len(inputs) == 4
    model.cuda().eval()
    torch.cuda.reset_peak_memory_stats()
    active = [layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active) == 1 and active[0].cluster_message_type == "context"
    cluster = model.dec.cluster_att
    original_canonical = hierarchy.canonical

    def clone(value):
        if torch.is_tensor(value):
            return value.detach().clone()
        if isinstance(value, tuple):
            return tuple(clone(v) for v in value)
        if isinstance(value, list):
            return [clone(v) for v in value]
        return value

    def maximum(left, right):
        return float((left - right).abs().max().detach().cpu())

    def capture(batch):
        held = {"canonical_calls": 0, "term_batches": [], "sum_errors": [], "term_norm_batches": [], "weight_batches": [], "support_batches": []}

        def instrument(points, banks, leaf, parent1, parent2, weights, heads=8):
            actual = original_canonical(points, banks, leaf, parent1, parent2, weights, heads=heads)
            held["canonical_calls"] += 1
            terms = branch_terms(torch, points, banks, leaf, parent1, parent2, weights, readout.support_masks, heads=heads)
            ordered = points * 0
            for term in terms:
                ordered = ordered + term
            error = maximum(ordered, actual)
            assert error <= 1e-6, ("component_reconstruction", error)
            held["term_batches"].append(clone(terms))
            held["sum_errors"].append(error)
            held["term_norm_batches"].append([float(t.norm().cpu()) for t in terms])
            held["weight_batches"].append(weights[:len(leaf)].mean(0).detach().cpu().tolist())
            held["support_batches"].append([int(m.any(-1).sum()) for m in readout.support_masks(leaf, parent1, parent2, [len(bank) for bank in banks])])
            return actual

        def point_hook(module, args, result):
            held["point_input"] = clone(args[0])
            held["point_mask"] = clone(args[2])
            held["point_message"] = clone(result["point"])

        def ila_hook(module, args):
            held["ila_args"] = clone(args)

        def decoder_hook(module, args):
            held["decoder_args"] = clone(args)

        def head_hook(module, args, result):
            held.update(q=module.out_norm(result[0]).detach().clone(), f=args[2].detach().clone(), mask=args[3].detach().clone(), logits=result[2].detach().clone(), indis=result[3].detach().clone())

        hooks = [cluster.register_forward_hook(point_hook), active[0].ila.register_forward_pre_hook(ila_hook), model.dec.decoder_layers[-1].register_forward_pre_hook(decoder_hook), model.dec.decoder_layers[-1].register_forward_hook(head_hook)]
        hierarchy.canonical = instrument
        try:
            gorilla.set_random_seed(1999)
            with torch.no_grad():
                progress["native_forwards"] += 1
                held["prediction"] = model(copy.deepcopy(batch), mode="predict")
        finally:
            hierarchy.canonical = original_canonical
            for hook in hooks:
                hook.remove()
        assert held["canonical_calls"] == held["point_input"].shape[0], (held["canonical_calls"], held["point_input"].shape)
        held["terms"] = [torch.stack([terms[level] for terms in held["term_batches"]], dim=0) for level in range(3)]
        held["sum_max_error"] = max(held["sum_errors"])
        held["weighted_term_norms"] = held["term_norm_batches"]
        held["weights_mean"] = held["weight_batches"]
        held["support_nonempty_counts"] = held["support_batches"]
        gate = torch.sigmoid(active[0].cluster_att_gate)
        held["injection_error"] = maximum(held["ila_args"][1], held["point_input"] + gate * held["point_message"])
        assert held["injection_error"] <= 1e-6
        return held

    @torch.no_grad()
    def message(prefix, subset):
        fused = prefix["point_input"] * 0
        for level, term in enumerate(prefix["terms"]):
            if subset & (1 << level):
                fused = fused + term
        value = cluster.point_out_proj(cluster.dropout(fused))
        value = value.masked_fill(prefix["point_mask"].unsqueeze(-1), 0)
        value = cluster.message_norm(value)
        return value.masked_fill(prefix["point_mask"].unsqueeze(-1), 0)

    def replay(prefix, batch, point_message):
        with torch.no_grad():
            args = list(clone(prefix["ila_args"]))
            args[1] = prefix["point_input"] + torch.sigmoid(active[0].cluster_att_gate) * point_message
            feature = active[0].ila(*args)[0]
            dec_args = list(clone(prefix["decoder_args"]))
            dec_args[2] = feature
            progress["native_suffix_replays"] += 1
            result = model.dec.decoder_layers[-1](*dec_args)
            query = model.dec.decoder_layers[-1].out_norm(result[0])
            logits = torch.einsum("bnd,bmd->bnm", query, feature)
        head_error = maximum(logits, result[2])
        assert head_error <= 1e-6
        selected = torch.softmax(result[3], -1)[..., 1].argmax(-1)
        return query.detach(), feature.detach(), logits.detach(), selected, head_error

    def iou_bce(logits, gt):
        return {"point_iou": float(native.get_iou(logits, gt).detach().cpu()), "point_bce": float(torch.nn.functional.binary_cross_entropy_with_logits(logits, gt).cpu())}

    for group, batch in zip(groups, inputs):
        assert (deadline - datetime.now(timezone.utc)).total_seconds() > 120
        gpu()
        prefix = capture(batch)
        full_message = message(prefix, 7)
        message_error = maximum(full_message, prefix["point_message"])
        assert message_error <= 1e-6, ("message_reconstruction", message_error)
        selection = torch.softmax(prefix["indis"], -1)[..., 1].argmax(-1)
        sp = batch["superpoints"].cuda().long()
        expression_rows = []
        for i in range(len(batch["ann_ids"])):
            objects = batch["object_idss"][i]
            if torch.is_tensor(objects):
                objects = objects.detach().cpu().reshape(-1).tolist()
            if not isinstance(objects, (list, tuple)):
                objects = [objects]
            expression_rows.append({"split": "train", "scene_id": str(batch["scan_ids"][0]), "object_ids": [int(x) for x in objects], "ann_id": int(batch["ann_ids"][i]), "group": group, "selected_query": int(selection[i]), "subsets": {}})
        full_errors = None
        max_head_error = 0.0
        for subset in range(8):
            with torch.no_grad():
                q, f, logits, own_selection, error = replay(prefix, batch, message(prefix, subset))
                fixed_q_logits = torch.einsum("bnd,bmd->bnm", prefix["q"], f)
                fixed_f_logits = torch.einsum("bnd,bmd->bnm", q, prefix["f"])
            max_head_error = max(max_head_error, error)
            if subset == 7:
                full_errors = {name: maximum(a, b) for name, a, b in (("q", q, prefix["q"]), ("f", f, prefix["f"]), ("logits", logits, prefix["logits"]))}
                assert max(full_errors.values()) <= 1e-6, full_errors
            for i, row in enumerate(expression_rows):
                gt = batch["gt_pmasks"][i].cuda().float()
                selected = int(selection[i])
                values = {"fixed_q_point": iou_bce(fixed_q_logits[i, selected][sp], gt), "fixed_f_query": iou_bce(fixed_f_logits[i, selected][sp], gt), "joint_fixed_selection": iou_bce(logits[i, selected][sp], gt), "joint_own_selection": iou_bce(logits[i, int(own_selection[i])][sp], gt), "own_selected_query": int(own_selection[i])}
                if subset == 7:
                    assert abs(values["fixed_q_point"]["point_iou"] - float(prefix["prediction"]["piou"][i])) <= 1e-6
                row["subsets"][str(subset)] = values
            del q, f, logits, fixed_q_logits, fixed_f_logits
        q, f, logits, own_selection, error = replay(prefix, batch, torch.zeros_like(prefix["point_message"]))
        with torch.no_grad():
            zero_fixed_q = torch.einsum("bnd,bmd->bnm", prefix["q"], f)
        for i, row in enumerate(expression_rows):
            gt = batch["gt_pmasks"][i].cuda().float()
            row["zero_message_fixed_q_point"] = iou_bce(zero_fixed_q[i, int(selection[i])][sp], gt)
            for key in ("fixed_q_point", "fixed_f_query", "joint_fixed_selection", "joint_own_selection"):
                for metric in ("point_iou", "point_bce"):
                    values = {s: row["subsets"][str(s)][key][metric] for s in range(8)}
                    contribution, residual = shapley(values)
                    row[key + "_" + metric + "_shapley"] = contribution
                    row[key + "_" + metric + "_efficiency_residual"] = residual
        progress["rows"].extend(expression_rows)
        progress["controls"].append({"group": group, "canonical_calls": prefix["canonical_calls"], "expression_batch_size": int(prefix["point_input"].shape[0]), "component_sum_max_error": prefix["sum_max_error"], "message_max_error": message_error, "injection_max_error": prefix["injection_error"], "all_scales_suffix_max_errors": full_errors, "head_max_error": max_head_error, "same_prefix_proposals_and_fps": True, "weighted_term_norms": prefix["weighted_term_norms"], "trained_weights_mean": prefix["weights_mean"], "support_nonempty_counts": prefix["support_nonempty_counts"], "empty_subset_message_norm": float(message(prefix, 0).norm().detach().cpu()), "true_zero_message_norm": 0.0})
        del prefix, q, f, logits, zero_fixed_q, full_message
    rows = progress["rows"]
    identities = [(r["split"], r["scene_id"], tuple(r["object_ids"]), r["ann_id"]) for r in rows]
    assert len(rows) == 16 and len(set(identities)) == 16
    scenes = sorted({r["scene_id"] for r in rows})
    assert len(scenes) == 4 and progress["native_forwards"] == 4 and progress["native_suffix_replays"] == 36
    scene_means = {scene: [sum(r["fixed_q_point_point_iou_shapley"][i] for r in rows if r["scene_id"] == scene) / sum(r["scene_id"] == scene for r in rows) for i in range(3)] for scene in scenes}
    means = [sum(r["fixed_q_point_point_iou_shapley"][i] for r in rows)/len(rows) for i in range(3)]
    for name, expected in manifest["source_hashes"].items():
        assert sha(ROOT / name) == expected, name
    assert sha(manifest["checkpoint"]) == manifest["checkpoint_sha256"]
    progress.update(passed_controls=True, observed_at=datetime.now(timezone.utc).isoformat(), checkpoint_sha256=manifest["checkpoint_sha256"], expressions=len(rows), independent_scenes=len(scenes), train_groups=groups, scale_names=["fine", "middle", "coarse"], scene_scale_point_iou_shapley=scene_means, mean_scale_point_iou_shapley=means, local_all_scales_nonnegative=all(v >= 0 for values in scene_means.values() for v in values), peak_diagnostic_allocated_bytes=torch.cuda.max_memory_allocated(), last_resources=gpu(), scope="Fixed4TRAINscene same-prefix off-distribution omission attribution only; no retraining,VAL selection,novelty,population efficacy,revision3 or admission.")
    (STAGE / "scale_result.json").write_text(json.dumps(progress, indent=2, allow_nan=False))
    print("SCALE_DIAGNOSTIC_PASS", flush=True)
except BaseException as error:
    progress.update(failed_at=datetime.now(timezone.utc).isoformat(), error_type=type(error).__name__, error=str(error), passed_controls=False)
    (STAGE / "scale_result.json").write_text(json.dumps(progress, indent=2, allow_nan=False))
    raise
finally:
    for handle in reversed(locks):
        handle.close()
