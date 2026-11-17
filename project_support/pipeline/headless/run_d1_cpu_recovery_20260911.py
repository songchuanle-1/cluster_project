"""Readback-only recovery, preserving the original failure and all GPU outputs."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

import yaml
from run_d1_grouping_20260911 import run
from run_d1_expansion_20260911 import ROOT, REMOTE, OUT


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("audit", "verify"))
    args = p.parse_args()
    filename = ("audit_d1_probability_drift_20260911.py" if args.mode == "audit"
                else "verify_d1_expansion_20260911.py")
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    hashes = {}
    for name in ("server-4", "server-6"):
        s = servers[name]
        host = f"{s['user']}@{s['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
        if args.mode == "verify":
            run(ssh + [f"test ! -e {REMOTE}/{filename}.attempt0 && cp {REMOTE}/{filename} {REMOTE}/{filename}.attempt0"])
        path = ROOT / "pipeline/headless" / filename
        run(["scp", "-q", str(path), f"{host}:{REMOTE}/{filename}"])
        digest = run(ssh + [f"sha256sum {REMOTE}/{filename}"]).decode().split()[0]
        assert digest == hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[name] = digest
    s = servers["server-4"]
    host = f"{s['user']}@{s['host']}"
    command = (
        f"set -e\nsource {shlex.quote(s['conda_source'])}\nconda activate {shlex.quote(s['conda_env'])}\n"
        "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1\n"
        f"python {REMOTE}/{filename} --root {REMOTE}"
        + (f" --code-root {s['remote_code_root']}" if args.mode == "verify" else "") + "\n")
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", host, "bash -s"],
                            input=command.encode(), capture_output=True, timeout=300)
    log = OUT / f"readback_{args.mode}.log"
    assert not log.exists()
    log.write_bytes(result.stdout + result.stderr)
    print((result.stdout + result.stderr).decode(errors="replace")[-4000:])
    result.check_returncode()
    artifact = "probability_drift_audit.json" if args.mode == "audit" else "verification.json"
    run(["scp", "-q", f"{host}:{REMOTE}/{artifact}", str(OUT)])
    evidence = dict(mode=args.mode, finished=datetime.now().isoformat(),
                    returncode=result.returncode, helper_hashes=hashes, gpu_reruns=0)
    (OUT / f"recovery_{args.mode}.json").write_text(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
