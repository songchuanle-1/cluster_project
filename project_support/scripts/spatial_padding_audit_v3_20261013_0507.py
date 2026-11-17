"""Original native mask-loss padding boundary with actual TRAIN supports."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
TOKEN = "f3d67c69338443d28eee4349fd8576ab"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert socket.gethostname() == "das"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import gorilla
    import torch
    import torch.nn.functional as F
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    source = ROOT / "framework/dataset/scannetv2.py"
    criterion_source = ROOT / "framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py"
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    manifest = PIPE / "point_detail_population_20261009/result.manifest.json"
    assert sha(source) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    assert sha(config) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    assert sha(manifest) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    assert sha(criterion_source) == "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999
    assert cfg.model.criterion.match_last_layer is True
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("spatial-padding-audit"))
    spec = importlib.util.spec_from_file_location("native_padding_loss_0507", criterion_source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    criterion = module.Criterion(**cfg.model.criterion)
    selected = json.loads(manifest.read_text())[:8]
    query_count = cfg.model.sampling_module.num_proposal
    assert query_count == 128
    trials = []
    for trial in range(2):
        gorilla.set_random_seed(1999)
        observations = []
        for start in range(0, len(selected), 2):
            selection = selected[start:start + 2]
            items = [dataset[row["native_group"]] for row in selection]
            batch = dataset.collate_fn(items)
            assert batch["ann_ids"] == [aid for item in items for aid in item[0]]
            masks, labels = [], []
            for item in items:
                for obj_ids in item[6]:
                    assert len(obj_ids) == 1
                    masks.append((item[11] == int(obj_ids[0])).float()[None])
                    labels.append(int(obj_ids[0]))
            lengths = [int(m.shape[-1]) for m in masks]
            maximum, bsz = max(lengths), len(masks)
            valid = torch.arange(maximum)[None] < torch.tensor(lengths)[:, None]
            assert valid.shape[0] == len(batch["ann_ids"])
            padding = (~valid)[:, None].expand(bsz, query_count, maximum)
            base = torch.linspace(-1, 1, bsz * query_count * maximum).reshape(bsz, query_count, maximum)
            indices = [(torch.tensor([0]), torch.tensor([0])) for _ in masks]
            targets = [{"masks": m} for m in masks]
            scores = torch.full((bsz, query_count, 1), 0.25)
            indicators = torch.linspace(-0.5, 0.5, bsz * query_count * 2).reshape(bsz, query_count, 2)

            def run(stress, broken=False):
                values = base.clone()
                if stress:
                    values[padding] += 7.0
                values.requires_grad_()
                out = {"masks": values, "scores": scores, "indis": indicators,
                       "proj_queries": None, "proj_tokens": None}
                t = targets
                keep = valid
                if broken:
                    t = [{"masks": F.pad(m, (0, maximum - m.shape[-1]))} for m in masks]
                    keep = torch.ones_like(valid)
                loss, parts = criterion.get_layer_loss(
                    0, out, keep, t, indices=indices, lang_masks=None)
                gradient, = torch.autograd.grad(loss, values)
                return loss.detach(), parts, gradient

            loss0, parts0, grad0 = run(False)
            loss1, parts1, grad1 = run(True)
            loss_repeat, _, grad_repeat = run(False)
            loss_broken, parts_broken, grad_broken = run(False, True)
            max_padded = float(grad0[padding].abs().max()) if padding.any() else None
            max_broken = float(grad_broken[padding].abs().max()) if padding.any() else None
            observation = {
                "groups": [r["native_group"] for r in selection],
                "scenes": [item[1] for item in items],
                "ann_ids": list(map(int, batch["ann_ids"])),
                "target_ids": labels, "lengths": lengths, "expressions": bsz,
                "maximum_supports": maximum,
                "padded_expressions": sum(n < maximum for n in lengths),
                "padded_support_slots": int((~valid).sum()),
                "padding_gradient_max": max_padded,
                "loss_delta_padding_only": float((loss1 - loss0).abs()),
                "valid_gradient_delta": float((grad1[~padding] - grad0[~padding]).abs().max()),
                "original_repeat_loss_delta": float((loss_repeat - loss0).abs()),
                "original_repeat_gradient_delta": float((grad_repeat - grad0).abs().max()),
                "padding_invariance_strict": bool(torch.equal(grad1, grad0)),
                "broken_filter_padding_gradient_max": max_broken,
                "original_loss": float(loss0), "broken_filter_loss": float(loss_broken),
                "component_losses": {k: float(v.detach()) for k, v in parts0.items()},
                "native_mask_hash": hashlib.sha256(
                    b"".join(m.numpy().tobytes() for m in masks)).hexdigest(),
                "loss_boundary_inputs": "deterministic decoder-shaped probes; actual native support labels/masks/collation; no native forward or matcher"
            }
            print(json.dumps({"observation": observation}), flush=True)
            if padding.any():
                assert max_padded == 0 and max_broken > 0
            assert all(torch.isfinite(v).all() for v in (grad0, grad1, grad_broken))
            observations.append(observation)
            print(json.dumps({"trial": trial, "pair": start // 2,
                              "padded_expressions": observation["padded_expressions"],
                              "padding_gradient": max_padded, "control_gradient": max_broken}), flush=True)
        trials.append(observations)
    exact_record_repeat = trials[0] == trials[1]
    totals = {
        "native_groups": len(selected),
        "expressions": sum(r["expressions"] for r in trials[0]),
        "paired_collations": len(trials[0]),
        "padded_expressions": sum(r["padded_expressions"] for r in trials[0]),
        "padded_support_slots": sum(r["padded_support_slots"] for r in trials[0]),
        "native_loss_trials": 2 * 4 * len(trials[0]),
        "strict_padding_gradient_failures": sum(not r["padding_invariance_strict"] for r in trials[0]),
        "nonvacuous_positive_controls": sum(r["broken_filter_padding_gradient_max"] is not None
                                           and r["broken_filter_padding_gradient_max"] > 0 for r in trials[0])
    }
    assert totals["padded_expressions"] > 0 and totals["nonvacuous_positive_controls"] > 0
    result = {
        "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(), "cpu_only": True, "seed": 1999,
        "script_sha256": sha(Path(__file__)), "dataset_sha256": sha(source),
        "criterion_sha256": sha(criterion_source), "config_sha256": sha(config),
        "manifest_sha256": sha(manifest), "selected_groups": selected,
        "totals": totals, "trials": trials, "exact_repeat": exact_record_repeat,
        "prior_v1_failure": "Exact valid-gradient invariance asserted before emitting readouts; v1 retained, no tolerance was relaxed.",
        "prior_v2_failure": "Two raw records differed by exact valid-gradient readouts; v2 retained. V3 persists rather than asserting an experimental outcome.",
        "scope": "Native mask-loss boundary only; synthetic decoder/assignment; exact padding-gradient failures are retained; no native forward, FPS, semantic alignment, model backward or resource/admission certification."
    }
    output = PIPE / "spatial_padding_audit_20261013_0507.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "totals": totals,
                      "exact_repeat": result["exact_repeat"]}), flush=True)


if __name__ == "__main__":
    main()
