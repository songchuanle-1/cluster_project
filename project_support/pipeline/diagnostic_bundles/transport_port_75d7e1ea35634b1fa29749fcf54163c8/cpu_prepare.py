"""Non-GPU preparation: immutable state, native inputs and actual slot guard."""

from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

root, output = sys.argv[1:]
bundle = Path(__file__).resolve().parent
assets = bundle / "assets"
report = {"observed_at": datetime.now(timezone.utc).isoformat(), "gpu_forwards": 0,
          "parameter_gradient_calls": 0, "optimizer_steps": 0}
try:
    assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    assert subprocess.check_output(["hostname"], text=True).strip() == "dl04-MS-7E06"
    manifest = json.loads((bundle / "assets_manifest.json").read_text())["assets"]
    for name, row in manifest.items():
        h = hashlib.sha256()
        with (assets / name).open("rb") as stream:
            for block in iter(lambda: stream.read(8 * 1024**2), b""):
                h.update(block)
        assert h.hexdigest() == row["sha256"], name
    spec = importlib.util.spec_from_file_location("prepared_native_adapter", bundle / "native_adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report["adapter_import_no_execution"] = True
    import torch
    import tools.train
    import gorilla
    from framework import resolve_network
    from framework.dataset import build_dataset
    from framework.utils import get_root_logger
    torch.set_num_threads(2)
    assert not torch.cuda.is_initialized()
    config = "configs/Quard/bps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps.yaml"
    cfg = gorilla.Config.fromfile(str(Path(root) / config))
    assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
    package = Path(root) / "framework/model/Quard_model" / Path(config).stem
    source_manifest = json.loads((assets / "source_manifest.json").read_text())
    for name, expected in source_manifest["package"].items():
        assert hashlib.sha256((package / name).read_bytes()).hexdigest() == expected, name
    saved = torch.load(assets / "checkpoint_snapshot.pth", map_location="cpu", weights_only=False, mmap=True)
    assert saved["meta"]["epoch"] == 4
    gorilla.set_random_seed(1999)
    Network = resolve_network(config)
    assert Path(config).stem in Network.__module__
    model = Network(**cfg.model)
    state = saved["model"]
    extra = set(state) - set(model.state_dict())
    assert extra == {"text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"}
    buffers = dict(model.named_buffers())
    assert all(torch.equal(state[key].cpu(), buffers[key].cpu()) and state[key].dtype == buffers[key].dtype
               for key in extra)
    model.load_state_dict({key: value for key, value in state.items() if key not in extra}, strict=True)
    cohort = {}
    for name in ("role_gradient_native_20261013_1012.json", "relation_gradient_native_20261013_0707.json"):
        for row in json.loads((assets / name).read_text())["rows"]:
            if row["trial"] == 0:
                group = row["selection"]["group"]
                cohort.setdefault(group, row["ann_ids"])
                assert cohort[group] == row["ann_ids"]
    first = list(cohort)[:4]
    assert first == [0, 60, 101, 124]
    dataset = build_dataset(cfg.data.train, get_root_logger())
    raw = __import__("ast").parse((assets / "raw_native_capture.py").read_text())
    function = next(node for node in raw.body if getattr(node, "name", None) == "input_hash")
    namespace = {"torch": torch, "hashlib": hashlib}
    exec(compile(__import__("ast").Module(body=[function], type_ignores=[]), "frozen_input_hash", "exec"), namespace)
    prepared = []
    for group in first:
        hashes = []
        for repeat in range(2):
            gorilla.set_random_seed(1999)
            batch = dataset.collate_fn([dataset[group]])
            assert list(map(int, batch["ann_ids"])) == cohort[group]
            assert all(value.device.type == "cpu" for value in batch.values() if isinstance(value, torch.Tensor))
            hashes.append(namespace["input_hash"](batch))
        assert hashes[0] == hashes[1]
        prepared.append({"group": group, "ann_ids": cohort[group], "input_sha256": hashes[0],
                         "repeat_exact": True})
    import runtime
    try:
        observation = runtime.guard(Path(root))
        slot = {"status": "available", "observation": observation}
    except RuntimeError as exc:
        assert "Exclusive GPU0 slot occupied by PID" in str(exc)
        slot = {"status": "occupied", "reason": str(exc)}
    handle = open("/tmp/cluster_project_gpu0_m201_migration.lock", "a+")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        training_lease = "available"
        fcntl.flock(handle, fcntl.LOCK_UN)
    except BlockingIOError:
        training_lease = "held"
    finally:
        handle.close()
    assert not torch.cuda.is_initialized()
    report.update(status="PASS", checkpoint_meta=saved["meta"], state_strict_after_identical_constant_audit=True,
                  assets_verified=len(manifest), package_source_exact=True,
                  native_cpu_groups=prepared, native_getter_calls=8, cuda_initialized=False,
                  gpu_slot=slot, training_lease=training_lease,
                  scope="All non-GPU adapter/state/input preparation completed. No native forward or model parameter gradient; old scientific failures remain. Resource denial is not a failed scientific test.")
except BaseException as exc:
    report.update(status="FAIL", error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
    raise
finally:
    Path(output).write_text(json.dumps(report, indent=2, default=lambda value: value.item()))
