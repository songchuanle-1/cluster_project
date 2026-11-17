"""Operations bound to this cluster-only foreground lease."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ.update(PROJECT_ROOT="D:/project", PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

ROOT = Path("D:/project/cluster_project")
OUT = Path(__file__).resolve().parent
CODE = ROOT / "Cluster"
TOKEN = "0571f421c86b4a618531fbcbed486920"
CID = "fine-leaf-local-point-exchange"
PARENT = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
NAME = PARENT + "_fle_r1"
STAGE = "/data/songcl/Project/Cluster_project/pipeline/fine_exchange_0571f421"
REMOTE_ROOT = "/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", "songcl@192.168.1.115"]


def guard():
    owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert tick.digest(ROOT / "pipeline/goal.json") == "42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec"
    return owner


def save(name, value):
    guard()
    tick.save(OUT / name, value)


def evidence(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": tick.digest(path)}


def run(args, timeout=90, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, **kwargs)


def remote(program, timeout=90):
    result = run(SSH + [shlex.join(["/usr/bin/python3", "-B", "-c", program])], timeout)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)
