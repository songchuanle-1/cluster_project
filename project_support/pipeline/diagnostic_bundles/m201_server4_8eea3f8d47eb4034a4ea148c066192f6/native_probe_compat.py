"""Verify serialization-only buffer differences and native resume/backward."""

from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

root, config, checkpoint, output = sys.argv[1:]
report = {"observed_at": datetime.now(timezone.utc).isoformat(), "optimizer_steps": 0}
lease = open("/tmp/cluster_project_gpu0_exclusive.lock", "a+")
try:
    fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert subprocess.check_output(["hostname"], text=True).strip() == "dl04-MS-7E06"
    gpu = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-gpu=uuid,memory.free",
                                   "--format=csv,noheader,nounits"], text=True).strip()
    assert gpu.split(",")[0] == "GPU-7f82edb9-f620-8045-caea-a75232265cd1"
    assert int(gpu.split(",")[1]) > 30000
    assert not subprocess.check_output(["nvidia-smi", "-i", "0", "--query-compute-apps=pid",
                                        "--format=csv,noheader"], text=True).strip()
    import torch
    import gorilla
    import tools.train
    from framework import resolve_network
    from framework.dataset import build_dataset
    from framework.utils import get_root_logger

    cfg = gorilla.Config.fromfile(str(Path(root) / config))
    gorilla.set_random_seed(cfg.train.seed)
    Network = resolve_network(config)
    assert Network.__module__.split(".")[-2] == Path(config).stem, "No fallback network"
    saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model = Network(**cfg.model)
    native_state = model.state_dict()
    missing = sorted(native_state.keys() - saved["model"].keys())
    extra = sorted(saved["model"].keys() - native_state.keys())
    assert not missing
    assert extra == ["text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"]
    buffers = dict(model.named_buffers())
    for name in extra:
        assert name in buffers
        assert torch.equal(saved["model"][name].cpu(), buffers[name].cpu()), name
        assert saved["model"][name].dtype == buffers[name].dtype
    # Only verified identical, nonpersistent constants are omitted here.
    normalized = {key: value for key, value in saved["model"].items() if key not in extra}
    incompatible = model.load_state_dict(normalized, strict=True)
    assert not incompatible.missing_keys and not incompatible.unexpected_keys
    report.update(checkpoint_missing_keys=missing, checkpoint_extra_keys=extra,
                  nonpersistent_buffer_values_exact=True, strict_parameter_load=True)
    model.cuda().train()
    optimizer = gorilla.build_optimizer(model, cfg.optimizer)
    scheduler = gorilla.build_lr_scheduler(optimizer, cfg.lr_scheduler)
    meta = gorilla.resume(model, checkpoint, optimizer, scheduler, strict=False, map_location="cpu")
    assert meta == saved["meta"]
    assert scheduler.state_dict() == saved["scheduler"]
    assert len(optimizer.state) == len(saved["optimizer"]["state"])
    for index, original in saved["optimizer"]["state"].items():
        restored = optimizer.state_dict()["state"][index]
        assert restored.keys() == original.keys()
        for key, value in original.items():
            if isinstance(value, torch.Tensor):
                assert torch.equal(value.cpu(), restored[key].cpu())
            else:
                assert value == restored[key]
    logger = get_root_logger()
    dataset = build_dataset(cfg.data.train, logger)
    val_dataset = build_dataset(cfg.data.val, logger)
    batch = dataset.collate_fn([dataset[0], dataset[1]])
    torch.cuda.reset_peak_memory_stats()
    started = time.time()
    loss, losses = model(batch, mode="loss")
    assert torch.isfinite(loss).all()
    loss.backward()
    gradients = [(name, param.grad) for name, param in model.named_parameters() if param.grad is not None]
    assert gradients and all(torch.isfinite(gradient).all() for _, gradient in gradients)
    assert any(gradient.abs().sum() > 0 for _, gradient in gradients)
    torch.cuda.synchronize()
    report.update(
        status="PASS", gpu=gpu, torch=torch.__version__, cuda=torch.version.cuda,
        code_root=root, network_module=Network.__module__, native_resume_strict=False,
        resume_meta=meta, scheduler_restored=True, optimizer_tensors_restored_exact=True,
        optimizer_state_count=len(optimizer.state), train_groups=len(dataset), val_groups=len(val_dataset),
        batch_size=2, scan_ids=batch["scan_ids"], loss=float(loss.detach()),
        loss_components={key: float(value.detach()) for key, value in losses.items()},
        finite_gradient_tensors=len(gradients),
        peak_allocated_mib=torch.cuda.max_memory_allocated() / 1024**2,
        peak_reserved_mib=torch.cuda.max_memory_reserved() / 1024**2,
        seconds=time.time() - started,
        scope="Host/ABI/dataset/resume readiness only. Original strict-load failure is retained; only exactly equal nonpersistent buffer serialization is reconciled. No new admission or trained benefit claim.",
    )
except BaseException as exc:
    report.update(status="FAIL", error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
    raise
finally:
    Path(output).write_text(json.dumps(report, indent=2, default=lambda value: value.item()))
    fcntl.flock(lease, fcntl.LOCK_UN)
    lease.close()
