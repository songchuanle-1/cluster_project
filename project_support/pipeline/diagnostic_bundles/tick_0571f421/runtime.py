"""Pinned server4 runtime; no GPU allocation before identity, hashes and locks."""
import os
os.environ.update(CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES="0", PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="1")
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import signal
import socket
import subprocess
import sys

STAGE = Path(__file__).resolve().parent
MANIFEST = json.loads((STAGE / "manifest.json").read_text())
ROOT = Path(MANIFEST["root"])
NAME = MANIFEST["name"]
PARENT = MANIFEST["parent"]
LOCKS = []


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8*1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def remaining():
    return (datetime.fromisoformat(MANIFEST["deadline_at"]) - datetime.now(timezone.utc)).total_seconds()


def observe():
    assert socket.gethostname() == "dl04-MS-7E06"
    row = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
    cells = [v.strip() for v in row.split(",")]
    assert cells[:2] == ["0", "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
    contexts = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
    assert all(int(line.split(",")[0]) == os.getpid() for line in contexts.splitlines()), "Foreign context; no eviction"
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "gpu": row, "contexts": contexts}


def acquire():
    assert remaining() > 180
    signal.alarm(min(1200, int(remaining()) - 150))
    before = observe()
    assert not before["contexts"]
    for kind in ("training", "diagnostic", "exclusive"):
        handle = open("/tmp/cluster_project_gpu0_" + kind + ".lock", "a+b")
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        LOCKS.append(handle)
    observe()
    verify()
    return before


def verify():
    for name, expected in MANIFEST["source_hashes"].items():
        assert sha(STAGE / NAME / name) == expected, name
    assert sha(STAGE / (NAME + ".yaml")) == MANIFEST["config_sha256"]
    for name, expected in MANIFEST["parent_source_hashes"].items():
        assert sha(ROOT / "framework/model/Quard_model" / PARENT / name) == expected, name
    for name, expected in MANIFEST["hds_source_hashes"].items():
        assert sha(ROOT / name) == expected, name
    assert sha(MANIFEST["checkpoint"]) == MANIFEST["checkpoint_sha256"]
    assert sha("/home/songcl/data/data/scanrefer/ScanRefer_train_new.json") == MANIFEST["annotation_sha256"]
    assert sha(ROOT / "framework/dataset/scannetv2.py") == MANIFEST["dataset_source_sha256"]


def release():
    for handle in reversed(LOCKS):
        handle.close()
    LOCKS.clear()


def setup(candidate=True):
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    from tools import train
    import torch, gorilla
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.75, 0)
    if candidate:
        importlib.import_module("framework.model.Quard_model")
        qualified = "framework.model.Quard_model." + NAME
        spec = importlib.util.spec_from_file_location(qualified, STAGE / NAME / "__init__.py", submodule_search_locations=[str(STAGE / NAME)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
        config = STAGE / (NAME + ".yaml")
    else:
        module = importlib.import_module("framework.model.Quard_model." + PARENT)
        config = ROOT / "configs/Quard/ctf_hcg_csort" / (PARENT + ".yaml")
    cfg = gorilla.Config.fromfile(str(config))
    assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
    assert cfg.dataloader.train.batch_size == 2 and cfg.dataloader.train.num_workers == 4
    cfg.model.data_root = cfg.data.train.data_root = cfg.data.val.data_root = "/home/songcl/data/data/"
    gorilla.set_random_seed(1999)
    model = module.Network(**cfg.model)
    state = torch.load(MANIFEST["checkpoint"], map_location="cpu")["model"]
    extra = set(state) - set(model.state_dict())
    removed = {k for k in extra if candidate and (".cluster_ffn.0." in k or ".cluster_ffn_norm.0." in k)}
    buffers = {"text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"}
    assert extra - removed <= buffers
    assert all(torch.equal(state[k], dict(model.named_buffers())[k]) for k in extra - removed)
    model.load_state_dict({k: v for k, v in state.items() if k not in extra}, strict=True)
    del state
    model.cuda()
    return torch, gorilla, cfg, model, sorted(removed)


def fingerprint(torch, value):
    h = hashlib.sha256()
    def feed(item):
        if torch.is_tensor(item):
            item = item.detach().cpu().contiguous()
            h.update(str((str(item.dtype), tuple(item.shape))).encode())
            h.update(item.numpy().tobytes())
        elif isinstance(item, dict):
            for key in sorted(item):
                h.update(str(key).encode()); feed(item[key])
        elif isinstance(item, (list, tuple)):
            for part in item: feed(part)
        else: h.update(repr(item).encode())
    feed(value)
    return h.hexdigest()


def save(name, value):
    value.update(observed_at=datetime.now(timezone.utc).isoformat(), token=MANIFEST["token"], optimizer_steps=0, training_started=False)
    with (STAGE / name).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
