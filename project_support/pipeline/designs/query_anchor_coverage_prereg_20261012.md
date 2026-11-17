# Native Physical Query-Anchor Coverage Diagnosis

## Frozen Hypothesis
Native scene-level query initialization may omit physical target support even
when the target survives the native point/superpoint representation. Such
omission would be an exposure deficit, distinct from ranking an already
available target candidate or restoring within-superpoint feature detail.

## Population And Readout
Use the existing prediction-blind 32-scene/128-expression TRAIN manifest,
M95 checkpoint and seed1999. Do not add data, seeds, labels or query counts.
Trace the original native initialization and indication-positive definition
before computing coverage. Report target support surviving preprocessing,
physical anchor membership, native positive-query counts and target size.
Keep absent inputs/targets separate from observed zero coverage.

## Matched Control
Keep each native batch, target, query count and loss definition fixed.
Compare physical seed membership with the native positive-query definition.
Use a non-target instance identity permutation as an association negative
control, not as an efficacy intervention. If the hypothesized missing exposure
is absent, reject this specific absent-anchor diagnosis rather than all query
mechanisms. If physical anchors and positives disagree, investigate original
source semantics before designing an operator.

## Next Test And Limits
First inspect native source and existing hash-addressed captures; then run the
lowest-cost authorized remote diagnostic required for the frozen population.
Existing tensors may answer a newly preregistered readout without another
native forward; label them with their original capture protocol and timestamp.
No coverage-threshold tuning, FPS-count change, routing successor, model edit,
efficacy claim, admission or launch is authorized by this diagnosis alone.
