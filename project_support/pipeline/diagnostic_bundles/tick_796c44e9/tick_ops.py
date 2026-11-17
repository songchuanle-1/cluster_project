"""Lease-bound orchestration for one cluster_project foreground tick."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ.update(PROJECT_ROOT="D:/project", PYTHONDONTWRITEBYTECODE="1")
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

ROOT = Path("D:/project/cluster_project")
OUT = Path(__file__).resolve().parent
PRIOR = ROOT / "pipeline/diagnostic_bundles/tick_21500d1a"
TOKEN = "796c44e9d39e4eb6a3305dd95a943fc7"
CID = "m202-trained-scale-contribution"
REMOTE_STAGE = "/data/songcl/Project/Cluster_project/pipeline/scale_diag_796c44e9"


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


def run(args, timeout=90):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def ssh(program, host="192.168.1.115", timeout=90):
    result = run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
                  "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=3", "songcl@" + host,
                  shlex.join(["/usr/bin/python3", "-B", "-c", program])], timeout)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def probe():
    guard()
    program = r'''
import datetime,fcntl,json,socket,subprocess
assert socket.gethostname()=="dl04-MS-7E06"
row=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
assert [v.strip() for v in row.split(",")][:2]==["0","GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
contexts=subprocess.check_output(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
locks={}
for kind in ("training","diagnostic","exclusive"):
    path="/tmp/cluster_project_gpu0_"+kind+".lock"
    with open(path,"rb") as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:locks[kind]="held"
        else:
            locks[kind]="acquired_and_released"
            fcntl.flock(handle,fcntl.LOCK_UN)
print(json.dumps({"observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"hostname":socket.gethostname(),"gpu":row,"contexts":contexts,"locks":locks,"no_gpu_computation_or_signals":True}))
'''
    observed = ssh(program)
    save("live_resource_precheck.json", observed)
    assert not observed["contexts"], "Authorized GPU0 has a live context; preserve it"
    assert all(v == "acquired_and_released" for v in observed["locks"].values())
    print(json.dumps(observed, indent=2))


def prepare():
    owner = guard()
    from scale_terms import cpu_controls
    for filename in ("tick_ops.py", "scale_terms.py", "scale_native.py"):
        compile((OUT / filename).read_text(encoding="utf-8"), filename, "exec")
    save("cpu_controls.json", cpu_controls())
    previous = tick.load(PRIOR / "trained_suffix_manifest.json")
    manifest = {key: previous[key] for key in ("root", "model", "config", "checkpoint", "checkpoint_sha256", "source_hashes")}
    assert manifest["checkpoint_sha256"] == "c863202420152aeeef3efd2b21932f24a33a636f3db2904e6772cfa7ece078e8"
    manifest.update(deadline_at=owner["deadline_at"], token=TOKEN,
                    producer_hashes={name: tick.digest(OUT / name) for name in ("scale_terms.py", "scale_native.py")})
    save("scale_manifest.json", manifest)
    work = tick.load(ROOT / "pipeline/research_work.json")
    assert not any(c["id"] == CID for c in work["candidates"]), "Do not register twice"
    candidate = {"id": CID, "stage": "validation", "kind": "TRAIN_mechanistic_diagnostic",
        "hypothesis": "Every fine/middle/coarse support has nonnegative scene-mean fixed-normal-query point-IoU Shapley contribution on all four already-fixed TRAIN scenes; a negative cell refutes only this local all-scales-beneficial premise.",
        "matched_control": "Same captured prefix, original weighted sum, frozen native projection/norm/ILA/decoder,1e-6; empty-scale and true-zero-message are distinct controls.",
        "next_action": "Run4native TRAIN captures and36suffix replays on pinned idle server4GPU0 under3locks; retain all controls and signed per-scene reports. No model/training admission.",
        "evidence": [evidence(OUT / name) for name in ("scale_prereg.md", "scale_terms.py", "cpu_controls.json", "scale_manifest.json", "scale_native.py")],
        "preregistered_at": datetime.now(timezone.utc).isoformat(), "failure_scope": "inconclusive"}
    work["candidates"].append(candidate)
    guard()
    tick.save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({"registered": CID, "stage": candidate["stage"], "cpu_controls": 4, "model_revisions": 0, "admissions": 0, "training_launches": 0}))


def execute():
    owner = guard()
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 900
    probe()
    result = run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", "songcl@192.168.1.115", shlex.join(["mkdir", "-p", REMOTE_STAGE])])
    assert result.returncode == 0, result.stderr
    for name in ("scale_native.py", "scale_terms.py", "scale_manifest.json", "scale_prereg.md"):
        guard()
        result = run(["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", str(OUT / name), "songcl@192.168.1.115:" + REMOTE_STAGE + "/"], 45)
        assert result.returncode == 0, result.stderr
    guard()
    command = "source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "
    command += shlex.join(["env", "PYTHONDONTWRITEBYTECODE=1", "python", "-B", REMOTE_STAGE + "/scale_native.py"])
    result = run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=3", "songcl@192.168.1.115", shlex.join(["bash", "-lc", command])], 780)
    save("scale_execution.json", {"observed_at": datetime.now(timezone.utc).isoformat(), "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    fetch = run(["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", "songcl@192.168.1.115:" + REMOTE_STAGE + "/scale_result.json", str(OUT / "scale_result.json")], 45)
    save("scale_fetch.json", {"returncode": fetch.returncode, "stderr": fetch.stderr})
    assert result.returncode == 0, result.stderr[-5000:]
    assert fetch.returncode == 0, fetch.stderr
    payload = tick.load(OUT / "scale_result.json")
    assert payload["passed_controls"]
    keys = ("observed_at", "passed_controls", "expressions", "independent_scenes", "native_forwards", "native_suffix_replays", "scene_scale_point_iou_shapley", "mean_scale_point_iou_shapley", "local_all_scales_nonnegative")
    print(json.dumps({k: payload[k] for k in keys}, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "probe": probe, "execute": execute}[sys.argv[1]]()
