"""One compatibility repair; preserve initial failure artifacts."""
from datetime import datetime
import json
import subprocess
import yaml
from run_d1_identity_geometry_20260911 import ROOT, P, OUT, REMOTE, run
from d1_identity_geometry_20260911 import sha

assert json.loads((OUT / "execution.json").read_text())["returncode"] != 0
assert not (OUT / "recovery_execution.json").exists()
servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
worker = P / "headless/d1_identity_geometry_20260911.py"
evidence = dict(attempt=1, started=datetime.now().isoformat(), deployments={})
for name in ("server-4", "server-6"):
    s = servers[name]
    host = f"{s['user']}@{s['host']}"
    ssh = ["ssh", "-o", "BatchMode=yes", host]
    before = run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
    run(["scp", "-q", str(worker), f"{host}:{REMOTE}/{worker.name}"])
    digest = run(ssh + [f"sha256sum {REMOTE}/{worker.name}"]).decode().split()[0]
    assert digest == sha(worker)
    assert before == run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
    evidence["deployments"][name] = digest
s = servers["server-4"]
host = f"{s['user']}@{s['host']}"
command = (
    f"set -e\nsource {s['conda_source']}\nconda activate {s['conda_env']}\n"
    "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1\n"
    f"timeout 600s python -u {REMOTE}/{worker.name} --protocol {REMOTE}/protocol.json "
    f"--audit {REMOTE}/instance_audit.json --data-root {s['data_root']} --out {REMOTE}/result\n")
result = subprocess.run(["ssh", "-o", "BatchMode=yes", host, "bash -s"],
                        input=command.encode(), capture_output=True, timeout=640)
(OUT / "recovery_worker.log").write_bytes(result.stdout + result.stderr)
evidence.update(returncode=result.returncode, finished=datetime.now().isoformat())
(OUT / "recovery_execution.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
print((result.stdout + result.stderr).decode(errors="replace")[-5000:])
result.check_returncode()
run(["scp", "-q", f"{host}:{REMOTE}/result/identity_geometry.json", str(OUT)])
digest = run(["ssh", host, f"sha256sum {REMOTE}/result/identity_geometry.json"]).decode().split()[0]
assert digest == sha(OUT / "identity_geometry.json")
print("DOWNLOADED", digest)
