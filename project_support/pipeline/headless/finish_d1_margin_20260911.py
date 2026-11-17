"""Hash-sync diagnostic artifacts only; leave all trainer deployments untouched."""
from datetime import datetime
import json
import subprocess
import yaml
from prepare_d1_margin_20260911 import ROOT,P,OUT
from d1_candidate_bank_20260911 import sha
from run_d1_grouping_20260911 import run
from close_tick_20260911_0707 import EXPECTED


def main():
    assert not (OUT / "execution.json").exists()
    remote = "/tmp/cluster_d1_margin_20260911_1410"
    files = [P / "headless" / n for n in (
        "prepare_d1_margin_20260911.py", "d1_margin_20260911.py", "verify_d1_margin_20260911.py")]
    files += [OUT / n for n in ("protocol.json","margin.json","verification.json","diagnostic_report.md")]
    files += [P / "reviews/motivation_review_20260911-141000.md",
              P / "designs/exp_design_20260911-141000.md"]
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    evidence = dict(created=datetime.now().isoformat(), execution="Local CPU only; remote archival copies",
                    deployments={}, state_hashes={n:sha(P/n) for n in EXPECTED})
    assert evidence["state_hashes"] == EXPECTED
    inv = json.loads((P / "reports/research_inventory_20260910-1324.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT / r["path"]) == r["sha256"] for r in inv["analyses"])
    evidence.update(historical_analyses_verified=len(inv["analyses"]),
                    current_analyses=len(list((P / "analyses").glob("*.md"))))
    assert not subprocess.check_output(["git","-C",str(ROOT/"Cluster"),"status","--porcelain"])
    for name in ("server-4","server-6"):
        srv = servers[name]
        host = f"{srv['user']}@{srv['host']}"
        ssh = ["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10",host]
        before = run(ssh+[f"git -C {srv['remote_code_root']} diff --binary HEAD"])
        run(ssh+[f"mkdir {remote}"])
        record = {}
        for path in files:
            run(["scp","-q",str(path),f"{host}:{remote}/{path.name}"])
            digest = run(ssh+[f"sha256sum {remote}/{path.name}"]).decode().split()[0]
            assert digest == sha(path)
            record[path.name] = digest
        assert before == run(ssh+[f"git -C {srv['remote_code_root']} diff --binary HEAD"])
        evidence["deployments"][name] = record
    evidence["finished"] = datetime.now().isoformat()
    (OUT / "execution.json").write_text(json.dumps(evidence,indent=2))
    print("SYNC_COMPLETE",evidence["historical_analyses_verified"],evidence["current_analyses"])


if __name__ == "__main__":
    main()
