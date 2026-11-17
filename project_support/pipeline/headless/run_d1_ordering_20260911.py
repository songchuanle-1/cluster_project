"""Isolated upload and bounded CPU execution; never sync active model packages."""
from datetime import datetime
import json
import subprocess
import yaml
from prepare_d1_ordering_20260911 import ROOT, P, OUT, sha

REMOTE = "/tmp/cluster_d1_ordering_20260911_1210"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    if r.returncode:
        raise RuntimeError((r.stdout + r.stderr).decode(errors="replace"))
    return r.stdout


def main():
    assert not (OUT / "execution.json").exists()
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    worker = P / "headless/d1_ordering_20260911.py"
    files = (worker, OUT / "protocol.json",
             P / "reviews/motivation_review_20260911-121000.md",
             P / "designs/exp_design_20260911-121000.md",
             P / "reports/d1_assignment_20260911-1113/assignment.json")
    evidence = dict(started=datetime.now().isoformat(), deployments={})
    for name in ("server-4", "server-6"):
        s = servers[name]
        host = f"{s['user']}@{s['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
        before = run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
        run(ssh + [f"mkdir {REMOTE}"])
        evidence["deployments"][name] = {}
        for file in files:
            run(["scp", "-q", str(file), f"{host}:{REMOTE}/{file.name}"])
            digest = run(ssh + [f"sha256sum {REMOTE}/{file.name}"]).decode().split()[0]
            assert digest == sha(file)
            evidence["deployments"][name][file.name] = digest
        assert before == run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
    s = servers["server-4"]
    host = f"{s['user']}@{s['host']}"
    command = (f"set -e\nsource {s['conda_source']}\nconda activate {s['conda_env']}\n"
               "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1\n"
               f"timeout 600s python -u {REMOTE}/{worker.name} --protocol {REMOTE}/protocol.json "
               f"--assignment {REMOTE}/assignment.json --code-root {s['remote_code_root']} "
               f"--banks /tmp/cluster_d1_expansion_20260911_0715 --out {REMOTE}/result\n")
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", host, "bash -s"],
                       input=command.encode(), capture_output=True, timeout=640)
    (OUT / "worker.log").write_bytes(r.stdout + r.stderr)
    evidence.update(returncode=r.returncode, finished=datetime.now().isoformat())
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
    print((r.stdout + r.stderr).decode(errors="replace")[-6000:])
    r.check_returncode()
    run(["scp", "-q", f"{host}:{REMOTE}/result/ordering.json", str(OUT)])
    assert sha(OUT / "ordering.json") == run(["ssh", host, f"sha256sum {REMOTE}/result/ordering.json"]).decode().split()[0]
    print("DOWNLOADED", sha(OUT / "ordering.json"))


if __name__ == "__main__":
    main()
