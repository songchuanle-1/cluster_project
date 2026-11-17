"""Freeze a source-gradient audit before computing any new aggregate results."""
from datetime import datetime
import json
from pathlib import Path
from d1_candidate_bank_20260911 import sha
from close_tick_20260911_0707 import EXPECTED

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_margin_20260911-1410"


def main():
    assert not OUT.exists()
    assert {n: sha(P / n) for n in EXPECTED} == EXPECTED
    inventory = json.loads((P / "reports/research_inventory_20260910-1324.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT / r["path"]) == r["sha256"] for r in inventory["analyses"])
    goal = json.loads((P / "goal.json").read_text(encoding="utf-8"))
    old = json.loads((P / "reports/d1_ordering_20260911-1210/protocol.json").read_text())
    now = datetime.now().isoformat()
    review = f"""================================================================================
  Motivation Review - cluster_project
  {now}
================================================================================
## 1. Goal
Complete authoritative goal:
```json
{json.dumps(goal, indent=2, ensure_ascii=False)}
```
Checker14:08:47 Phase1NOTYET;baseline.4894/champion.5020/target.5100.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
|Missing useful positive dominates recoverables|not supported|M95 only12/111,99have useful positives|Score-level behavior|
|Padding exposure explains ranking|not supported by selected evaluation|mean relativequery gradientchange.000154M95|Training causal effect unknown|
|Existing CE fails to point toward good rankings|untested precise claim|Source gradients archived|Independent-logit versus parameter updates|
## 3. Experiment Assessment
| Experiment | mIoU | Motivation relation | Contribution |
|---|---|---|---|
|Baseline/M95 archive|.489449/.502461|References|Historical identity limitations|
|M183/M186|.491549/.494500|Legacy structural controls|No champion gain|
|D1baseline/M95|.535914/.502217 on284|Error diagnosis|Not whole-validation estimates|
223historical analysis hashes reconciled;224current includingM186. No new
terminal since13:07, no duplicate terminal analysis. Full ledger unchanged.
## 4. Gap Analysis
Q1:Do independent score gradients oppose bad rankings, and when are eligible
high-IoU candidates penalized as negatives? This is not shared-parameter causality.
New mechanism/primary novelty/intervention/generalization/efficiency incomplete.
## 5. Design Rationale
Q2:Use568existing scores/IoUs/assignments/source gradients. Define margins and
direction derivatives; verify formula against stored source autograd and finite
differences. Q3:reject or qualify objective-level explanations before new losses.
All12constraints/11bans reviewed: no model, schedule, seed, weight, projection,
gate/routing/pooling changes; no new data, reserved inference or annotation API.
## 6. Next Batch
exp_design_20260911-141000.md;CPU-only diagnostic, no model admission/enqueue.
"""
    (P / "reviews/motivation_review_20260911-141000.md").write_text(review, encoding="utf-8")
    design = f"""================================================================================
  Experiment Design - cluster_project
  {now}
================================================================================
## 1. Motivation
{goal['description']}
Upstreamreview141000. Waiting4/capacity4 triggersresearch; scientific admission
precedesrefill. Audit existing scoring objective, not a novel loss proposal.
## 2. Current Best Results
| ID | Config | State | Best mIoU | Acc50 | spmIOU | Epochs |
|---|---|---|---|---|---|---|
|baseline|model_base1|historical|.4894491136|.541|.451|best15|
|M95|ctf_hcg_csort|done_earlystop|.5024607182|.557|.465|archivebest16|
|M186|mqht_tr|done_earlystop|.4944996834|.548|.459|27/best17|
## 3. Analysis & Direction
### 3.1 Confirmed
Most recoverable samples contain an eligible positive. Padding exposure small
on selected21IDs/model, not whole training. Current source matching known.
### 3.2 Rejected extrapolation
No causal explanation from aggregate mIoU or missing-supervision minority.
### 3.3 Derivation
For each ofQ=128 candidates, z_q=(z0,z1), d_q=z1-z0,p_q=sigmoid(d_q),
y_q from archived source assignment, w_q=1 ifpositive else eos=.1,M=sum y.
Source CE L=sum w[-y logp-(1-y)log(1-p)+log(1+1e-6)]/M.
Constant entropy term retained for scalar check, irrelevant to gradients.
g_q=dL/dz1=w(p-y)/M;dL/dz0=-g_q.
Independent two-logit gradient flow gives dot(d_q)=-2g_q.
For selecteds andfixed eligibleh, margin m=d_s-d_h>=0,
dot(m)=-2(g_s-g_h). Save m,g_s,g_h,velocity,2M(g_s-g_h),individual
probabilities/labels. No finite learning rate sweep or deployable score update.
For snegative/hpositive, dot(m)<0 for finite nonsaturated probabilities.
For bothpositive, dot(m)=-2(p_s-p_h)/M<=0. At ties it is0.
For spositive/hnegative, dot(m)>0, so an eligible negative can be penalized.
Bothnegative:dot(m)=-2eos(p_s-p_h)/M<=0. Boundary saturation may yield0.
These are exact at fixed logitcoordinates, not actual parameter dynamics:
z=z(theta),J=dz/dtheta, dot(z)=-JJ^T grad_z L for plain gradient flow
on this loss alone. Other losses/Adam/dropout/augmentations change dynamics.
No assertion that dot(m) computed withidentityJJ^T matches training.
If h=s, velocity0 bydefinition. Emptyeligible sets missing,notzero.
Changing globalbatchM orfinalpositiveweight rescales butdoesnot reversesign.
Qx2inputs/O(Q)perbank, no modelforward or NxN attention.
### 3.4 Controls and decision
Audit G=IoU>.5 andH=G intersecty=1, each highestd member; ties firstindex.
Report all284/model andsuccess/recoverable/bankfailure,selectedpositive/negative.
For Hnonempty anderror withsnegative, compare analyticdirection tosourcegrad.
Do notcall a usefulnegative a labelingbug: assignmenttargets seedidentity,
notmaskIoU. Do notinfer CE absence/causalharm if corrective direction exists.
## 4. Experiment Plan
| # | ID | Config | Purpose | Expected result | Priority | Depends |
|---|---|---|---|---|---|---|
|1|D1-margin-source|existing JSONbanks|Audit568 margins/gradientdirections|Quantify and test objective explanations|P0|assignment/ordering|
|2|D1-margin-controls|CPUsynthetic|4labelpairs/ties/permutation/FD|Analytic agreement|P0|sourceformula|
Use entirefrozen284IDs/71scenes/model,no newselection. Allsuccesses controls.
Pair baseline/M95 oncommonHnonempty IDs for margin difference; equal
description withineligible scene/equal scene weights;10000scenebootstrap1999,
95%percentile intervals,report all denominators. Alsoall284pairedscene rates
for recoverable+H+selectednegative andHabsence; exploratoryconditional only.
Reject malformed SHA/IDs/nonfinite/gradient disagreement;report missing.
## 5. GPU Allocation Plan
| Server | GPU | Assignment | Reason |
|---|---|---|---|
|server-4|0|M188retained|Existingtrainer|
|server-4|1|M187retained|Existingtrainer|
|server-6|7|M184/M185retained|Capacity2|
DiagnosticslocalCPU JSON/NumPy only. No GPUworker. Bothserver isolatedsync.
## 6. Implementation Checklist
- [x] Read authoritativegoal/references/source/evidence;reviewbeforedesign.
- [ ] Freeze source/inputhashes and all284IDs.
- [ ] Implement finite-differencecontrols and568sourcegradient readbacks.
- [ ] Stratifiedsummaries/pairedsceneuncertainty/independentverification.
- [ ] Sync helper/protocol/docs/results bothservers withouttrainingdiffchanges.
- [ ] Final report/decisions/memory/stateintegrity.
Modelpackage/config/commit/push/enqueue/Phase3a N/A: no new model variant.
## 7. Risk Assessment
No tuning/newforward/newloss;smellcheckN/A for observationaldiagnostics.
Sourceidentity/assignment iscurrentevaluation nothistoricaltraining.
Repeatedlyminedvalidation andconditionaleligibility bias remain;no test claim.
Syntheticindependentlogitgradient isnot optimizerprediction orcausalintervention.
Primarynovelty, matchedmechanismcontrols, generalization/fullmodelresource
admission remainincomplete; no scientifically admitted new mechanism.
No productioncode changes. <=3 documentedhelperrepairs; preservefailurelogs.
Status:APPROVED forCPUdiagnostics only; completiontracked byexecutionartifacts.
"""
    (P / "designs/exp_design_20260911-141000.md").write_text(design, encoding="utf-8")
    OUT.mkdir()
    inputs = {name: sha(P / path) for name, path in {
        "assignment": "reports/d1_assignment_20260911-1113/assignment.json",
        "ordering": "reports/d1_ordering_20260911-1210/ordering.json",
        "assignment_verification": "reports/d1_assignment_20260911-1113/verification.json",
        "ordering_verification": "reports/d1_ordering_20260911-1210/verification.json",
    }.items()}
    protocol = dict(created=datetime.now().isoformat(), ids=old["ids"],
                    input_hashes=inputs, models=old["models"], source_hashes=old["source_hashes"],
                    summary_hashes=old["summary_hashes"], goal_sha256=sha(P / "goal.json"),
                    design_sha256=sha(P / "designs/exp_design_20260911-141000.md"),
                    historical_analyses_verified=len(inventory["analyses"]),
                    current_analyses=len(list((P / "analyses").glob("*.md"))),
                    finite_difference_eps=1e-5, finite_difference_atol=1e-8,
                    source_gradient_atol=1e-7, source_gradient_rtol=1e-5,
                    bootstrap_seed=1999, bootstrap_resamples=10000)
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2))
    print(OUT, protocol["created"])


if __name__ == "__main__":
    main()
