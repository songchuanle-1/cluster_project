# D1 Frozen Diagnostic Expansion
Completed evidence reviewed 2026-09-11 07:36:51 Asia/Shanghai.

## Scope And Provenance
Upstream motivation_review/exp_design_20260911-071200; decision071110.
sample_manifest_v2 SHA84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468.
Expected284 descriptions,71physicalscenes,4each;70reserved scenes never inferred.
Audited fixed baseline/M95 checkpoints, explicitmodule/config/package/source hashes;
two legacy textbuffers omitted only in memory after exactruntime equality.
Original languagegroups, seed1999, no training/config/modelpackage changes.
Historical forwardidentity still not proven; not a fullvalidation replay.

## Denominators And Missingness
| Model | Descriptions | Physical scenes | Complete scenes | Missing IDs | Groups | Context descriptions |
|---|---|---|---|---|---|---|
| baseline | 284 | 71 | 71 | 0 | 141 | 4078 |
| m95 | 284 | 71 | 71 | 0 | 141 | 4078 |

Groupcontext descriptions outside284IDs are nuisance inputs, not extra observations.
MissingIDs/skippedgroups are explicitly stored in summary.json and verification.json.
Matched denominator: 284 descriptions;
71 complete physicalscenes.
Eight previously measured IDs included once; expansion adds up to276newIDs/69scenes.

## Error Measurements
| Metric | Baseline | M95 |
|---|---|---|
| selected_iou | 0.535914148 | 0.502216606 |
| oracle_iou | 0.834245822 | 0.848107879 |
| bank_limitation | 0.165754178 | 0.151892121 |
| selection_gap | 0.298331675 | 0.345891273 |
| acc50 | 0.602112676 | 0.556338028 |
| recoverable_failure50 | 0.316901408 | 0.390845070 |
| bank_failure50 | 0.080985915 | 0.052816901 |

| Model | Acc50 count | Selection failure with oracle>.5 | Bank oracle<=.5 |
|---|---|---|---|
| baseline | 171 | 90 | 23 |
| m95 | 158 | 111 | 15 |
Each row count uses its model's measured denominator above.
Acc50 uses IoU>.5 per tools/train.py; recoverable a<=.5<o; bankfailure o<=.5.
These latter two groups partition threshold failures, not causal failure labels.
The samebank identity1-a=(1-o)+(o-a) holds. It doesnot distinguish absent targets
from inaccurate boundaries or explain selection errors as language/relation faults.
Oracle is an upper-bound diagnostic, never a deployable prediction.

## Scene Uncertainty
| M95 minus baseline | Mean | 95% low | 95% high |
|---|---|---|---|
| selected_iou | -0.033697542 | -0.071752253 | 0.004763571 |
| oracle_iou | 0.013862056 | -0.001133296 | 0.030119812 |
| bank_limitation | -0.013862056 | -0.030119812 | 0.001133296 |
| selection_gap | 0.047559598 | 0.008933127 | 0.085786392 |
| acc50 | -0.045774648 | -0.098591549 | 0.003521127 |
| recoverable_failure50 | 0.073943662 | 0.021126761 | 0.126760563 |
| bank_failure50 | -0.028169014 | -0.056338028 | -0.003521127 |

10000 paired physical-scene bootstrap replicates, seed1999, percentile95.
Complete scenes only, no imputation; scene is resampling unit, not description.
These intervals describe conditional exploratory sample uncertainty, not untouched-
test significance or dataset-wide prevalence. No modeltraining multiseed sweep.
Equal-scene sampling is not description-population weighting; validation was mined
historically and the reserved split is prospective, not independent fresh testdata.

## Correctness And Resources
568 savedbanks verified onCPU; allcandidateIoUs within1e-7,
same selectedindices, probabilities at establishedatol1e-7/rtol1e-6, exactselectedbinarymasks.
Crossmodel GT, GTsuperpoint masks and superpointmaps equal on matchedIDs;
scene point/CLIP/source/graph hashes equal. CUDA uninitialized duringreadback.
Actualget_iou AST equal across baseline/M95, verifiedlocally.
Seven existingIoUtests pass; four scene-statistics tests pass;28pipeline tests pass.
| Model | Peak allocated MiB | Peak reserved MiB | Inference seconds | Worker exit |
|---|---|---|---|---|
| baseline | 3850.943 | 4046.000 | 175.272 | 0 |
| m95 | 3346.865 | 4064.000 | 458.441 | 0 |
8GiB launch/5GiB batchfree guards,4GiB allocatorcap,600s inferencebudget.
SharedGPU runtime is not a matched efficiencybenchmark or trainingpeak.
Onecandidateatime O(N)temporary, QxS savedbank; no QxNbank allocation.
Workers completed before final snapshot; helperSHA evidence in execution.json.
CPUverifier retry1 restored omitted pilotrelative tolerance after independentdrift
audit: maxabsolute1.1920928955078125e-7,0binarychanges/all568banks.
Originalfailedlog preserved; see bugfix_20260911-073200.md/recovery_verify.json.
No GPUrerun or changes to IoUthreshold/candidateIoUtolerance.

## Pilot Continuity
```json
{
  "baseline": {
    "n": 8,
    "selected_index_changes": 0,
    "max_selected_iou_delta": 0.0,
    "max_oracle_iou_delta": 0.0
  },
  "m95": {
    "n": 8,
    "selected_index_changes": 0,
    "max_selected_iou_delta": 0.0,
    "max_oracle_iou_delta": 0.0
  }
}
```
Only same8IDs compared with previousoriginalgroups; not universalfloatdeterminism.

## Interpretation And Next Work
Measured candidate-bank and selection errors now have a broader frozen denominator.
M95 selectedmean.502217 is belowbaseline.535914 in thissample, whileoracle.848108
exceedsbaseline.834246. Pairedselecteddelta-.033698 has95%CI[-.071752,.004764],
which includeszero. M95selectiongap exceedsbaseline by.047560,
CI[.008933,.085786]; these are exploratory comparisons, not a fullvalregression
claim or untouchedtest confirmation. Thresholdrecoverableerrors111/284vs90/284;
bankfailures15/284vs23/284. Prioritize inspecting why goodcandidates lose,
without assuming that rankingalone, relationbinding or sharedanchors is thecause.
Do not select a mechanism solely from an oraclegap or a positive aggregate delta.
Next D1 task: freeze operational boundary/target-identity/ambiguity/relation labeling
rules; audit fixed errorcases and matched successful negatives from these banks.
Use existing scene assets, report missing labels/disagreements, no externalannotation
API/newdatasets. Then choose at mostone evidenced hypothesis and complete N1
formula derivation, degeneracies/gradient/complexity, primary-paper comparison and
matched falsification controls. No newmechanism trainingadmitted in this tick.
