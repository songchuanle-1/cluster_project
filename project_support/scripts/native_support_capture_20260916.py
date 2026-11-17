"""Same-forward M95 TRAIN diagnostic. Never modifies training or enqueues a model."""
import argparse
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys

from capture_support_20260916 import CaptureDataset, bind_queries, support_record

IDENTITY = ("capture_id", "producer_sha256", "scene", "scene_occurrence",
            "dataset_index", "ann_id", "expression_slot",
            "original_superpoint_ids", "sample_inverse")


def physical_join(left, right):
    for row in (left, right):
        if any(key not in row for key in IDENTITY):
            raise ValueError("Missing exact capture identity")
        support_record(row["original_superpoint_ids"], row["sample_inverse"])
    if any(left[key] != right[key] for key in IDENTITY):
        raise ValueError("Different physical observation")
    return True


def exact_rows(axis, values):
    if len(values) != len(axis["original_superpoint_ids"]):
        raise ValueError("Feature rows differ from captured support")
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batches", type=int, default=2)
    args = parser.parse_args()
    if args.batches < 1 or os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Positive batch count and authorized physical GPU7 required")
    import torch
    root = Path(args.root).resolve()
    out = Path(args.output).resolve()
    if not out.is_relative_to(root.parent / "pipeline") or out.exists():
        raise ValueError("Require a new project-local output directory")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    from framework.dataset import build_dataset, build_dataloader

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.15)
    name = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
    config = root / "configs/Quard/ctf_hcg_csort" / (name + ".yaml")
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    producer = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    dataset = CaptureDataset(build_dataset(cfg.data.train, logging.getLogger("capture")),
                             out.name, producer)
    loader = build_dataloader(dataset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    model = importlib.import_module("framework.model.Quard_model." + name).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    del state
    model.cuda().eval()
    held, calls, handles = {}, [], []

    def projection(tag):
        def hook(module, inputs, output):
            held["raw_" + tag] = inputs[0].detach()
            held["projected_" + tag] = output.detach()
        return hook

    handles.append(model.dec.input_proj.register_forward_hook(projection("3d")))
    handles.append(model.dec.input_proj_2d.register_forward_hook(projection("2d")))
    handles.append(model.dec.sum_norm.register_forward_hook(
        lambda module, inputs, output: held.update(fused=output.detach())))
    handles.append(model.dec.encoder_layers[-1].register_forward_hook(
        lambda module, inputs, output: held.update(final=output[1].detach())))

    def criterion(module, inputs):
        held.update(pred=inputs[0], gt=inputs[1], objects=inputs[3],
                    labels=inputs[4], fps=inputs[7], offsets=inputs[9])

    handles.append(model.criterion.register_forward_pre_hook(criterion))
    native_match = model.criterion.match_sampled_ins

    def match(*inputs, **kwargs):
        result = native_match(*inputs, **kwargs)
        calls.append(result[2][0].detach())
        return result

    model.criterion.match_sampled_ins = match
    out.mkdir(parents=True)
    rows, artifacts = [], []
    try:
        with torch.no_grad():
            for step, (batch, axes) in enumerate(loader):
                held.clear()
                calls.clear()
                gorilla.set_random_seed(1999)
                loss, _ = model(batch, mode="loss")
                if not bool(torch.isfinite(loss).all()):
                    raise ValueError("Nonfinite native loss")
                pred = held["pred"]
                if len(axes) != len(pred["masks"]):
                    raise ValueError("Expression output axis differs")
                nonempty = [b for b, ids in enumerate(held["objects"]) if len(ids)]
                if len(calls) != 2 * len(nonempty):
                    raise ValueError("Unexpected native matcher call structure")
                positive_ids = {b: calls[2 * i + 1] for i, b in enumerate(nonempty)}
                features = {}
                for tag in ("raw_3d", "raw_2d", "projected_3d", "projected_2d", "fused"):
                    features[tag] = model.dec.get_batches(held[tag], held["offsets"])[0]
                features["final"] = held["final"]
                payload = []
                for b, axis in enumerate(axes):
                    labels = held["labels"][b].long().reshape(-1)
                    target = held["gt"][b].reshape(-1).bool()
                    n = len(axis["original_superpoint_ids"])
                    if len(labels) != n or len(target) != n:
                        raise ValueError("Native target/instance support differs")
                    if int((~pred["batch_mask"][b]).sum()) != n:
                        raise ValueError("Native valid mask differs from support")
                    masks = pred["masks"][b, :, :n] > 0
                    ious = ((masks & target).sum(-1).float()
                            / (masks | target).sum(-1).clamp_min(1))
                    scores = pred["indis"][b].softmax(-1)[:, 1]
                    positive = torch.zeros_like(scores, dtype=torch.bool)
                    if b in positive_ids:
                        positive[positive_ids[b]] = True
                    seeds = held["fps"][b][pred["sample_inds"][b]].long()
                    seed_inside = target[seeds]
                    row = bind_queries(axis, scores.cpu(), ious.cpu(), seed_inside.cpu(),
                                       positive.cpu(), labels.cpu())
                    if row["selected_query"] != int(scores.argmax()):
                        raise ValueError("Static/native argmax tie mismatch")
                    row.update(step=step, target_instances=[int(x) for x in held["objects"][b]],
                               target_superpoints=int(target.sum()),
                               fps_superpoints=held["fps"][b].cpu().tolist(),
                               sampled_seed_indices=pred["sample_inds"][b].cpu().tolist())
                    vectors = {tag: exact_rows(axis, value[b, :n].cpu())
                               for tag, value in features.items()}
                    physical_join(row, axis)
                    payload.append(dict(axis=axis, features=vectors, target=target.cpu(),
                                        instance_labels=labels.cpu()))
                    rows.append(row)
                artifact = out / ("features_%03d.pt" % step)
                torch.save(payload, artifact)
                artifacts.append(dict(path=artifact.name,
                                      sha256=hashlib.sha256(artifact.read_bytes()).hexdigest()))
                print(json.dumps(dict(step=step, expressions=len(rows), loss=float(loss))), flush=True)
                if step + 1 >= args.batches:
                    break
        if not rows:
            raise ValueError("No captured expressions")
        report = dict(scope="Native fixed M95 TRAIN diagnostic; no new model or efficacy claim",
                      producer_sha256=producer, batches=step + 1, rows=rows,
                      feature_artifacts=artifacts, native_capture_completed=True,
                      selected_success=sum(r["ious"][r["selected_query"]] > .5 for r in rows),
                      no_acceptable=sum(r["best_acceptable_rank"] is None for r in rows))
        (out / "capture.json").write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    finally:
        model.criterion.match_sampled_ins = native_match
        for handle in handles:
            handle.remove()


if __name__ == "__main__":
    main()
