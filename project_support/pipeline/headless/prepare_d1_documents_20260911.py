"""Freeze the diagnostic protocol before pilot inference."""
import json
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
goal = json.loads((ROOT / "pipeline/goal.json").read_text(encoding="utf-8"))
stamp = "20260911-051200"
review = """# Motivation Review - cluster_project
2026-09-11 05:12 Asia/Shanghai, before D1 pilot.

## 1. Goal
Full authoritative goal:
```json
GOAL_JSON
```
Checker05:11:08: Phase1 NOT YET, ledger M95=.5020, target=.5100, gap+.0080.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Context platform improves baseline | Historical descriptive support | Exact audited .5024607182 vs .4894491136 | No fresh replay; seed fragility |
| Terminal transport improves champion | Unsupported M186 | .4944996834, normal stop27 | Not a diagnosis |
| Bank versus selection error can guide one new mechanism | Unmeasured | Frozen manifest and compatible checkpoints | Capture and verify candidate bank |
| Shared-anchor identity is a useful novel mechanism | Provisional only | Rethink memo | Diagnosis, derivation and verified primary papers |

## 3. Experiment Assessment
| Experiment | mIoU | Motivation relation | Contribution |
|------------|------|---------------------|--------------|
| Baseline exact best15 | .4894491136 | Reference platform | Weights/log match, current explicit module strict-compatible |
| M95 exact best16 | .5024607182 | Strongest historical context | Checkpoint identity audited, not historical-forward verified |
| M183 best14 | .4915492237 | Fixed ancestor initialization | Tested variant closed |
| M186 best17 | .4944996834 | Terminal transport | Tested variant closed; already analyzed |
| M184/M185/M187/M188 | unfinished | Legacy controls | Preserve, no final comparisons |
Earlier full assessment inventories and immutable analyses remain authoritative.
No new terminal experiment at05:10; no duplicate analysis or CSV row.

## 4. Gap Analysis
D0 fixed284 descriptions/71physical scenes, reserved4646/70; historical
validation reuse prevents untouched-test claims. No candidate banks measured.
Original get_iou uses sigmoid>=.5, whereas export binary encoding uses>.5.
D1 must preserve actual IoU semantics, point weighting, argmax and same bank.
CPU strict compatibility excludes only two exactly-equal nonpersistent buffers;
it does not establish historical code identity or fresh full-validation accuracy.
Eight-description pilot cannot estimate error prevalence or select a mechanism.

## 5. Design Rationale
Q1: Need reliable per-example selected/oracle masks to quantify headroom.
Q2: Isolated wrapper calls original predictor and checks exact equality, then
stores original logits/scores/point mappings/GT without modifying packages.
Q3: A bounded fixed pilot can validate the collector and expose protocol defects.
Six coverage areas: diagnosis now; derivation is diagnostic identity only,
not novelty; original-paper novelty and causal controls remain prerequisites
to NEW mechanisms; robustness needs scene-level analysis; efficiency pilot
is a resource safety check, not the bs1/warmup20/repeat100 model benchmark.
All12constraints/11bans retained. No tuning, training, new seed, dataset,
annotation service, schedule change, resource waiver or queue mutation.

## 6. Next Batch
Evaluation-only D1-PILOT, exp_design_20260911-051200.md.
First two lexicographically ordered diagnostic scenes from frozen v2,
all four sampled descriptions each, baseline/M95 same eight inputs.
Singleton language grouping explicitly differs from historical validation;
results are correctness-only until batch/grouping and replay checks complete.
Legacy FIFO M189/M190/M191/M193 preserved. No new mechanism admission.
"""
design = """# Experiment Design - cluster_project
2026-09-11 05:12 Asia/Shanghai.

## 1. Motivation
Authoritative goal description: DESCRIPTION
Review051200 precedes this design. Waiting4<reserve5 triggers review, but
scientific admission overrides refill. D1-PILOT is an evaluation diagnostic,
not an independent novelty claim or a new full-training experiment.

## 2. Current Best Results
| ID | Config | State | Best mIoU | Acc50 | spmIOU | Epoch |
|----|--------|-------|-----------|-------|--------|-------|
| Baseline | saved model_base2.yaml; explicit model_base1 | done | .4894491136 | .541 | .451 | 15 |
| M95 | ctf_hcg_csort | done | .5024607182 | .557 | .465 | 16 |
| M186 | mqht_tr | done_earlystop | .4944996834 | .548 | .459 | 17 |
Historical exact audit, not fresh replay; ledger remains .4894/.5020.

## 3. Analysis & Direction
### 3.1 Effective
Context platform historically outperforms baseline; no new causal conclusion.
### 3.2 Failed
M183/M186 below champion; preserve failed variants without automatic descendants.
### 3.3 Unverified
For fixed logits L[Q,S], scores Z[Q,2], point mapping s[N], GT y[N]:
q_hat=argmax softmax(Z)[:,1]; b_qn=1[sigmoid(L[q,s[n]])>=.5].
I_q=sum_n b_qn*1[y_n>.5]; U_q=sum_n(b_qn+1[y_n>.5])-I_q.
IoU_q=I_q/(U_q+1e-6); a=IoU_q_hat; o=max_q IoU_q.
Adding/subtracting o gives 1-a=(1-o)+(o-a), with o>=a for a
nonempty same-bank selection. Oracle uses GT only for diagnosis.
This algebra has no trainable gradients and is NOT a novel mechanism.
Collector temporary point storage O(N), retained bank O(Q*S), scoring
O(Q*N); no N-squared attention, no change to model FLOPs or scores.
### 3.4 Conclusion
Test collector correctness first. No mechanism choice from eight pilot examples.

## 4. Experiment Plan
| # | ID | Config Path | Purpose | Expected Result | Priority | Depends On |
|---|----|-------------|---------|-----------------|----------|------------|
| 1 | D1-PILOT-baseline | audited saved model_base2.yaml | Capture same-bank outputs | Exact original prediction equality | P0 | D0 audit |
| 2 | D1-PILOT-M95 | audited saved ctf_hcg_csort YAML | Matched eight inputs | Exact original prediction equality | P0 | D0 audit |
Freeze first two lexicographic diagnostic scene IDs/all4frozen descriptions.
Use singleton language batches, test seed1999; no source mutation.
Save logits, scores, selected/oracle index, per-candidate IoUs, point mappings,
GT, input/checkpoint/config/code/manifest hashes and original-output equality.
Do not access reserved samples for mechanism selection or run fullvalidation.

## 5. GPU Allocation Plan
| Server | GPU | Assignment | Config | Justification |
|--------|-----|------------|--------|---------------|
| server-4 | 0 | Preserve M188 | mqb_tr | Active trainer |
| server-4 | 1 | Preserve M187; bounded sequential pilot | baseline then M95 | Fresh free>=8GiB, allocatorcap4GiB |
| server-6 | 7 | Preserve M184/M185 | mqst_tr/mqpp_tr | cap2, no extra worker |
One evaluation worker only; fresh memory check before every case/batch,
abort below5GiB free; max600seconds inference/case. No extra training slot.

## 6. Implementation Checklist
- [x] Required upstream review and explicit diagnostic derivation.
- [x] Standalone pipeline/headless worker, remote/tmp, not active model packages.
- [x] Check immutable manifest, checkpoint, config and package hashes.
- [x] Strict learned-weight load; only exact equal historical buffers omitted.
- [ ] Synthetic threshold, identity and failure-case tests.
- [ ] Safe upload both allocated servers; inference only on server-4GPU1.
- [ ] Pilot original prediction equality and artifact readback verification.
- [ ] Report missing measurements and update durable memory.
No variant package/config/enqueue/commit required: evaluation-only helper.

## 7. Risk Assessment
Reject collector results on identity/hash mismatch, nonfinite/empty bank,
original-output discrepancy or incomplete bank membership. Preserve failures.
Singleton grouping may alter padding/numerics relative to historical32;
pilot does not establish fullvalidation reproduction or representative metrics.
Baseline historical forward equivalence remains unverified despite strict
weights. Resource guard bounds torch allocator, not all CUDA context overhead.
No efficacy/speedup claim. At most3 repair attempts; no trainer termination.
Smell/constraints: no training graph/config tuning, no banned family,
all12constraints/11bans retained; science prerequisites block new admission.

Status: APPROVED for bounded evaluation only, not training.
"""
(ROOT / f"pipeline/reviews/motivation_review_{stamp}.md").write_text(
    review.replace("GOAL_JSON", json.dumps(goal, ensure_ascii=False, indent=2)), encoding="utf-8")
(ROOT / f"pipeline/designs/exp_design_{stamp}.md").write_text(
    design.replace("DESCRIPTION", goal["description"]), encoding="utf-8")
print("D1 upstream review and diagnostic design frozen", stamp)
