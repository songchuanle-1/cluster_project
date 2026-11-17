"""Freeze final diagnostics on both servers and validate unchanged registries."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import yaml
from d1_candidate_bank_20260911 import sha
from run_d1_grouping_20260911 import run
from run_d1_padding_20260911 import ROOT, P, OUT, REMOTE
from close_tick_20260911_0707 import EXPECTED


def main():
    evidence = dict(created=datetime.now().isoformat(), synced={}, state_hashes={})
    evidence["state_hashes"] = {n: sha(P / n) for n in EXPECTED}
    assert evidence["state_hashes"] == EXPECTED
    inventory = json.loads((P / "reports/research_inventory_20260910-1324.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT / r["path"]) == r["sha256"] for r in inventory["analyses"])
    evidence["historical_analyses_verified"] = len(inventory["analyses"])
    evidence["current_analyses"] = len(list((P / "analyses").glob("*.md")))
    assert not subprocess.check_output(["git", "-C", str(ROOT / "Cluster"), "status", "--porcelain"])
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    files = [OUT / n for n in ("padding.json", "verification.json", "diagnostic_report.md", "retry1.json")]
    files += [P / "headless/verify_d1_padding_20260911.py",
              P / "bugfixes/bugfix_20260911-132200.md"]
    for name in ("server-4", "server-6"):
        s = servers[name]
        host = f"{s['user']}@{s['host']}"
        before = run(["ssh", host, f"git -C {s['remote_code_root']} diff --binary HEAD"])
        record = {}
        for path in files:
            run(["scp", "-q", str(path), f"{host}:{REMOTE}/{path.name}"])
            digest = run(["ssh", host, f"sha256sum {REMOTE}/{path.name}"]).decode().split()[0]
            assert digest == sha(path)
            record[path.name] = digest
        assert before == run(["ssh", host, f"git -C {s['remote_code_root']} diff --binary HEAD"])
        evidence["synced"][name] = record
    (OUT / "final_integrity.json").write_text(json.dumps(evidence, indent=2))
    print("INTEGRITY", evidence["historical_analyses_verified"], evidence["current_analyses"])


if __name__ == "__main__":
    main()
