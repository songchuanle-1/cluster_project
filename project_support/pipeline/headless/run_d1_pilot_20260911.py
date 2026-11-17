"""Scoped helper deployment and sequential bounded diagnostic evaluation."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

import yaml

ROOT = Path("D:/project/cluster_project")
OUT = ROOT / "pipeline/reports/d1_pilot_20260911-0516"
REMOTE = "/tmp/cluster_d1_pilot_20260911_0516"


def run(args, timeout=90):
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode:
        print(result.stdout.decode(errors="replace"))
        print(result.stderr.decode(errors="replace"))
        result.check_returncode()
    return result.stdout


def main():
    OUT.mkdir(exist_ok=True)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    evidence = dict(started=datetime.now().isoformat(), deployments={}, cases={})
    files = [ROOT / "pipeline/headless" / name for name in (
        "d1_candidate_bank_20260911.py", "test_d1_candidate_bank_20260911.py")]
    files += list((ROOT / "pipeline/reports/d0_checkpoint_identity_20260911-0413").glob("d0_*_identity_20260911.json"))
    files += [ROOT / "pipeline/reports/d0_inventory_20260911-0316/sample_manifest_v2.json"]
    for name in ("server-4", "server-6"):
        srv = servers[name]
        target = f"{srv['user']}@{srv['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", target]
        code = shlex.quote(srv["remote_code_root"])
        before = run(ssh + [f"git -C {code} diff --binary HEAD"])
        run(ssh + [f"mkdir -p {REMOTE}"])
        for path in files:
            run(["scp", "-q", str(path), f"{target}:{REMOTE}/{path.name}"])
            remote_hash = run(ssh + [f"sha256sum {REMOTE}/{path.name}"]).decode().split()[0]
            assert remote_hash == hashlib.sha256(path.read_bytes()).hexdigest()
        after = run(ssh + [f"git -C {code} diff --binary HEAD"])
        assert before == after
        evidence["deployments"][name] = dict(files={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                                  for p in files}, active_tracked_diff_unchanged=True)
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
    srv = servers["server-4"]
    target = f"{srv['user']}@{srv['host']}"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", target]
    env = (
        f"source {shlex.quote(srv['conda_source'])}\n"
        f"conda activate {shlex.quote(srv['conda_env'])}\n"
        f"cd {shlex.quote(srv['remote_code_root'])}\n"
        'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH:-}"\n'
        "export CUDA_VISIBLE_DEVICES=1 OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1\n"
    )
    tests = env + f"python {REMOTE}/test_d1_candidate_bank_20260911.py {srv['remote_code_root']}"
    completed = subprocess.run(ssh + ["bash -s"], input=tests.encode(), capture_output=True, timeout=120)
    (OUT / "unit_tests.log").write_bytes(completed.stdout + completed.stderr)
    completed.check_returncode()
    for name in ("baseline", "m95"):
        preflight = run(ssh + [
            "nvidia-smi -i 1 --query-gpu=memory.free,memory.used,utilization.gpu --format=csv,noheader,nounits"
        ]).decode().strip()
        assert int(preflight.split(",")[0]) >= 8192
        command = env + (
            f"timeout 720s python -u {REMOTE}/d1_candidate_bank_20260911.py "
            f"--code-root {srv['remote_code_root']} "
            f"--audit {REMOTE}/d0_{name}_identity_20260911.json "
            f"--manifest {REMOTE}/sample_manifest_v2.json "
            f"--out {REMOTE}/{name} --scene-limit 2\n")
        print(name, "preflight", preflight, flush=True)
        completed = subprocess.run(ssh + ["bash -s"], input=command.encode(),
                                   capture_output=True, timeout=760)
        (OUT / f"{name}_worker.log").write_bytes(completed.stdout + completed.stderr)
        evidence["cases"][name] = dict(returncode=completed.returncode, preflight=preflight)
        (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
        print(name, "exit", completed.returncode,
              completed.stdout.decode(errors="replace")[-1800:],
              completed.stderr.decode(errors="replace")[-1200:], flush=True)
        completed.check_returncode()
        run(["scp", "-q", "-r", f"{target}:{REMOTE}/{name}", str(OUT)], timeout=120)
        summary = json.loads((OUT / name / "summary.json").read_text())
        for row in summary["rows"]:
            assert hashlib.sha256((OUT / name / row["artifact"]).read_bytes()).hexdigest() == row["artifact_sha256"]
        assert summary["status"] == "pilot_complete"
    evidence["finished"] = datetime.now().isoformat()
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
    print("Pilot artifacts downloaded and hash verified", OUT)


if __name__ == "__main__":
    main()
