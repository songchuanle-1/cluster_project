"""Deploy and run the isolated CPU head-ownership audit on the existing hosts."""
from datetime import datetime
from pathlib import Path
import hashlib
import json
import shlex
import subprocess

import yaml

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_head_20260911-171500"
REMOTE = "/tmp/cluster_d1_head_20260911_171500_r3"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(args, timeout=120, input_bytes=None):
    result = subprocess.run(args, input=input_bytes, capture_output=True, timeout=timeout)
    if result.returncode:
        print((result.stdout + result.stderr).decode(errors="replace"))
    result.check_returncode()
    return result.stdout


def main():
    assert OUT.exists() and (OUT / "protocol.json").exists()
    assert not (OUT / "head.json").exists()
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    files = [
        P / "headless/d1_head_ownership_20260911.py",
        OUT / "protocol.json",
        P / "reports/d0_checkpoint_identity_20260911-0413/d0_baseline_identity_20260911.json",
        P / "reports/d0_checkpoint_identity_20260911-0413/d0_m95_identity_20260911.json",
    ]
    evidence = dict(
        started=datetime.now().isoformat(),
        local_cpu_only=True,
        remote_cpu_only=True,
        no_training=True,
        no_real_data_forward=True,
        no_checkpoint_write=True,
        deployments={},
    )
    for name in ("server-4", "server-6"):
        srv = servers[name]
        host = f"{srv['user']}@{srv['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
        before = run(ssh + [f"git -C {srv['remote_code_root']} diff --binary HEAD"])
        run(ssh + [f"mkdir {REMOTE}"])
        record = {}
        for path in files:
            run(["scp", "-q", str(path), f"{host}:{REMOTE}/{path.name}"])
            digest = run(ssh + [f"sha256sum {REMOTE}/{path.name}"]).decode().split()[0]
            assert digest == sha(path)
            record[path.name] = digest
        assert before == run(ssh + [f"git -C {srv['remote_code_root']} diff --binary HEAD"])
        evidence["deployments"][name] = record
    srv = servers["server-4"]
    host = f"{srv['user']}@{srv['host']}"
    logs = {}
    for name in ("baseline", "m95"):
        command = (
            f"set -e\n"
            f"source {shlex.quote(srv['conda_source'])}\n"
            f"conda activate {shlex.quote(srv['conda_env'])}\n"
            f"cd {srv['remote_code_root']}\n"
            'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH:-}"\n'
            "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1\n"
            f"timeout 300s python -u {REMOTE}/d1_head_ownership_20260911.py "
            f"--model {name} --code-root {srv['remote_code_root']} "
            f"--baseline-audit {REMOTE}/d0_baseline_identity_20260911.json "
            f"--m95-audit {REMOTE}/d0_m95_identity_20260911.json "
            f"--out {REMOTE}/{name}.json\n"
        )
        result = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, "bash -s"],
            input=command.encode(), capture_output=True, timeout=340,
        )
        logs[name] = result.stdout + result.stderr
        (OUT / f"{name}.log").write_bytes(logs[name])
        evidence[f"{name}_returncode"] = result.returncode
        (OUT / "execution.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        result.check_returncode()
        run(["scp", "-q", f"{host}:{REMOTE}/{name}.json", str(OUT / f"{name}.json")], timeout=120)
        evidence[f"{name}_sha256"] = sha(OUT / f"{name}.json")
    evidence["finished"] = datetime.now().isoformat()
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print("HEAD_AUDIT_COMPLETE", OUT)


if __name__ == "__main__":
    main()
