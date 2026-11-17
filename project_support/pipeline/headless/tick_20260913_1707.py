"""Read-only run snapshot and independent frozen-bootstrap correctness audit."""
import csv
from datetime import datetime, timedelta
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex

import numpy as np
import yaml

from close_m185_20260912 import parse_log, run
from verify_control_archives_20260912 import remote, sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
STAMP = "20260913-171000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    prior_dir = P / "reports/tick_evidence_20260913-161000"
    prior = load(prior_dir / "audit.json")
    protected = {n: sha(P / n) for n in prior["protected"]}
    assert protected == prior["protected"], "Changed project state needs reconciliation"
    inventory = []
    for path in sorted((P / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                              characters=len(text)))
    assert inventory == prior["analyses"]
    with (P / "experiments.csv").open(encoding="utf-8-sig", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    assert len(ledger) == prior["ledger_rows"]
    OUT.mkdir(exist_ok=False)
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("tick_monitor", skill / "pipeline_monitor.py")
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
        rows = parse_log(text)
        assert all({"acc50", "spmiou"} <= r.keys() for r in rows)
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

    assignment = P / "reports/d1_assignment_20260911-1113/assignment.json"
    protocol = assignment.with_name("protocol.json")
    assert sha(assignment) == prior["assignment_sha256"]
    assert sha(protocol) == prior["protocol_sha256"] == load(assignment)["protocol_sha256"]
    pr = load(protocol)
    for rel, digest in pr["source_hashes"].items():
        assert sha(ROOT / "Cluster" / rel) == digest
    banks = {}
    for model, digest in pr["summary_hashes"].items():
        path = P / f"reports/d1_expansion_20260911-0715/{model}/summary.json"
        assert sha(path) == digest
        rows = load(path)["rows"]
        banks[model] = {tuple(str(r[k]) for k in ("scene_id", "object_id", "ann_id")): r for r in rows}
        assert len(banks[model]) == len(rows) == 284
    assert banks["baseline"].keys() == banks["m95"].keys()
    grouped = {}
    for key in sorted(banks["baseline"]):
        b, m = banks["baseline"][key], banks["m95"][key]
        for r in (b, m):
            assert 0 <= r["selected_iou"] <= r["oracle_iou"] <= 1
        selected = m["selected_iou"] - b["selected_iou"]
        oracle = m["oracle_iou"] - b["oracle_iou"]
        regret = (m["oracle_iou"] - m["selected_iou"]) - (b["oracle_iou"] - b["selected_iou"])
        success = int(m["selected_iou"] > .5) - int(b["selected_iou"] > .5)
        grouped.setdefault(key[0], []).append([selected, oracle, regret, success])
    assert sorted(grouped) == prior["scenes"]
    assert len(grouped) == 71 and all(len(v) == 4 for v in grouped.values())
    values = np.array([np.mean(grouped[s], axis=0) for s in sorted(grouped)])
    np.testing.assert_allclose(values, prior["scene_values"], rtol=0, atol=1e-14)
    frozen = np.load(prior_dir / "bootstrap_draws.npy", allow_pickle=False)
    assert sha(prior_dir / "bootstrap_draws.npy") == prior["draws_sha256"]
    assert frozen.shape == (10000, 4)
    indices = np.random.default_rng(1999).integers(0, 71, size=(10000, 71))
    # Multiplicity weights independently reproduce repeated-row indexing.
    counts = np.array([np.bincount(row, minlength=71) for row in indices])
    assert np.all(counts.sum(axis=1) == 71)
    recomputed = counts @ values / 71
    np.testing.assert_allclose(recomputed, frozen, rtol=0, atol=1e-14)
    np.testing.assert_allclose(recomputed[:, 0], recomputed[:, 1] - recomputed[:, 2], rtol=0, atol=1e-14)
    names = ["selected_delta", "oracle_delta", "regret_delta", "success_rate_delta"]
    for i, name in enumerate(names):
        np.testing.assert_allclose(np.quantile(recomputed[:, i], [.025, .975]),
                                   prior["result"][name]["percentile_95"], rtol=0, atol=1e-14)
    diagnostic = dict(pairs=284, scenes=71, missing=0, duplicates=0, draws=10000,
                      max_abs_draw_error=float(np.max(np.abs(recomputed - frozen))),
                      tolerance=1e-14, method="scene multiplicity matrix times independently reconstructed means",
                      source_audit_sha256=sha(prior_dir / "audit.json"),
                      draws_sha256=prior["draws_sha256"], result=prior["result"])
    evidence = dict(at=datetime.now().isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu, apps=apps,
                    assignment_sha256=sha(assignment), protocol_sha256=sha(protocol),
                    summary_hashes=pr["summary_hashes"], diagnostic=diagnostic)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    (OUT / "diagnostic.md").write_text(
        "# Frozen Bootstrap Correctness Audit\n\n"
        "Reconstructed 284 paired records across 71 four-record scenes from hash-verified "
        "upstream summaries. Checked five source hashes and assignment/protocol hashes. "
        "Recomputed 10,000 joint scene draws using a multiplicity-count matrix, independently "
        "of the prior repeated-row indexing implementation. Direct per-model regret "
        "differences reproduce the oracle-minus-selected decomposition. All four stored "
        "marginal percentile intervals reproduce within 1e-14.\n\n"
        f"Maximum absolute draw discrepancy: {diagnostic['max_abs_draw_error']:.17g}.\n\n"
        "This is a numerical correctness check, not new statistical evidence. No new "
        "samples, checkpoint evaluation, causal identification, representative validation "
        "or novelty verification. The previous conditional exploratory interpretation "
        "and sampling limitations remain unchanged.\n", encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical; see individual analysis |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
Tick #{STAMP}
## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal17:08:13: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; gap .0075392818450928.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context benefit | historical | M95 vs baseline | Novel derived mechanism |
| Wrong-instance selection | exploratory | D1/D2 frozen banks | Matched causal intervention |
| Terminal controls beat M95 | unsupported | M184-M190 0/7 | M191/M193 running |
| Bootstrap implementation | verified numerically | Independent multiplicity audit | Sampling/generalization unchanged |
## 3. Experiment Assessment
Read/hash-inventoried all {len(inventory)} analyses and {len(ledger)} ledger rows; unchanged.
No new terminal requires duplicate analysis.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}
## 4. Gap Analysis
Q1: A derived primary-source-distinct forward/loss, matched controls, predefined
error subsets/negative controls, robustness and efficiency admission remain incomplete.
M191 platform and M193 parent patience prevent matched causal claims.
## 5. Design Rationale
Q2: Audit numerical reproducibility of the prior uncertainty artifact using
independent multiplicity aggregation. Q3: Close implementation uncertainty only;
do not present recycled-bank recomputation as independent scientific confirmation.
Reviewed all12 constraints and11 bans; no new mechanism or numerical tuning proposed.
No literature lookup or novelty claim this tick. Scientific admission overrides depth.
## 6. Next Batch
No admitted candidate: no exp_design, model/config edit, enqueue or sync.
Preserve M191/M193, patience10 and scheduler. This is not a global pause.
Evidence: reports/tick_evidence_{STAMP}/audit.json and diagnostic.md.
"""
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Does independent bootstrap reproducibility justify refill at zero waiting?",
                    "Preserve M191/M193 patience10; no unadmitted refill or legacy successors.",
                    "Numerical correctness is not new causal or novelty evidence; scientific admission remains incomplete.",
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
    assert not [t for tasks in load(P / "queue.json")["gpu_queues"].values() for t in tasks if t["status"] == "waiting"]
    report = f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})
## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal17:08:13).
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
Metrics paired at best completed epoch; every completed validation reports9508.
## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| - | - | - | No waiting tasks | - | - |
Queue depth:0 waiting/5 declared slots -> NEED MORE (requires6).
SERVERS.yaml capacity4 (requires5); scientific admission overrides refill.
## 4. This Tick's Actions
- Health sentinel absent; monitor17:07 and check_goal17:08:13 succeeded once each.
- No new terminal, crash, launch or early-stop; training repair attempts0.
- Read/hash-inventoried{len(inventory)} analyses and{len(ledger)} ledger rows; unchanged.
- Read ten complete decisions, both admitted designs, recent bugfixes/report.
- Archived live logs and whitelisted GPU/compute-process snapshot.
- Independently reproduced all10,000 prior bootstrap draws and marginal intervals.
- Correctness only, no new efficacy/causality/novelty claim.
- No model/config edits, checkpoint pull, enqueue, sync or scheduler mutation.
## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no unadmitted refill or successors.
  See decisions/_index.md and this tick's review/audit.
## \u26a0 Pending User Decisions
{chr(10).join(questions) if questions else 'No type=question records in last24h. No user interaction.'}

Next tick:2026-09-13 18:07 Asia/Shanghai.
"""
    (P / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=[{k: v for k, v in r.items() if k != "metrics"} for r in live],
                          gpu=gpu, diagnostic=diagnostic, questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
