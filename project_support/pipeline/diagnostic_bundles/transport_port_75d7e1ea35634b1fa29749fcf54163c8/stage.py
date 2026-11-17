"""Stage immutable diagnostic assets; never execute diagnostics on the source."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
import pipeline_monitor as monitor

TOKEN = "75d7e1ea35634b1fa29749fcf54163c8"
PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
ASSETS = BUNDLE / "assets"
ROOT = "/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b"
REMOTE = "/data/songcl/Project/Cluster_project/pipeline/transport_port_" + TOKEN
PYTHON = "/home/songcl/.conda/envs/project_cluster/bin/python"
SOURCE = "songcl@100.64.3.28"
SOURCE_PIPE = "/data3/songcl/Project/Cluster_project/pipeline"
OLD = SOURCE_PIPE + "/diagnostics/bps_population_f8bdf4cb21774bf2af11f959fa12d89a"
OPTS = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=12"]
PINS = {
    "scalar_checkpoint.py": "70055ed9aa157347ca045e536bfef9412dea0447ab1ab0fb6145f9095ee1bc60",
    "task_head.py": "5076dd523e638a650281ec0e77d4721367636505790f1f77073ad7248ab13ef3",
    "raw_native_capture.py": "f29e5f8dd8dd70a8cb7428f8facd7f8e37401ced27e01cdf1e0ef2db19c175e9",
    "native_role_calibration_20261014_0115.py": "0ad3570f4aaf40a4122f92287b4bb88a69a8d387ed5ea917af3c409231fab67b",
    "native_role_head_20261014_0126.py": "684244f76a8e81abb7679a1af7c958262e376888ba18a00e149a6bca2584af4c",
    "native_role_direction_v2_20261014_0010.py": "c5a9c1157421bd9cc386a2da160ac1cf0ae376948ddff5b7f0c6808be690d749",
    "role_gradient_native_20261013_1012.json": "ca0697d740a4d239dfe4465542ac75beed09a0d95b963022fc7b796ec6368187",
    "relation_gradient_native_20261013_0707.json": "f98351adaf132046fca6ca11158a89a21ca8e0fc5a223d635cf3207b214eb7d4",
    "checkpoint_snapshot.pth": "f17f2ec3b08422f033a6683a4030bff1d69a1112514c6ac96dcb38870be735fd",
}


def guard(seconds=30):
    owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > seconds


def command(args, code=None, timeout=60):
    guard(min(timeout + 20, 900))
    p = subprocess.run(args, input=code, text=True, encoding="utf-8", capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError(json.dumps({"args": args, "rc": p.returncode,
                                      "stdout": p.stdout[-3500:], "stderr": p.stderr[-3500:]}))
    return p.stdout


def remote(code, timeout=60, python="python3"):
    return command(["ssh", *OPTS, "server-4", python, "-B", "-"], code, timeout)


def save(name, value):
    path = BUNDLE / (name + ".json")
    assert not path.exists(), "Reconcile recorded stages instead of replay"
    tick.save(path, {"token": TOKEN, "observed_at": datetime.now().astimezone().isoformat(), **value})


def fetch():
    assert not (BUNDLE / "assets_manifest.json").exists()
    ASSETS.mkdir(exist_ok=True)
    locals = {
        "scalar_checkpoint.py": PROJECT / "pipeline/diagnostic_bundles/bps_native_16d02ebf70a846bdad7f1c4f4d30b0c9/scalar_checkpoint.py",
        "task_head.py": PROJECT / "pipeline/diagnostic_bundles/bps_task_2bbb4e0b9a814185a795b2ea2178483f/task_head.py",
        "parameter_transport.py": PROJECT / "pipeline/diagnostic_bundles/parameter_instrument_6e56a11f72b04b37b9595704b8cec930/tested_parameter_transport.py",
        "raw_native_capture.py": PROJECT / "pipeline/diagnostic_bundles/bps_population_f8bdf4cb21774bf2af11f959fa12d89a/native_capture.py",
    }
    for name, source in locals.items():
        if not (ASSETS / name).exists():
            shutil.copyfile(source, ASSETS / name)
    for name in (
        "native_role_calibration_20261014_0115.py", "native_role_head_20261014_0126.py",
        "native_role_direction_v2_20261014_0010.py", "role_gradient_native_20261013_1012.json",
        "relation_gradient_native_20261013_0707.json", "source_manifest.json", "checkpoint_snapshot.pth",
    ):
        target = ASSETS / name
        if target.exists():
            continue
        base = OLD if name in ("source_manifest.json", "checkpoint_snapshot.pth") else SOURCE_PIPE
        command(["scp", *OPTS, SOURCE + ":" + base + "/" + name, str(target)],
                timeout=300 if name.endswith(".pth") else 45)
    rows = {p.name: {"sha256": tick.digest(p), "bytes": p.stat().st_size}
            for p in ASSETS.iterdir() if p.is_file()}
    assert all(rows[name]["sha256"] == expected for name, expected in PINS.items())
    instrument = tick.load(PROJECT / "pipeline/diagnostic_bundles/parameter_instrument_6e56a11f72b04b37b9595704b8cec930/result.json")
    assert rows["parameter_transport.py"]["sha256"] == instrument["source_sha256"]
    save("assets_manifest", {"assets": rows, "science_pins": PINS,
                             "source_reads_only": True, "native_source_executions": 0})
    print(json.dumps({"files": len(rows), "checkpoint_sha256": rows["checkpoint_snapshot.pth"]["sha256"]}))


def deploy():
    assert (BUNDLE / "native_adapter.py").exists()
    assert (BUNDLE / "ast_audit.json").exists()
    rows = tick.load(BUNDLE / "assets_manifest.json")["assets"]
    remote(f"""
import pathlib,subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
p=pathlib.Path({REMOTE!r});p.mkdir(exist_ok=False)
(p/'assets').mkdir()
print('target bundle created')
""")
    for name in rows:
        command(["scp", *OPTS, str(ASSETS / name), "server-4:" + REMOTE + "/assets/"],
                timeout=300 if name.endswith(".pth") else 45)
    for name in ("runtime.py", "native_adapter.py", "cpu_prepare.py", "assets_manifest.json", "ast_audit.json"):
        command(["scp", *OPTS, str(BUNDLE / name), "server-4:" + REMOTE + "/"])
    result = json.loads(remote(f"""
import hashlib,json,pathlib
root=pathlib.Path({REMOTE!r});expected={rows!r}
for name,row in expected.items():
    p=root/'assets'/name;h=hashlib.sha256()
    with p.open('rb') as stream:
        for part in iter(lambda:stream.read(8*1024*1024),b''):h.update(part)
    assert h.hexdigest()==row['sha256'],name
print(json.dumps({{'assets_verified':len(expected),'checkpoint_verified':True}}))
""", timeout=60))
    save("deployment", result)
    print(json.dumps(result))


def prepare():
    env = {
        "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2",
        "PYTHONPATH": ROOT + ":" + ROOT + "/framework/lib:" + REMOTE,
        "LD_LIBRARY_PATH": "/home/songcl/.conda/envs/project_cluster/lib:/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/torch/lib",
        "HF_HUB_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false",
        "TMPDIR": "/data/songcl/Project/Cluster_project/pipeline/tmp", "PYTHONDONTWRITEBYTECODE": "1",
    }
    result = json.loads(remote(f"""
import json,os,subprocess
env=os.environ.copy();env.update({env!r})
p=subprocess.run(['timeout','--signal=TERM','--kill-after=10s','300',{PYTHON!r},
                  '-B',{REMOTE + '/cpu_prepare.py'!r},{ROOT!r},{REMOTE + '/preparation.json'!r}],
                 env=env,cwd={ROOT!r},capture_output=True,text=True)
print(json.dumps({{'returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-5000:]}}))
""", timeout=340))
    command(["scp", *OPTS, "server-4:" + REMOTE + "/preparation.json", str(BUNDLE / "preparation.json")])
    save("preparation_execution", result)
    assert result["returncode"] == 0, json.dumps(result)
    print(json.dumps(tick.load(BUNDLE / "preparation.json")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("fetch", "deploy", "prepare"))
    args = parser.parse_args()
    guard()
    try:
        {"fetch": fetch, "deploy": deploy, "prepare": prepare}[args.stage]()
    except BaseException as exc:
        guard(0)
        tick.save(BUNDLE / ("failure_" + args.stage + "_" + datetime.now().strftime("%H%M%S") + ".json"),
                  {"token": TOKEN, "error_type": type(exc).__name__, "error": str(exc)})
        raise
