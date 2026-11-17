"""Versioned, read-only criterion geometry capture, separate from objectness.

The source manifest covers transitive local producer scripts. Imported packages
and model dependencies outside the bound model package are explicitly external.
"""
import argparse
import ast
import copy
import importlib
import json
import logging
import math
import os
from pathlib import Path
import subprocess
import sys

from frozen_capture_contract_20260916 import (
    file_sha256, fingerprint, model_package_sha256,
)
from native_frozen_capture_20260916 import FrozenDataset
from referent_geometry_capture_20260919 import capture_batch, check_binding, plain


RUNTIME_CONTRACT = "criterion_geometry_runtime_v1"
MODEL_CLASS = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def source_manifest(directory=None, entry=None):
    """Follow local AST imports, including function-local imports, without execution."""
    directory = Path(directory or Path(__file__).parent).resolve()
    entry = entry or Path(__file__).name
    pending, sources, external = [entry], {}, set()
    while pending:
        name = pending.pop()
        if name in sources:
            continue
        path = (directory / name).resolve()
        if path.parent != directory or path.suffix != ".py" or not path.is_file():
            raise ValueError("Producer source must be a local Python file")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        sources[name] = file_sha256(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    raise ValueError("Relative producer import needs explicit binding")
                modules = [node.module] if node.module else []
            elif isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            else:
                continue
            for module in modules:
                top = module.split(".")[0]
                local = directory / (top + ".py")
                if local.is_file():
                    pending.append(local.name)
                else:
                    external.add(module)
    rows = [dict(path=name, sha256=value) for name, value in sorted(sources.items())]
    return dict(
        contract=RUNTIME_CONTRACT, sources=rows, producer_sha256=fingerprint(rows),
        external_imports=sorted(external),
        scope="Transitive local producer scripts; not a full environment attestation",
    )


def verify_batch_axis(batch, axes):
    if not axes:
        raise ValueError("Missing expression axes")
    counts = plain(batch["scenes_len"])
    scenes = batch["scan_ids"]
    if len(counts) != len(scenes) or any(type(n) is not int or n <= 0 for n in counts):
        raise ValueError("Invalid collated scene counts")
    expanded = [scene for scene, count in zip(scenes, counts) for _ in range(count)]
    anns = plain(batch["ann_ids"])
    if len(axes) != len(expanded) or len(axes) != len(anns):
        raise ValueError("Collated expression count differs")
    for axis, scene, ann in zip(axes, expanded, anns):
        if type(ann) is not int or axis["scene"] != scene or axis["ann_id"] != ann:
            raise ValueError("Collated physical identity differs")
    start = 0
    for count in counts:
        group = axes[start:start + count]
        if [axis["expression_slot"] for axis in group] != list(range(count)):
            raise ValueError("Collated expression slots differ")
        for field in ("scene_occurrence", "dataset_index", "native_input_sha256",
                      "original_superpoint_ids", "sample_inverse",
                      "physical_instance_labels"):
            if any(axis[field] != group[0][field] for axis in group):
                raise ValueError("Collated scene binding differs: " + field)
        start += count


def capture_forward(model, batch, axes, binding):
    """Capture exactly one successful criterion call and always remove our hook."""
    check_binding(binding)
    verify_batch_axis(batch, axes)
    axes = copy.deepcopy(axes)
    batch_hash = fingerprint(batch)
    captured = []
    calls = 0

    def observe(module, inputs):
        nonlocal calls
        calls += 1
        if calls != 1:
            raise ValueError("Expected exactly one criterion call")
        captured.append(capture_batch(inputs, axes, binding))
        # Returning None preserves the criterion's original arguments.

    handle = model.criterion.register_forward_pre_hook(observe)
    try:
        output = model(batch, mode="loss")
        if calls != 1 or len(captured) != 1:
            raise ValueError("Expected exactly one criterion call")
        if fingerprint(batch) != batch_hash:
            raise ValueError("Model mutated collated native input")
        loss = output[0]
        loss_value = float(loss.detach().cpu() if hasattr(loss, "detach") else loss)
        if not math.isfinite(loss_value):
            raise ValueError("Nonfinite native loss")
        result = dict(
            runtime_contract=RUNTIME_CONTRACT, collated_input_sha256=batch_hash,
            criterion_calls=calls, loss=loss_value, geometry=captured[0],
        )
        result["payload_sha256"] = fingerprint(result)
        return result
    finally:
        handle.remove()


def check_capacity():
    """Fail closed before allocating memory; this is not a dispatcher or reservation."""
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Only authorized physical GPU7 may execute")
    gpu = subprocess.check_output([
        "nvidia-smi", "-i", "7",
        "--query-gpu=uuid,memory.total,memory.free", "--format=csv,noheader,nounits",
    ], text=True).strip().split(",")
    if len(gpu) != 3:
        raise ValueError("Ambiguous GPU observation")
    uuid, total, free = (value.strip() for value in gpu)
    processes = subprocess.check_output([
        "nvidia-smi", "--query-compute-apps=gpu_uuid,pid",
        "--format=csv,noheader,nounits",
    ], text=True)
    pids = [line.split(",")[1].strip() for line in processes.splitlines()
            if line.split(",")[0].strip() == uuid]
    if len(set(pids)) >= 2 or float(free) < .15 * float(total):
        raise ValueError("GPU7 process cap or measured memory blocks native capture")
    return dict(gpu=7, process_ids=pids, total_mib=float(total), free_mib=float(free))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batches", type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.batches <= 2:
        raise ValueError("Bounded diagnostic requires one or two batches")
    root, out = Path(args.root).resolve(), Path(args.output).resolve()
    if out.exists() or not out.is_relative_to(root.parent / "pipeline"):
        raise ValueError("Require new project-local diagnostic output directory")
    capacity = check_capacity()
    import torch

    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    from framework.dataset import build_dataset, build_dataloader

    manifest = source_manifest()
    config = root / "configs/Quard/ctf_hcg_csort" / (MODEL_CLASS + ".yaml")
    binding = dict(
        producer_sha256=manifest["producer_sha256"],
        model_source_sha256=model_package_sha256(root, MODEL_CLASS),
        config_sha256=file_sha256(config),
        checkpoint_sha256=file_sha256(args.checkpoint),
    )
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.15)
    gorilla.set_random_seed(1999)

    class GeometryDataset(FrozenDataset):
        checkpoint_sha256 = binding["checkpoint_sha256"]

    dataset = GeometryDataset(build_dataset(cfg.data.train, logging.getLogger("geometry")),
                              out.name, binding["producer_sha256"])
    loader = build_dataloader(dataset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    model = importlib.import_module(
        "framework.model.Quard_model." + MODEL_CLASS).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids",
                "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    del state
    model.cuda().eval()
    out.mkdir(parents=True, exist_ok=False)
    records = []
    with torch.no_grad():
        for step, (batch, axes) in enumerate(loader):
            gorilla.set_random_seed(1999)
            record = capture_forward(model, batch, axes, binding)
            records.append(record)
            with (out / ("geometry_%03d.json" % step)).open("x", encoding="ascii") as stream:
                json.dump(record, stream, indent=2, allow_nan=False)
            print(json.dumps(dict(step=step, loss=record["loss"],
                                  expressions=len(record["geometry"]["rows"]))), flush=True)
            if step + 1 == args.batches:
                break
    if len(records) != args.batches:
        raise ValueError("Loader ended before requested bounded capture")
    if source_manifest() != manifest:
        raise ValueError("Producer sources changed during capture")
    report = dict(
        contract=RUNTIME_CONTRACT, binding=binding, producer_manifest=manifest,
        capacity_observation=capacity, native_capture_completed=True,
        scientific_validation_complete=False, independent_objectness_resolved=False,
        batches=len(records), config_data_root_override=cfg.data.train.data_root,
        artifacts=[dict(path="geometry_%03d.json" % step,
                        sha256=file_sha256(out / ("geometry_%03d.json" % step)))
                   for step in range(len(records))],
        limitations=[
            "Annotation-assisted nuisance geometry is not objectness.",
            "Conditional on language-dependent selected query seeds.",
            "Native diagnostic completion is not a backward or admission gate.",
            "Source manifest does not attest external packages or full model dependencies.",
            "Caller must use authorized server-6 and coordinate capacity; no slot reservation.",
        ],
    )
    with (out / "capture.json").open("x", encoding="ascii") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
