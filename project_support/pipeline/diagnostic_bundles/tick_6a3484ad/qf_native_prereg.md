# Frozen Native Query / Point Factorial Attribution

Continuation of fle-native-nonself-target-mixing-audit, not a new model or
training admission. Preserve the unique terminal best epoch13, the SAME
32 TRAIN scene / 128 expression cohort and input seed1999, same prefix,
source/config/data hashes and tested neighbor_content diagnostic revision2.
The prior terminal diagnostic and its uncertainty remain negative/inconclusive
evidence. Do not rerun validation or select a checkpoint using this analysis.

Capture the ACTUAL last decoder prediction_head mask_feats and its ACTUAL
out_norm(query) output through temporary pass-through hooks. Restore the
head wrapper and hooks in finally. Run one native loss forward per scene,
then normal/identity/nonself-permuted last-layer suffixes. No backward,
optimizer, parameter change, new norm revision, gate relaxation or training.

Build L00=Q0barF0, L01=Q0barF1, L10=Q1barF0, L11=Q1barF1 with the original
native float32 einsum. FIRST require L00/L11 reconstruct their corresponding
native masks at unchanged absolute1e-6. Native suffix, message replay,
repeat, identity Q/F/mask and revision2 norm controls also retain1e-6.
Stop and preserve the failure if any control fails; no arithmeticrevision3.

Use each expression's ORIGINAL selected query INDEX for all four point-mask
Piou/BCE values. Report query feature changes separately from index flips.
Compute point=.5*((L01-L00)+(L11-L10)) and
query=.5*((L10-L00)+(L11-L01)) on frozen float32 outputs cast to float64;
their sum must reconstruct L11-L00 within1e-12. This only checks a logit
identity; it does not decompose IoU or justify percent-attribution claims.

All six paired contrasts of Piou and BCE: equal-weight scene means,
10000 paired scene bootstrap draws, seed1999, 95% percentile intervals.
These are exploratory same-TRAIN-cohort contrasts, not multiple-comparison
corrected confirmatory results, generalization or trained improvement.
Compare saved input fingerprints and L00/native losses to the previous
terminal run without changing cohort or rerunning cached experiments.

Require current local owned token/deadline, verified pinned server4 identity,
physical GPU0 UUID, fresh idle/no foreign contexts and all THREE lifetime
training/diagnostic/exclusive flocks before CUDA. Preserve foreign work.
Bound execution by the original tick deadline, save each scene incrementally,
verify frozen assets after completion and verify resource release.
