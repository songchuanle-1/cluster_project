"""Freeze this tick's diagnostic documents and provenance before execution."""
from datetime import datetime
import json
from pathlib import Path
from d1_candidate_bank_20260911 import sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_ordering_20260911-1210"


def main():
    assert not OUT.exists()
    goal = json.loads((P / "goal.json").read_text(encoding="utf-8"))
    previous = json.loads((P / "reports/d1_assignment_20260911-1113/protocol.json").read_text(encoding="utf-8"))
    assert sha(P / "goal.json") == previous["goal_sha256"]
    stamp = datetime.now().isoformat()
    review = f"""================================================================================
  Motivation Review - cluster_project
  {stamp}
================================================================================
## 1. Goal
Full authoritative goal snapshot:
```json
{json.dumps(goal, indent=2, ensure_ascii=False)}
```
Checker12:08:27 Phase1 NOT YET; target.5100/M95.5020/baseline.4894/gap+.0080.
Historical goal.findings strings are not live states.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Selection headroom | measured |90/111 recoverable of284 baseline/M95|Score ordering|
| Missing usable-positive supervision dominates | rejected on sample |84/99 recoverable retain usable positives|Shared gradients/causal training effects|
| Semantic alignment token-mask invariance | untested |source denominator includes full length|Synthetic invariance and real padding exposure|
## 3. Experiment Assessment
| Experiment | mIoU | Motivation | Contribution |
|---|---|---|---|
| Baseline/M95 archives |.489449/.502461|Reference|Historical identity limits remain|
| M183/M186 |.491549/.494500|Legacy controls|No champion gain|
| D1 baseline/M95 sample |.535914/.502217|Fixed diagnosis|Not population efficacy|
223 historical analyses hash-reconciled; subsequent M186 analyzed,224total.
Routing/gate/residual/auxloss historical failures remain binding context.
## 4. Gap Analysis
Need ranks and margins of usable positives versus selected negatives, with
success/bank-failure controls. Need source-level alignment masking audit before
collecting projection tensors. Current banks lack proj_queries/proj_tokens,
lang_masks and dense maps, so no real semantic-gradient claim is possible.
## 5. Design Rationale
Q1:Close evidence gaps for ranking and alignment semantics. Q2:CPU bank scores
plus source-extracted loss invariance/gradient tests. Q3:accept or reject bounded
mathematical claims, not propose a scalar rescore or novel model.
All12constraints/11bans checked: no config/model/schedule/seed/loss change;
no new data/annotation/attention/projection/gating/routing. Diagnostic arithmetic
is not a novelty claim. Core mechanism, primary comparison, causal matched
intervention, generalization and full-model efficiency remain incomplete.
## 6. Next Batch
exp_design_20260911-121000.md. CPU diagnostics only, no training admission.
"""
    (P / "reviews/motivation_review_20260911-121000.md").write_text(review, encoding="utf-8")
    design = f"""================================================================================
  Experiment Design - cluster_project
  {stamp}
================================================================================
## 1. Motivation
{goal['description']}
Upstreamreview121000. Waiting4/capacity4 triggers research; goal scientific
admission overrides refill. Roles:ranking diagnosis and formal correctness.
## 2. Current Best Results
| ID | Config | State | Best mIoU | Acc50 | spmIOU | Epochs |
|---|---|---|---|---|---|---|
|baseline|model_base1|historical|.4894491136|.541|.451|best15|
|M95|ctf_hcg_csort|done_earlystop|.5024607182|.557|.465|archivebest16|
|M186|mqht_tr|done_earlystop|.4944996834|.548|.459|27/best17|
## 3. Analysis & Direction
### 3.1 Effective evidence
Current candidate banks often contain usable positives but selection fails.
### 3.2 Failed claims
Missing-positive supervision is not dominant in current frozen sample.
Shared-witness applicability/novelty not established; no newvariant admitted.
### 3.3 Missing controls
Score ranks/margins, semantic-loss padding invariance, actual semantic tensors.
### 3.4 Derivation and falsification
Let d_q=z_q1-z_q0, p_q=sigmoid(d_q). Ordering should agree with p in exact
arithmetic; check savedfloat32 argmax, ties and stablefloat64 independently.
G=IoU>.5, P=replayedpositiveindices, H=G intersect P.
For nonemptyG/H record best score, rank=1+count strictlygreater scores,
score margin selected-minus-bestG/H, and countUsable/positive. Use all284IDs
permodel, split success/recoverable/bankfailure. No tuned score threshold.
Report medians/quartiles rather than call a margin 'confident' arbitrarily.
Ranks and restricted maxima are GT diagnostics, not a deployable improvement.

Semantic source S=V T^T/temperature. Extract actual loss_sem_align and index
helper. With no modifier/pronoun/relation/other maps, A is sourcepositive map,
w query weights, t token weights, n_q=sum_l A+eps, m_l=sum_q A+eps:
 L=[sum_q w_q(-sum_l A*S/n_q+LSE_l S)
   +sum_l t_l I(any_q A)(entropy_l-sum_q A*S/m_l+LSE_q S)]/(2M).
 dL/dS_ql=[w_q(softmax_l S-A/n_q)
   +t_l I(any_q A)(softmax_q S-A/m_l)]/(2M).
Source sets unmatched queries to two sentence-end tokens; t assignments
overwrite in code order. Formula and tests restricted to no-overlap maps.
Other-entity map doubles selected logits inside query->token LSE, not a mask.
Allmaps/overlap semantics will be documented; no blanket ordinary-CE claim.

Padding test:hold validunit embeddings/labels fixed; append two padding
tokens withunit embeddings and lang_masks=0. If source loss changes, reject
padding invariance for this controlled input, NOT claim real training harm.
For padded token withnoannotations, query->token gradient is w_q softmax_l
S/(2M)>0. Compare actual source autograd to formula and finite differences.
Controls:valid-only baseline;two different padding embeddings;no padding;
query permutation with remappedindices;common token/query reorder wherevalid.
No production loss masking repair or numerical tuning.
## 4. Experiment Plan
| # | ID | Config | Purpose | Expected result | Priority | Depends |
|---|---|---|---|---|---|---|
|1|D1-ordering|CPUhelper|568bank scores/labels|Quantify ranks/margins, no efficacyclaim|P0|assignmentverified|
|2|D1-semantic-formal|CPUhelper|sourceASTloss tests|Bounded invariance/gradient result|P0|sourcehashmatch|
Freeze inputSHA/IDs beforeexecution. Independent localscalar readback, all
counts/quantiles and missingness. Scene bootstrap10kseed1999 for mean
per-description bestusable rank and paired difference overcommoneligible
physicalscenes; conditional populations explicit. No newinference.
## 5. GPU Allocation Plan
| Server | GPU | Assignment | Config | Reason |
|---|---|---|---|---|
|server-4|0|M188 retained|mqb_tr|existingtrainer|
|server-4|1|M187 retained|mqfc_tr|existingtrainer|
|server-6|7|M184/M185 retained|mqst_tr/mqpp_tr|capacity2|
|server-4|none|CPU audit|isolated/tmp|oneCPUthread/CUDAhidden|
M189/M190/M191/M193 FIFO/nullGPU unchanged; helperssyncbothservers.
## 6. Implementation Checklist
- [x] Read source/config/goal andfreeze review beforedesign.
- [ ] Freeze protocol/source/bank hashes.
- [ ] ImplementsourceAST tests andbank audit inisolated helper.
- [ ] Hashsyncbothservers,preservediff;CPU bounded execution.
- [ ] Independent verification,interpretation,decisions/report/memory.
No model/YAML/commit/push/enqueue;Phase3a N/A because no model created.
Execution and verification artifacts track completion.
## 7. Risk Assessment
Score probabilities not calibration orconfidence truth. Historical training
targets/augmentations/forward identity not recovered. Synthetic padding
counterexample not measured occurrence or efficacy; real projections missing.
No primary novelty claim; no bannedauxloss/rescore descendant; no newmodel.
All six scientific areas remain requirements beforefutureadmission:
diagnosis/formalcontrols now; novelty/causalcontrols/generalization/efficiency
NOTcompleted. CPU timing NOTfullmodel benchmark. <=3documentedhelperrepairs.
Smell check:diagnostic arithmetic, no tuning or training graph change.
Status: APPROVED for CPUdiagnostics only.
"""
    (P / "designs/exp_design_20260911-121000.md").write_text(design, encoding="utf-8")
    OUT.mkdir()
    protocol = dict(created=stamp, source_hashes=previous["source_hashes"],
                    models=previous["models"], summary_hashes=previous["summary_hashes"],
                    ids=previous["ids"], manifest_sha256=previous["manifest_sha256"],
                    assignment_sha256=sha(P / "reports/d1_assignment_20260911-1113/assignment.json"),
                    goal_sha256=sha(P / "goal.json"),
                    review_sha256=sha(P / "reviews/motivation_review_20260911-121000.md"),
                    design_sha256=sha(P / "designs/exp_design_20260911-121000.md"))
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
    print(OUT, stamp)


if __name__ == "__main__":
    main()
