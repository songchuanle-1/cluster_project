"""Bounded isolated prepare/execute transport; never invokes tools/train.py."""
import argparse
import json
from pathlib import Path
import subprocess
import yaml
from run_d1_head_20260911 import run, sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/train_step_20260913-2155"
REMOTE = "/tmp/cluster_train_step_20260913_2155"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--identity-followup", action="store_true")
    args = parser.parse_args()
    srv = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
    host = f"{srv['user']}@{srv['host']}"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
    if not args.execute:
        OUT.mkdir(exist_ok=False)
        run(ssh + [f"mkdir {REMOTE}"])
    files = [P / "headless/train_step_20260913.py"]
    files += ([OUT / "acceptance.json"] if args.execute else [
        P / "reports/d0_checkpoint_identity_20260911-0413/d0_m95_identity_20260911.json"])
    for f in files:
        run(["scp", "-q", str(f), f"{host}:{REMOTE}/{f.name}"])
        assert run(ssh + [f"sha256sum {REMOTE}/{f.name}"]).decode().split()[0] == sha(f)
    if args.execute:
        run(ssh + [f"cp {REMOTE}/acceptance.json {REMOTE}/output/acceptance.json"])
        gpu = run(ssh + ["nvidia-smi -i 1 --query-gpu=memory.used --format=csv,noheader,nounits"]).decode().strip()
        assert int(gpu) < 1024, gpu
    script = (
        f"set -e\nsource {srv['conda_source']}\nconda activate {srv['conda_env']}\n"
        f"cd {srv['remote_code_root']}\n"
        'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH:-}"\n'
        f"export CUDA_VISIBLE_DEVICES={'1' if args.execute else chr(39)+chr(39)} OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1\n"
        f"timeout 600s python -u {REMOTE}/train_step_20260913.py --code-root {srv['remote_code_root']} "
        f"--audit {REMOTE}/d0_m95_identity_20260911.json --out {REMOTE}/output "
        f"{'' if args.execute else '--prepare'} {'--identity-followup' if args.identity_followup else ''}\n")
    process = subprocess.run(ssh + ["bash -s"], input=script.encode(), capture_output=True, timeout=630)
    label = "identity" if args.identity_followup else ("execute" if args.execute else "prepare")
    (OUT / f"{label}.log").write_bytes(process.stdout + process.stderr)
    print((process.stdout+process.stderr).decode(errors="replace"))
    process.check_returncode()
    names = (["identity_result.json", "identity_replay.json"] if args.identity_followup else
             (["result.json", "replay.json"] if args.execute else ["manifest.json"]))
    for name in names:
        run(["scp", "-q", f"{host}:{REMOTE}/output/{name}", str(OUT / name)])
        assert run(ssh + [f"sha256sum {REMOTE}/output/{name}"]).decode().split()[0] == sha(OUT / name)


if __name__ == "__main__":
    main()
