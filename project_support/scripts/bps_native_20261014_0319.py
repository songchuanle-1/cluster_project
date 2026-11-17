"""Independent full native TRAIN forward/backward, without optimizer steps."""
import argparse
from datetime import datetime, timezone
import gc
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
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps"
TOKEN = "1d59938f077948578e91e2cf34fc9d53"
MANIFEST_SHA = "c69d1f0397b031f9bdbad7af291f9a6bfc36041cd0088e4283545e62f8eb6b1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    import torch
    digest = hashlib.sha256()
    def visit(item):
        if isinstance(item, torch.Tensor):
            x = item.detach().cpu().contiguous()
            digest.update(str((tuple(x.shape), x.dtype)).encode())
            digest.update(x.numpy().tobytes())
        elif isinstance(item, dict):
            for k in sorted(item):
                digest.update(str(k).encode())
                visit(item[k])
        elif isinstance(item, (list, tuple)):
            digest.update(str(len(item)).encode())
            for part in item:
                visit(part)
        else:
            digest.update(repr(item).encode())
    visit(value)
    return digest.hexdigest()


def setup(token):
    assert token == TOKEN and socket.gethostname() == "das"
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "7"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset
    import framework.model.Quard_model
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.25)
    package = PIPE / ("bps_staging_" + token) / NAME
    sources = json.loads((package.parent / "source_manifest.json").read_text())
    assert {p.name: sha(p) for p in package.glob("*.py")} == sources["package"]
    original = ROOT / "framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
    assert sha(original / "loss.py") == "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"
    assert sha(original / "network.py") == "5a77eb852b3c6e5de2804d80a2c7a16504f1fd8a57aa94dc6045d9f35587625d"
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    assert sha(config) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = str(DATA) + "/"
    cfg.model.between_catalog = str(PIPE / ("bps_catalog_" + token + ".json"))
    assert cfg.train.seed == 1999 and cfg.train.epochs == 50
    assert cfg.lr_scheduler.max_iters == 70 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("bps-native"))
    full_name = "framework.model.Quard_model." + NAME
    spec = importlib.util.spec_from_file_location(
        full_name, package / "__init__.py", submodule_search_locations=[str(package)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    model = module.Network(**cfg.model)
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda()
    manifest = PIPE / "between_pair_typed_66fa1e81aec94d5eb10265ea533669ac.manifest.json"
    prior = json.loads((PIPE / "between_pair_typed_inventory_66fa1e81aec94d5eb10265ea533669ac.json").read_text())
    assert sha(manifest) == prior["frozen_manifest_sha256"]
    frozen = json.loads(manifest.read_text())["frozen"]
    assert len(frozen) == 8
    for row in frozen:
        assert [int(a["ann_id"]) for a in dataset.scene_inputs[row["native_group"]]] == row["group_ann_ids"]
    return torch, gorilla, dataset, model, state, frozen, sources, full_name


def get_batch(torch, gorilla, dataset, groups):
    from torch.utils.data import DataLoader
    gorilla.set_random_seed(1999)
    return next(iter(DataLoader(torch.utils.data.Subset(dataset, groups),
                                batch_size=len(groups), num_workers=0, shuffle=False,
                                collate_fn=dataset.collate_fn)))


def parameters(model):
    return [(name, value) for name, value in model.named_parameters() if value.requires_grad]


def gradient_summary(torch, values):
    reached = nonzero = 0
    maximum = 0.
    square = 0.
    for value in values:
        if value is None:
            continue
        assert bool(torch.isfinite(value).all())
        reached += 1
        nonzero += bool((value != 0).any())
        maximum = max(maximum, float(value.abs().max()))
        square += float(value.double().square().sum())
    return {"finite": True, "reached_tensors": reached, "nonzero_tensors": nonzero,
            "max_abs": maximum, "l2_norm": square ** .5}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    torch, gorilla, dataset, model, state, frozen, sources, full_name = setup(args.token)
    loss_module = sys.modules[full_name + ".loss"]
    original_operator = loss_module.support_excess
    held = {}
    def capture(*values):
        value = original_operator(*values)
        held["operator_args"] = values
        held["component"] = value
        return value
    loss_module.support_excess = capture
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs, kwargs: held.update(pred=inputs[0]), with_kwargs=True)
    cases = [{"groups": [r["native_group"]], "native_batch_size": 1} for r in frozen]
    cases += [{"groups": [r["native_group"] for r in frozen[i:i + 2]],
               "native_batch_size": 2} for i in range(0, 8, 2)]
    output = PIPE / ("bps_native_" + args.token + ".json")
    progress = PIPE / ("bps_native_" + args.token + ".progress.jsonl")
    rows = []
    torch.cuda.reset_peak_memory_stats()
    try:
        with progress.open("x") as stream:
            for case in cases:
                previous = None
                trials = []
                maxima = {"full_loss": 0., "component_loss": 0., "masks": 0.,
                          "indis": 0., "scores": 0., "proj_queries": 0.,
                          "proj_tokens": 0., "parameter_gradient": 0.}
                input_shas = []
                for repeat in (0, 1):
                    model.load_state_dict(state, strict=True)
                    model.train()
                    batch = get_batch(torch, gorilla, dataset, case["groups"])
                    input_shas.append(fingerprint(batch))
                    model.zero_grad(set_to_none=True)
                    held.clear()
                    gorilla.set_random_seed(1999)
                    loss, parts = model(batch, mode="loss")
                    component = parts["between_support_loss"]
                    assert component is held["component"]
                    assert bool(torch.isfinite(loss).all()) and bool(torch.isfinite(component).all())
                    named = parameters(model)
                    grads = torch.autograd.grad(component, [p for _, p in named],
                                                retain_graph=True, allow_unused=True)
                    direct = gradient_summary(torch, grads)
                    del grads
                    readout = model.between_support.last_readout
                    fields = {key: held["pred"][key].detach().cpu().clone()
                              for key in ("masks", "indis", "scores", "proj_queries", "proj_tokens")}
                    fields["full_loss"] = loss.detach().cpu().clone()
                    fields["component_loss"] = component.detach().cpu().clone()
                    loss.backward()
                    full = gradient_summary(torch, [p.grad for _, p in named])
                    fields["grads"] = {name: p.grad.detach().cpu().clone()
                                       for name, p in named if p.grad is not None}
                    if previous is not None:
                        assert previous["grads"].keys() == fields["grads"].keys()
                        for key in maxima:
                            if key == "parameter_gradient":
                                maxima[key] = max(float((fields["grads"][name] -
                                                        previous["grads"][name]).abs().max())
                                                  for name in fields["grads"])
                            else:
                                assert fields[key].shape == previous[key].shape
                                maxima[key] = float((fields[key] - previous[key]).abs().max())
                    previous = fields
                    trials.append({"trial": repeat, "full_loss": float(loss.detach()),
                                   "component_loss": float(component.detach()),
                                   "full_gradient": full, "component_gradient": direct,
                                   "original_trainable_tensors": len(named),
                                   "readout": readout, "expressions": len(batch["ann_ids"])})
                    held.clear()
                    del loss, parts, component, batch, named
                    gc.collect()
                    torch.cuda.empty_cache()
                row = {**case, "input_sha256": input_shas,
                       "input_repeat_exact": len(set(input_shas)) == 1,
                       "max_repeat_delta": maxima,
                       "full_repeat_pass1e6": all(v <= 1e-6 for v in maxima.values()),
                       "trials": trials}
                rows.append(row)
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(json.dumps({**case, "repeat_pass": row["full_repeat_pass1e6"],
                                  "max_delta": max(maxima.values()),
                                  "component": trials[0]["component_loss"]}), flush=True)
                del previous, fields
    finally:
        hook.remove()
        loss_module.support_excess = original_operator
    result = {"tick_token": args.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "source_manifest": sources,
              "catalog_sha256": sha(PIPE / ("bps_catalog_" + args.token + ".json")),
              "rows": rows, "full_forward_count": len(rows) * 2,
              "full_backward_count": len(rows) * 2, "optimizer_steps": 0,
              "new_trainable_tensors": 0, "training_mode": True,
              "allocator_peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
              "allocator_peak_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
              "scope": "Independent candidate native TRAIN loss/repeats, not trained efficacy or exclusive resources."}
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "all_repeat_pass": all(r["full_repeat_pass1e6"] for r in rows)}), flush=True)


if __name__ == "__main__":
    main()
