"""Run the frozen native diagnostic only under a future verified foreground lease."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
import pipeline_monitor as monitor

PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
REMOTE = "/data/songcl/Project/Cluster_project/pipeline/" + BUNDLE.name
ROOT = "/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b"
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=12", "server-4"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
    mode = tick.load(PROJECT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground"
    assert owner["token"] == args.token
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"] == mode["target_thread_id"]
    remaining = (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds()
    assert remaining >= (60 if args.check_only else 720), "Insufficient immutable deadline margin"
    server = monitor.load_servers(str(PROJECT))["server-4"]
    assert server["allowed_gpus"] == [0] and server["max_tasks_per_gpu"] == 1
    assert server["dispatch_enabled"] and server["remote_code_root"] == ROOT
    manifest = tick.load(BUNDLE / "frozen_manifest.json")
    for row in manifest["files"]:
        assert tick.digest(PROJECT / row["path"]) == row["sha256"], row["path"]
    output = REMOTE + "/native_parameter_" + args.token + ".json"
    program = f"""
import hashlib,json,os,pathlib,subprocess,sys
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
sys.path.insert(0,{REMOTE!r});import runtime
for row in {manifest["remote_files"]!r}:
    p=pathlib.Path({REMOTE!r})/row['name'];h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
    assert h.hexdigest()==row['sha256'],row['name']
try:
    observation=runtime.guard(pathlib.Path({ROOT!r}))
except RuntimeError as exc:
    assert 'Exclusive GPU0 slot occupied by PID' in str(exc)
    print(json.dumps({{'status':'BLOCKED','reason':str(exc),'gpu_launches':0}}))
    sys.exit(0)
if {args.check_only!r}:
    print(json.dumps({{'status':'AVAILABLE','observation':observation,'gpu_launches':0}}))
    sys.exit(0)
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
    PYTHONPATH={ROOT + ':' + ROOT + '/framework/lib:' + REMOTE!r},
    LD_LIBRARY_PATH='/home/songcl/.conda/envs/project_cluster/lib:/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/torch/lib',
    TMPDIR='/data/songcl/Project/Cluster_project/pipeline/tmp',HF_HUB_OFFLINE='1',
    TOKENIZERS_PARALLELISM='false',PYTHONDONTWRITEBYTECODE='1')
assert not pathlib.Path({output!r}).exists(),'Never replay an existing diagnostic output'
p=subprocess.run(['timeout','--signal=TERM','--kill-after=10s','600',{PYTHON!r},'-B',
    {REMOTE + '/native_adapter.py'!r},'--runner',{REMOTE + '/assets/raw_native_capture.py'!r},
    '--output',{output!r},'--token',{args.token!r}],env=env,cwd={ROOT!r},capture_output=True,text=True)
print(json.dumps({{'returncode':p.returncode,'stdout':p.stdout[-5000:],'stderr':p.stderr[-5000:],
                  'native_result':{output!r},'scientific_pass':'not inferred from process exit'}}))
"""
    run = subprocess.run(SSH + ["python3", "-B", "-"], input=program, text=True,
                         encoding="utf-8", capture_output=True, timeout=60 if args.check_only else 640)
    artifact = BUNDLE / ("launch_guard_" + args.token + ".json" if args.check_only
                         else "native_execution_" + args.token + ".json")
    assert not artifact.exists()
    tick.save(artifact, {"token": args.token, "observed_at": datetime.now().astimezone().isoformat(),
                        "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
    assert run.returncode == 0, run.stderr
    result = json.loads(run.stdout)
    print(json.dumps(result))
    if not args.check_only and result.get("native_result"):
        copied = subprocess.run(["scp", *SSH[1:-1], "server-4:" + output,
                                  str(BUNDLE / ("native_parameter_" + args.token + ".json"))],
                                 capture_output=True, text=True, timeout=45)
        assert copied.returncode == 0, copied.stderr
        assert result["returncode"] == 0, result


if __name__ == "__main__":
    main()
