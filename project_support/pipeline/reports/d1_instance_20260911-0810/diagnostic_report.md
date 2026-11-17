# D1 Instance-Overlap Audit

## Protocol And Denominators
All284 fixed descriptions on71physicalscenes, two models,568bank records.
Original banks/pointfiles/source/graphs verified bySHA, rawpoint instanceGT exact,
np.unique superpoint reindexing exact to eachsavedbank. No missing joins.
Only selected and oracle masks expanded onCPU; no newinference, GPU use,
reservedscene analysis, externalannotation or training. Protocol.json contains
prespecified labelrules and12error9control case selection, threecontrols missing.
8synthetic attributiontests pass locally andremote; all568localarithmetic checks pass.

## Measured Labels
| Selected label | Baseline /284 | M95 /284 |
|---|---|---|
| no_instance_pass50 | 23 | 27 |
| target_pass50 | 171 | 158 |
| wrong_instance_different_semantic | 2 | 2 |
| wrong_instance_same_semantic | 71 | 69 |
| wrong_instance_semantic_unknown | 17 | 28 |

| Selected label among recoverable | Baseline /90 | M95 /111 |
|---|---|---|
| no_instance_pass50 | 12 | 21 |
| wrong_instance_different_semantic | 2 | 2 |
| wrong_instance_same_semantic | 63 | 63 |
| wrong_instance_semantic_unknown | 13 | 25 |

Labels partition selectedoutputs, not causes. Same_semantic means homogeneous
nonnegative coarse semantic ID equality, not identical fine category.
Targetsemantic unavailable for71/284 inbothmodels; retain unknown.
Same-semantic wronginstance counts include coarse semantic ID19 (NYU40 ID39):
baseline6,M956.
No-instance-pass masks whose best-overlap instance is stilltarget:
baseline6,M958.
Do not call all these masks wrongobject, absentproposal or boundaryfailure.

## Formula And Identification Limits
TP=|P intersect G|,FP=|P minus G|,FN=|G minus P|.
IoU=TP/(TP+FP+FN+1e-6), precision=TP/(TP+FP) (empty=>null),
recall=TP/(TP+FN). Both FP/|G| and FN/|G| are stored.
These derive overlap accounting only, not a newmodel contribution.
Best labelledinstance uses pointIoU; >.5 determines overlapmatch; emptyseparate.
Unknown semantic labels and unlabelledpredictedpoints are explicit, not majority-imputed.
All568relationcause and boundarycause fields unknown. Textgraph edges are parser
outputs, not objectgroundings or geometric truth; no annotatoragreement claim.

## Scene Uncertainty
| Paired label prevalence delta M95-baseline | Mean | 95% low | 95% high |
|---|---|---|---|
| no_instance_pass50 | 0.014085 | -0.024648 | 0.052817 |
| target_pass50 | -0.045775 | -0.098592 | 0.003521 |
| wrong_instance_different_semantic | 0.000000 | -0.010563 | 0.010563 |
| wrong_instance_same_semantic | -0.007042 | -0.045775 | 0.031690 |
| wrong_instance_semantic_unknown | 0.038732 | 0.007042 | 0.073944 |

10000 pairedphysicalscene bootstrap draws,seed1999,percentile95.
Exploratory conditional intervals, no multiplicity-adjusted test or untouchedtest
claim. Equal-scene sample, historicallyminedvalidation, not datasetprevalence.

## Fixed Case Interpretation
See casebook.md for12hash-selectederrors/9same-scene successcontrols.
scene0046_00 target26 ann27 fails, target26 ann34 succeeds withinbothmodels;
same target/scene but differenttext, not a controlled paraphrase experiment.
scene0146_00 target16 ann8 has target asbestinstance butIoU<=.5,
so its label is no_instance_pass50, not demonstrated different-object selection.
Other examples contain relations, but co-occurrence doesnot establish causality.
Cases selected by M95 outcome, no bias-free causal effect inference.

## Conclusion And Next Work
Wrong-instance overlap is observed in many recoverableerrors. However bothmodels
have63recoverable same-semantic substitutions: M95's extra21recoverableerrors
are not an increase in that count (unknownsemantic+12,no-instance-pass+9).
Do not claim more same-class confusion from thiscomparison.
Next: audit exactobjectidentities and geometric/text evidence on frozen cases,
especially unknownsemantic and coarse ID19, with explicit labeling rules
and missingness. Boundary/relationshipmechanisms remain unproven.
N1 primarypaper comparison, singlecoremechanism derivation/gradients/degeneracies/
complexity and matchedfalsificationcontrols are prerequisites, not completedwork.
No newtrainingadmission, selectorfamily/refill, or championledgerchange.

## Resources And Provenance
Workerelapsed23.694s,peakRSS743.918MiB,
CUDAinitialized=false,threads1; CPUonly, not a fullmodel efficiencybenchmark.
WorkerSHA83716e33359ef04b040a718b2e3ca0ae59d89ba3919e2f10c4d7698973470237; auditSHAb4ae7b49570af648a336153776bdccbd5ecaf10b20a3281038000f2e3c05df69.
Hashsynced standalonehelpers tobothservers; no trainingpackage/deploymentmutation.
Sourcecode get_ref_mask/transform_test supplies local implementation semantics.
No novelty or external-paper facts asserted by this diagnostic.
