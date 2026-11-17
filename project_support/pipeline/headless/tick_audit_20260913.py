"""Snapshot preserved controls and generate a read-only tick evidence bundle."""
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import shlex
from statistics import mean

import yaml

from close_m185_20260912 import parse_log
from verify_control_archives_20260912 import remote, sha

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
STAMP = "20260913-011200"
OUT = PIPE / "reports" / f"tick_evidence_{STAMP}"


def main():
    OUT.mkdir(exist_ok=False)
    names = ("goal.json", "queue.json", "running.json", "experiments.csv")
    protected = {n: sha(PIPE / n) for n in names}
    prior = json.loads((PIPE / "reports/tick_evidence_20260913-001200/audit.json").read_text())
    inventory = []
    for p in sorted((PIPE / "analyses").glob("*.md")):
        text = p.read_text(encoding="utf-8")
        inventory.append(dict(path=str(p.relative_to(ROOT)), sha256=sha(p), characters=len(text)))
    assert inventory == prior["analyses"], "New or changed analysis requires explicit review"
    with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == prior["ledger_rows"]
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    parents = json.loads((PIPE / "reports/control_provenance_20260912-201000/audit.json").read_text())["parents"]
    live = []
    for prefix, parent_prefix in (("M190", "M178"), ("M191", "M176")):
        paths = list((PIPE / "experiments").glob(prefix + "-*.json"))
        assert len(paths) == 1
        exp = json.loads(paths[0].read_text(encoding="utf-8"))
        assert exp["status"] == "running"
        server = servers[exp["server"]]
        base = Path(exp["config"]).stem
        directory = server["work_dir"] + "/" + base
        logs = remote(server, "find " + shlex.quote(directory) + " -name '*.log' -type f").decode().splitlines()
        assert len(logs) == 1, logs
        path = OUT / f"{prefix}_live.log"
        path.write_bytes(remote(server, "cat " + shlex.quote(logs[0])))
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"Early stopping at epoch|Traceback", text)
        rows = [r for r in parse_log(text) if {"epoch", "miou", "acc50", "spmiou"} <= r.keys()]
        assert rows and [r["epoch"] for r in rows] == list(range(1, len(rows) + 1))
        counts = list(map(int, re.findall(r"Evaluate referring segmentation:\s*(\d+)", text)))
        assert len(counts) >= len(rows) and set(counts) == {9508}
        best = max(rows, key=lambda r: r["miou"])
        parent = next(p for p in parents if p["id"].startswith(parent_prefix + "-"))
        assert sha(ROOT / parent["local_log"]) == parent["sha256"]
        horizon = min(len(rows), len(parent["metrics"]))
        pairs = list(zip(rows[:horizon], parent["metrics"][:horizon]))
        live.append(dict(id=exp["id"], config=exp["config"], server=exp["server"],
                         gpu=exp["gpu"], best=best, metrics=rows, completed=len(rows),
                         current_epoch=int(re.findall(r"Epoch \[(\d+)/50\]", text)[-1]),
                         no_improve=len(rows)-best["epoch"], log_sha256=sha(path),
                         remote_log=logs[0], parent=parent["id"], horizon=horizon,
                         common_best_delta=max(c["miou"] for c, p in pairs)-max(p["miou"] for c, p in pairs),
                         last_window_size=min(5, horizon),
                         last_window_mean_delta=mean(c["miou"]-p["miou"] for c, p in pairs[-5:])))
    gpu, trainers = {}, {}
    for name in ("server-4", "server-6"):
        server = servers[name]
        ids = ",".join(map(str, server["allowed_gpus"]))
        gpu[name] = remote(server, f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()
        processes = remote(server, "ps -eo pid,args").decode()
        trainers[name] = [s for s in processes.splitlines() if "tools/train.py" in s and "ctf_hcg_csort" in s]
    assert all(any(Path(r["config"]).stem in s for s in trainers[r["server"]]) for r in live)
    assert protected == {n: sha(PIPE / n) for n in names}
    evidence = dict(at=datetime.now().isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, gpu=gpu, trainers=trainers)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    table = "\n".join(f"| {r['id']} | {r['parent']} | {r['horizon']} | {r['common_best_delta']:+.10f} | {r['last_window_size']} | {r['last_window_mean_delta']:+.10f} |" for r in live)
    (OUT / "audit.md").write_text(f"""# Preserved-Control Audit
Sample: {evidence['at']} Asia/Shanghai.

| Child | Parent | Common epochs | Best delta | Tail window | Tail mean delta |
|-------|--------|---------------|------------|-------------|-----------------|
{table}

Both runs remain live and censored. Compare only common completed epochs.
Every completed validation reports 9508 expressions; counts do not establish
identical identities/order. Exact metrics and snapshot hashes are in audit.json.
M191 is too early for efficacy inference. M190 also changes padding; M191
changes server platform. No causal effect or scene-paired uncertainty is claimed.
Parent hashes match the previously remote-verified local archives, not a fresh
remote parent check. No terminal or crash markers in either live snapshot.
All {len(inventory)} analysis hashes match the prior inventory; {len(ledger)} ledger rows.
No new mechanism, successor, training, checkpoint pull or deployment change.
Goal, queue, running map and ledger hashes unchanged.
""", encoding="utf-8")
    old = (PIPE / "reviews/motivation_review_20260913-001200.md").read_text(encoding="utf-8")
    assessment = old.split("## 3. Experiment Assessment", 1)[1].split("## 4. Gap Analysis", 1)[0]
    goal = (PIPE / "goal.json").read_text(encoding="utf-8")
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}, 2026-09-13 Asia/Shanghai.

## 1. Goal
```json
{goal.strip()}
```
check_goal01:08:24: Phase1 NOT YET. Ledger champion .5020, target .5100.
Exact M95 .5024607181549072@16; baseline .4894491136074066@15.
Exact gap .0075392818450928. All12 constraints and11 bans remain binding.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Historical context benefit | historical support | M95 above baseline | Novel mechanism absent |
| Wrong-instance selection | exploratory | Frozen D1/D2 | Independent confirmation |
| Narrow shared-anchor explanation | unsupported | Prior0/21 applicability | No reopening evidence |
| Terminal readout exceeds M95 | unsupported so far | M184-M189 0/6 | M190/M191 live, M193 waiting |

## 3. Experiment Assessment{assessment}
## 4. Gap Analysis
No evidence-selected novel forward/loss passes scientific admission.
Parent-child common horizons reduce unequal-budget distortion, not padding,
platform, seed, validation reuse or uncertainty confounding. M191's first
completed validation is not a performance conclusion.

## 5. Design Rationale
Q1: Missing derived primary-source-distinct mechanism and independent validation.
Q2: Verify original live controls, denominators and common horizons offline.
Q3: Preserve evidence integrity without declaring censored experiments failed.
C1-8: no resource, seed, schedule, graph or numerical modifications.
C9-12: diagnostic/derivation/novelty/control/robustness/efficiency admission
remains incomplete. All11 bans respected; no candidate proposed or renamed.
Smell check: analysis only, not a training variant or hyperparameter search.
Scientific admission overrides waiting1/declared5, configured4.

## 6. Next Batch
No admitted candidate, design, implementation, enqueue or model synchronization.
Preserve live M190/M191, patience10 and original server-4 FIFO M193.
Evidence: reports/tick_evidence_{STAMP}/audit.json and audit.md.
"""
    (PIPE / "reviews" / f"motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    print(json.dumps({k: v for k, v in evidence.items() if k not in ("analyses", "trainers")}, indent=2))


if __name__ == "__main__":
    main()
