"""Read-only live logs/GPU snapshot for the foreground research report."""
from datetime import datetime
import json
from pathlib import Path
import re
import shlex
import yaml

from close_m185_20260912 import parse_log
from verify_control_archives_20260912 import remote, sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/source_head_interference_20260913-1938"


def main():
    assert not (OUT / "live.json").exists()
    prior = json.loads((P / "reports/tick_evidence_20260913-191000/audit.json").read_text())
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    records = []
    processes = remote(servers["server-4"], "ps -eo pid,args").decode()
    for previous in prior["live"]:
        name = previous["id"].split("-")[0]
        text = remote(servers["server-4"], "cat " + shlex.quote(previous["remote_log"])).decode()
        path = OUT / (name + "_live.log")
        path.write_text(text, encoding="utf-8")
        metrics = parse_log(text)
        best = max(metrics, key=lambda r: r["miou"])
        records.append(dict(id=previous["id"], config=previous["config"], gpu=previous["gpu"],
            remote_log=previous["remote_log"], log_sha256=sha(path), best=best,
            completed=len(metrics), epoch=int(re.findall(r"Epoch \[(\d+)/50\]", text)[-1]),
            no_improve=metrics[-1]["epoch"]-best["epoch"],
            early_stop=bool(re.search("Early stopping at epoch", text)),
            traceback="Traceback" in text,
            trainer_present=any(Path(previous["config"]).stem in line and "tools/train.py" in line for line in processes.splitlines()),
            metrics=metrics))
    gpu = {}
    for name in ("server-4", "server-6"):
        srv = servers[name]
        ids = ",".join(map(str, srv["allowed_gpus"]))
        gpu[name] = remote(srv, f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()
    result = dict(at=datetime.now().isoformat(), live=records, gpu=gpu)
    (OUT / "live.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({**result, "live": [{k: v for k,v in r.items() if k != "metrics"} for r in records]}, indent=2))


if __name__ == "__main__":
    main()
