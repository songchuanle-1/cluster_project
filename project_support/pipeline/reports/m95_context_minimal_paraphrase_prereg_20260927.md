# Fixed-target near-identical-text context contrast

Stable `m95-sample-context-support`, diagnosis. The previous 64-scene,
same-target physical-instance audit found context on/off pairs but with
different texts. Before reading pair outcomes, restrict to expressions
sharing the same scene and exact target-instance set. Reconstruct the
dataset's whitespace tokenization of graph utterances and exact class-key
membership. A minimal pair must differ by exactly one inserted or deleted
class-key token; all other tokens must be identical in order. For each
physical non-target instance with an eligible native class, count such
pairs whose context membership switches for that class. Report unique
scene/target/instance and annotation-pair units, as well as total
candidate same-target annotation pairs. Reject the near-identical-text
control realization if none exist; looser semantic paraphrases are not
equivalent controls without explicit matching criteria.

This is an outcome-blind source check. Even a positive pair does not
establish same transformed input, native FPS exposure, loss causality,
new model, or trained benefit. No GPU, dispatch or admission.
