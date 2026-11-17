"""Pinned saved-only native factory, called after the same-child scratch probe.

No launcher or host authorization is provided. External package/extension
attestation remains a deployment gate, separate from this input-file contract.
"""
import copy
import importlib
import inspect
import json
import logging
import os
from pathlib import Path
import sys

from frozen_capture_contract_20260916 import file_sha256, model_package_sha256
from native_geometry_runtime_20260919 import MODEL_CLASS
from native_registry_geometry_runner_20260920 import runner_manifest
from native_saved_batch_validation_20260920 import require_cpu_runtime
from pinned_diagnostic_imports_20260920 import checked_digest
from relocated_factory_core_20260920 import assemble_inputs
from saved_physical_location_20260920 import SavedPhysicalLocation
from saved_replay_migration_20260920 import DESTINATION, DESTINATION_DATA


REQUEST = "native_factory.json"
REQUIRED_ASSETS = {
    "scanrefer/ScanRefer_train_new.json",
    "scanrefer/scene_graphs_new_train.json",
    "scannetv2-labels.combined.tsv",
    "roberta-base/tokenizer_config.json",
    "roberta-base/vocab.json",
    "roberta-base/merges.txt",
}
DOCUMENTS = {"migration", "physical", "prior", "registry", "config", "checkpoint"}


def inspect_file(value):
    path = Path(value).absolute()
    if (path.is_symlink() or any(p.is_symlink() for p in path.parents)
            or not path.is_file()):
        raise ValueError("Missing or redirected native factory input")
    return dict(regular_file=True, symlink=False, parent_chain_verified=True,
                sha256=file_sha256(path))


def verify_files(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("Nonempty native input inventory required")
    seen = set()
    for row in rows:
        if set(row) != {"path", "sha256"}:
            raise ValueError("Exact native input record required")
        path = Path(row["path"])
        if not path.is_absolute() or ".." in path.parts or str(path) in seen:
            raise ValueError("Absolute distinct native input paths required")
        seen.add(str(path))
        if inspect_file(path)["sha256"] != checked_digest(row["sha256"]):
            raise ValueError("Native factory input hash differs")


def verify_assets(root, rows):
    """Bind all files in the local tokenizer directory, including optional ones."""
    root = Path(root)
    verify_files(rows)
    mapped = {}
    for row in rows:
        path = Path(row["path"])
        if not path.is_relative_to(root):
            raise ValueError("Constructor asset outside data root")
        mapped[path.relative_to(root).as_posix()] = row["sha256"]
    if not REQUIRED_ASSETS.issubset(mapped):
        raise ValueError("Missing constructor assets")
    tokenizer = root / "roberta-base"
    actual = set()
    for path in tokenizer.rglob("*"):
        if path.is_symlink():
            raise ValueError("Redirected tokenizer asset")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != {name for name in mapped if name.startswith("roberta-base/")}:
        raise ValueError("Tokenizer file inventory differs")


def read_pinned_request():
    """Accept only a request covered by the active producer import manifest."""
    loader = globals().get("__loader__")
    if (not getattr(loader, "active", False)
            or REQUEST not in getattr(loader, "files", {})
            or loader.loaded.get(__name__) is not sys.modules.get(__name__)):
        raise ValueError("Factory requires active pinned request loader")
    loader.verify()
    path, expected = loader.files[REQUEST]
    raw = path.read_bytes()
    import hashlib
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Pinned factory request changed")
    return json.loads(raw)


def construct_inputs(request):
    """Construct metadata and saved-item callbacks, never sample or load a model.

    The caller supplies the host, filesystem and external dependency boundaries.
    All request paths are pinned by read_pinned_request in the public entrypoint.
    """
    if (not isinstance(request, dict)
            or set(request) != {"contract", "code_root", "documents", "assets",
                               "dataset_sources", "capture_id"}
            or request["contract"] != "relocated-native-factory-v1"
            or request["code_root"] != str(DESTINATION / "Cluster")):
        raise ValueError("Server-4 factory request contract differs")
    if not isinstance(request["capture_id"], str) or not request["capture_id"].strip():
        raise ValueError("Explicit saved capture identity required")
    documents = request["documents"]
    if not isinstance(documents, dict) or set(documents) != DOCUMENTS:
        raise ValueError("Exact factory document inventory required")
    root = Path(request["code_root"])
    expected_sources = {
        root / "framework/__init__.py",
        root / "framework/dataset/__init__.py",
        root / "framework/dataset/scannetv2.py"}
    sources = request["dataset_sources"]
    if {Path(row["path"]) for row in sources} != expected_sources:
        raise ValueError("Exact dataset entry source inventory required")
    verify_files(list(documents.values()) + sources)
    verify_assets(DESTINATION_DATA, request["assets"])
    if Path(documents["config"]["path"]) != (
            root / "configs/Quard/ctf_hcg_csort" / (MODEL_CLASS + ".yaml")):
        raise ValueError("Original M95 configuration path required")

    def read(name):
        return json.loads(Path(documents[name]["path"]).read_bytes())

    contract, physical, prior = (read(name) for name in ("migration", "physical", "prior"))
    registry = Path(documents["registry"]["path"]).read_bytes()
    dataset_source = root / "framework/dataset/scannetv2.py"

    def source_check():
        verify_files(list(documents.values()) + sources)
        verify_assets(DESTINATION_DATA, request["assets"])
        return dict(
            producer_sha256=runner_manifest()["producer_sha256"],
            model_source_sha256=model_package_sha256(root, MODEL_CLASS),
            config_sha256=file_sha256(documents["config"]["path"]),
            checkpoint_sha256=file_sha256(documents["checkpoint"]["path"]),
            dataset_source_sha256=file_sha256(dataset_source),
            registry_sha256=file_sha256(documents["registry"]["path"]))

    location = SavedPhysicalLocation(contract, physical, prior, inspect_file, source_check)
    # Check original capture binding and destination bytes before native imports.
    location.verify()
    if any(name in sys.modules for name in ("torch", "gorilla", "framework")):
        raise ValueError("Native dependencies imported before factory verification")
    for name, value in (("HF_HUB_OFFLINE", "1"), ("TRANSFORMERS_OFFLINE", "1"),
                        ("TOKENIZERS_PARALLELISM", "false")):
        os.environ[name] = value
    original_path = list(sys.path)
    try:
        sys.path[:0] = [str(root), str(root / "framework/lib")]
        torch = importlib.import_module("torch")
        require_cpu_runtime(torch)
        gorilla = importlib.import_module("gorilla")
        dataset_module = importlib.import_module("framework.dataset")
        if Path(inspect.getfile(dataset_module)).absolute() != root / "framework/dataset/__init__.py":
            raise ValueError("Native dataset entrypoint identity differs")
        cfg = gorilla.Config.fromfile(documents["config"]["path"])
        train = copy.deepcopy(cfg.data.train)
        if (train.get("type") != "scannetv2_sample_graph_edge"
                or train.get("dataset") != "scanrefer"
                or train.get("prefix") != "train" or train.get("training") is not True):
            raise ValueError("Original ScanRefer TRAIN configuration required")
        train["data_root"] = str(DESTINATION_DATA)
        # No dataloader, __getitem__, manual transform or model construction.
        native = dataset_module.build_dataset(train, logging.getLogger("saved_collation"))
        location.verify()
        require_cpu_runtime(torch)
        return assemble_inputs(location, registry, native, torch,
                               request["capture_id"], dataset_source)
    finally:
        sys.path[:] = original_path


def build_inputs():
    if (not sys.flags.isolated or not sys.dont_write_bytecode
            or os.environ.get("CUDA_VISIBLE_DEVICES") != ""):
        raise ValueError("Isolated CPU child required")
    return construct_inputs(read_pinned_request())
