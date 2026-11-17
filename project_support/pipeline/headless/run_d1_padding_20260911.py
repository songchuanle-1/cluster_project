"""Isolated hash-checked deployment and bounded sequential diagnostic workers."""
from datetime import datetime
import json
from pathlib import Path
import shlex
import subprocess

import yaml
from d1_candidate_bank_20260911 import sha
from run_d1_grouping_20260911 import run

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_padding_20260911-1310"
REMOTE = "/tmp/cluster_d1_padding_20260911_1310"
OLD = "/tmp/cluster_d1_pilot_20260911_0516"


def main():
    assert not (OUT / "execution.json").exists()
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    files = [P / "headless" / n for n in (
        "d1_padding_capture_20260911.py", "d1_padding_audit_20260911.py",
        "d1_candidate_bank_20260911.py", "d1_assignment_20260911.py", "d1_ordering_20260911.py")]
    files += [OUT / "protocol.json", P / "reviews/motivation_review_20260911-131000.md",
              P / "designs/exp_design_20260911-131000.md"]
    evidence = dict(started=datetime.now().isoformat(), deployments={}, cases={})
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
            assert hashes[path.name] == sha(path)
        assert before == run(ssh + [f"git -C {srv['remote_code_root']} diff --binary HEAD"])
        evidence["deployments"][name] = hashes
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
    srv = servers["server-4"]
    host = f"{srv['user']}@{srv['host']}"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
    environment = (
        f"set -e\nsource {shlex.quote(srv['conda_source'])}\nconda activate {shlex.quote(srv['conda_env'])}\n"
        f"cd {srv['remote_code_root']}\n"
        'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH:-}"\n'
        "export OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1\n")
    for name in ("baseline", "m95"):
        preflight = run(ssh + ["nvidia-smi -i 1 --query-gpu=memory.free,memory.used,utilization.gpu --format=csv,noheader,nounits"]).decode().strip()
        if int(preflight.split(",")[0]) < 8192:
            evidence["cases"][name] = dict(status="resource_guard", preflight=preflight)
            continue
        command = environment + "export CUDA_VISIBLE_DEVICES=1\n" + (
            f"timeout 600s python -u {REMOTE}/d1_padding_capture_20260911.py "
            f"--code-root {srv['remote_code_root']} --audit {OLD}/d0_{name}_identity_20260911.json "
            f"--manifest {OLD}/sample_manifest_v2.json --protocol {REMOTE}/protocol.json --out {REMOTE}/{name}\n")
        print(name, preflight, flush=True)
        result = subprocess.run(ssh + ["bash -s"], input=command.encode(), capture_output=True, timeout=650)
        (OUT / f"{name}.log").write_bytes(result.stdout + result.stderr)
        evidence["cases"][name] = dict(returncode=result.returncode, preflight=preflight)
        (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
        print(name, result.returncode, (result.stdout+result.stderr).decode(errors="replace")[-2400:], flush=True)
        result.check_returncode()
        run(["scp", "-q", "-r", f"{host}:{REMOTE}/{name}", str(OUT)], timeout=180)
        summary = json.loads((OUT / name / "summary.json").read_text())
        for r in summary["rows"]:
            assert sha(OUT / name / r["artifact"]) == r["artifact_sha256"]
    if all((OUT / n / "summary.json").exists() for n in ("baseline", "m95")):
        command = environment + "export CUDA_VISIBLE_DEVICES=''\n" + (
            f"timeout 360s python -u {REMOTE}/d1_padding_audit_20260911.py "
            f"--code-root {srv['remote_code_root']} --data-root {srv['data_root']} "
            f"--protocol {REMOTE}/protocol.json --banks /tmp/cluster_d1_expansion_20260911_0715 "
            f"--capture {REMOTE} --assignment /tmp/cluster_d1_assignment_20260911_1113/result/assignment.json "
            f"--out {REMOTE}/result\n")
        result = subprocess.run(ssh + ["bash -s"], input=command.encode(), capture_output=True, timeout=410)
        (OUT / "audit.log").write_bytes(result.stdout + result.stderr)
        evidence["audit_returncode"] = result.returncode
        (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
        print("audit", result.returncode, (result.stdout+result.stderr).decode(errors="replace")[-2400:], flush=True)
        result.check_returncode()
        run(["scp", "-q", f"{host}:{REMOTE}/result/padding.json", str(OUT)], timeout=90)
    evidence["finished"] = datetime.now().isoformat()
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
