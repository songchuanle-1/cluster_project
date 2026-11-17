"""Deploy hash-checked isolated helpers, then run sequential bounded workers."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

import yaml
from run_d1_grouping_20260911 import run

ROOT = Path("D:/project/cluster_project")
REMOTE = "/tmp/cluster_d1_expansion_20260911_0715"
OLD = "/tmp/cluster_d1_pilot_20260911_0516"
OUT = ROOT / "pipeline/reports/d1_expansion_20260911-0715"


def main():
    assert not OUT.exists()
    OUT.mkdir()
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    evidence = dict(started=datetime.now().isoformat(), deployments={}, cases={})
    files = [ROOT / "pipeline/headless" / n for n in (
        "d1_expansion_20260911.py", "d1_candidate_bank_20260911.py",
        "verify_d1_expansion_20260911.py", "test_d1_candidate_bank_20260911.py")]
    for name in ("server-4", "server-6"):
        srv = servers[name]
        host = f"{srv['user']}@{srv['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
        before = run(ssh + [f"git -C {srv['remote_code_root']} diff --binary HEAD"])
        run(ssh + [f"mkdir {REMOTE}"])
        hashes = {}
        for path in files:
            run(["scp", "-q", str(path), f"{host}:{REMOTE}/{path.name}"])
            hashes[path.name] = run(ssh + [f"sha256sum {REMOTE}/{path.name}"]).decode().split()[0]
            assert hashes[path.name] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert before == run(ssh + [f"git -C {srv['remote_code_root']} diff --binary HEAD"])
        evidence["deployments"][name] = hashes
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
    srv = servers["server-4"]
    host = f"{srv['user']}@{srv['host']}"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
    for name in ("baseline", "m95"):
        preflight = run(ssh + ["nvidia-smi -i 1 --query-gpu=memory.free,memory.used,utilization.gpu --format=csv,noheader,nounits"]).decode().strip()
        assert int(preflight.split(",")[0]) >= 8192
        command = (
            f"set -e\nsource {shlex.quote(srv['conda_source'])}\nconda activate {shlex.quote(srv['conda_env'])}\n"
            f"cd {srv['remote_code_root']}\n"
            'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH:-}"\n'
            "export CUDA_VISIBLE_DEVICES=1 OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1\n"
            f"timeout 720s python -u {REMOTE}/d1_expansion_20260911.py --code-root {srv['remote_code_root']} "
            f"--audit {OLD}/d0_{name}_identity_20260911.json --manifest {OLD}/sample_manifest_v2.json "
            f"--out {REMOTE}/{name}\n")
        print(name, "preflight", preflight, flush=True)
        result = subprocess.run(ssh + ["bash -s"], input=command.encode(), capture_output=True, timeout=760)
        (OUT / f"{name}.log").write_bytes(result.stdout + result.stderr)
        evidence["cases"][name] = dict(returncode=result.returncode, preflight=preflight)
        (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
        print(name, "exit", result.returncode, (result.stdout + result.stderr).decode(errors="replace")[-2200:], flush=True)
        result.check_returncode()
        run(["scp", "-q", "-r", f"{host}:{REMOTE}/{name}", str(OUT)], timeout=180)
        summary = json.loads((OUT / name / "summary.json").read_text())
        for row in summary["rows"]:
            assert hashlib.sha256((OUT / name / row["artifact"]).read_bytes()).hexdigest() == row["artifact_sha256"]
    command = (
        f"set -e\nsource {shlex.quote(srv['conda_source'])}\nconda activate {shlex.quote(srv['conda_env'])}\n"
        "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1\n"
        f"python {REMOTE}/test_d1_candidate_bank_20260911.py {srv['remote_code_root']}\n"
        f"python {REMOTE}/verify_d1_expansion_20260911.py --root {REMOTE} --code-root {srv['remote_code_root']}\n")
    result = subprocess.run(ssh + ["bash -s"], input=command.encode(), capture_output=True, timeout=300)
    (OUT / "readback.log").write_bytes(result.stdout + result.stderr)
    result.check_returncode()
    run(["scp", "-q", f"{host}:{REMOTE}/verification.json", str(OUT)])
    evidence["finished"] = datetime.now().isoformat()
    evidence["verification_returncode"] = result.returncode
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
    print("Expansion and CPU verification finished", OUT, flush=True)


if __name__ == "__main__":
    main()
