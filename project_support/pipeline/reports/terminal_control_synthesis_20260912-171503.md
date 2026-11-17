# Legacy Terminal-Readout Evidence Synthesis

Date: 2026-09-12T17:15:03, Asia/Shanghai.
Question: do the completed, preserved legacy controls justify another
terminal-readout successor or establish the effect of removing recurrence?

## Fixed Scope And Integrity

This review includes all five terminal runs M184-M188, chosen by the existing
legacy batch, not their scores. M189/M190 are censored live runs; M191/M193
are waiting and excluded. Four full archived logs match their recorded SHA256.
M188 has a rounded result and analysis but no archived log in its registry;
its exact precision and hash verification remain missing. No value is invented.
All 228 analysis files were read and hashed; all 226 ledger
rows were loaded. Corpus inventory is in the accompanying JSON.

## Results

| Experiment | Best mIoU | Delta baseline | Delta M95 | Parent evidence | FLOPs G |
|------------|-----------|----------------|-----------|-----------------|---------|
| M184-CTF-HCG-CSORT-MQST-TR | 0.4876259565 | -0.001823 | -0.014835 | M179 not trained | 9.845648 |
| M185-CTF-HCG-CSORT-MQPP-TR | 0.4884226322 | -0.001026 | -0.014038 | M180 not trained | 9.845845 |
| M186-CTF-HCG-CSORT-MQHT-TR | 0.4944996834 | +0.005051 | -0.007961 | M181 not trained | 9.843485 |
| M187-CTF-HCG-CSORT-MQFC-TR | 0.4902902544 | +0.000841 | -0.012170 | M182 not trained | 9.843485 |
| M188-CTF-HCG-CSORT-MQB-TR | 0.4916000000 (rounded) | +0.002151 | -0.010861 | M169 trained | 9.832737 |

Denominator: 5/5 completed terminal controls fall below M95.
Two are below baseline; three are above baseline, of which M187 gains less
than 0.002. The strongest, M186, remains 0.0079610348
below M95. These different mechanisms are not independent seed replications;
no pooled standard error or significance statement is justified.

## Causal Boundary

M179-M182 were resource-withdrawn before training. Their replacements
M184-M187 satisfy the resource bound but have no trained parent score.
Thus four of five controls cannot isolate an intermediate-feedback effect
from a matched parent comparison. M188 has a trained M169 parent (ledger
0.5000), with a descriptive rounded delta of -0.0084; no paired scene
predictions or multi-seed uncertainty is available here. This does not prove
that all recurrence or hierarchy mechanisms fail.

The full resource audit established eligibility, not usefulness. Existing
fixed-checkpoint diagnostics identify selection errors, but they do not
connect these aggregate terminal-control failures to a specific causal
selection dependency.

## Admission Outcome And Next Evidence

Admit no successor. Keep the two live runs and original waiting FIFO.
No exact new forward/loss distinct from closed candidate matching, ranking,
mask-scoring, and relation routes has been derived. Do not confuse the
absence of such a derivation with proof that no new mechanism exists.

Before a new mechanism: name a remaining measured error, derive its graph
and counterexamples, then verify primary-source distinctions. Preserve an
independent confirmation subset; the existing repeatedly mined diagnostic
banks and this validation-based review are exploratory only.

This is a CPU-only evidence/causal-control audit. No new inference, training,
config, package, checkpoint, dataset, GPU reservation, or deployment mutation.
