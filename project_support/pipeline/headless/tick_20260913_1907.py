"""Read-only live snapshot and structured admission-resource consistency audit."""
import csv
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex

import yaml

from close_m185_20260912 import parse_log, run
from verify_control_archives_20260912 import remote, sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
STAMP = "20260913-191000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    prior = load(P / "reports/tick_evidence_20260913-181000/audit.json")
    protected = {n: sha(P / n) for n in prior["protected"]}
    assert protected == prior["protected"], "State changed; reconcile first"
    inventory = []
    for path in sorted((P / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                              characters=len(text)))
    assert inventory == prior["analyses"]
    with (P / "experiments.csv").open(encoding="utf-8-sig", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    assert len(ledger) == prior["ledger_rows"]
    OUT.mkdir(exist_ok=True)
    assert not (OUT / "audit.json").exists()
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("monitor", skill / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    trainers = [line for line in remote(srv, "ps -eo pid,args").decode().splitlines()
                if "tools/train.py" in line and "ctf_hcg_csort" in line]
    live, resource = [], []
    for prefix in ("M191", "M193"):
        exp = load(next((P / "experiments").glob(prefix + "-*.json")))
        assert exp["status"] == "running"
        base = Path(exp["config"]).stem
        assert any(base in line for line in trainers)
        log = monitor.find_latest_log(base, srv["work_dir"], srv["host"], srv["user"])
        assert log
        snapshot = OUT / f"{prefix}_live.log"
        snapshot.write_bytes(remote(srv, "cat " + shlex.quote(log)))
        text = snapshot.read_text(encoding="utf-8")
        assert not re.search(r"Traceback|Early stopping at epoch", text)
        rows = parse_log(text)
        assert all({"acc50", "spmiou"} <= r.keys() for r in rows)
        assert [r["epoch"] for r in rows] == list(range(1, len(rows) + 1))
        counts = re.findall(r"Evaluate referring segmentation:\s*(\d+)", text)
        assert len(counts) >= len(rows) and set(counts) == {"9508"}
        live.append(dict(id=exp["id"], config=exp["config"], gpu=exp["gpu"],
                         epoch=int(re.findall(r"Epoch \[(\d+)/50\]", text)[-1]),
                         completed=len(rows), best=max(rows, key=lambda r: r["miou"]),
                         metrics=rows, remote_log=log, log_sha256=sha(snapshot)))
        path = ROOT / exp["validation_report"]
        records = load(path)
        matched = next(r for r in records if r["config"] == exp["config"])
        baseline = next(r for r in records if Path(r["config"]).stem.endswith("_ctf_hcg_csort"))
        for r in (matched, baseline):
            assert (r["batch_size"], r["warmup"], r["repeat"]) == (1, 20, 100)
            assert r["flops"] / 1e9 == r["flops_g"]
            assert r["flops_by_module"][""] == r["flops"]
            assert 0 < r["median_ms"] <= r["p90_ms"]
        assert matched["flops_g"] == exp["measured_flops_g"] <= 10
        ratio = matched["peak_allocated_mb"] / baseline["peak_allocated_mb"]
        assert ratio <= 1.15
        resource.append(dict(id=exp["id"], source=exp["validation_report"], sha256=sha(path),
                             flops_g=matched["flops_g"], headroom_g=10-matched["flops_g"],
                             inference_memory_ratio=ratio,
                             unsupported_ops=matched["unsupported_ops"],
                             median_ms=matched["median_ms"], p90_ms=matched["p90_ms"],
                             baseline_median_ms=baseline["median_ms"],
                             baseline_p90_ms=baseline["p90_ms"]))
    gpu = {}
    for name in ("server-4", "server-6"):
        s = servers[name]
        ids = ",".join(map(str, s["allowed_gpus"]))
        gpu[name] = remote(s, f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()
    now = datetime.now()
    questions = []
    for path in sorted((P / "decisions").glob("*_question.md")):
        age = (now-datetime.strptime(path.name[:15], "%Y%m%d-%H%M%S")).total_seconds()
        if 0 <= age <= 86400:
            questions.append(dict(path=path.name, text=path.read_text(encoding="utf-8")))
    evidence = dict(at=now.isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu,
                    resource_consistency=resource, questions=questions)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical evidence; individual analysis authoritative |" for r in ledger)
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(f"""# Motivation Review - cluster_project
Tick #{STAMP}
## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal19:08:23: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; gap .0075392818450928.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context improves localization | historical | M95 vs baseline | Seed fragility; not novel |
| Same-category selection bottleneck | exploratory | Existing D1/D2 banks | Matched causal intervention |
| Terminal controls improve champion | unsupported | M184-M190 0/7 above M95 | M191/M193 ongoing |
| Resource admission internally consistent | checked | Original JSON vs experiment registry | Unsupported operations and one-scene scope |
## 3. Experiment Assessment
Read all {len(inventory)} analyses and {len(ledger)} ledger rows; hashes unchanged.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}
## 4. Gap Analysis
Q1: Derived forward/loss, verified primary-source novelty, matched causal controls,
predefined error subsets/negative controls, robustness and efficiency remain
incomplete. Frozen-bank statistics are exploratory and not independent evidence.
M191 parent ran on another server; M193 parent has incomplete full-patience control.
## 5. Design Rationale
Q2: Independently check recorded resource arithmetic and its registry linkage.
Both controls equal9.885821484G, headroom .114178516G in the recorded operation
counter; matched inference memory ratio below1.15. Protocol bs1/warmup20/repeat100.
Q3: Detect inconsistent admission bookkeeping without another GPU experiment.
This is NOT re-profiling, training memory verification, speedup evidence, or a
bound on omitted operations. Nested module FLOPs are inclusive; do not sum them.
All12 constraints and11 bans reviewed. No new candidate or smell-check exception.
No new literature verification or novelty claim.
## 6. Next Batch
No scientifically eligible mechanism; no new exp_design, model/config change,
enqueue or sync. Preserve M191/M193 patience10; no legacy successor.
Evidence: reports/tick_evidence_{STAMP}/audit.json.
""", encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Do zero waiting and consistent resource admission justify new training?",
                    "Preserve M191/M193 patience10; no unadmitted refill or legacy successors.",
                    "Recorded resource consistency does not provide the missing derived novel mechanism; scientific admission overrides queue depth.",
                    f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json"])
    gpu_rows = []
    for name, lines in gpu.items():
        for line in lines.splitlines():
            idx, util, used, total = [v.strip() for v in line.split(",")]
            proc = next((r["id"] for r in live if name == "server-4" and str(r["gpu"]) == idx),
                        "No project trainer; external occupancy")
            gpu_rows.append(f"| {name} | {idx} | {util}% | {used}/{total} MiB | {proc} |")
    live_rows = []
    for r in live:
        b = r["best"]
        live_rows.append(f"| {r['id']} | {r['config']} | server-4 | {r['gpu']} | {r['epoch']}/50 | {b['miou']:.10f}@{b['epoch']} | {b['acc50']} | {b['spmiou']} | {r['completed']-b['epoch']}/10 | running |")
    waiting = [t for tasks in load(P / "queue.json")["gpu_queues"].values() for t in tasks if t["status"] == "waiting"]
    assert not waiting
    (P / f"reports/summary_{STAMP}.md").write_text(f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})
## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal19:08:23).
## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs: None confirmed completely idle. GPU7 external occupancy; shared slots
are not idle GPUs. No eligible waiting task.
## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
Metrics paired at best completed epoch; each completed validation count9508.
## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| - | - | - | No waiting tasks | - | - |
Queue depth:0 waiting/5 declared slots -> NEED MORE (requires6).
SERVERS.yaml capacity4 (requires5); scientific admission overrides refill.
## 4. This Tick's Actions
- Health sentinel absent; monitor19:07 and check_goal19:08:23 succeeded once each.
- No new terminal, crash, launch or early-stop; training repair attempts0.
- Read/hash-inventoried{len(inventory)} analyses and{len(ledger)} ledger rows; unchanged.
- Read ten complete decisions, both admitted designs, latest design/bugfix/report.
- Saved fresh paired live metrics, complete logs and whitelisted GPU snapshot.
- Offline resource audit: both controls match registry9.885821484G, protocol1/20/100,
  original total-module count and <=1.15 matched inference allocation.
- Original unsupported ops preserved in audit; no re-profiling, latency gain,
  complete operation count, new efficacy, causal or novelty claim.
- No model/config edits, checkpoint pull, enqueue, sync or scheduler mutation.
## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no unadmitted refill or successors.
  See decisions/_index.md and this tick's review/audit.
## \u26a0 Pending User Decisions
{chr(10).join(q['path'] + chr(10) + q['text'] for q in questions) if questions else 'No type=question records in last24h. No user interaction.'}

Next tick:2026-09-13 20:07 Asia/Shanghai.
""", encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=[{k: v for k, v in r.items() if k != "metrics"} for r in live],
                          gpu=gpu, resource=resource, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
