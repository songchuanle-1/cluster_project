"""Independent-process full-model checks on frozen TRAIN inputs."""
import argparse
import copy
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import time

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--work", required=True)
    p.add_argument("--variant", action="store_true")
    p.add_argument("--profile-only", action="store_true")
    args = p.parse_args()
    root, work = Path(args.root), Path(args.work)
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    from framework.dataset import build_dataset
    import framework.model.Quard_model as packages
    packages.__path__ = [str(work), *packages.__path__]
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.cuda.set_per_process_memory_fraction(.45)
    base = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
    name = base + ("_scm" if args.variant else "")
    label = "scm" if args.variant else "parent"
    cfg = gorilla.Config.fromfile(str(work / (base + "_scm.yaml")))
    cfg.model.data_root = "/data3/songcl/data/data_cluster/"
    cfg.data.train.data_root = cfg.model.data_root
    gorilla.set_random_seed(1999)
    module = importlib.import_module("framework.model.Quard_model." + name)
    model = module.Network(**cfg.model)
    state = torch.load(work / "best.pth", map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        if key in state:
            assert torch.equal(state[key], getattr(model.text_encoder.embeddings,
                                                  key.rsplit(".", 1)[1]))
            del state[key]
    model.load_state_dict(state, strict=True)
    del state
    model.cuda()
    if args.profile_only:
        from fvcore.nn import FlopCountAnalysis
        cfg.data.train.lang_num_max = 1
        logger = logging.getLogger("scm_flops")
        gorilla.set_random_seed(1999)
        ds = build_dataset(cfg.data.train, logger)
        candidates = [(tuple((r["scene_id"], str(r["object_id"]), str(r["ann_id"]))
                             for r in group), i) for i, group in enumerate(ds.scene_inputs)
                      if group[0]["scene_id"] == "scene0000_00"]
        identity, index = min(candidates)
        bs1 = ds.collate_fn([ds[index]])
        model.eval()
        sparse_counts = []
        handles = []
        from spconv.pytorch.conv import SparseConvolution
        def sparse_hook(module, inputs, output):
            if module.conv1x1:
                return  # Already visible as mm to fvcore.
            data = output.indice_dict[module.indice_key]
            if hasattr(data, "pair_fwd"):
                pairs = data.pair_bwd if module.inverse else data.pair_fwd
                count = int((pairs >= 0).sum())
            else:
                count = int(data.indice_pair_num.sum())
            sparse_counts.append(dict(name=module.indice_key, pairs=count,
                macs=count * module.in_channels * module.out_channels))
        for module in model.modules():
            if isinstance(module, SparseConvolution):
                handles.append(module.register_forward_hook(sparse_hook))
        with torch.no_grad():
            model(bs1, mode="predict")
        for handle in handles:
            handle.remove()
        with torch.no_grad():
            flop = FlopCountAnalysis(model, (bs1, "predict"))
            flop.unsupported_ops_warnings(False)
            flop.uncalled_modules_warnings(False)
            total = flop.total()
        report = dict(identity=identity, fvcore_g=total / 1e9,
                      unsupported=dict(flop.unsupported_ops()),
                      modules=dict(flop.by_module()),
                      sparse_convolutions=sparse_counts,
                      sparse_macs_g=sum(r["macs"] for r in sparse_counts) / 1e9,
                      counted_plus_sparse_g=(total + sum(r["macs"] for r in sparse_counts)) / 1e9,
                      complete=False, convention="fvcore: one fused multiply-add counts as one")
        (work / (label + "_fvcore.json")).write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return
    batch = torch.load(work / "fixed_batch.pth", map_location="cpu",
                       weights_only=False)["batch"]
    result = dict(label=label, torch=torch.__version__, gpu=torch.cuda.get_device_name(),
                  train_scenes=batch["scan_ids"], train_expressions=len(batch["object_idss"]))
    capture = {}
    def hook(_module, inputs):
        capture["pred"] = inputs[0]
    handle = model.criterion.register_forward_pre_hook(hook)
    model.eval()
    gorilla.set_random_seed(1999)
    with torch.no_grad():
        loss, details = model(copy.deepcopy(batch), mode="loss")
    assert torch.isfinite(loss).all()
    pred = capture.pop("pred")
    snapshot = {k: pred[k].detach().cpu() for k in ("masks", "indis", "sample_inds")}
    # Diagnostic predictions only, never a trained model checkpoint.
    torch.save(snapshot, work / (label + "_outputs.pth"))
    result["eval_loss"] = float(loss)
    if args.variant:
        parent = torch.load(work / "parent_outputs.pth", weights_only=False)
        result["parity"] = {}
        for key in snapshot:
            equal = torch.equal(snapshot[key], parent[key])
            result["parity"][key] = dict(exact=equal,
                max_difference=float((snapshot[key] - parent[key]).abs().max()))
        # Same object and kernels isolate the criterion from process-level differences.
        scm_criterion = model.criterion
        registry = gorilla.LOSSES
        registry.obj_map.pop("Criterion")
        parent_module = importlib.import_module("framework.model.Quard_model." + base)
        model.criterion = parent_module.network.Criterion(**cfg.model.criterion).cuda()
        parent_capture = {}
        parent_hook = model.criterion.register_forward_pre_hook(
            lambda _m, inputs: parent_capture.update(pred=inputs[0]))
        gorilla.set_random_seed(1999)
        with torch.no_grad():
            model(copy.deepcopy(batch), mode="loss")
        result["same_process_parity"] = {}
        for key in snapshot:
            got = parent_capture["pred"][key].detach().cpu()
            result["same_process_parity"][key] = dict(
                exact=torch.equal(snapshot[key], got),
                max_difference=float((snapshot[key] - got).abs().max()))
        parent_hook.remove()
        parent_capture.clear()
        model.criterion = scm_criterion
    del snapshot, pred, loss, details
    model.train()
    gorilla.set_random_seed(1999)
    torch.cuda.reset_peak_memory_stats()
    loss, details = model(copy.deepcopy(batch), mode="loss")
    loss.backward()
    assert torch.isfinite(loss).all()
    assert all(torch.isfinite(v.grad).all() for v in model.parameters() if v.grad is not None)
    result["real_batch"] = dict(loss=float(loss), finite_backward=True,
        peak_mib=torch.cuda.max_memory_allocated() / 2**20,
        details={k: float(v.detach()) for k, v in details.items()})
    del loss, details
    capture.clear()
    model.zero_grad(set_to_none=True)
    try:
        gorilla.set_random_seed(1999)
        with torch.autocast("cuda", dtype=torch.float16):
            loss, details = model(copy.deepcopy(batch), mode="loss")
        loss.backward()
        result["full_cuda_amp"] = dict(finite_loss=bool(torch.isfinite(loss).all()),
            finite_backward=all(bool(torch.isfinite(v.grad).all())
                                for v in model.parameters() if v.grad is not None))
        del loss, details
    except Exception as exc:
        result["full_cuda_amp"] = dict(error=repr(exc))
    capture.clear()
    handle.remove()
    model.zero_grad(set_to_none=True)
    # The bs1 timing input is one TRAIN scene and one expression, fixed before timing.
    cfg.data.train.lang_num_max = 1
    logger = logging.getLogger("scm_admission")
    logger.addHandler(logging.StreamHandler())
    gorilla.set_random_seed(1999)
    ds = build_dataset(cfg.data.train, logger)
    candidates = [(tuple((r["scene_id"], str(r["object_id"]), str(r["ann_id"]))
                         for r in group), i) for i, group in enumerate(ds.scene_inputs)
                  if group[0]["scene_id"] == "scene0000_00"]
    identity, index = min(candidates)
    bs1 = ds.collate_fn([ds[index]])
    result["timing_input"] = dict(identity=identity, batch_size=1,
                                  expressions=len(bs1["object_idss"]))
    assert len(bs1["object_idss"]) == 1
    model.eval()
    with torch.inference_mode():
        for _ in range(20):
            model(bs1, mode="predict")
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        durations = []
        for _ in range(100):
            torch.cuda.synchronize()
            start = time.perf_counter()
            model(bs1, mode="predict")
            torch.cuda.synchronize()
            durations.append((time.perf_counter() - start) * 1000)
        result["timing"] = dict(warmup=20, repeat=100, median_ms=float(np.median(durations)),
            p90_ms=float(np.percentile(durations, 90)),
            peak_allocated_mib=torch.cuda.max_memory_allocated() / 2**20,
            peak_reserved_mib=torch.cuda.max_memory_reserved() / 2**20)
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
                torch.profiler.ProfilerActivity.CUDA], with_flops=True) as prof:
            model(bs1, mode="predict")
        ops = [(e.key, e.flops) for e in prof.key_averages() if e.flops]
        result["flops"] = dict(counted_g=sum(v for _, v in ops) / 1e9, operators=ops,
            complete=False, note="Torch profiler excludes custom sparse/point ops; lower bound only")
    (work / (label + "_full_results.json")).write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
