# M95 physical-instance context bag diagnostic

Stable ID `m95-sample-context-support`. On the unchanged M95 checkpoint,
run the first two native TRAIN batches on server-6 GPU7 (seed 1999,
no optimizer step). Hold the model forward, matcher, indicator and mask
predictions fixed. The current `sample_loss` assigns 0.25 separately
to every unprotected non-target class-context FPS seed.

Test a different supervision unit: set those individual seed targets
to zero, then for each physical non-target context instance with at
least two eligible seeds add one group-level focal target 0.25 on
`logit(1 - product_j(1 - sigmoid(ref_score_j)))`. The bag probability
asks for existence of context evidence somewhere in an instance while
the seed-wise zeros do not promote every location. No selected-query
ranking, test-time selector, new parameter or loss-weight sweep.
Use the same native focal function and normalize the group term per
expression by the number of eligible groups, then scale by the fraction
of valid FPS seeds belonging to those groups to retain an explicit
per-expression normalization. This normalization is a diagnostic
choice, not a tuned or admitted training schedule.

Controls on the same forward: (1) native original sample loss;
(2) hard-zero only, without group supervision; (3) hard-zero plus
size-matched deterministic shuffled assignments of eligible seeds
to bags, preserving bag count, bag sizes, targets and normalization.
Compare values and native sampling-module parameter gradients for
finite/nonzero branch differences; report coverage and matched
negative seed counts. A shuffled bag gradient indistinguishable from
physical-instance grouping would reject the identity-specific claim.
No immediate argmax or mIoU benefit follows without training.
Require whole-mechanism prior-art/closed-route review, native
implementation tests, uniform resource gate, independence, goal
constraints, admission receipt, sync and verified training before
queue admission.
