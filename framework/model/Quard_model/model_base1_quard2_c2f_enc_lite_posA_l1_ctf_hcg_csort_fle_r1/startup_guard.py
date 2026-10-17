"""Lifetime ownership guard for this candidate's original train.py entry."""
import atexit
from datetime import datetime, timezone
import fcntl
import json
import os
import socket
import subprocess

UUID = "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
_handles = []


def release():
    for handle in reversed(_handles):
        handle.close()
    _handles.clear()


def observe():
    assert socket.gethostname() == "dl04-MS-7E06", "Only verified server4 is enabled for this candidate"
    row = subprocess.check_output([
        "nvidia-smi", "-i", "0", "--query-gpu=index,uuid,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
    cells = [value.strip() for value in row.split(",")]
    assert cells[:2] == ["0", UUID]
    contexts = subprocess.check_output([
        "nvidia-smi", "-i", "0", "--query-compute-apps=pid,used_memory",
        "--format=csv,noheader,nounits"], text=True, timeout=10).strip()
    assert not contexts and int(cells[2]) < 1024 and int(cells[3]) < 10, "GPU0 not idle; no eviction"
    return row


def acquire():
    if _handles:
        raise RuntimeError("Candidate guard cannot be acquired twice")
    import torch
    assert not torch.cuda.is_initialized(), "Refuse late GPU identity binding"
    before = observe()
    try:
        for kind in ("training", "diagnostic", "exclusive"):
            handle = open("/tmp/cluster_project_gpu0_" + kind + ".lock", "a+b")
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BaseException:
                handle.close()
                raise
            _handles.append(handle)
        observe()
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = UUID
        atexit.register(release)
        result = {"observed_at": datetime.now(timezone.utc).isoformat(),
                  "pid": os.getpid(), "hostname": socket.gethostname(),
                  "physical_gpu": 0, "gpu_uuid": UUID, "before": before,
                  "locks": ["training", "diagnostic", "exclusive"],
                  "cuda_initialized": torch.cuda.is_initialized()}
        print("FLE_STARTUP_GUARD=" + json.dumps(result), flush=True)
        return result
    except BaseException:
        release()
        raise


if __name__ == "__main__":
    acquire()
    release()
    print("FLE_STARTUP_GUARD_CHECK_PASS", flush=True)
