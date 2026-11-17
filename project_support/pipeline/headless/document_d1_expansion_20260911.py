"""Render the preregistered review/design with the authoritative goal snapshot."""
import json
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
goal = json.loads((ROOT / "pipeline/goal.json").read_text(encoding="utf-8"))
stamp = "20260911-071200"
review = f"""# Motivation Review - cluster_project
2026-09-11 07:12 Asia/Shanghai; D1 expansion, evaluation only.

## 1. Goal
Complete authoritative goal:
```json
{json.dumps(goal, ensure_ascii=False, indent=2)}
```
Checker07:10:24: Phase1 NOT YET; ledgerM95 .5020 / target .5100 / gap +.0080.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context improves baseline | Historical support | .5024607182 vs .4894491136 | Historical replay/seed fragility |
| Selection may miss a good bank mask | Confirmed pilot only | 3/8 failures with oracle>.5 in bothmodels | Remaining276 IDs |
| Pilot binary results tolerate original grouping | Pilot supported | 8IDs/model; five comparisons zero discrete change | Not universal invariance |
| Shared-anchor mechanism is useful/novel | Unverified | Provisional rethink memo | Causal labels, derivation, primary papers |

## 3. Experiment Assessment
| Experiment | mIoU | Relation to motivation | Contribution |
|------------|------|------------------------|--------------|
| Baseline historical | .4894491136 | Reference | Audited checkpoint |
| M95 historical | .5024607182 | Context platform | Ledger champion, not fullreplay |
| M183 | .4915492237 | Fixed ancestor initialization | Closed variant |
| M186 | .4944996834 | Legacy terminal transport | Normalstop27, already analyzed |
| D1pilot8 baseline/M95 | .538820513/.550915219 | Collector correctness | 16banks verified, not fullval |
| D1group audit | Same8 pilot IoUs | Protocol control | Discrete stable, floats not exact |
| M184/M185/M187/M188 | Unfinished | Legacy controls | Preserve running/FIFO |
Historical 223-analysis inventory remains supporting context, not new causal evidence.

## 4. Gap Analysis
Only2/71 frozen diagnostic scenes measured. Need complete coverage and missingness
before mechanism ranking. Candidate bank limitation does not distinguish missing
targets from inaccurate boundaries; selection gap does not identify relation cause.
No reserved inference. Equal-scene four-description sample is not description-
weighted population prevalence. Historical validation reuse is explicit.

## 5. Design Rationale
Q1: Does oracle headroom persist beyond two pilot scenes?
Q2: Capture originalgroup outputs for all284 frozen IDs, including8 as continuity
anchors; never count nuisance language-group members as added diagnostic coverage.
Q3: Obtain matched errors and scene uncertainty with explicit resource exclusions.
All12constraints/11bans retained. Six coverage areas: D1 quantifieddiagnosis now;
mechanism/derivation and primarypaper novelty remain N1; efficacy controls E1;
scene uncertainty here plus robustness V1; guarded eval is not efficiencybenchmark.
No graph/numeric tuning, newdataset, externalannotation or multiseedtraining.

## 6. Next Batch
See exp_design_{stamp}.md. D1-EXPAND, no newtraining enqueue.
"""
design = f"""# Experiment Design - cluster_project
2026-09-11 07:12 Asia/Shanghai.

## 1. Motivation
Project motivation (verbatim goal.description): {goal['description']}
Waiting4 below reserve5 triggers review. Scientific admission overrides refill.
Parentquestion: quantify candidate-bank limitation and selection headroom using
both audited checkpoints and the entire previously frozen diagnostic sample.

## 2. Current Best Results
| Experiment ID | Config | State | Best mIoU | Acc50 | spmIOU | Epochs |
|---------------|--------|-------|-----------|-------|--------|--------|
| Baseline | Audited model_base2.yaml; explicit model_base1 | historical | .4894491136 | .541 | .451 | best15 |
| M95 | Audited csort config/module | historical | .5024607182 | .557 | .465 | best16 |
| M183 | hqi | done_earlystop | .4915492237 | .545 | .455 | 24 |
| M186 | mqht_tr | done_earlystop | .4944996834 | .548 | .459 | 27 |
Upstream review071200 and terminal analyses/CSV/index; ledger not rewritten.

## 3. Analysis & Direction
### 3.1 Effective
Historical context platform improves reference; pilot exhibits selection errors.
### 3.2 Failed
Explicit routing and prior banned families remain closed. M186 did notbeatM95.
### 3.3 Unverified
Boundary/identity/relation labels, coremechanism, novelty, robustness and efficiency.
### 3.4 Conclusion And Prespecified Analysis
For each SAME nonemptybank P, selected a=IoU(p_hat,y), oracle o=max IoU(p,y).
Point masks use sigmoid>=.5, GT>.5, union+1e-6. Verify1-a=(1-o)+(o-a).
This algebra is bookkeeping, not a novel loss or coverage/boundary decomposition.
Use original saved languagegroups and seed1999, no changedforward/gradients.
Save128candidate logits/scores, allIoUs, GT/mapping, selectedprobabilities and indices.
Same-forward equality and CPU allcandidate readback required before interpretation.
Report selectedIoU, oracleIoU, banklimitation, selectiongap, Acc50 with IoU>.5,
recoverable failure a<=.5<o and bankfailure o<=.5. No outcome-chosen cutoffs.
Scene uncertainty:10000 physical-scene bootstrap replicates, seed1999,
percentile95; paired M95-minus-baseline on matched complete4-ID scenes only.
Report incomplete scenes and model-specific missing IDs separately; no imputation.
Not statistical confirmation on untouchedtest, nor deployableoracle gains.

## 4. Experiment Plan
| # | ID | Config Path | Purpose | Expected Result | Priority | Depends On |
|---|----|-------------|---------|-----------------|----------|------------|
| 1 | D1-EXPAND-BASE | Audited savedconfig | All284 fixed diagnostic IDs | Honest denominator/banks | P0 | D0+D1GROUP |
| 2 | D1-EXPAND-M95 | Audited savedconfig | Matched sameIDs/groups | Paired decomposition | P0 | BASE completion |
Full frozen list sample_manifest_v2 SHA84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468.
71physicalscenes/284IDs;70reserved physicalscenes not inferred.
Eight pilot IDs rerun in originalgroups as part of284, not duplicated observations.

## 5. GPU Allocation Plan
| Server | GPU | Assignment | Config | Justification |
|--------|-----|------------|--------|---------------|
| server-4 | 0 | Preserve M188 | mqb_tr | Active trainer |
| server-4 | 1 | Preserve M187; sequential eval | mqfc_tr + audited configs | Freshfree>=8GiB;4GiB allocatorcap |
| server-6 | 7 | Preserve M184/M185 | mqst_tr/mqpp_tr | Capacity2 occupied |
Per-groupfree>=5GiB;600s inferencebudget;720s shelltimeout.
Originalgroups only. Allocator OOM=>recordgroup missing, no increasedcap or regrouping.

## 6. Implementation Checklist
- [x] Existing audited configs, immutable checkpoint SHA and explicitmodules selected.
- [x] Upstream full-goal six-section review saved before design.
- [ ] Isolated capture, checkpoint/source/package/hash validation and guard implementation.
- [ ] Compile and seven existing actual-IoU CPUtests.
- [ ] Hashverified helper sync to both available servers, preserve deployment diffs.
- [ ] Sequential bounded inference, outputsdownload/hashverification.
- [ ] CPUreadback, matcheddenominators and scene summaries.
- [ ] Postflight trainers/queue and finalreport.
Trainingpackage independence checks, training YAML/commit/push/enqueue: N/A,
no new model variant. Helper provenance uses SHA; activepackage untouched.

## 7. Risk Assessment
All12constraints/11bans checked: diagnostic only, no tuning/injection/projection/
schedulechanges, no efficiencyadmission waiver. No newtrainingsmell candidate.
Checkpoint strictload only omits two alreadyaudited exactruntimeequal buffers.
Other errors failclosed,<=3 documented repairs. SharedGPU resourcecap protects
trainers; resource missingness may bias any incomplete-sample interpretation.
Batchcontext includes unsampled descriptions in diagnostic scenes only; no scores
from these become diagnostic observations. No reservedscene leakage.
Original grouping doesnot establish exact historicalforward identity.
Onecandidateatime O(N)temporary; bankstored QxS not QxN. No N^2attention added.
N1 novelty/derivation gate remains closed; do not turn oracle gap into a selector
family or infer same-category/relation causes without labels.

Status: APPROVED for bounded evaluation only; implementation checkpoints pending.
Designed by: Research Pipeline (autonomous)
"""
for folder, prefix, text in (("reviews", "motivation_review", review),
                             ("designs", "exp_design", design)):
    path = ROOT / "pipeline" / folder / f"{prefix}_{stamp}.md"
    assert not path.exists()
    path.write_text(text, encoding="utf-8")
    print(path)
