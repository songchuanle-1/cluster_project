"""Create immutable diagnostic protocol and execute one CPU worker on server-4."""
from datetime import datetime
import json
from pathlib import Path
import shlex
import subprocess

import yaml

from run_d1_head_20260911 import sha, run

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/source_head_interference_20260913-1938"
REMOTE = "/tmp/cluster_source_head_interference_20260913_1938"


def main():
    assert not OUT.exists()
    OUT.mkdir()
    goal = json.loads((P / "goal.json").read_text(encoding="utf-8"))
    old = json.loads((P / "reports/d1_assignment_20260911-1113/protocol.json").read_text(encoding="utf-8"))
    identity = json.loads((P / "reports/d0_checkpoint_identity_20260911-0413/d0_m95_identity_20260911.json").read_text())
    srv = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
    host = f"{srv['user']}@{srv['host']}"
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
    original_summary = json.loads(run(ssh + ["cat /tmp/cluster_d1_expansion_20260911_0715/m95/summary.json"]))
    protected = {str(f): sha(f) for f in (P / "queue.json", P / "experiments.csv", P / "goal.json", ROOT / "SERVERS.yaml")}
    code_before = run(ssh + [f"git -C {srv['remote_code_root']} diff --binary HEAD"])
    protocol = dict(created=datetime.now().isoformat(), goal=goal,
                    source_hashes=old["source_hashes"], ids=old["ids"],
                    manifest_sha256=old["manifest_sha256"],
                    capture_summary_sha256="17ea5448f1d3021d634a36eeeaf78dd20db362a9c624cc83a1e9e1ec4956155c",
                    checkpoint=identity["checkpoint"], checkpoint_sha256=identity["checkpoint_sha256"],
                    checkpoint_config=identity["config"], checkpoint_config_sha256=identity["config_sha256"],
                    loss_path=old["models"]["m95"]["loss_path"], eos_coef=.1, outer_loss_weight=.1,
                    input_hashes=original_summary["input_hashes"],
                    preregistered_design_sha256=sha(P / "designs/exp_design_20260913-1938.md"),
                    review_sha256=sha(P / "reviews/motivation_review_20260913-1938.md"))
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2, ensure_ascii=False), encoding="utf-8")
    # Mechanical insertion of the exact authoritative JSON, before any execution.
    review = P / "reviews/motivation_review_20260913-1938.md"
    marker = "## 2. Story Status"
    text = review.read_text(encoding="utf-8")
    assert text.count(marker) == 1 and "```json" not in text
    text = text.replace(marker, "```json\n" + (P / "goal.json").read_text(encoding="utf-8").rstrip() + "\n```\n\n" + marker)
    review.write_text(text, encoding="utf-8")
    protocol["review_sha256"] = sha(review)
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2, ensure_ascii=False), encoding="utf-8")
    run(ssh + [f"mkdir {REMOTE}"])
    files = [P / "headless/source_head_interference_20260913.py",
             P / "headless/d1_assignment_20260911.py", OUT / "protocol.json"]
    for f in files:
        run(["scp", "-q", str(f), f"{host}:{REMOTE}/{f.name}"])
        assert run(ssh + [f"sha256sum {REMOTE}/{f.name}"]).decode().split()[0] == sha(f)
    script = (
        "set -e\n"
        f"source {shlex.quote(srv['conda_source'])}\n"
        f"conda activate {shlex.quote(srv['conda_env'])}\n"
        f"cd {shlex.quote(srv['remote_code_root'])}\n"
        'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH:-}"\n'
        "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1\n"
        f"timeout 900s nice -n 10 python -u {REMOTE}/source_head_interference_20260913.py "
        f"--protocol {REMOTE}/protocol.json --code-root {srv['remote_code_root']} "
        f"--data-root {srv['data_root']} --capture /tmp/cluster_semantic_projection_20260912/full "
        f"--output {REMOTE}/result.json\n")
    process = subprocess.run(ssh + ["bash -s"], input=script.encode(), capture_output=True, timeout=930)
    (OUT / "execution.log").write_bytes(process.stdout + process.stderr)
    evidence = dict(returncode=process.returncode, started=protocol["created"],
                    finished=datetime.now().isoformat(), protected_before=protected,
                    protected_after={f: sha(f) for f in protected},
                    remote_code_diff_unchanged=code_before == run(ssh + [f"git -C {srv['remote_code_root']} diff --binary HEAD"]))
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
    print((process.stdout + process.stderr).decode(errors="replace"))
    process.check_returncode()
    run(["scp", "-q", f"{host}:{REMOTE}/result.json", str(OUT / "result.json")])
    assert run(ssh + [f"sha256sum {REMOTE}/result.json"]).decode().split()[0] == sha(OUT / "result.json")
    assert evidence["remote_code_diff_unchanged"]
    print("SOURCE_HEAD_AUDIT_COMPLETE", OUT)


if __name__ == "__main__":
    main()
