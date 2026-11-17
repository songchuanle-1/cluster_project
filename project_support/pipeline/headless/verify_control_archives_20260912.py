"""Verify archived control provenance and snapshot live runs without state edits."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess

import yaml

from close_m185_20260912 import parse_log


ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
STAMP = "20260912-201000"
OUT = PIPE / "reports" / f"control_provenance_{STAMP}"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remote(server, command):
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=12",
         f"{server['user']}@{server['host']}", command],
        check=True, capture_output=True, timeout=90,
    )
    return result.stdout


def main():
    OUT.mkdir(exist_ok=False)
    protected = {name: sha(PIPE / name) for name in
                 ("goal.json", "queue.json", "running.json", "experiments.csv")}
    prior_path = PIPE / "reports/remaining_control_audit_20260912-191500/audit.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    inventory = []
    for path in sorted((PIPE / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path),
                          "characters": len(text)})
    with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    parents = []
    live = []
    for pair in prior["pairs"]:
        path = ROOT / pair["parent_log"]
        registry = json.loads((PIPE / "experiments" / f"{pair['parent']}.json")
                              .read_text(encoding="utf-8"))
        server = servers[registry["server"]]
        relative = path.relative_to(ROOT / "Checkpoints" / registry["server"])
        remote_path = server["work_dir"] + "/" + relative.as_posix()
        digest = remote(server, "sha256sum " + shlex.quote(remote_path)).decode().split()[0]
        assert re.fullmatch("[a-f0-9]{64}", digest), digest
        assert digest == sha(path) == pair["parent_log_sha256"], pair["parent"]
        text = path.read_text(encoding="utf-8")
        rows = parse_log(text)
        assert all({"epoch", "miou", "acc50", "spmiou"} <= r.keys() for r in rows)
        assert [r["epoch"] for r in rows] == list(range(1, len(rows) + 1))
        counts = [int(n) for n in re.findall(r"Evaluate referring segmentation:\s*(\d+)", text)]
        assert len(counts) == len(rows) and set(counts) == {9508}
        parents.append({
            "id": pair["parent"], "server": registry["server"],
            "remote_log": remote_path, "local_log": pair["parent_log"],
            "sha256": digest, "verified_at": datetime.now().isoformat(),
            "validations": len(rows), "best": max(rows, key=lambda r: r["miou"]),
            "validation_denominators": counts, "metrics": rows,
            "post_best": pair["parent_stale"],
        })
        child = json.loads((PIPE / "experiments" / f"{pair['child']}.json")
                           .read_text(encoding="utf-8"))
        if child["status"] != "running":
            continue
        run_stamp = {"M189": "20260912_030730", "M190": "20260912_050805"}[child["id"][:4]]
        base = Path(child["config"]).stem
        child_server = servers[child["server"]]
        log_path = f"{child_server['work_dir']}/{base}/{run_stamp}/{run_stamp}.log"
        snapshot = OUT / f"{child['id'][:4]}_live.log"
        snapshot.write_bytes(remote(child_server, "cat " + shlex.quote(log_path)))
        text = snapshot.read_text(encoding="utf-8")
        rows = parse_log(text)
        complete = [r for r in rows if {"acc50", "spmiou"} <= r.keys()]
        assert [r["epoch"] for r in complete] == list(range(1, len(complete) + 1))
        best = max(complete, key=lambda r: r["miou"])
        live.append({
            "id": child["id"], "server": child["server"], "gpu": child["gpu"],
            "snapshot": str(snapshot.relative_to(ROOT)), "sha256": sha(snapshot),
            "at": datetime.now().isoformat(), "best": best,
            "completed_validations": len(complete),
            "current_epoch": int(re.findall(r"Epoch \[(\d+)/50\]", text)[-1]),
            "no_improve": len(complete) - best["epoch"],
            "terminal_marker": bool(re.search(r"Early stopping at epoch|Traceback", text)),
        })
    gpu = {}
    processes = {}
    for name in ("server-4", "server-6"):
        server = servers[name]
        ids = ",".join(str(n) for n in server["allowed_gpus"])
        gpu[name] = remote(server, "nvidia-smi -i " + ids +
                           " --query-gpu=index,utilization.gpu,memory.used,memory.total"
                           " --format=csv,noheader,nounits").decode().strip()
        processes[name] = remote(server, "ps -eo pid,args").decode()
        (OUT / f"{name}_processes.txt").write_text(processes[name], encoding="utf-8")
        processes[name] = [line for line in processes[name].splitlines()
                           if "tools/train.py" in line and "ctf_hcg_csort" in line]
    assert protected == {name: sha(PIPE / name) for name in protected}
    evidence = {
        "at": datetime.now().isoformat(), "prior_audit_sha256": sha(prior_path),
        "protected_state": protected, "analyses": inventory, "ledger_rows": len(ledger),
        "parents": parents, "live": live, "gpu": gpu, "trainers": processes,
    }
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assessment = "\n".join(
        f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | "
        "Historical evidence; retain route-specific terminal interpretation |"
        for r in ledger)
    goal = (PIPE / "goal.json").read_text(encoding="utf-8")
    review = f"""# Motivation Review - cluster_project
2026-09-12, tick #20260912-2007.

## 1. Goal
Full authoritative goal:
```json
{goal.strip()}
```
check_goal20:08:28: Phase1 NOT YET, target .5100, ledger champion .5020.
Exact M95 .5024607181549072; exact baseline .4894491136074066.
Exact gap .0075392818450928; ledger gap .0080.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Historical context gain | historical support | M95 above baseline | Not novel mechanism evidence |
| Wrong-instance selection bottleneck | exploratory support | D1/D2 fixed banks | Independent confirmation |
| Terminal controls exceed champion | unsupported so far | 0/5 completed M184-M188 | M189/M190 censored, M191/M193 waiting |
| Preserved parent logs equal remote logs | verified this tick | Four matching SHA256 digests | Does not establish environment matching |

## 3. Experiment Assessment
Read/hash-inventoried all {len(inventory)} analysis documents and {len(ledger)} ledger rows.
Old waiting entries in the ledger are history, not the current queue.
Prior route-specific assessments remain authoritative; no result reclassified.

| Experiment | mIoU ledger | State | Motivation assessment |
|------------|-------------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: No new measured error has a fully derived, primary-source-distinct
forward/loss with matched controls and preregistered rejection criteria.
Remote log verification closes provenance only, not this admission gap.
M190 includes padding repair; M193 parent has only five stale validations;
M191 changes server platform. Do not claim uniformly matched causal controls.

## 5. Design Rationale
Q2: Verify existing parent archive integrity before interpreting preserved runs.
Q3: Carry exact paired metrics and stopping limits into future terminal analyses.
Constraints1-8: no training, compute, schedule, seed, numerical or routing changes.
Constraints9-12: evidence, derivation, novelty, controls, validation and admission
priority remain binding. All11 bans checked; no new candidate graph is proposed.
Smell check: provenance audit only, not an admitted training mechanism.
Scientific admission overrides queue2/declared5; configured capacity4 also lacks depth.

## 6. Next Batch
No new mechanism, successor, exp_design, implementation, enqueue or code sync.
Preserve M189/M190 and server-4 FIFO M191 then M193.
Continue bounded diagnosis/derivation; do not reopen closed families to fill slots.
"""
    (PIPE / "reviews" / f"motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    print(json.dumps({k: v for k, v in evidence.items()
                      if k not in ("analyses", "parents")}, indent=2))
    print("PARENTS", json.dumps([{k: v for k, v in p.items() if k != "metrics"}
                                 for p in parents], indent=2))


if __name__ == "__main__":
    main()
