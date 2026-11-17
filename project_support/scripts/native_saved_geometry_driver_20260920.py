"""Bounded saved-input capture orchestration, separate from immutable producer."""
import argparse
from contextlib import nullcontext
import json
from pathlib import Path

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from native_registry_geometry_runner_20260920 import dump_new, require_expected
from referent_geometry_registry_20260919 import evaluate
from saved_geometry_replay_20260920 import prepare_replay, replay_forward, verify_artifacts

CONTRACT = "saved_geometry_driver_v1"


def run_saved(request, exporter, registry, load, model_factory, source_check,
              capacity_check, output, forward_context=nullcontext):
    """Callbacks own native loading and capacity; no training or admission path."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    expected = request["physical"]["observed_binding"]
    require_expected(expected, source_check())
    prepared, joins = prepare_replay(request, exporter, load)
    capacity = capacity_check()
    if capacity.get("coordinated_slot") is not True:
        raise ValueError("Coordinated slot required before model allocation")
    if (capacity.get("process_cap_reached") is not False
            or capacity.get("measured_memory_sufficient") is not True):
        raise ValueError("Current measured GPU capacity required")
    output.mkdir(parents=True, exist_ok=False)
    try:
        # Recheck the bound sources after deserialization and before allocation.
        require_expected(expected, source_check())
        model = model_factory()

        def sink(step, index, record):
            dump_new(output / ("geometry_%03d.json" % step), record)

        with forward_context():
            records = replay_forward(model, prepared, exporter.source_binding, sink)
        result = evaluate(registry, expected["registry_sha256"], records,
                          exporter.source_binding, joins)
        require_expected(expected, source_check())
        for key in ("physical", "collated"):
            verify_artifacts(request[key]["artifacts"], request[key]["scratch"])
        dump_new(output / "bindings.json", joins)
        dump_new(output / "evaluation.json", result)
        names = ["bindings.json", "evaluation.json"] + [
            "geometry_%03d.json" % i for i in range(len(records))]
        report = dict(
            contract=CONTRACT, expected_binding=expected, capacity=capacity,
            completed_items=len(records),
            original_dataset_indices=[saved["dataset_index"] for saved, _ in prepared],
            saved_payload_sha256=[digest for _, digest in prepared],
            full_binding_sha256=fingerprint(joins), registry_denominators=result["overall"],
            native_capture_completed=True, native_execution_verified=False,
            scientific_validation_complete=False, new_train_transforms=False,
            training_launch=False, admission=False,
            artifacts=[dict(path=name, sha256=file_sha256(output / name)) for name in names])
        dump_new(output / "capture.json", report)
        return report
    except Exception as exc:
        dump_new(output / "failure.json", dict(
            contract=CONTRACT, error_type=type(exc).__name__, message=str(exc),
            native_capture_completed=False, scientific_validation_complete=False))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--coordinated-slot", action="store_true")
    args = parser.parse_args(argv)
    if not args.coordinated_slot:
        raise ValueError("External GPU7 slot coordination required")
    import importlib
    import inspect
    import logging
    import os
    import sys
    from frozen_capture_contract_20260916 import model_package_sha256
    from native_geometry_runtime_20260919 import MODEL_CLASS, check_capacity
    from referent_registry_binding_20260919 import BindingExporter

    root = Path("/data3/songcl/Project/Cluster_project/Cluster")
    bundle = root.parent / ("pipeline/diagnostic_bundles/"
                           "registry_geometry_20260920_0315_88b51c997a74")
    output = Path(args.output).resolve()
    if (not root.is_dir() or output.exists()
            or not output.is_relative_to(bundle.parent)):
        raise ValueError("Require authorized native root and fresh diagnostic output")
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    manifest = request["manifest"]
    registry_path = bundle / manifest["registry_path"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    config = root / "configs/Quard/ctf_hcg_csort" / (MODEL_CLASS + ".yaml")
    checkpoint = root.parent / "pipeline/scm_admission_20260914/best.pth"
    dataset_source = root / "framework/dataset/scannetv2.py"
    adapter = Path(inspect.getfile(prepare_replay))

    def source_check():
        if json.loads((bundle / "manifest.json").read_text()) != manifest:
            raise ValueError("Immutable manifest differs")
        for row in manifest["files"]:
            path = (bundle / row["path"]).resolve()
            if not path.is_relative_to(bundle) or file_sha256(path) != row["sha256"]:
                raise ValueError("Immutable source differs")
        # Verify the imported producer paths too, not only unused bundle copies.
        for module in tuple(sys.modules.values()):
            path = getattr(module, "__file__", None)
            if path is None:
                continue
            path = Path(path).resolve()
            for row in manifest["files"]:
                if path.name == Path(row["path"]).name and path.suffix == ".py":
                    if path != (bundle / row["path"]).resolve():
                        raise ValueError("Imported producer outside immutable bundle")
        if (file_sha256(adapter) != request["adapter_sha256"]
                or file_sha256(__file__) != request["driver_sha256"]):
            raise ValueError("Separate replay adapter/driver differs")
        for path, sha in request["physical"]["annotation_and_cache_before"].items():
            if file_sha256(path) != sha:
                raise ValueError("Annotation/cache changed")
        for row in request["physical"]["input_files"]:
            if file_sha256(row["path"]) != row["sha256"]:
                raise ValueError("Scene/CLIP input changed")
        return dict(
            producer_sha256=manifest["expected"]["producer_sha256"],
            model_source_sha256=model_package_sha256(root, MODEL_CLASS),
            config_sha256=file_sha256(config), checkpoint_sha256=file_sha256(checkpoint),
            dataset_source_sha256=file_sha256(dataset_source),
            registry_sha256=file_sha256(registry_path))

    expected = request["physical"]["observed_binding"]
    require_expected(expected, source_check())
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Only physical GPU7 authorized")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset

    torch.set_num_threads(1)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    native = build_dataset(cfg.data.train, logging.getLogger("saved_geometry"))
    if Path(inspect.getfile(type(native))).resolve() != dataset_source:
        raise ValueError("Loaded dataset source differs")
    binding = {k: v for k, v in expected.items()
               if k not in ("dataset_source_sha256", "registry_sha256")}
    exporter = BindingExporter(registry, expected["registry_sha256"],
                               native.scene_inputs, binding, expected["dataset_source_sha256"])

    def capacity_check():
        observation = check_capacity()
        return dict(observation=observation, coordinated_slot=True,
                    process_cap_reached=False, measured_memory_sufficient=True)

    def model_factory():
        torch.cuda.set_per_process_memory_fraction(.15)
        gorilla.set_random_seed(1999)
        model = importlib.import_module(
            "framework.model.Quard_model." + MODEL_CLASS).Network(**cfg.model)
        state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
        for key in ("text_encoder.embeddings.position_ids",
                    "text_encoder.embeddings.token_type_ids"):
            state.pop(key, None)
        model.load_state_dict(state, strict=True)
        return model.cuda().eval()

    report = run_saved(
        request, exporter, registry,
        lambda path: torch.load(path, map_location="cpu", weights_only=False),
        model_factory, source_check, capacity_check, output, torch.no_grad)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
