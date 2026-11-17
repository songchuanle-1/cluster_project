"""Host-only adapter; original diagnostic and model operators are unchanged."""

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

PACKAGE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps"
ROOT = Path("/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b")
ASSETS = Path(__file__).resolve().parent / "assets"
UUID = "GPU-7f82edb9-f620-8045-caea-a75232265cd1"


def guard(root):
    assert Path(root).resolve() == ROOT
    assert subprocess.check_output(["hostname"], text=True).strip() == "dl04-MS-7E06"
    line = subprocess.check_output([
        "nvidia-smi", "-i", "0", "--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits"], text=True).strip()
    cells = [value.strip() for value in line.split(",")]
    assert cells[0] == "0" and cells[1] == UUID
    processes = subprocess.check_output([
        "nvidia-smi", "-i", "0", "--query-compute-apps=pid,used_memory",
        "--format=csv,noheader,nounits"], text=True).strip()
    own = 0
    for row in processes.splitlines():
        pid, memory = [part.strip() for part in row.split(",")]
        if int(pid) != os.getpid():
            raise RuntimeError("Exclusive GPU0 slot occupied by PID " + pid)
        own += int(memory)
    # Keep the .25 allocator cap; account for our own allocation after startup.
    assert int(cells[4]) + own >= 30000, "Idle-equivalent headroom below 30000MiB"
    assert own <= int(int(cells[2]) * .25) + 1024, "Diagnostic allocation budget exceeded"
    return {"gpu": line, "processes": processes, "own_memory_mib": own,
            "scope": "Exclusive authorized GPU0, no foreign process or extra task slot."}


def get_native(runner):
    path = Path(runner)
    assert path.resolve() == (ASSETS / "raw_native_capture.py").resolve()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "f29e5f8dd8dd70a8cb7428f8facd7f8e37401ced27e01cdf1e0ef2db19c175e9"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["OMP_NUM_THREADS"] = "2"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_OFFLINE"] = "1"
    import torch
    torch.set_num_threads(2)
    names = {"digest", "input_hash", "save"}
    functions = [node for node in ast.parse(path.read_text()).body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in functions} == names
    namespace = {"Path": Path, "hashlib": hashlib, "json": json, "torch": torch}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), "exec"), namespace)
    return SimpleNamespace(torch=torch, PACKAGE=PACKAGE, guard=guard,
                           **{name: namespace[name] for name in names})
