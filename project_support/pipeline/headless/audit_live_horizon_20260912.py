"""Read-only common-epoch comparison of the two preserved live controls."""
import csv
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import shlex
from statistics import mean

import yaml

from verify_control_archives_20260912 import remote, sha
from close_m185_20260912 import parse_log


ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
STAMP = "20260912-211000"
OUT = PIPE / "reports" / f"live_horizon_{STAMP}"


def main():
    global STAMP, OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--stamp", default=STAMP)
    parser.add_argument("--goal-checked-at", default="21:08:00")
    args = parser.parse_args()
    datetime.strptime(args.stamp, "%Y%m%d-%H%M%S")
    STAMP = args.stamp
    OUT = PIPE / "reports" / f"live_horizon_{STAMP}"
    OUT.mkdir(exist_ok=False)
    names = ("goal.json", "queue.json", "running.json", "experiments.csv")
    protected = {name: sha(PIPE / name) for name in names}
    source = PIPE / "reports/control_provenance_20260912-201000/audit.json"
    prior = json.loads(source.read_text(encoding="utf-8"))
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    inventory = []
    for path in sorted((PIPE / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path),
                          "characters": len(text)})
    with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    results = []
    for prefix, parent_id, run_stamp in (
        ("M189", "M177-CTF-HCG-CSORT-MQBC", "20260912_030730"),
        ("M190", "M178-CTF-HCG-CSORT-MQTD", "20260912_050805"),
    ):
        matches = list((PIPE / "experiments").glob(f"{prefix}-*.json"))
        assert len(matches) == 1
        child = json.loads(matches[0].read_text(encoding="utf-8"))
        assert child["status"] == "running"
        parent = next(p for p in prior["parents"] if p["id"] == parent_id)
        assert sha(ROOT / parent["local_log"]) == parent["sha256"]
        base = Path(child["config"]).stem
        log_path = f"{servers[child['server']]['work_dir']}/{base}/{run_stamp}/{run_stamp}.log"
        snapshot = OUT / f"{prefix}_live.log"
        snapshot.write_bytes(remote(servers[child["server"]], "cat " + shlex.quote(log_path)))
        text = snapshot.read_text(encoding="utf-8")
        rows = [r for r in parse_log(text) if {"epoch", "miou", "acc50", "spmiou"} <= r.keys()]
        assert rows and [r["epoch"] for r in rows] == list(range(1, len(rows) + 1))
        counts = [int(n) for n in re.findall(r"Evaluate referring segmentation:\s*(\d+)", text)]
        assert len(counts) >= len(rows) and set(counts) == {9508}
        assert not re.search(r"Early stopping at epoch|Traceback", text)
        horizon = min(len(rows), len(parent["metrics"]))
        parent_rows = parent["metrics"][:horizon]
        child_rows = rows[:horizon]
        best = max(rows, key=lambda r: r["miou"])
        parent_best = max(parent_rows, key=lambda r: r["miou"])
        child_best = max(child_rows, key=lambda r: r["miou"])
        comparisons = [
            {"epoch": c["epoch"], "parent_miou": p["miou"], "child_miou": c["miou"],
             "delta": c["miou"] - p["miou"]}
            for p, c in zip(parent_rows, child_rows)
        ]
        results.append({
            "id": child["id"], "config": child["config"], "server": child["server"],
            "gpu": child["gpu"], "parent": parent_id, "horizon": horizon,
            "snapshot": str(snapshot.relative_to(ROOT)), "sha256": sha(snapshot),
            "at": datetime.now().isoformat(), "best": best,
            "current_epoch": int(re.findall(r"Epoch \[(\d+)/50\]", text)[-1]),
            "completed_validations": len(rows), "no_improve": len(rows) - best["epoch"],
            "common_parent_best": parent_best, "common_child_best": child_best,
            "common_best_delta": child_best["miou"] - parent_best["miou"],
            "last5_mean_delta": mean(r["delta"] for r in comparisons[-5:]),
            "positive_epoch_deltas": sum(r["delta"] > 0 for r in comparisons),
            "comparisons": comparisons, "metrics": rows,
            "parent_sha256": parent["sha256"], "terminal_marker": False,
        })
    gpu = {}
    trainers = {}
    for name in ("server-4", "server-6"):
        server = servers[name]
        ids = ",".join(map(str, server["allowed_gpus"]))
        gpu[name] = remote(server, "nvidia-smi -i " + ids +
                           " --query-gpu=index,utilization.gpu,memory.used,memory.total"
                           " --format=csv,noheader,nounits").decode().strip()
        processes = remote(server, "ps -eo pid,args").decode()
        (OUT / f"{name}_processes.txt").write_text(processes, encoding="utf-8")
        trainers[name] = [line for line in processes.splitlines()
                          if "tools/train.py" in line and "ctf_hcg_csort" in line]
    assert all(any(Path(r["config"]).stem in line for line in trainers[r["server"]])
               for r in results)
    assert protected == {name: sha(PIPE / name) for name in names}
    evidence = {
        "at": datetime.now().isoformat(), "source_sha256": sha(source),
        "protected_state": protected, "analyses": inventory, "ledger_rows": len(ledger),
        "results": results, "gpu": gpu, "trainers": trainers,
    }
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    table = "\n".join(
        f"| {r['id'][:4]} | {r['parent'][:4]} | {r['horizon']} | "
        f"{r['common_child_best']['miou']:.10f} | {r['common_parent_best']['miou']:.10f} | "
        f"{r['common_best_delta']:+.10f} | {r['last5_mean_delta']:+.10f} |"
        for r in results)
    report = f"""# Live Common-Epoch Audit
Tick #{STAMP}; sampled {evidence['at']} Asia/Shanghai.

## Protocol
Read-only log analysis of the original preserved M189/M190 controls.
Compare epochs 1 through min(completed child validations, completed parent
validations), without extrapolation, smoothing choices or early-stop changes.
Pairs were fixed by the existing designs, not selected from these scores.
Each complete live validation reports 9508 expressions. Counts do not prove
identical expression identities/order or input preprocessing.

## Observations
| Child | Parent | Common epochs | Child best | Parent best | Best delta | Last5 mean epoch delta |
|-------|--------|---------------|------------|-------------|------------|------------------------|
{table}

The best delta compares two maxima within a common epoch budget; best epochs
need not coincide. Last5 is a descriptive paired-epoch mean, not independent
replication or a scene-paired confidence interval. All epoch metrics are in
audit.json. Raw live snapshots are retained with SHA256.

## Interpretation
Both children remain live and censored. Do not label either as failed or
complete and do not stop before the existing patience criterion. This
comparison reduces unequal epoch-budget distortion but does not establish
a causal or statistically reliable effect. M190 also fixes padding, so its
recurrence effect cannot be isolated. Single-seed and unverified environment
matching remain limitations. No new mechanism or successor is admitted.

## Integrity
All {len(inventory)} analyses read/hash-inventoried; {len(ledger)} ledger rows loaded.
Parent local hashes match the prior remote-verified provenance record;
no fresh remote parent hash check is claimed. Goal, queue, running map and
ledger hashes are unchanged. No model/config, checkpoint, schedule, GPU job,
deployment or training modification. No terminal or crash marker in snapshots.
"""
    (OUT / "audit.md").write_text(report, encoding="utf-8")
    goal = (PIPE / "goal.json").read_text(encoding="utf-8").strip()
    assessment = "\n".join(
        f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | "
        "Historical evidence; retain existing route-specific analysis |"
        for r in ledger)
    review = f"""# Motivation Review - cluster_project
{datetime.now():%Y-%m-%d}, tick #{STAMP}.

## 1. Goal
Full authoritative goal:
```json
{goal}
```
check_goal {args.goal_checked_at}: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072@16; baseline .4894491136074066@15.
Exact gap .0075392818450928; ledger gap .0080.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Historical context gain | supported historically | M95 above baseline | Novel core mechanism absent |
| Wrong-instance selection | exploratory support | Frozen D1/D2 diagnostics | Independent confirmation |
| Shared-anchor explains fixed errors | not supported | Prior 0/21 applicability audit | Do not reopen without new evidence |
| Terminal controls beat M95 | unsupported so far | M184-M188 0/5 | M189/M190 censored; M191/M193 waiting |

## 3. Experiment Assessment
Read all {len(inventory)} analysis files and {len(ledger)} ledger rows.
The ledger includes historical waiting states, not the live queue.
No terminal result reclassified; detailed existing route analyses retained.

| Experiment | Ledger mIoU | State | Motivation assessment |
|------------|-------------|-------|-----------------------|
{assessment}

## 4. Gap Analysis
Q1: No evidence-selected, primary-source-distinct forward/loss derivation
passes the current admission gate. Earlier candidate scoring, relation,
mask-conditioning and parameter-coupling directions remain closed.
Common-epoch comparisons clarify existing controls but cannot fill novelty,
scene uncertainty, robustness or independent-validation gaps.

## 5. Design Rationale
Q2: Audit preserved parent-child trajectories at a common completed horizon.
Q3: Keep censoring and M190 padding confounding explicit in future analyses.
C1-8: no compute/seed/schedule/numerical/architecture changes or new training.
C9-12: diagnosis, derivation, primary-source novelty, matched controls,
robustness, efficiency and validation boundaries remain mandatory.
All11 bans checked: no new graph or numerical candidate proposed.
Smell check: this is an existing-control analysis, not a mechanism.
Scientific admission overrides depth2/declared5 (configured4).

## 6. Next Batch
No new exp_design, implementation, enqueue or training-code sync.
Preserve live M189/M190 and server-4 FIFO M191 then M193.
Continue bounded scientific work; no automatic legacy successors.
Evidence: reports/live_horizon_{STAMP}/audit.md and audit.json.
"""
    (PIPE / "reviews" / f"motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    print(json.dumps({k: v for k, v in evidence.items() if k != "analyses"}, indent=2))


if __name__ == "__main__":
    main()
