"""Snapshot active experiments and audit admitted artifact integrity, read-only."""
import copy
import csv
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

import yaml

from close_m185_20260912 import parse_log, run
from verify_control_archives_20260912 import remote, sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
STAMP = "20260913-181000"
OUT = P / f"reports/tick_evidence_{STAMP}"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    prior = load(P / "reports/tick_evidence_20260913-171000/audit.json")
    protected = {n: sha(P / n) for n in prior["protected"]}
    assert protected == prior["protected"], "Reconcile state changes before proceeding"
    inventory = []
    for path in sorted((P / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), characters=len(text)))
    assert inventory == prior["analyses"]
    with (P / "experiments.csv").open(encoding="utf-8-sig", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    assert len(ledger) == prior["ledger_rows"]
    OUT.mkdir(exist_ok=True)
    assert not (OUT / "audit.json").exists(), "Do not repeat a completed tick"
    skill = ROOT.parent / ".claude/skills/songcl_research_pipeline"
    spec = importlib.util.spec_from_file_location("tick_monitor", skill / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    trainers = [s for s in remote(srv, "ps -eo pid,args").decode().splitlines()
                if "tools/train.py" in s and "ctf_hcg_csort" in s]
    live, integrity, gpu, apps = [], [], {}, {}
    for prefix in ("M191", "M193"):
        exp = load(next((P / "experiments").glob(prefix + "-*.json")))
        assert exp["status"] == "running"
        base = Path(exp["config"]).stem
        assert any(base in s for s in trainers)
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
        paths = [ROOT / "Cluster" / exp["config"]]
        package = ROOT / "Cluster/framework/model/Quard_model" / base
        paths += sorted(package.glob("*.py"))
        assert len(paths) == 8, "Expected admitted config and seven source files"
        for path in paths:
            rel = path.relative_to(ROOT / "Cluster").as_posix()
            committed = subprocess.run(
                ["git", "show", f"{exp['code_commit']}:{rel}"], cwd=ROOT / "Cluster",
                check=True, capture_output=True, timeout=30).stdout
            assert committed == path.read_bytes(), rel
            entry = dict(id=exp["id"], path=rel, sha256=sha(path),
                         admission_commit=exp["code_commit"], remote={})
            for name in ("server-4", "server-6"):
                server = servers[name]
                remote_path = server["remote_code_root"] + "/" + rel
                digest = remote(server, "sha256sum " + shlex.quote(remote_path)).decode().split()[0]
                if path.suffix == ".yaml":
                    actual = yaml.safe_load(remote(server, "cat " + shlex.quote(remote_path)))
                    expected = copy.deepcopy(yaml.safe_load(path.read_text(encoding="utf-8")))
                    expected["work_dir"] = server["work_dir"]
                    expected["train"]["pretrain"] = server["data_root"].rstrip("/") + "/sp_unet_backbone.pth"
                    expected["model"]["data_root"] = server["data_root"]
                    for split in ("train", "val"):
                        expected["data"][split]["data_root"] = server["data_root"]
                    original = yaml.safe_load(path.read_text(encoding="utf-8"))
                    assert actual == expected or actual == original, (name, rel, "Unexpected semantic config drift")
                    entry["remote"][name] = dict(
                        sha256=digest, config_mode="registered_deployment" if actual == expected else "original_undeployed",
                        non_path_settings_equal=True)
                else:
                    assert digest == entry["sha256"], (name, rel)
                    entry["remote"][name] = dict(sha256=digest, exact=True)
            integrity.append(entry)
    for name in ("server-4", "server-6"):
        s = servers[name]
        ids = ",".join(map(str, s["allowed_gpus"]))
        gpu[name] = remote(s, f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()
        apps[name] = remote(s, f"nvidia-smi -i {ids} --query-compute-apps=pid,process_name,used_memory --format=csv,noheader").decode().strip()
    questions = []
    now = datetime.now()
    for path in sorted((P / "decisions").glob("*_question.md")):
        age = (now - datetime.strptime(path.name[:15], "%Y%m%d-%H%M%S")).total_seconds()
        if 0 <= age <= 86400:
            questions.append(dict(path=path.name, text=path.read_text(encoding="utf-8")))
    evidence = dict(at=now.isoformat(), protected=protected, analyses=inventory,
                    ledger_rows=len(ledger), live=live, trainers=trainers, gpu=gpu,
                    apps=apps, integrity=integrity, questions=questions)
    (OUT / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assessment = "\n".join(f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | Historical; individual analysis remains authoritative |" for r in ledger)
    (P / f"reviews/motivation_review_{STAMP}.md").write_text(f"""# Motivation Review - cluster_project
Tick #{STAMP}
## 1. Goal
```json
{(P / 'goal.json').read_text(encoding='utf-8').strip()}
```
check_goal 18:08:19: Phase1 NOT YET; target .5100; ledger champion .5020.
Exact M95 .5024607181549072; gap .0075392818450928.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context improves localization | historical | M95 vs baseline | Seed fragility and novelty |
| Wrong-instance selection bottleneck | exploratory | Frozen D1/D2 banks | Causal matched intervention |
| Terminal controls improve champion | unsupported | M184-M190 0/7 above M95 | M191/M193 ongoing |
| Admitted code has not drifted | verified on disk | 14 source files exact; 2 configs deployment-adjusted | Runtime loaded bytes and environment not verified |
## 3. Experiment Assessment
Read all {len(inventory)} analyses and {len(ledger)} ledger rows; hashes unchanged.
No new terminal requires duplicate analysis.
| Experiment | mIoU | State | Motivation Assessment |
|------------|------|-------|-----------------------|
{assessment}
## 4. Gap Analysis
Q1: No evidence-selected primary-source-distinct derived forward/loss has passed
scientific admission. Matched controls, predefined error subsets/negative controls,
robustness and efficiency remain incomplete. M191 cross-server parent and M193
short-patience parent prevent matched causal claims.
## 5. Design Rationale
Q2: Check the two ongoing admitted controls for config/source drift across both
servers and original admission commits. Q3: Reduce reproducibility uncertainty,
without reusing bootstrap calculations as new research evidence.
Reviewed all12 constraints and11 bans: no new candidate, tuning or renamed selector.
No literature lookup or novelty claim. No checkpoint reevaluation.
Integrity of current on-disk files does not prove bytes loaded at process start.
## 6. Next Batch
No eligible mechanism: no exp_design, model edit, enqueue or code sync.
Scientific admission overrides depth; retain M191/M193 patience10 and scheduler.
Evidence: reports/tick_evidence_{STAMP}/audit.json.
""", encoding="utf-8")
    decision = run([monitor.bash_executable(), str(skill / "log_decision.sh"),
                    "cluster_project", "route_change",
                    "Do zero waiting and unchanged admitted control artifacts justify refill?",
                    "Preserve M191/M193 patience10; no unadmitted refill or legacy successors.",
                    "Fourteen source files match exactly; two configs match with registered deployment paths on both servers. Integrity does not supply the missing novel derived mechanism.",
                    f"pipeline/reviews/motivation_review_{STAMP}.md; pipeline/reports/tick_evidence_{STAMP}/audit.json"])
    gpu_rows, live_rows = [], []
    for name, lines in gpu.items():
        for line in lines.splitlines():
            idx, util, used, total = [v.strip() for v in line.split(",")]
            proc = next((r["id"] for r in live if name == "server-4" and str(r["gpu"]) == idx), "No project trainer; external occupancy")
            gpu_rows.append(f"| {name} | {idx} | {util}% | {used}/{total} MiB | {proc} |")
    for r in live:
        b = r["best"]
        live_rows.append(f"| {r['id']} | {r['config']} | server-4 | {r['gpu']} | {r['epoch']}/50 | {b['miou']:.10f}@{b['epoch']} | {b['acc50']} | {b['spmiou']} | {r['completed']-b['epoch']}/10 | running |")
    waiting = [t for tasks in load(P / "queue.json")["gpu_queues"].values() for t in tasks if t["status"] == "waiting"]
    assert not waiting
    (P / f"reports/summary_{STAMP}.md").write_text(f"""# Research Pipeline Report - cluster_project
{now:%Y-%m-%d %H:%M:%S} Asia/Shanghai (tick #{STAMP})
## 0. Goal Status
Target:mIoU >=.5100 | Champion:M95 .5020 (exact .5024607182)
Gap:+.0080 ledger /+.0075392818 exact | Phase:1 NOT YET (check_goal18:08:19).
## 1. GPU Overview
| Server | GPU | Util | Memory | Process |
|--------|-----|------|--------|---------|
{chr(10).join(gpu_rows)}
Free GPUs: None confirmed completely idle; no eligible waiting task.
GPU7 external occupancy; configured shared slots are not the same as idle cards.
## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
{chr(10).join(live_rows)}
Metrics paired at best completed epoch; all completed validation counts9508.
## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| - | - | - | No waiting tasks | - | - |
Queue depth:0 waiting/5 declared slots -> NEED MORE (requires6).
SERVERS.yaml capacity4 (requires5); scientific admission overrides refill.
## 4. This Tick's Actions
- Health sentinel absent; monitor18:07/check_goal18:08:19 succeeded once each.
- No new terminal, crash, launch or early-stop; repair attempts0.
- Read/hash-inventoried{len(inventory)} analyses and{len(ledger)} ledger rows; unchanged.
- Read ten complete decisions, both admitted designs, latest design/bugfix/report.
- Saved fresh live logs, GPU/compute-process snapshot and paired validation metrics.
- Local16 config/source files match original admission commits; both servers match14
  source files exactly and2 YAML configs after registered deployment-path substitution.
- Audit helper repaired in2 attempts: server-4 YAML uses registered deployment
  paths; inactive server-6 retains original YAML. No launch readiness claim for
  server-6; structured comparison retains every non-path setting. No training repair.
- On-disk integrity only; no runtime-loaded-byte, environment, efficacy or novelty claim.
- No model/config edits, checkpoint pull, enqueue, sync or scheduler mutation.
## 5. Decisions Made
- route_change: preserve M191/M193 patience10; no unadmitted refill or successors.
  See decisions/_index.md and this tick's review/audit.
## \u26a0 Pending User Decisions
{chr(10).join(q['path'] + chr(10) + q['text'] for q in questions) if questions else 'No type=question records in last24h. No user interaction.'}

Next tick:2026-09-13 19:07 Asia/Shanghai.
""", encoding="utf-8")
    assert protected == {n: sha(P / n) for n in protected}
    print(decision)
    print(json.dumps(dict(live=[{k: v for k, v in r.items() if k != "metrics"} for r in live],
                          gpu=gpu, verified_files=len(integrity), questions=len(questions)), indent=2))


if __name__ == "__main__":
    main()
