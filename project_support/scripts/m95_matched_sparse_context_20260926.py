"""Bounded, frozen-batch M95 sparse-boundary comparison; never trains."""
import argparse
import importlib
import json
import os
from pathlib import Path
import sys

from m95_frozen_batch_cluster_control_20260926 import (
    CHECKPOINT_SHA256, CONFIG_SHA256, EXPECTED, MODEL_NAME, MODEL_SHA256,
    digest, sha256,
)


ROW83_BATCH_SHA256 = "ed835ab21f071048e1d1cdd8fb19b6dd4ac24770b65e85ee4048931edb3d0529"
ROW174_BATCH_SHA256 = "37d3a64de34b3703c0bb682b7be11942afee8c723721b5672a1951af8362732d"
FULL_ORDER_SHA256 = "0de128c44bb103ad2e3b7690e27e83b5d2f310c1e59b0087f9ddf2457dbbd742"


def compare_tensors(left, right):
    if left.shape != right.shape:
        return {"comparable": False, "left_shape": list(left.shape),
                "right_shape": list(right.shape)}
    delta = (left.float() - right.float()).abs()
    return {"comparable": True, "max_abs": float(delta.max()),
            "mean_abs": float(delta.mean()),
            "changed_elements": int((delta != 0).sum())}


def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "bundle", "checkpoint", "row83", "row174",
                 "full-order", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Only authorized physical GPU7")
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    root = Path(args.root).resolve()
    sys.path[:0] = [str(Path(args.bundle).resolve()), str(Path(__file__).resolve().parent),
                    str(root), str(root / "framework/lib")]
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    import gorilla
    import torch
    from frozen_capture_contract_20260916 import model_package_sha256

    config = root / "configs/Quard/ctf_hcg_csort" / (MODEL_NAME + ".yaml")
    required = ((config, CONFIG_SHA256), (args.checkpoint, CHECKPOINT_SHA256),
                (args.row83, ROW83_BATCH_SHA256),
                (args.row174, ROW174_BATCH_SHA256),
                (args.full_order, FULL_ORDER_SHA256))
    if any(sha256(path) != expected for path, expected in required):
        raise ValueError("Frozen artifact hash differs")
    if model_package_sha256(root, MODEL_NAME) != MODEL_SHA256:
        raise ValueError("Frozen model source differs")
    full_order = json.loads(Path(args.full_order).read_text(encoding="ascii"))
    if (full_order["contract"] != "m95_full_producer_boundary_v1"
            or full_order["native_item_sha256"] != EXPECTED[83][0]
            or full_order["checkpoint_sha256"] != CHECKPOINT_SHA256):
        raise ValueError("Full-order binding differs")
    batches = {}
    for row, path in ((83, args.row83), (174, args.row174)):
        saved = torch.load(path, map_location="cpu", weights_only=False)
        if (saved["contract"] != "m95_frozen_target_batch_v1"
                or saved["manifest_index"] != row
                or saved["native_item_sha256"] != EXPECTED[row][0]
                or saved["frozen_native_input_sha256"] != EXPECTED[row][0]):
            raise ValueError("Saved batch identity differs")
        batches[row] = saved["batch"]

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    model = importlib.import_module("framework.model.Quard_model." + MODEL_NAME).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    del state
    model.cuda().eval()
    held = {}

    def capture(name):
        def hook(module, inputs, result=None):
            tensor = inputs[0] if result is None else result
            held[name] = tensor.features.detach().cpu().clone()
            held[name + "_indices"] = tensor.indices.detach().cpu().clone()
        return hook

    hooks = [
        model.input_conv.register_forward_pre_hook(capture("input")),
        model.input_conv.register_forward_hook(capture("first")),
        model.output_layer.register_forward_hook(capture("sparse")),
        model.criterion.register_forward_pre_hook(
            lambda module, inputs: held.update(pred=inputs[0], gt=inputs[1],
                                                offsets=inputs[9])),
    ]
    records = []
    cold = None
    try:
        with torch.no_grad():
            for arm in ("cold", "primed"):
                for repeat in range(2):
                    if arm == "primed":
                        gorilla.set_random_seed(1999)
                        held.clear()
                        model(batches[174], mode="loss")
                    gorilla.set_random_seed(1999)
                    held.clear()
                    loss, _ = model(batches[83], mode="loss")
                    if not bool(torch.isfinite(loss)):
                        raise ValueError("Nonfinite native loss")
                    snapshot = {key: held[key] for key in
                                ("input", "input_indices", "first", "first_indices",
                                 "sparse", "sparse_indices")}
                    if cold is None:
                        cold = snapshot
                    batch = batches[83]
                    n = int(held["offsets"][7] - held["offsets"][6])
                    # Row 83 is expression slot six in the frozen two-scene batch.
                    scores = held["pred"]["indis"][6].softmax(-1)[:, 1]
                    selected = int(scores.argmax())
                    target = held["gt"][6].reshape(-1).bool()
                    mask = held["pred"]["masks"][6, selected, :n] > 0
                    logits = held["pred"]["masks"][6, 103, :n]
                    records.append({
                        "arm": arm, "repeat": repeat,
                        "stages": {key: {"sha256": digest(snapshot[key]),
                                         "vs_cold": compare_tensors(snapshot[key], cold[key])}
                                   for key in snapshot},
                        "p2v_map_sha256": digest(batch["p2v_map"]),
                        "superpoints_sha256": digest(batch["superpoints"]),
                        "matches_full_order_sparse": digest(snapshot["sparse"])
                        == full_order["sparse_output_sha256"],
                        "selected_query": selected,
                        "selected_iou": float((mask & target).sum().float() /
                                               (mask | target).sum().clamp_min(1)),
                        "point169_logit": float(logits[169]),
                    })
    finally:
        for hook in hooks:
            hook.remove()
    output.write_text(json.dumps({
        "contract": "m95_matched_sparse_context_v1",
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "model_source_sha256": MODEL_SHA256,
        "row83_batch_sha256": ROW83_BATCH_SHA256,
        "row174_batch_sha256": ROW174_BATCH_SHA256,
        "full_order_sha256": FULL_ORDER_SHA256,
        "arms": "cold row83 x2; row174 then row83 x2; seed1999 reset before each forward",
        "records": records, "admission": False,
    }, indent=2, allow_nan=False) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
