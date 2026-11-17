"""Render the evidence-recovery tick from the current authoritative files."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
STAMP = "20260912-181300"


def main():
    goal_text = (PIPE / "goal.json").read_text(encoding="utf-8")
    goal = json.loads(goal_text)
    assert len(goal["constraints"]) == 12 and len(goal["banned"]) == 11
    audit = json.loads((PIPE / "reports/m188_archive_audit_20260912-181200.json").read_text())
    for name, expected in audit["protected_state"].items():
        assert hashlib.sha256((PIPE / name).read_bytes()).hexdigest() == expected
    with (PIPE / "experiments.csv").open(encoding="utf-8", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    assert len(ledger) == 226
    assessment = "\n".join(
        f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | "
        "Historical evidence; no automatic successor or causal claim |"
        for r in ledger)
    review = f"""================================================================================
  Motivation Review - cluster_project
  2026-09-12 18:13:00 (tick #20260912-1807)
================================================================================

## 1. Goal
Full authoritative goal.json:
```json
{goal_text.strip()}
```
Target .5100; champion M95 .5024607181549072; exact gap .0075392818450928.
check_goal at18:09 and18:12: Phase1 NOT YET, ledger .5020/gap .0080.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Historical multi-scale context helps | Supported historical result | Exact M95-baseline +.0130116045 | Not a new mechanism |
| Selection is the principal frozen-bank error | Supported exploratory diagnostic | D1 99/111 recoverable M95 errors contain a usable positive | Independent confirmation |
| Narrow shared-anchor binding explains fixed errors | Unsupported in reviewed sample | 0/21 text readings applicable | No applicable fixed case |
| Completed terminal controls retain M95 performance | Not supported | 0/5 M184-M188 exceed M95 | Live M189/M190 and waiting M191/M193 not included |
| Exact log recovery identifies recurrence causality | No | M188 now .49161195755004883@13, SHA verified | Four parents never trained; no paired scene uncertainty |

## 3. Experiment Assessment
All 229 current analysis files were read/hash-inventoried in
`pipeline/reports/m188_archive_audit_20260912-181200.json`.
All 226 ledger rows are listed without treating stale historical waiting
rows as the current queue; current dispatch state comes from queue/running.

| Experiment | mIoU (ledger) | State | Motivation assessment |
|------------|---------------|-------|-----------------------|
{assessment}

Focused result update: M188 exact mIoU .49161195755004883, Acc@50 .544,
spmIOU .457 at13; final23; 10 stale validations. Exact differences are
+.0021628439 vs baseline and -.0108487606 vs M95. It is above baseline
but fails to preserve the champion gain. All five completed child logs
now have matching archive hashes. The prior17:15 synthesis's missing-M188-log
statement is superseded, not its0/5 result or causal caveats.

## 4. Gap Analysis
- Q1: A specific measured error still needs an exact derived mechanism
  distinguishable from the already reviewed scoring/ranking/relation families.
- The log-precision gap is closed. Mechanism novelty, matched causal controls,
  independent confirmation, robustness and efficiency are not supplied by it.
- M169 parent remains rounded in this comparison; no fabricated precision.
- Four untrained parents prevent isolating recurrence effects for M184-M187.
- Repeated validation-bank mining remains exploratory, never a test result.

## 5. Design Rationale
- Q2: This tick performs a bounded offline evidence-correctness check of the
  existing terminal-control hypothesis, not a new selector or pooling variant.
- Q3: It makes the complete five-child result auditable without inventing
  additional efficacy or causal evidence. No successor is justified.
- Constraints1-8: no resource/training/schedule/seed/graph change, no tuning,
  no routing or multi-injection claim. Constraints9-12: retain diagnosis,
  derivation, primary-source novelty, control and validation admission gates.
- All11 bans checked: no banned family is implemented or revived.
- Queue2/5 triggers review; constraint11 prioritizes admission over refill.
- Smell check: no candidate forward/loss is proposed, no numeric rescue.

## 6. Next Batch
No newly admitted mechanism, exp_design, implementation, training enqueue
or code sync. Preserve M189/M190 and FIFO M191 then M193 on server-4.
Next scientific step requires a distinct derivation with independent evidence,
not more variants of closed routes. No user interaction is required.
================================================================================
"""
    (PIPE / f"reviews/motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    report = """================================================================================
  Research Pipeline Report - cluster_project
  2026-09-12 18:13:00 (tick #20260912-1807)
================================================================================

## 0. Goal Status
Target: mIoU >= 0.5100 | Champion: M95-CTF-HCG-CSORT 0.5020 (ledger)
Gap: +0.0080 (ledger) | Phase: 1 (NOT YET).
Exact champion .5024607181549072; exact gap .0075392818450928.
Exact baseline .4894491136074066. Goal checked at18:09 and18:12.

## 1. GPU Overview
| Server | GPU | Util | Memory MiB | Process |
|--------|-----|------|------------|---------|
| server-4 | 0 | 77% | 27902/32607 | M190 PID3595977 plus external co-tenant |
| server-4 | 1 | 67% | 21517/32607 | M189 PID3398172 |
| server-6 | 7 | 0% | 6/81559 | IDLE |

Live SSH readings at18:09. Free GPU: server-6:7, two configured slots,
but no server-6 waiting tasks. No cross-server FIFO migration.
Declared capacity5 vs SERVERS.yaml configured4 (2+2) remains explicit;
no capacity settings or external processes changed.

## 2. Running Experiments
| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |
|----|--------|--------|-----|-------|-----------|--------|--------|---------|--------|
| M189-CTF-HCG-CSORT-MQBC-TR | model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqbc_tr | server-4 | 1 | 21/50 | 0.4908618331 | 0.542 | 0.452 | 1/10 | running |
| M190-CTF-HCG-CSORT-MQTD-TR | model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqtd_tr | server-4 | 0 | 17/50 | 0.4890006185 | 0.542 | 0.454 | 2/10 | running |

Epochs/no-improve are the18:08 live monitor counters. Best paired metrics
were verified in remote logs at18:10; both trainer PIDs remain present.
No newly terminal experiment this tick.

## 3. Queue Status
| Position | ID | Config | Status | Depends On | Server |
|----------|----|--------|--------|------------|--------|
| 1 | M191-CTF-HCG-CSORT-MQSD-TR | configs/Quard/ctf_hcg_csort_mqsd_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqsd_tr.yaml | waiting | - | server-4 |
| 2 | M193-CTF-HCG-CSORT-MQHC-TR | configs/Quard/ctf_hcg_csort_mqhc_tr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhc_tr.yaml | waiting | - | server-4 |

Queue depth:2 waiting /5 declared capacity slots -> NEED MORE (minimum6).
Configured capacity4 also implies NEED MORE (minimum5). Scientific admission
takes priority; no new qualified mechanism or FIFO mutation.

## 4. This Tick's Actions
- [Health] .tick_unhealthy absent. Read durable memory, authoritative goal,
  queue, ledger, recent full decisions, designs, analyses, bugfixes and reports.
- [Monitor/Goal] Required monitor completed; goal checks before/after archive
  metadata update remain Phase1 NOT YET.
- [Evidence] Recovered M188 log only. Remote/local SHA256:
  92790e62ccd35df7fee0310ac8b5c179a7623df29fd64da27df0fe0c445ea0bc.
  23 contiguous9508-expression validations; exact best .49161195755004883@13;
  final .4848948121070862@23; explicit10-patience normal stop.
- [Analysis] Supplement:
  pipeline/analyses/M188-CTF-HCG-CSORT-MQB-TR_done_earlystop_20260912-181200.md.
  Actual logger end04:04:56+08 differs from registry detection04:08:31.
- [Metadata] Under monitor lock, backfilled M188 archive/precision fields and
  ledger log_local. Preserved terminal state, old history, all226 ledger rows,
  rounded ledger best, and byte-identical goal/queue/running. No re-finalization.
- [Research] Verified all five M184-M188 child-log hashes. Read/hash-inventoried
  229 analysis documents; all5 remain below M95, four parents never trained.
  Wrote full-goal motivation_review_20260912-181300.md; no mechanism admitted.
- [Crash/Sync] No new model crash, repair attempt, training, model/config edit
  or deployment sync. Evidence scripts are local pipeline utilities only.
- [Housekeeping] Remove only expired summary_*.md older than24h; preserve
  analyses and scientific reports. Replace durable memory and validate output.

## 5. Decisions Made
- [18:11:45] other: archive M188 evidence without repeating its transition;
  pipeline/decisions/20260912-181145_other.md.
- [18:12:06] route_change: precision recovery does not change admission;
  preserve legacy runs and FIFO without successors;
  pipeline/decisions/20260912-181206_route_change.md.

## \u26a0 Pending User Decisions
- The2026-09-11 21:13:33 external-overlay question is inside the24h window,
  but its dispatch blocker was operationally resolved by M189 launch at03:07
  on September12. No active pending decision or user interaction.

================================================================================
  Next tick: 2026-09-12 19:07
================================================================================
"""
    (PIPE / f"reports/summary_{STAMP}.md").write_text(report, encoding="utf-8")
    assert len(audit["analyses"]) == 229
    assert all(f"## {n}." in report for n in range(6))
    assert all(f"## {n}." in review for n in range(1, 7))
    print("Wrote validated six-section review and tick report:", STAMP)


if __name__ == "__main__":
    main()
