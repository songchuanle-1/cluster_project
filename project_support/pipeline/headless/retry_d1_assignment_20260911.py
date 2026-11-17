"""One documented harness-only repair, no re-execution of preparation."""
from datetime import datetime
import json
import subprocess
import yaml
from run_d1_assignment_20260911 import ROOT, P, OUT, REMOTE, run, sha

servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
worker = P / "headless/d1_assignment_20260911.py"
evidence = dict(attempt=1, started=datetime.now().isoformat(), files={})
for name in ("server-4", "server-6"):
    s = servers[name]
    host = f"{s['user']}@{s['host']}"
    before = run(["ssh", host, f"git -C {s['remote_code_root']} diff --binary HEAD"])
    run(["scp", "-q", str(worker), f"{host}:{REMOTE}/{worker.name}"])
    digest = run(["ssh", host, f"sha256sum {REMOTE}/{worker.name}"]).decode().split()[0]
    assert digest == sha(worker)
    assert before == run(["ssh", host, f"git -C {s['remote_code_root']} diff --binary HEAD"])
    evidence["files"][name] = digest
s = servers["server-4"]
host = f"{s['user']}@{s['host']}"
command = (f"set -e\nsource {s['conda_source']}\nconda activate {s['conda_env']}\n"
           "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1\n"
           f"timeout 600s python -u {REMOTE}/{worker.name} --protocol {REMOTE}/protocol.json "
           f"--code-root {s['remote_code_root']} --data-root {s['data_root']} "
           f"--banks /tmp/cluster_d1_expansion_20260911_0715 --out {REMOTE}/result\n")
r = subprocess.run(["ssh", "-o", "BatchMode=yes", host, "bash -s"],
                   input=command.encode(), capture_output=True, timeout=640)
(OUT / "retry1.log").write_bytes(r.stdout + r.stderr)
evidence.update(returncode=r.returncode, finished=datetime.now().isoformat())
(OUT / "retry1.json").write_text(json.dumps(evidence, indent=2))
print((r.stdout + r.stderr).decode(errors="replace")[-5000:])
r.check_returncode()
run(["scp", "-q", f"{host}:{REMOTE}/result/assignment.json", str(OUT)])
assert sha(OUT / "assignment.json") == run(["ssh", host, f"sha256sum {REMOTE}/result/assignment.json"]).decode().split()[0]
print("DOWNLOADED", sha(OUT / "assignment.json"))
