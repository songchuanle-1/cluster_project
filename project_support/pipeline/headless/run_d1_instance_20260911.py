"""Deploy isolated CPU audit to both servers, execute only on server-4."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import yaml
from d1_candidate_bank_20260911 import sha
from run_d1_grouping_20260911 import run

ROOT = Path("D:/project/cluster_project")
OUT = ROOT / "pipeline/reports/d1_instance_20260911-0810"
REMOTE = "/tmp/cluster_d1_instance_20260911_0810"
OLD = "/tmp/cluster_d1_expansion_20260911_0715"


def main():
    assert (OUT / "protocol.json").exists() and not (OUT / "execution.json").exists()
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    evidence = dict(started=datetime.now().isoformat(), deployments={})
    files = [ROOT / "pipeline/headless" / n for n in
             ("d1_instance_audit_20260911.py", "d1_candidate_bank_20260911.py", "test_d1_instance_audit_20260911.py")]
    for name in ("server-4", "server-6"):
        s = servers[name]
        host = f"{s['user']}@{s['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
        before = run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
        run(ssh + [f"mkdir {REMOTE}"])
        hashes = {}
        for f in files:
            run(["scp", "-q", str(f), f"{host}:{REMOTE}/{f.name}"])
            digest = run(ssh + [f"sha256sum {REMOTE}/{f.name}"]).decode().split()[0]
            assert sha(f) == digest
            hashes[f.name] = digest
        assert before == run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
        evidence["deployments"][name] = hashes
    s = servers["server-4"]
    host = f"{s['user']}@{s['host']}"
    command = (
        f"set -e\nsource {s['conda_source']}\nconda activate {s['conda_env']}\n"
        "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1\n"
        f"python {REMOTE}/test_d1_instance_audit_20260911.py\n"
        f"timeout 720s python -u {REMOTE}/d1_instance_audit_20260911.py --banks {OLD} "
        f"--data-root {s['data_root']} --manifest /tmp/cluster_d1_pilot_20260911_0516/sample_manifest_v2.json --out {REMOTE}/result\n")
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", host, "bash -s"],
                            input=command.encode(), capture_output=True, timeout=760)
    (OUT / "worker.log").write_bytes(result.stdout + result.stderr)
    evidence.update(returncode=result.returncode, finished=datetime.now().isoformat())
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print((result.stdout + result.stderr).decode(errors="replace")[-3500:])
    result.check_returncode()
    run(["scp", "-q", f"{host}:{REMOTE}/result/instance_audit.json", str(OUT)])
    digest = run(["ssh", host, f"sha256sum {REMOTE}/result/instance_audit.json"]).decode().split()[0]
    assert digest == sha(OUT / "instance_audit.json")
    print("CPU_AUDIT_DOWNLOADED", digest, flush=True)


if __name__ == "__main__":
    main()
