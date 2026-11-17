"""Freeze real-projection diagnostic scope before inference."""
from datetime import datetime
import json
from pathlib import Path
from d1_candidate_bank_20260911 import sha, MANIFEST_SHA

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_padding_20260911-1310"


def main():
    assert not OUT.exists()
    goal = json.loads((P / "goal.json").read_text(encoding="utf-8"))
    old = json.loads((P / "reports/d1_ordering_20260911-1210/protocol.json").read_text())
    assert sha(P / "goal.json") == old["goal_sha256"]
    cases = json.loads((P / "reports/d1_identity_20260911-0912/protocol.json").read_text())
    assert len(cases["ids"]) == 21
    now = datetime.now().isoformat()
    review = f"""================================================================================
  Motivation Review - cluster_project
  {now}
================================================================================
## 1. Goal
Full authoritative goal snapshot:
```json
{json.dumps(goal, indent=2, ensure_ascii=False)}
```
Checker13:08:39 Phase1NOTYET;target.5100/champion.5020/baseline.4894/gap+.0080.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Candidate ranking failures | measured |99of111M95 recoverables retain usable positives|Why scores fail|
| Semantic padding invariance | falsified synthetically |sourcecriterion +.286024delta|Real projection exposure|
| Padding harms actual training efficacy | unverified |no realgradients yet|Capture and causal controlled experiment|
## 3. Experiment Assessment
| Experiment | mIoU | Motivation | Contribution |
|---|---|---|---|
|Baseline/M95 historical|.489449/.502461|References|Historicalidentitylimits|
|M183/M186|.491549/.494500|Legacycontrols|Nochampiongain|
|D1fixedsample baseline/M95|.535914/.502217|Diagnosis|Conditionalnotpopulation|
223historicalanalyses hash-reconciled,224totalinclalreadyanalyzedM186.
## 4. Gap Analysis
Existing568banks lack semantic projections, token masks and densemaps.
Need actual final-layer criterion gradients with full annotation maps before
calling padding an actionable training problem. No new mechanism admitted.
## 5. Design Rationale
Q1:How large is paddingmass/lossdifference/projected-gradient share in known
cases? Q2:recapture21existingIDs/model inoriginalgroups;CPU fullsourcecriterion
versus validtoken-prefix restriction withfixed projections. Q3:quantified
evaluation-criterion exposure, not training trajectory or causal performance.
All12constraints/11bans reviewed: no training graph/config/schedule/seed/loss
change,newdataset,annotationAPI,gate/routing/projection/attention variant.
Diagnostic comparison is not newnovelty. Causal matched intervention,primary
novelty,generalization/full-model efficiency remain incomplete.
## 6. Next Batch
exp_design_20260911-131000.md;boundeddiagnosticcaptureonly,noenqueue.
"""
    (P / "reviews/motivation_review_20260911-131000.md").write_text(review, encoding="utf-8")
    design = f"""================================================================================
  Experiment Design - cluster_project
  {now}
================================================================================
## 1. Motivation
{goal['description']}
Upstreamreview131000. Waiting4/capacity4 triggersresearch,goal scientific
admissionprecedesrefill. Diagnose actualcriterion exposure,notnewvariant.
## 2. Current Best Results
| ID | Config | State | Best mIoU | Acc50 | spmIOU | Epochs |
|---|---|---|---|---|---|---|
|baseline|model_base1|historical|.4894491136|.541|.451|best15|
|M95|ctf_hcg_csort|done_earlystop|.5024607182|.557|.465|archivebest16|
|M186|mqht_tr|done_earlystop|.4944996834|.548|.459|27/best17|
## 3. Analysis & Direction
### 3.1 Effective evidence
Candidatebank/assignment/ranking andsourcepaddingcounterexample verified.
### 3.2 Unsupported claims
No actualtrainingcausalharm established; ordinarymaskcorrectnessisnotnovelty.
### 3.3 Missing evidence
Real fullmaps,projections,paddingmass andgradientcontribution.
### 3.4 Derivation and controls
Usefinal-layer S=V T^T/tau, taufromsavedconfig/default. Reconstructassignment
fromcapturedFPS/sampleindices anddatausingactualsourcecriterionmethod.
Capture original full densemaps, tokenIDs, validmask and normalized V/T.
CPU compute actual loss_sem_align L_full and L_valid using same V and only
valid tokenprefix T[:length] withsame densemaps clippedbysource. End-token
positions are unchanged. No forwardrerun forrestriction/noactualmodelpatch.
Verify allannotationmaps havezero support inpadding; otherwise flag and do
notapplypadding-onlyidentity. Matchsource main-map activity b_q, queryweight
w_q and otherentity doubling O. A_q=LSE_all[(1+O)S],C_q=LSE_valid[(1+O)S].
 DeltaL=sum_q w_q*b_q*(A_q-C_q)/(2M).
 padding logitgradient g_qj=w_q*b_q*softmax((1+O)S)_qj/(2M)
 forunannotatedpadding. Fullothermap,modifier/pronoun/relation effects
retainedinoriginalsourcecriterion; identity cancelsunchangedterms.
Use actualsourceautograd withCPUdetachedV/T,plus ASTlogit-input equivalent
andanalyticpaddinggradient/lossdelta check. Chaincheck g_V=g_S*T/tau,
g_T=g_S^T*V/tau. Report projectedgradientonly,notnormalization/wholemodel.
Metrics:length,paddingcount,meanpaddingdenominatormass,weightedmass,
lossdelta,full/cropquerygradientnorm,change/fullnorm,paddedtoken-gradient
norm/fulltoken-gradientnorm; numerator/denominator saved, zeros handled.
Controls:fixed9successcases/12errors,3missing;unpaddedexamples ifpresent;
syntheticbaseline/padding/permutation frompriorstage aspositivecontrols.
Reject applyingformula withnonzeropaddingannotation/nonfinite/missingIDs.
If exposure negligible, deprioritize; no posthoc threshold or efficacyclaim.
## 4. Experiment Plan
| # | ID | Config | Purpose | Expected result | Priority | Depends |
|---|---|---|---|---|---|---|
|1|D1-realpaddingcapture|existingbaseline/M95|21IDs/model/originalgroups|Realprojectionsandmaps|P0|identityprotocol|
|2|D1-realpaddinggradient|isolatedCPU|fullsourcecriterionversusvalidprefix|Exposureestimate,notgain|P0|captureverified|
Same21IDs fromidentityprotocol,11scenes. Outcomeselected12errors9controls,
notrandom/causalmatchedsample;3missingcontrolsretained. Noreservedinference.
Record all originalgroupcontextIDs butscoreonly21. CompareFPS/sample,masks,
indis,IoUs againstexistingbanks; mismatchreportedandrejectlinkedclaims.
No historicaltrainingreplay. No multi-seed, dataset orbenchmark expansion.
## 5. GPU Allocation Plan
| Server | GPU | Assignment | Config | Reason |
|---|---|---|---|---|
|server-4|0|M188retained|mqb_tr|existingtrainer|
|server-4|1|M187retained+boundeddiagnostic|baseline thenM95|free9557MiB13:08|
|server-6|7|M184/M185retained|mqst_tr/mqpp_tr|capacity2|
Start>=8GiBfree,allocatorcap4GiB,between-groups>=5GiBfree,300s/model
forwardbudget,hardtimeout600s/model. Stop/markmissingonresourceguard;do not
touchtrainer. GradientcalculationCPUafterGPUinference,oneCPUthread.
## 6. Implementation Checklist
- [x] Goal/source/referencesread;reviewbeforedesign;casespreexisting.
- [ ] Freezeprotocol andsource/data/checkpoint/config hashes.
- [ ] Isolatedcapture andCPUanalysis helpers;hashsyncbothservers.
- [ ] Strictcheckpointload withonlyverifiedlegacybufferexception.
- [ ] Originalgroupinference,exactID/assignment/bankreadback.
- [ ] Fullsourcecriterion/analyticidentity/gradientverification.
- [ ] Reportlimits/decisions/finalstate/memory.
Modelconfig/commit/push/enqueue/Phase3a N/A,no modelvariantcreated.
## 7. Risk Assessment
SharedGPU boundedmemory/time,maystoppartial;neverfilltraining slot orreset
deployment. Evalprojectioncriterionnotactualtrainaugmentation/dropout/loss
batchnormalizer;perdescriptionM changesmagnitudeonly. Noautogradthroughmodel.
Primarynovelty/causalcontrols/generalization/bs1warmup20repeat100efficiency
NOTdone. Maskcorrectionaloneisnotcorecontribution. No bannedauxlossdescendant.
Retainfailurelogs,<=3documentedhelperrepairs,noautomatictrainingrerun.
Status:APPROVED forboundeddiagnostics only;executionartifacts trackcompletion.
"""
    (P / "designs/exp_design_20260911-131000.md").write_text(design, encoding="utf-8")
    OUT.mkdir()
    protocol = dict(created=now, ids=cases["ids"], pairs=cases["pairs"],
                    identity_protocol_sha256=sha(P / "reports/d1_identity_20260911-0912/protocol.json"),
                    manifest_sha256=MANIFEST_SHA, source_hashes=old["source_hashes"],
                    summary_hashes=old["summary_hashes"], models=old["models"],
                    assignment_sha256=sha(P / "reports/d1_assignment_20260911-1113/assignment.json"),
                    goal_sha256=sha(P / "goal.json"),
                    design_sha256=sha(P / "designs/exp_design_20260911-131000.md"))
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2))
    print(OUT, now)


if __name__ == "__main__":
    main()
