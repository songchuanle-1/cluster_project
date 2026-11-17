"""Freeze exact diagnostic inputs after CPU controls; never initialize CUDA."""
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
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def guard():
    owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == "d7dee0a18225465284ff88f668cfc050"
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])


def save(name, value):
    guard()
    tick.save(OUT / name, value)

guard()
program = r'''
import datetime,hashlib,json,pathlib,socket,sys
assert socket.gethostname()=='sysu311-MS-7C59'
import torch
assert not torch.cuda.is_initialized()
root=pathlib.Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
checkpoint=root.parent/'pipeline/server3_fallback_abdff23d/frozen_m95.pth'
h=hashlib.sha256()
with checkpoint.open('rb') as handle:
    for block in iter(lambda:handle.read(8*1024*1024),b''):h.update(block)
expected='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
assert h.hexdigest()==expected
config='configs/Quard/ctf_hcg_csort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml'
sha=hashlib.sha256((root/config).read_bytes()).hexdigest()
assert sha=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'hostname':socket.gethostname(),'python_executable':sys.executable,'python':sys.version,
 'torch':torch.__version__,'cuda_initialized':torch.cuda.is_initialized(),
 'checkpoint':str(checkpoint),'checkpoint_sha256':expected,'checkpoint_bytes':checkpoint.stat().st_size,
 'config':config,'config_sha256':sha,'root':str(root),'native_forwards':0,'optimizer_steps':0}))
'''
command = "source /home/sysu311/anaconda3/etc/profile.d/conda.sh; conda activate 3d-stmn; " + shlex.join(
    ["env", "CUDA_VISIBLE_DEVICES=", "PYTHONDONTWRITEBYTECODE=1", "python", "-B", "-c", program])
response = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
                           "songcl@192.168.1.120", shlex.join(["bash", "-lc", command])],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
assert response.returncode == 0, response.stderr
assets = json.loads(response.stdout)
save("assets_d7dee0a1.json", assets)
files = ("aligned_evidence.py", "test_aligned_evidence.py", "native_equivalence.py")
for name in files:
    compile((OUT / name).read_text(encoding="utf-8"), name, "exec")
resources = tick.load(OUT / "resources_d7dee0a1.json")
sources = dict(resources["server-3"]["source_hashes"])
sources[assets["config"]] = assets["config_sha256"]
manifest = {key: assets[key] for key in ("hostname", "root", "checkpoint", "checkpoint_sha256", "config")}
manifest.update({"physical_gpu": 1, "gpu_uuid": "GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0",
                 "model": BASE, "train_groups": [0, 60, 101, 124], "seed": 1999,
                 "source_hashes": sources,
                 "producer_hashes": {name: tick.digest(OUT / name) for name in files},
                 "lifetime_locks": list(resources["server-3"]["samples"][0]["lock_observation"]),
                 "native_test_status": "UNRUN: both authorized slots occupied; no upload or GPU execution",
                 "scope": "Existing M95 weights for exporter equivalence, never HDS resume or trained benefit"})
save("native_manifest.json", manifest)
save("preparation_result.json", {"observed_at": datetime.now(timezone.utc).isoformat(),
     "cpu_tests_passed": tick.load(OUT / "cpu_controls.json")["tests_run"],
     "source_contract_passed": tick.load(OUT / "source_contract.json")["passed"],
     "static_compile_files": list(files), "static_compile_passed": True,
     "current_checkpoint_hash_verified_on_cpu": True, "cuda_initialized": assets["cuda_initialized"],
     "native_forwards": 0, "optimizer_steps": 0,
     "scope": "CPU implementation/preparation complete; native equivalence remains unmeasured"})
print(json.dumps({"checkpoint_sha256": assets["checkpoint_sha256"], "python": assets["python_executable"],
                  "torch": assets["torch"], "cuda_initialized": assets["cuda_initialized"],
                  "native_manifest_saved": True, "native_test_status": manifest["native_test_status"]}, indent=2))
