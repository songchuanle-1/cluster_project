"""Freeze diagnostic label rules and fixed case/control selection before attribution."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_instance_20260911-0810"
assert not OUT.exists()
OUT.mkdir()
goal = json.loads((P / "goal.json").read_text(encoding="utf-8"))
old = P / "reports/d1_expansion_20260911-0715"
summaries = {n: json.loads((old / n / "summary.json").read_text(encoding="utf-8")) for n in ("baseline", "m95")}
key = lambda r: (r["scene_id"], str(r["object_id"]), str(r["ann_id"]))
hashkey = lambda r: hashlib.sha256(("d1-instance-v1|" + "|".join(key(r))).encode()).hexdigest()
rs = summaries["m95"]["rows"]
errors = sorted([r for r in rs if r["selected_iou"] <= .5 < r["oracle_iou"]], key=hashkey)[:12]
used, pairs = set(), []
for error in errors:
    candidates = [r for r in rs if r["scene_id"] == error["scene_id"] and r["selected_iou"] > .5 and key(r) not in used]
    control = min(candidates, key=hashkey) if candidates else None
    if control:
        used.add(key(control))
    pairs.append(dict(error=list(key(error)), control=list(key(control)) if control else None,
                      missing_reason=None if control else "no_unused_same_scene_success_in_frozen_sample"))
protocol = dict(created=datetime.now().isoformat(), version="d1-instance-v1", pairs=pairs,
                expected_ids=sorted([list(key(r)) for r in rs]), label_threshold=.5,
                selection_rule="First12 SHA256(d1-instance-v1|scene|object|ann) ordered M95 recoverable errors. Greedy same-scene successful frozen-ID controls, same hash order, no reuse; absent control stays missing. Cases descriptive, not representative subset.",
                rule="Selected mask IoU>.5 targetpass; else best-labelled-instance IoU>.5 wronginstance, subdivided by homogeneous valid semantic ID equality; else no_instance_pass50; empty separate. Never interpret maskoverlap as cause.",
                formulas="TP=|P intersect G|;FP=|P minus G|;FN=|G minus P|;precision=TP/(TP+FP), null when empty;recall=TP/(TP+FN);IoU=TP/(TP+FP+FN+1e-6). FP/|G| and FN/|G| report contamination/omission, not boundary cause.",
                boundaries="No_instance_pass50 is not proof of missing target candidate. Same-semantic wronginstance is overlap evidence, not language ambiguity cause. Parser relations ungrounded; all relation-failure/boundary-cause labels unknown unless separate adjudication is recorded.")
(OUT / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
review = f"""# Motivation Review - cluster_project
2026-09-11 08:10 Asia/Shanghai.
## 1. Goal
```json
{json.dumps(goal,ensure_ascii=False,indent=2)}
```
Checker08:08:17 Phase1 NOT YET; ledgerM95.5020 target.5100 gap+.0080.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Context platform improves baseline | Historical | M95.5020 vs.4894 | Historical forward identity |
| Good candidate sometimes not selected | Measured | Baseline90/M95111 of284 recoverable | Which instance/error type |
| M95 relation/anchor failure | Unknown | No grounded labels | Identity/geometry/adjudication |
## 3. Experiment Assessment
| Experiment | mIoU | Relation | Contribution |
|---|---|---|---|
| Baseline/M95 historical | .489449/.502461 | Reference | Audited checkpoints |
| M183/M186 | .491549/.494500 | Legacy controls | Closed variants |
| D1 diagnostic baseline/M95 | .535914/.502217 | Sample diagnosis |71scenes568banks verified |
| M184/M185/M187/M188 | Unfinished | Legacy training | Preserve |
223historical analyses reconciled through immutable inventory; no newterminal.
## 4. Gap Analysis
Oracle gap cannot identify target substitution versus mixed/partial masks.
Need raw instance-label join, FP/FN, semantic-category checks and fixed cases.
Scenegraphs give parser evidence only, not grounded object IDs or relationcause.
## 5. Design Rationale
Q1 which observed masks overlap wronginstances? Q2 CPUjoin all568banks with
existing pointlabels, freeze exact rules/case-controls. Q3 bounded descriptive
attribution, with causal/geometry labels explicitlyunknown.
Sixareas:diagnosis now; derivation/novelty N1 pending; controls here descriptive
not causal; robustness V1 pending; CPUaudit not fullmodel efficiencybenchmark.
All12constraints/11bans checked; no newmechanism, tuning, dataset, annotations,
multiseedtraining, schedulechange or resourcewaiver. Sciencegate overridesrefill.
## 6. Next Batch
exp_design_20260911-081000.md; CPU-only D1-INSTANCE.
"""
(P / "reviews/motivation_review_20260911-081000.md").write_text(review, encoding="utf-8")
design = f"""# Experiment Design - cluster_project
2026-09-11 08:10 Asia/Shanghai.
## 1. Motivation
Verbatim goal.description: {goal['description']}
Waiting4/capacity4 triggersreview; sciencegate prevents mechanismrefill.
## 2. Current Best Results
| ID | Config | State | mIoU | Acc50 | spmIOU | Epochs |
|---|---|---|---|---|---|---|
| Baseline | Audited model_base2.yaml/model_base1 | historical | .489449 | .541 | .451 | best15 |
| M95 | csort | historical | .502461 | .557 | .465 | best16 |
| M186 | mqht_tr | done_earlystop | .494500 | .548 | .459 |27 |
## 3. Analysis & Direction
### 3.1 Effective
Existing bankoracle supports descriptive erroranalysis, not mechanism admission.
### 3.2 Failed
Explicitrouting and allbanned families remainclosed. No numericalrescue.
### 3.3 Unverified
Relations, boundary causes, novelty, derivation and robustness remainpending.
### 3.4 Diagnostic Rules
{protocol['rule']}
{protocol['formulas']}
{protocol['boundaries']}
All284IDs permodel; pointfile hashes, reindexed superpoints and targetGT exactjoin.
Use semanticlabels only when homogeneous/nonnegative; otherwiseunknown.
{protocol['selection_rule']}
Protocol.json frozen before attribution. Original source description and parsed
utterance both retained; parser disagreement not silentlyresolved.
No new objective/gradient/forward: formulas are diagnostic arithmetic, notinnovation.
## 4. Experiment Plan
| # | ID | Config/Inputs | Purpose | Expected Result | Priority | Depends On |
|---|---|---|---|---|---|---|
|1|D1-INSTANCE|568immutablebanks+71pointfiles|instance/FP/FN audit|explicit denominators|P0|D1expansion|
|2|D1-CASES|protocol.json|12fixederrors and same-scenecontrols|casebook, missing controls|P0|instanceaudit|
## 5. GPU Allocation Plan
| Server | GPU | Assignment | Config | Justification |
|---|---|---|---|---|
|server-4|0/1|preserve M188/M187|existing|no GPU diagnostic |
|server-6|7|preserve M184/M185|existing|capacity2 occupied |
CPUonly server-4 existingconda, CUDAhidden,threads1,600s timeguard/720s timeout.
Sequentialscenes/banks; no model import, no pointdatasetdownload or inference.
## 6. Implementation Checklist
- [x] Fullgoalreview before design; protocol/caseIDs frozen.
- [ ] Isolated CPUworker and synthetic attributiontests.
- [ ] Hashsync worker tobothservers withoutdeploymentchanges.
- [ ] CPUaudit/JSONdownload/hashverification and fixedcasebook.
- [ ] Final livecheck/report/memory refresh.
Newtrainingpackage/config/commit/push/enqueue N/A. No newmodel admitted.
## 7. Risk Assessment
Reject any mismatchedinputsha/GT/mapping; explicit missing/ambiguoussemanticlabels.
No label inference from nouns alone; semanticIDs coarse, not exactobjecttaxonomy.
Wronginstance overlap is not causal languagefault. No_instance_pass50 is not
targetabsence/boundaryfailure proof. Missing groundings remainunknown.
No newmodel smellcandidate; all12constraints/11bans retained; <=3documented
helperrepairs, no trainingrerun. Existing FIFO untouched.
Status: APPROVED for CPUdiagnostics.
"""
(P / "designs/exp_design_20260911-081000.md").write_text(design, encoding="utf-8")
print("Protocol frozen", OUT, "pairs", len(pairs), "controls", len(used))
