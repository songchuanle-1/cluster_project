"""Bounded registry-aware native diagnostic; never launches training.

Uses new TRAIN transforms, not replicas of historical failure inputs. Native
execution requires coordinated server-6 GPU7 capacity and expected source hashes.
"""
import argparse
import copy
import importlib
import inspect
import json
import logging
import os
from pathlib import Path
import sys
import tempfile

from frozen_capture_contract_20260916 import (
    file_sha256, fingerprint, model_package_sha256,
)
from native_frozen_capture_20260916 import FrozenDataset
from native_geometry_runtime_20260919 import (
    MODEL_CLASS, capture_forward, check_capacity, source_manifest,
)
from referent_geometry_registry_20260919 import evaluate
from referent_registry_binding_20260919 import BindingExporter


CONTRACT = "registry_geometry_runner_v1"
AUTHORIZED_ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")


def runner_manifest():
    result = source_manifest(entry=Path(__file__).name)
    result["contract"] = CONTRACT
    return result


def require_expected(expected, actual):
    if set(expected) != set(actual) or expected != actual:
        raise ValueError("Expected native source binding differs")


class RegistryDataset(FrozenDataset):
    """Serial observer on the original dataset, with no subset reindexing."""

    def __init__(self, dataset, capture_id, registry, registry_sha256, binding,
                 dataset_source_sha256):
        if dataset.training is not True:
            raise ValueError("Native TRAIN dataset required")
        super().__init__(dataset, capture_id, binding["producer_sha256"])
        self.checkpoint_sha256 = binding["checkpoint_sha256"]
        self.exporter = BindingExporter(
            registry, registry_sha256, dataset.scene_inputs, binding,
            dataset_source_sha256)
        self.indices = tuple(sorted({
            row["dataset_index"] for row in self.exporter.plan["rows"]
            if row["status"] == "planned"}))
        self.consumed = set()
        self.failed = False

    def __getitem__(self, index):
        if self.failed:
            raise ValueError("Failed observation cannot be resumed in this capture")
        if type(index) is not int or index not in self.indices or index in self.consumed:
            raise ValueError("Require unconsumed original planned dataset index")
        try:
            expected = self.exporter.plan["dataset_metadata_sha256"]
            if fingerprint(self.dataset.scene_inputs) != expected:
                raise ValueError("Native metadata changed before observation")
            item, axes = super().__getitem__(index)
            if fingerprint(self.dataset.scene_inputs) != expected:
                raise ValueError("Native metadata changed during observation")
            self.exporter.export_item(index, item, axes)
            self.consumed.add(index)
            return item, axes
        except Exception:
            self.failed = True
            raise


def capture_planned(model, dataset, binding, item_limit, sink=None):
    """One original scene group per forward; retain every registry denominator."""
    if type(item_limit) is not int or not 1 <= item_limit <= 2:
        raise ValueError("Bounded diagnostic requires one or two original items")
    if dataset.failed or dataset.consumed:
        raise ValueError("Require fresh registry dataset")
    if not dataset.indices:
        raise ValueError("No unambiguous planned native metadata")
    records = []
    try:
        for step, index in enumerate(dataset.indices[:item_limit]):
            item, axes = dataset[index]
            before = fingerprint((item, axes))
            batch, batch_axes = dataset.collate_fn([(item, axes)])
            if before != fingerprint((item, axes)):
                raise ValueError("Collation mutated observed item or axes")
            record = capture_forward(model, batch, batch_axes, binding)
            records.append(record)
            if sink is not None:
                sink(step, index, copy.deepcopy(record))
    except Exception:
        dataset.failed = True
        raise
    return records


def dump_new(path, value):
    payload = json.dumps(value, indent=2, allow_nan=False)
    fd, temporary = tempfile.mkstemp(prefix=".pending_", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="ascii") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # A hard link publishes complete bytes atomically and never replaces a file.
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def verify_output(out, expected):
    """Validate bundle completeness, not the truth of native execution."""
    out = Path(out)
    if (out / "failure.json").exists():
        raise ValueError("Failed capture bundle")
    report = json.loads((out / "capture.json").read_text(encoding="utf-8"))
    if report.get("contract") != CONTRACT or report.get("native_capture_completed") is not True:
        raise ValueError("Incomplete capture marker")
    require_expected(expected, report["expected_binding"])
    count = report["completed_items"]
    limit = report["requested_item_limit"]
    if (type(count) is not int or type(limit) is not int
            or not 1 <= count <= limit <= 2):
        raise ValueError("Invalid completed item count")
    names = {"bindings.json", "evaluation.json"} | {
        "geometry_%03d.json" % i for i in range(count)}
    artifacts = report["artifacts"]
    if len(artifacts) != len(names) or {a["path"] for a in artifacts} != names:
        raise ValueError("Incomplete or unexpected artifact inventory")
    if {p.name for p in out.iterdir()} != names | {"capture.json"}:
        raise ValueError("Partial or unexpected bundle files")
    for artifact in artifacts:
        path = out / artifact["path"]
        if path.is_symlink() or file_sha256(path) != artifact["sha256"]:
            raise ValueError("Capture artifact differs")
        json.loads(path.read_text(encoding="utf-8"))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--expected-binding", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--items", type=int, default=2)
    args = parser.parse_args(argv)
    if not 1 <= args.items <= 2:
        raise ValueError("Bounded diagnostic requires one or two original items")
    root, out = Path(args.root).resolve(), Path(args.output).resolve()
    if root != AUTHORIZED_ROOT:
        raise ValueError("Require authorized server-6 project root")
    if out.exists() or not out.is_relative_to(root.parent / "pipeline"):
        raise ValueError("Require new project-local diagnostic output directory")
    registry_path = Path(args.registry).resolve()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    expected = json.loads(Path(args.expected_binding).read_text(encoding="utf-8"))
    manifest = runner_manifest()
    config = root / "configs/Quard/ctf_hcg_csort" / (MODEL_CLASS + ".yaml")
    dataset_source = root / "framework/dataset/scannetv2.py"
    binding = dict(
        producer_sha256=manifest["producer_sha256"],
        model_source_sha256=model_package_sha256(root, MODEL_CLASS),
        config_sha256=file_sha256(config),
        checkpoint_sha256=file_sha256(args.checkpoint))
    actual = dict(binding, dataset_source_sha256=file_sha256(dataset_source),
                  registry_sha256=file_sha256(registry_path))
    require_expected(expected, actual)
    capacity = check_capacity()
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.15)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    native = build_dataset(cfg.data.train, logging.getLogger("registry_geometry"))
    if Path(inspect.getfile(type(native))).resolve() != dataset_source:
        raise ValueError("Loaded dataset implementation differs from bound source")
    dataset = RegistryDataset(native, out.name, registry, actual["registry_sha256"],
                              binding, actual["dataset_source_sha256"])
    if not dataset.indices:
        raise ValueError("No unambiguous native metadata; no model capture authorized")
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

    def sink(step, index, record):
        dump_new(out / ("geometry_%03d.json" % step), record)
        print(json.dumps(dict(step=step, dataset_index=index, loss=record["loss"],
                              expressions=len(record["geometry"]["rows"]))), flush=True)

    try:
        with torch.no_grad():
            records = capture_planned(model, dataset, binding, args.items, sink)
        joins = dataset.exporter.manifest()
        result = evaluate(registry, actual["registry_sha256"], records, binding, joins)
        final = dict(
            producer_sha256=runner_manifest()["producer_sha256"],
            model_source_sha256=model_package_sha256(root, MODEL_CLASS),
            config_sha256=file_sha256(config),
            checkpoint_sha256=file_sha256(args.checkpoint),
            dataset_source_sha256=file_sha256(dataset_source),
            registry_sha256=file_sha256(registry_path))
        require_expected(expected, final)
        dump_new(out / "bindings.json", joins)
        dump_new(out / "evaluation.json", result)
        artifacts = ["bindings.json", "evaluation.json"] + [
            "geometry_%03d.json" % i for i in range(len(records))]
        report = dict(
            contract=CONTRACT, binding=binding, producer_manifest=manifest,
            expected_binding=actual, capacity_observation=capacity,
            native_capture_completed=True, native_execution_verified=False,
            scientific_validation_complete=False, independent_objectness_resolved=False,
            requested_item_limit=args.items, completed_items=len(records),
            original_dataset_indices=sorted(dataset.consumed),
            registry_denominators=result["overall"],
            config_data_root_override=cfg.data.train.data_root,
            seed=1999, native_train_transforms=True, model_mode="eval/loss",
            artifacts=[dict(path=p, sha256=file_sha256(out / p)) for p in artifacts],
            limitations=[
                "External verification of authorized execution and outputs is required.",
                "New transforms are not historical failure-input replicas.",
                "One or two original scene groups are not full 31-pair coverage.",
                "Failure-local annotation-assisted geometry is not objectness or efficacy.",
                "Capacity check is not a slot reservation; coordinate before execution.",
                "Manifest excludes external packages and full model dependencies.",
                "No backward, training launch, admission or mechanism validation.",
            ])
        dump_new(out / "capture.json", report)
        verify_output(out, expected)
    except Exception as exc:
        dump_new(out / "failure.json", dict(
            contract=CONTRACT, error_type=type(exc).__name__, message=str(exc),
            native_capture_completed=False, scientific_validation_complete=False))
        raise


if __name__ == "__main__":
    main()
