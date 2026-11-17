"""Hash-sync completed head-audit artifacts without touching trainer deployments."""
from datetime import datetime
import json
from pathlib import Path
import subprocess

import yaml

from close_tick_20260911_0707 import EXPECTED
from d1_candidate_bank_20260911 import sha
from run_d1_grouping_20260911 import run

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_head_20260911-171500"
FINAL = "/tmp/cluster_d1_head_20260911_171500_final"


def main():
    assert (OUT / "diagnostic_report.md").exists()
    assert (OUT / "verification.json").exists()
    verification = json.loads((OUT / "verification.json").read_text(encoding="utf-8"))
    assert verification["status"] == "passed"
    evidence = dict(
        created=datetime.now().isoformat(),
        execution="Local CPU only; isolated remote archival copies",
        state_hashes={name: sha(P / name) for name in EXPECTED},
        deployments={},
    )
    assert evidence["state_hashes"] == EXPECTED
    inventory = json.loads((P / "reports/research_inventory_20260910-1324.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT / row["path"]) == row["sha256"] for row in inventory["analyses"])
    assert not subprocess.check_output(["git", "-C", str(ROOT / "Cluster"), "status", "--porcelain"])
    files = [
        P / "headless/d1_head_ownership_20260911.py",
        P / "headless/prepare_d1_head_20260911.py",
        P / "headless/run_d1_head_20260911.py",
        P / "headless/verify_d1_head_20260911.py",
        P / "reviews/motivation_review_20260911-171500.md",
        P / "designs/exp_design_20260911-171500.md",
        P / "bugfixes/bugfix_20260911-172300.md",
        OUT / "protocol.json",
        OUT / "protocol_retry3.json",
        OUT / "baseline.json",
        OUT / "m95.json",
        OUT / "verification.json",
        OUT / "diagnostic_report.md",
        OUT / "execution.json",
        OUT / "baseline.log",
        OUT / "m95.log",
        OUT / "baseline_attempt1.log",
        OUT / "m95_attempt1.log",
        OUT / "execution_attempt1.json",
    ]
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    for name in ("server-4", "server-6"):
        srv = servers[name]
        host = f"{srv['user']}@{srv['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
        before = run(ssh + [f"git -C {srv['remote_code_root']} diff --binary HEAD"])
        run(ssh + [f"mkdir {FINAL}"])
        record = {}
        for path in files:
            run(["scp", "-q", str(path), f"{host}:{FINAL}/{path.name}"])
            digest = run(ssh + [f"sha256sum {FINAL}/{path.name}"]).decode().split()[0]
            assert digest == sha(path)
            record[path.name] = digest
        assert before == run(ssh + [f"git -C {srv['remote_code_root']} diff --binary HEAD"])
        evidence["deployments"][name] = record
    evidence["historical_analyses_verified"] = len(inventory["analyses"])
    evidence["current_analyses"] = len(list((P / "analyses").glob("*.md")))
    evidence["finished"] = datetime.now().isoformat()
    (OUT / "execution_final.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print("SYNC_COMPLETE", evidence["historical_analyses_verified"], evidence["current_analyses"])


if __name__ == "__main__":
    main()
