"""Produce the terminal-control evidence review and six-section tick snapshot."""
import csv
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
BASELINE = 0.4894491136074066
CHAMPION = 0.5024607181549072


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    now = datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    goal = load(PIPE / "goal.json")
    queue = load(PIPE / "queue.json")
    running = load(PIPE / "running.json")
    assert len(goal["constraints"]) == 12 and len(goal["banned"]) == 11
    assert "server-6" not in running
    waiting = [
        (server, task) for server, tasks in queue["gpu_queues"].items()
        for task in tasks if task["status"] == "waiting"
    ]
    assert [t["id"] for _, t in waiting] == [
        "M191-CTF-HCG-CSORT-MQSD-TR", "M193-CTF-HCG-CSORT-MQHC-TR",
    ]
    with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    # Read the complete analysis corpus, not only truncated decision-index rows.
    corpus = []
    for path in sorted((PIPE / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        corpus.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "characters": len(text)})
    assert corpus
    terminal = []
    for prefix, suffix in [(184, "MQST"), (185, "MQPP"), (186, "MQHT"), (187, "MQFC"), (188, "MQB")]:
        eid = f"M{prefix}-CTF-HCG-CSORT-{suffix}-TR"
        exp = load(PIPE / "experiments" / f"{eid}.json")
        assert exp["status"] == "done_earlystop"
        matches = list((PIPE / "analyses").glob(f"{eid}_done_earlystop_*.md"))
        assert len(matches) == 1
        if exp.get("log_sha256"):
            assert sha(Path(exp["log_local"])) == exp["log_sha256"]
        entry = dict(
            id=eid, status=exp["status"], analysis=str(matches[0].relative_to(ROOT)),
            analysis_sha256=sha(matches[0]), log_verified=bool(exp.get("log_sha256")),
            flops_g=exp["measured_flops_g"],
        )
        if prefix == 187:
            # Exact value is present in the hash-verified paired analysis.
            assert "0.49029025435447693" in matches[0].read_text(encoding="utf-8")
            best = 0.49029025435447693
        else:
            best = exp.get("best_miou_exact", float(exp["final_best"]))
        entry.update(
            best=best, precision="rounded" if prefix == 188 else "exact",
            delta_baseline=best - BASELINE, delta_champion=best - CHAMPION,
            parent=f"M{prefix - 5}" if prefix < 188 else "M169",
            parent_trained=prefix == 188,
        )
        terminal.append(entry)
    table = "\n".join(
        f"| {r['id']} | {r['best']:.10f}{' (rounded)' if r['precision']=='rounded' else ''} | "
        f"{r['delta_baseline']:+.6f} | {r['delta_champion']:+.6f} | "
        f"{r['parent']} {'trained' if r['parent_trained'] else 'not trained'} | {r['flops_g']:.6f} |"
        for r in terminal
    )
    synthesis_path = PIPE / "reports" / f"terminal_control_synthesis_{stamp}.md"
    synthesis = f"""# Legacy Terminal-Readout Evidence Synthesis

Date: {now.isoformat(timespec='seconds')}, Asia/Shanghai.
Question: do the completed, preserved legacy controls justify another
terminal-readout successor or establish the effect of removing recurrence?

## Fixed Scope And Integrity

This review includes all five terminal runs M184-M188, chosen by the existing
legacy batch, not their scores. M189/M190 are censored live runs; M191/M193
are waiting and excluded. Four full archived logs match their recorded SHA256.
M188 has a rounded result and analysis but no archived log in its registry;
its exact precision and hash verification remain missing. No value is invented.
All {len(corpus)} analysis files were read and hashed; all {len(ledger)} ledger
rows were loaded. Corpus inventory is in the accompanying JSON.

## Results

| Experiment | Best mIoU | Delta baseline | Delta M95 | Parent evidence | FLOPs G |
|------------|-----------|----------------|-----------|-----------------|---------|
{table}

Denominator: 5/5 completed terminal controls fall below M95.
Two are below baseline; three are above baseline, of which M187 gains less
than 0.002. The strongest, M186, remains {CHAMPION - terminal[2]['best']:.10f}
below M95. These different mechanisms are not independent seed replications;
no pooled standard error or significance statement is justified.

## Causal Boundary

M179-M182 were resource-withdrawn before training. Their replacements
M184-M187 satisfy the resource bound but have no trained parent score.
Thus four of five controls cannot isolate an intermediate-feedback effect
from a matched parent comparison. M188 has a trained M169 parent (ledger
0.5000), with a descriptive rounded delta of -0.0084; no paired scene
predictions or multi-seed uncertainty is available here. This does not prove
that all recurrence or hierarchy mechanisms fail.

The full resource audit established eligibility, not usefulness. Existing
fixed-checkpoint diagnostics identify selection errors, but they do not
connect these aggregate terminal-control failures to a specific causal
selection dependency.

## Admission Outcome And Next Evidence

Admit no successor. Keep the two live runs and original waiting FIFO.
No exact new forward/loss distinct from closed candidate matching, ranking,
mask-scoring, and relation routes has been derived. Do not confuse the
absence of such a derivation with proof that no new mechanism exists.

Before a new mechanism: name a remaining measured error, derive its graph
and counterexamples, then verify primary-source distinctions. Preserve an
independent confirmation subset; the existing repeatedly mined diagnostic
banks and this validation-based review are exploratory only.

This is a CPU-only evidence/causal-control audit. No new inference, training,
config, package, checkpoint, dataset, GPU reservation, or deployment mutation.
"""
    synthesis_path.write_text(synthesis, encoding="utf-8")
    inventory_path = synthesis_path.with_suffix(".json")
    inventory_path.write_text(json.dumps(
        {"timestamp": now.isoformat(), "terminal": terminal, "analysis_corpus": corpus,
         "ledger_rows": len(ledger), "state_hashes": {
             name: sha(PIPE / name) for name in ["goal.json", "queue.json", "experiments.csv"]
         }}, indent=2), encoding="utf-8")
    assessment = "\n".join(
        f"| {r['id']} | {r['best_miou']} | {r['state']} | "
        "Historical evidence only; no automatic successor or new causal claim |"
        for r in ledger
    )
    review_path = PIPE / "reviews" / f"motivation_review_{stamp}.md"
    review_path.write_text(f"""================================================================================
  Motivation Review - cluster_project
  {now.strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

## 1. Goal
Complete authoritative goal.json:
```json
{json.dumps(goal, ensure_ascii=False, indent=2)}
```
Target 0.5100; exact champion {CHAMPION}; gap {0.51 - CHAMPION:.10f}.
check_goal at 17:12:06: Phase1 NOT YET (ledger display 0.5020).

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Multi-scale context helps historical baseline | Supported | M95-baseline +0.0130116045 | Not a new mechanism |
| Usable candidates usually exist in recoverable failures | Supported diagnostic | 99/111 M95 | Selection causality unresolved |
| Narrow shared-anchor binding explains fixed errors | Unsupported in sample | 0/21 applicable text readings | No applicable case |
| Terminal-readout controls preserve M95 gain | Unsupported on completed runs | 0/5 beat M95 | Two runs live, two waiting |
| Terminal comparisons isolate recurrence benefit | Mostly unidentifiable | 4/5 parents never trained | No causal edge effect for those four |

## 3. Experiment Assessment
Complete ledger inventory below, including historical/incomplete states to
avoid hiding missing evidence. All analysis texts were read; this inventory
does not assign a mechanism-specific explanation from a score alone.

| Experiment | mIoU | State | Motivation assessment |
|------------|------|-------|-----------------------|
{assessment}

Focused motivation/causal analysis of the newly completed batch:
`{synthesis_path.relative_to(ROOT).as_posix()}`.

## 4. Gap Analysis
- Five completed terminal controls fail to retain champion performance.
- Four lack trained parent comparisons; aggregate differences cannot identify
  the causal effect of removing intermediate feedback.
- The fixed-case, score-head, decoder and upstream audits have not produced
  an exact admissible new mechanism. Their negative results are scope-limited.
- Independent confirmation, exact novel derivation, matched mechanism
  controls, robustness and full-model efficiency remain required.
- M188 raw log is not archived in its registry; rounded metrics are explicit.

## 5. Design Rationale
Queue 2 waiting / 5 declared slots triggers review, not unconditional entry.
All 12 constraints and 11 bans were reread. Constraints 9-12 require concrete
error evidence, derivation, novelty and validation boundaries; constraint 11
explicitly places these above queue depth. No candidate passes admission.
The old-model aggregate audit is linked to the existing terminal-recurrence
question, not presented as a new mechanism. No numerical tuning, forbidden
route, seed, schedule, or model structural change is introduced.

## 6. Next Batch
No exp_design or new batch is admitted. Keep M189/M190 live and preserve
M191 then M193 on server-4. The next scientific work must fill the exact
derivation/independent-evidence gap rather than expand legacy selectors.
================================================================================
""", encoding="utf-8")
    os.environ["PROJECT_ROOT"] = "D:/project"
    result = subprocess.run([
        "bash", "D:/project/.claude/skills/songcl_research_pipeline/log_decision.sh",
        "cluster_project", "route_change",
        "Five terminal controls M184-M188 are complete; does their evidence admit successors or refill the 2/5 queue?",
        "Close completed variants without successors; admit no new mechanism; preserve live M189/M190 and server-4 FIFO M191 then M193.",
        "0/5 completed controls beat exact M95;4/5 parents never trained, so recurrence effect is not isolated. Scientific admission overrides depth; no distinct derived mechanism exists.",
        str(synthesis_path.relative_to(ROOT)) + "; " + str(review_path.relative_to(ROOT)),
    ], check=True, capture_output=True, text=True, encoding="utf-8")
    print(result.stdout)
    decision = sorted((PIPE / "decisions").glob("*_route_change.md"))[-1]
    report_path = PIPE / "reports" / f"summary_{stamp}.md"
    queue_table = "\n".join(
        f"| {i} | {t['id']} | {t['config']} | waiting | - | {server} |"
        for i, (server, t) in enumerate(waiting, 1)
    )
    report_path.write_text(f"""================================================================================
  Research Pipeline Report - cluster_project
  {now.strftime('%Y-%m-%d %H:%M:%S')} (tick #20260912-1707)
================================================================================

## 0. Goal Status
Target: mIoU >= 0.5100 | Champion: M95-CTF-HCG-CSORT 0.5020 (ledger)
Gap: +0.0080 (ledger) | Phase: 1 (NOT YET).
Exact archive champion: {CHAMPION}; exact gap: {0.51 - CHAMPION:.10f}.
Baseline exact: {BASELINE}. Goal checks ran at 17:09 and 17:12.

## 1. GPU Overview
| Server | GPU | Util | Memory MiB | Process |
|--------|-----|------|------------|---------|
| server-4 | 0 | 75% | 27904/32607 | M190 PID3595977 plus external co-tenant |
| server-4 | 1 | 25% | 21393/32607 | M189 PID3398172 |
| server-6 | 7 | 0% | 6/81559 | IDLE |

Live GPU readings taken about 17:09. Free GPU: server-6:7, two configured
task slots. No server-6 waiting task; existing FIFO remains on server-4.
Capacity discrepancy retained: declared 5; SERVERS.yaml configured 4 (2+2).
No allocation, cross-server migration, overlay, or capacity setting changed.

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
| M189-CTF-HCG-CSORT-MQBC-TR | model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqbc_tr | server-4 | 1 | 20/50 | 0.4908618331 | 0.542 | 0.452 | 0/10 | running |
| M190-CTF-HCG-CSORT-MQTD-TR | model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqtd_tr | server-4 | 0 | 17/50 | 0.4890006185 | 0.542 | 0.454 | 2/10 | running |

Epochs are live monitor progress counters; paired metrics checked directly in
remote logs. M184 is terminal, not a third live trainer.

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
{queue_table}

Queue depth: 2 waiting / 5 declared allowed-GPU slots -> NEED MORE (minimum6).
Configured capacity4 also implies NEED MORE (minimum5). Scientific admission
blocks new entries; no reorder or migration was performed.

## 4. This Tick's Actions
- [Health] .tick_unhealthy absent; durable memory and authoritative state reconciled.
- [Monitor] Ran required pipeline_monitor; M184 process absent, deathwatch1/3.
- [Goal] Ran check_goal twice, including after terminal ledger update; NOT YET.
- [Terminal] Verified explicit M184 normal stop,25 contiguous validations,
  best0.4876259565@15, ten stale validations; no trainer process; remote/local
  SHA256 b615b2f6dcacb15a2233bf48842988566a4bcdfda57932293c0d4ff1f6434c6d.
- [Archive] Pulled log only; generated
  `pipeline/analyses/M184-CTF-HCG-CSORT-MQST-TR_done_earlystop_20260912-171500.md`.
- [State] Finalized M184 using the monitor's locked writer; preserved history,
  server-4 queue and running map. Released GPU7; checkpoint remains remote.
- [Research] Read/hash-inventoried {len(corpus)} analyses and {len(ledger)}
  ledger rows. Wrote terminal-control causal-evidence synthesis and full-goal
  motivation review. No admitted mechanism, implementation or new queue entry.
- [Crash repair] No new model crash; zero repair attempts required.
- [Sync] No Cluster source/config changes; no deployment sync needed.
- [Housekeeping] Summary retention restricted to summary_*.md older than24h;
  final check and durable-memory replacement completed by tick close.

## 5. Decisions Made
- [17:11:44] other: finalize only M184 on verified terminal evidence; see
  `pipeline/decisions/20260912-171144_other.md`.
- [{now.strftime('%H:%M')}] route_change: no successors or new batch; keep
  legacy FIFO and admission gate; see `{decision.relative_to(ROOT).as_posix()}`.

## ⚠ Pending User Decisions
- [2026-09-11 21:13:33] GPU1 external-overlay question remains within24h
  reporting window, but was operationally resolved by M189's normal launch
  at03:07. No active user decision or interaction is needed.

================================================================================
  Next tick: 2026-09-12 18:07
================================================================================
""", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "review": str(review_path),
                      "synthesis": str(synthesis_path), "corpus_count": len(corpus)}, indent=2))


if __name__ == "__main__":
    main()
