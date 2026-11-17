"""Read-only live snapshot and scene-level frozen-bank error decomposition."""
import csv
from collections import defaultdict
from datetime import datetime, timedelta
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
STAMP = "20260913-151000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    prior = load(P / "reports/tick_evidence_20260913-141000/audit.json")
    protected = {n: sha(P / n) for n in prior["protected"]}
    assert protected == prior["protected"], "State changed; reconcile before continuing"
    inventory = []
    for path in sorted((P / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                              characters=len(text)))
    assert inventory == prior["analyses"]
    with (P / "experiments.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    assert len(ledger) == prior["ledger_rows"]
    OUT.mkdir(exist_ok=False)
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("monitor_tick", skill / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    trainers = [x for x in remote(srv, "ps -eo pid,args").decode().splitlines()
                if "tools/train.py" in x and "ctf_hcg_csort" in x]
    live, gpu, apps = [], {}, {}
    for prefix in ("M191", "M193"):
        exp = load(next((P / "experiments").glob(prefix + "-*.json")))
        assert exp["status"] == "running"
        base = Path(exp["config"]).stem
        assert any(base in x for x in trainers)
        log = monitor.find_latest_log(base, srv["work_dir"], srv["host"], srv["user"])
        assert log
        snapshot = OUT / f"{prefix}_live.log"
        snapshot.write_bytes(remote(srv, "cat " + shlex.quote(log)))
        text = snapshot.read_text(encoding="utf-8")
        assert not re.search(r"Traceback|Early stopping at epoch", text)
        parsed = parse_log(text)
        rows = [r for r in parsed if {"acc50", "spmiou"} <= r.keys()]
        assert len(rows) == len(parsed)
        assert [r["epoch"] for r in rows] == list(range(1, len(rows) + 1))
        counts = re.findall(r"Evaluate referring segmentation:\s*(\d+)", text)
        assert len(counts) >= len(rows) and set(counts) == {"9508"}
        live.append(dict(id=exp["id"], config=exp["config"], gpu=exp["gpu"],
                         epoch=int(re.findall(r"Epoch \[(\d+)/50\]", text)[-1]),
                         completed=len(rows), best=max(rows, key=lambda r: r["miou"]),
                         metrics=rows, remote_log=log, log_sha256=sha(snapshot)))
    for name in ("server-4", "server-6"):
        s = servers[name]
        ids = ",".join(map(str, s["allowed_gpus"]))
        gpu[name] = remote(s, f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()
        apps[name] = remote(s, f"nvidia-smi -i {ids} --query-compute-apps=pid,process_name,used_memory --format=csv,noheader").decode().strip()

    ap = P / "reports/d1_assignment_20260911-1113/assignment.json"
    pp = ap.with_name("protocol.json")
    protocol = load(pp)
    assert sha(ap) == prior["assignment_sha256"]
    assert sha(pp) == prior["protocol_sha256"] == load(ap)["protocol_sha256"]
    for rel, digest in protocol["source_hashes"].items():
        assert sha(ROOT / "Cluster" / rel) == digest
    banks = {}
    for model, digest in protocol["summary_hashes"].items():
        path = P / f"reports/d1_expansion_20260911-0715/{model}/summary.json"
        assert sha(path) == digest
        rows = load(path)["rows"]
        banks[model] = {tuple(str(r[k]) for k in ("scene_id", "object_id", "ann_id")): r for r in rows}
        assert len(banks[model]) == len(rows) == 284
    assert banks["baseline"].keys() == banks["m95"].keys()
    scenes = defaultdict(list)
    for key, b in banks["baseline"].items():
        m = banks["m95"][key]
        for row in (b, m):
            assert 0 <= row["selected_iou"] <= row["oracle_iou"] <= 1
        selected = m["selected_iou"] - b["selected_iou"]
        oracle = m["oracle_iou"] - b["oracle_iou"]
        regret = (m["oracle_iou"] - m["selected_iou"]) - (b["oracle_iou"] - b["selected_iou"])
        assert abs(selected - (oracle - regret)) < 1e-12
        scenes[key[0]].append(dict(id=list(key), selected_delta=selected,
                                  oracle_delta=oracle, regret_delta=regret))
    assert len(scenes) == 71 and all(len(v) == 4 for v in scenes.values())
    scene_rows = []
    for scene, rows in sorted(scenes.items()):
        item = dict(scene=scene, n=len(rows))
        item.update({k: sum(r[k] for r in rows) / len(rows)
                     for k in ("selected_delta", "oracle_delta", "regret_delta")})
        assert abs(item["selected_delta"] - item["oracle_delta"] + item["regret_delta"]) < 1e-12
        scene_rows.append(item)
    result = dict(pairs=284, scenes=71, missing=0, duplicates=0,
                  mean={k: sum(r[k] for r in scene_rows) / 71
                        for k in ("selected_delta", "oracle_delta", "regret_delta")},
                  signs={k: dict(positive=sum(r[k] > 0 for r in scene_rows),
                                zero=sum(r[k] == 0 for r in scene_rows),
                                negative=sum(r[k] < 0 for r in scene_rows))
                         for k in ("selected_delta", "oracle_delta", "regret_delta")},
                  better_oracle_worse_selected=sum(r["oracle_delta"] > 0 and r["selected_delta"] < 0 for r in scene_rows),
                  max_identity_residual=max(abs(r["selected_delta"] - r["oracle_delta"] + r["regret_delta"]) for r in scene_rows))
    evidence = dict(at=datetime.now().isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu, apps=apps,
                    assignment_sha256=sha(ap), protocol_sha256=sha(pp),
                    summary_hashes=protocol["summary_hashes"], result=result,
                    manifest=scenes, scene_rows=scene_rows)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    diagnostic = f"""# Scene-Level Frozen-Bank Error Decomposition
## Protocol
284 paired descriptions, 71 scenes, four descriptions each; zero missing or
duplicate identities. All 568 rows satisfy 0 <= selected IoU <= oracle IoU <= 1.
For each model, regret = oracle - selected. For M95 minus baseline:
delta(selected) = delta(oracle) - delta(regret). Average within each scene.
Equal scene sizes make the scene-weighted mean equal the description-weighted
mean. Verify this arithmetic identity per description and per scene.
Assignment, protocol, five source files and both summaries hash-verified.

## Results
```json
{json.dumps(result, indent=2)}
```
The 284-pair manifest and all 71 scene decompositions are in audit.json.

## Limits
This is an arithmetic decomposition of an exploratory validation-derived bank.
Oracle is not deployable. Regret is not an isolated causal selector effect:
the models have different candidate masks. Sign counts are descriptive, not
significance tests or confidence intervals; neither scene grouping nor this
identity fixes sample selection bias. No training-target repair, new efficacy,
independent generalization or novel mechanism is established.
"""
    (OUT / "diagnostic.md").write_text(diagnostic, encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical; individual analysis authoritative |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}
## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal15:07:55: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; gap .0075392818450928.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 vs baseline | New derived mechanism |
| Wrong-instance selection | exploratory | Frozen D1/D2 | Matched causal intervention |
| Terminal controls exceed M95 | unsupported | M184-M190 0/7 | M191/M193 running |
| Oracle improvement implies selection improvement | descriptive audit | Scene decomposition | Not a causal test |
## 3. Experiment Assessment
Read all {len(inventory)} terminal analyses and {len(ledger)} ledger rows.
Their hashes/count match prior tick; no new terminal needs duplicate analysis.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}
## 4. Gap Analysis
Q1: A derived, primary-source-distinct mechanism, matched controls, predefined
error subsets, scene uncertainty, robustness and efficiency remain incomplete.
M191 parent differs in platform; M193 parent lacks full patience.
## 5. Design Rationale
Q2: Audit scene-level candidate-oracle and selection-gap differences offline.
Q3: Determine whether the overall decomposition masks heterogeneous directions,
without upgrading validation-derived associations to causal evidence.
All12 constraints/11 bans reviewed. No new forward/loss, numerical sweep,
renamed selector or legacy successor proposed. Scientific admission takes
priority over depth. No new literature verification or novelty claim this tick.
## 6. Next Batch
No qualified candidate: no exp_design, implementation, enqueue or code sync.
Preserve admitted M191/M193 patience10 and scheduler, not a global pause.
Evidence: reports/tick_evidence_{STAMP}/diagnostic.md.
"""
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Does scene-level oracle and regret decomposition justify refill at zero waiting?",
                    "Preserve M191/M193 patience10; no unadmitted refill or legacy successors.",
                    "Arithmetic and scene sign counts do not isolate a causal selection effect; scientific admission remains incomplete.",
                    f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json"])
    now = datetime.now()
    questions = []
    for path in (P / "decisions").glob("*_question.md"):
        when = datetime.strptime(path.name[:15], "%Y%m%d-%H%M%S")
        if now - timedelta(hours=24) <= when <= now:
            questions.append(path.name + "\n" + path.read_text(encoding="utf-8"))
    gpu_rows, live_rows, free = [], [], []
    for name, lines in gpu.items():
        for line in lines.splitlines():
            idx, util, used, total = [x.strip() for x in line.split(",")]
            proc = next((r["id"] for r in live if name == "server-4" and str(r["gpu"]) == idx),
                        "External occupancy" if int(used) >= 1024 else "IDLE")
            gpu_rows.append(f"| {name} | {idx} | {util}% | {used}/{total} MiB | {proc} |")
            if int(util) < 10 and int(used) < 1024 and not apps[name]:
                free.append(f"{name}:{idx}")
    for r in live:
        b = r["best"]
        live_rows.append(f"| {r['id']} | {r['config']} | server-4 | {r['gpu']} | {r['epoch']}/50 | {b['miou']:.10f}@{b['epoch']} | {b['acc50']} | {b['spmiou']} | {r['completed']-b['epoch']}/10 | running |")
    assert not [t for tasks in load(P / "queue.json")["gpu_queues"].values()
                for t in tasks if t["status"] == "waiting"]
    report = f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})
## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal15:07:55).
## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs: {', '.join(free) or 'None confirmed'}; no eligible waiting task.
Whitelisted GPU and compute-process snapshot retained in audit.json.
## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
Metrics paired at best completed epoch; each completed validation reports9508.
## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| - | - | - | No waiting tasks | - | - |
Queue depth:0 waiting/5 declared slots -> NEED MORE (requires6).
SERVERS.yaml capacity4 (requires5); scientific admission overrides refill.
## 4. This Tick's Actions
- Health sentinel absent; monitor15:07 and check_goal15:07:55 succeeded once each.
- No new terminal, crash, launch or early-stop; training repair attempts0.
- Read/hash-inventoried{len(inventory)} analyses and{len(ledger)} ledger rows; unchanged.
- Read ten complete decisions, both admitted designs, recent bugfixes/report.
- Archived live logs and whitelisted GPU/compute-process snapshot.
- Completed scene-level frozen-bank oracle/regret decomposition; no causal claim.
- No model/config edits, checkpoint pull, enqueue, sync or scheduler mutation.
## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no unadmitted refill or successors.
  See decisions/_index.md and this tick's review/audit.
## \u26a0 Pending User Decisions
{chr(10).join(questions) if questions else 'No type=question records in last24h. No user interaction.'}

Next tick:2026-09-13 16:07 Asia/Shanghai.
"""
    (P / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=[{k: v for k, v in r.items() if k != "metrics"} for r in live],
                          gpu=gpu, apps=apps, result=result, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
