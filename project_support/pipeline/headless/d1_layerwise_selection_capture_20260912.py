"""Read-only layerwise candidate-selection audit for the frozen M95 checkpoint.

The deployed selector uses only the final decoder layer's ``indis`` scores.
This worker replays the same 284 frozen diagnostic descriptions, reads the
already-computed auxiliary decoder outputs from the forward pass, and compares
per-layer selector quality against the final layer. It writes no candidate
tensors and changes no model, config, checkpoint, queue, or training artifact.
"""
import argparse
import gc
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import time

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

MANIFEST_SHA = "84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468"
BUFFER_KEYS = {
    "text_encoder.embeddings.position_ids",
    "text_encoder.embeddings.token_type_ids",
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def key(record):
    return record["scene_id"], str(record["object_id"]), str(record["ann_id"])


def mean(values):
    values = [float(value) for value in values]
    return sum(values) / len(values) if values else 0.0


def fraction(values):
    values = [bool(value) for value in values]
    return sum(values) / len(values) if values else 0.0


def rank_of(index, values):
    order = sorted(range(len(values)), key=lambda i: float(values[i]), reverse=True)
    return order.index(index)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--scene-limit", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    root = Path(args.code_root)
    output = Path(args.out)
    assert not output.exists(), "Immutable output directory already exists"
    assert sha(args.manifest) == MANIFEST_SHA
    audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    assert sha(audit["checkpoint"]) == audit["checkpoint_sha256"]
    assert sha(audit["config"]) == audit["config_sha256"]

    import subprocess

    assert subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip() == audit["code_head"]

    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    import torch
    import torch.nn.functional as F
    from framework.dataset import build_dataset

    torch.set_num_threads(1)
    free, total = torch.cuda.mem_get_info()
    assert free >= 8 * 1024**3, f"Insufficient preflight free memory: {free}"
    torch.cuda.set_per_process_memory_fraction(8 * 1024**3 / total)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(audit["config"])
    assert cfg.test.seed == 1999
    assert not cfg.data.val.training and cfg.data.val.get("src_sample", -1) == -1

    data_root = Path(cfg.data.val.data_root)
    source = data_root / "scanrefer/ScanRefer_val_new.json"
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    assert sha(source) == manifest["source_sha256"]
    records = json.loads(source.read_text(encoding="utf-8"))
    by_key = {key(record): record for record in records}
    assert len(by_key) == len(records)
    samples = [sample for sample in manifest["samples"] if sample["subset"] == "diagnostic"]
    scenes = sorted({sample["scene_id"] for sample in samples})
    if args.scene_limit:
        scenes = scenes[: args.scene_limit]
    chosen = [sample for sample in samples if sample["scene_id"] in scenes]
    if args.limit:
        chosen = chosen[: args.limit]
    assert chosen

    output.mkdir(parents=True)
    logger = logging.getLogger("layerwise_selection")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    dataset = build_dataset(cfg.data.val, logger)
    dataset.scene_inputs = [[by_key[key(sample)]] for sample in chosen]

    module = importlib.import_module(audit["explicit_module"])
    package = Path(module.__file__).parent
    assert {path.name: sha(path) for path in sorted(package.glob("*.py"))} == audit["package_sha256"]
    get_iou = importlib.import_module(audit["explicit_module"] + ".loss").get_iou
    model = module.Network(**cfg.model)
    assert model.task_type == "res"
    checkpoint = torch.load(audit["checkpoint"], map_location="cpu", weights_only=False)
    state = checkpoint["model"]
    expected = model.state_dict()
    assert set(state) - set(expected) == BUFFER_KEYS
    assert not set(expected) - set(state)
    for name in BUFFER_KEYS:
        runtime = getattr(model.text_encoder.embeddings, name.rsplit(".", 1)[1])
        assert torch.equal(state[name], runtime)
    model.load_state_dict(
        {name: value for name, value in state.items() if name not in BUFFER_KEYS},
        strict=True,
    )
    del state, checkpoint, expected
    gc.collect()
    model.cuda().eval()

    original_predict = model.predict_by_feat
    rows = []

    def capture_predict(scan_ids, object_idss, ann_ids, out, superpoints,
                        gt_pmasks, gt_spmasks, fps_seed_sp):
        result = original_predict(
            scan_ids, object_idss, ann_ids, out, superpoints,
            gt_pmasks, gt_spmasks, fps_seed_sp,
        )
        assert len(ann_ids) == 1 and len(scan_ids) == 1
        aux = out.get("aux_outputs", [])
        layer_masks = [item["masks"] for item in aux] + [out["masks"]]
        layer_indis = [item["indis"] for item in aux] + [out["indis"]]
        assert len(layer_masks) == len(layer_indis) == model.dec.num_layer

        i = 0
        for i, ann_id in enumerate(ann_ids):
            gt = gt_spmasks[i].bool()
            layer_rows = []
            final_oracle = None
            final_selected = None
            final_selected_iou = None
            final_oracle_iou = None
            for layer_index, (masks, indis) in enumerate(
                zip(layer_masks, layer_indis)
            ):
                masks_i = masks[i].float()
                indis_i = indis[i].float()
                target = gt.unsqueeze(0).expand_as(masks_i)
                candidate_ious = get_iou(masks_i, target).float()
                probabilities = F.softmax(indis_i, dim=-1)[:, 1]
                selected_index = int(probabilities.argmax())
                oracle_index = int(candidate_ious.argmax())
                selected_iou = float(candidate_ious[selected_index])
                oracle_iou = float(candidate_ious[oracle_index])
                oracle_rank = rank_of(
                    oracle_index, probabilities.detach().cpu().tolist()
                )
                top_values = torch.topk(probabilities, k=2).values
                margin = float(top_values[0] - top_values[1])
                layer_rows.append(
                    {
                        "layer": layer_index,
                        "candidate_count": int(candidate_ious.numel()),
                        "selected_index": selected_index,
                        "selected_iou": selected_iou,
                        "oracle_index": oracle_index,
                        "oracle_iou": oracle_iou,
                        "oracle_rank": oracle_rank,
                        "oracle_top1": oracle_rank == 0,
                        "oracle_top5": oracle_rank < 5,
                        "top2_margin": margin,
                        "chance_iou": float(candidate_ious.mean()),
                        "valid": selected_iou > 0.5,
                    }
                )
                if layer_index == len(layer_masks) - 1:
                    final_oracle = oracle_index
                    final_selected = selected_index
                    final_selected_iou = selected_iou
                    final_oracle_iou = oracle_iou

            for layer_row in layer_rows:
                layer_row["final_oracle_index"] = final_oracle
                layer_row["final_oracle_rank"] = rank_of(
                    final_oracle,
                    [
                        float(value)
                        for value in F.softmax(
                            layer_indis[layer_row["layer"]][i].float(), dim=-1
                        )[:, 1].detach().cpu()
                    ],
                )
                layer_row["selects_final_oracle"] = (
                    layer_row["selected_index"] == final_oracle
                )
                layer_row["selects_final_selection"] = (
                    layer_row["selected_index"] == final_selected
                )
                layer_row["final_valid"] = final_selected_iou > 0.5
                layer_row["final_recoverable"] = (
                    final_selected_iou <= 0.5 and final_oracle_iou > 0.5
                )
                layer_row["final_success"] = (
                    final_selected_iou > 0.5 and final_oracle_iou > 0.5
                )
                layer_row["early_valid_on_final_recoverable"] = (
                    layer_row["final_recoverable"] and layer_row["valid"]
                )
                layer_row["early_harm_on_final_success"] = (
                    layer_row["final_success"] and not layer_row["valid"]
                )

            rows.append(
                {
                    "scene_id": scan_ids[0],
                    "object_id": str(object_idss[i][0]),
                    "ann_id": str(ann_id),
                    "final_oracle_index": final_oracle,
                    "final_selected_index": final_selected,
                    "final_selected_iou": final_selected_iou,
                    "final_oracle_iou": final_oracle_iou,
                    "final_recoverable": (
                        final_selected_iou <= 0.5 and final_oracle_iou > 0.5
                    ),
                    "final_success": (
                        final_selected_iou > 0.5 and final_oracle_iou > 0.5
                    ),
                    "layers": layer_rows,
                }
            )
        return result

    model.predict_by_feat = capture_predict
    start = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    for index in range(len(dataset)):
        assert time.monotonic() - start < 1200, "Capture time budget exceeded"
        free, _ = torch.cuda.mem_get_info()
        assert free >= 5 * 1024**3, "Shared memory headroom dropped"
        batch = dataset.collate_fn([dataset[index]])
        with torch.no_grad():
            result = model(batch, mode="predict")
        del batch, result
        if (index + 1) % 4 == 0:
            print(f"CAPTURED {len(rows)} of {len(chosen)}", flush=True)

    assert len(rows) == len(chosen)
    recoverable = [row for row in rows if row["final_recoverable"]]
    successes = [row for row in rows if row["final_success"]]
    subsets = {
        "all": rows,
        "final_recoverable": recoverable,
        "final_success": successes,
    }
    layer_summary = {}
    for subset_name, subset in subsets.items():
        layer_summary[subset_name] = {}
        for layer_index in range(model.dec.num_layer):
            layer_rows = [row["layers"][layer_index] for row in subset]
            layer_summary[subset_name][str(layer_index)] = {
                "count": len(layer_rows),
                "acc50": fraction(row["valid"] for row in layer_rows),
                "selected_iou_mean": mean(row["selected_iou"] for row in layer_rows),
                "oracle_iou_mean": mean(row["oracle_iou"] for row in layer_rows),
                "chance_iou_mean": mean(row["chance_iou"] for row in layer_rows),
                "oracle_rank_mean": mean(row["oracle_rank"] for row in layer_rows),
                "oracle_top1_fraction": fraction(
                    row["oracle_top1"] for row in layer_rows
                ),
                "oracle_top5_fraction": fraction(
                    row["oracle_top5"] for row in layer_rows
                ),
                "top2_margin_mean": mean(row["top2_margin"] for row in layer_rows),
                "final_oracle_rank_mean": mean(
                    row["final_oracle_rank"] for row in layer_rows
                ),
                "selects_final_oracle_fraction": fraction(
                    row["selects_final_oracle"] for row in layer_rows
                ),
                "selects_final_selection_fraction": fraction(
                    row["selects_final_selection"] for row in layer_rows
                ),
                "early_valid_on_final_recoverable": fraction(
                    row["early_valid_on_final_recoverable"] for row in layer_rows
                ),
                "early_harm_on_final_success": fraction(
                    row["early_harm_on_final_success"] for row in layer_rows
                ),
            }

    any_early = [
        any(layer["valid"] for layer in row["layers"][:-1])
        for row in recoverable
    ]
    all_early = [
        all(layer["valid"] for layer in row["layers"][:-1])
        for row in recoverable
    ]
    summary = {
        "status": "complete",
        "protocol": (
            "Read-only layerwise selection audit. For each frozen checkpoint "
            "forward pass, the six decoder layers' auxiliary masks and indis "
            "scores are evaluated with the same deployed selector. Layers 0-4 "
            "are not used for deployment."
        ),
        "checkpoint_sha256": audit["checkpoint_sha256"],
        "module": audit["explicit_module"],
        "audit_sha256": sha(args.audit),
        "manifest_sha256": sha(args.manifest),
        "worker_sha256": sha(__file__),
        "selected_scenes": scenes,
        "descriptions": len(rows),
        "limits": {"scene_limit": args.scene_limit, "limit": args.limit},
        "subsets": {
            name: len(subset) for name, subset in subsets.items()
        },
        "layer_summary": layer_summary,
        "recoverable_any_early_valid_fraction": fraction(any_early),
        "recoverable_all_early_valid_fraction": fraction(all_early),
        "elapsed_seconds": time.monotonic() - start,
        "peak_allocated_mib": torch.cuda.max_memory_allocated() / 1024**2,
        "peak_reserved_mib": torch.cuda.max_memory_reserved() / 1024**2,
        "rows": rows,
        "limitation": (
            "Auxiliary outputs are computed during the same forward pass but "
            "are not used by deployment. This is an exploratory diagnostic on "
            "one frozen checkpoint and one validation-derived manifest."
        ),
    }
    (output / "result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# M95 Layerwise Candidate-Selection Audit",
        "",
        f"Date: 2026-09-12. Read-only evaluation on {len(rows)} frozen diagnostic banks.",
        "",
        "## Question",
        "",
        "Does recoverable candidate evidence already exist in decoder layers 0-4",
        "and then disappear when the deployed selector uses only layer 5?",
        "",
        "## Metrics",
        "",
        "| Layer | Acc@50 | Selected IoU | Chance IoU | Oracle rank | Oracle top-5 | Final-oracle rank | Selects final oracle |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for layer_index in range(model.dec.num_layer):
        item = layer_summary["all"][str(layer_index)]
        lines.append(
            f"| {layer_index} | {item['acc50']:.4f} | "
            f"{item['selected_iou_mean']:.4f} | {item['chance_iou_mean']:.4f} | "
            f"{item['oracle_rank_mean']:.1f} | "
            f"{item['oracle_top5_fraction']:.4f} | "
            f"{item['final_oracle_rank_mean']:.1f} | "
            f"{item['selects_final_oracle_fraction']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Final-Recoverable Subset",
            "",
            f"Count: {len(recoverable)}. These are banks where the final selector",
            "picked a candidate with IoU <= 0.5 while its own final-layer mask",
            "candidate set contained a candidate with IoU > 0.5.",
            "",
            "| Layer | Acc@50 | Selected IoU | Early valid rescue | Early final-success harm |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for layer_index in range(model.dec.num_layer):
        item = layer_summary["final_recoverable"][str(layer_index)]
        lines.append(
            f"| {layer_index} | {item['acc50']:.4f} | "
            f"{item['selected_iou_mean']:.4f} | "
            f"{item['early_valid_on_final_recoverable']:.4f} | "
            f"{item['early_harm_on_final_success']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- At least one of decoder layers 0-4 selects a valid candidate on",
            f"  {fraction(any_early):.4f} of final-recoverable banks.",
            f"- All of decoder layers 0-4 select a valid candidate on",
            f"  {fraction(all_early):.4f} of final-recoverable banks.",
            "- The deployed selector is the final layer. A high early-layer rescue",
            "  rate would indicate that useful evidence is present before layer 5",
            "  but is not preserved by the final selector.",
            "",
            "## Limitation",
            "",
            "Auxiliary decoder outputs are trained by the existing auxiliary loss but",
            "are not an independently validated deployment path. This diagnostic does",
            "not establish a new mechanism or a training-time causal effect.",
        ]
    )
    (output / "diagnostic_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, indent=2))
    print("D1_LAYERWISE_SELECTION_CAPTURE_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
