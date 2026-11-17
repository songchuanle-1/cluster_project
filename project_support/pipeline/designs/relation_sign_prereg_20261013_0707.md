# Relation Versus Other-Entity Token Sign Diagnostic

Stable ID: m95-native-relation-other-sign-conflict.
Hypothesis ID: root-relation-positive-tokens-also-receive-other-entity-negative-sign.

The native semantic alignment objective may receive the same relation token as
both root-relation supervision and a doubled other-entity negative term. This
is a specific map-to-loss contract hypothesis, not a task-weighting successor.

Use the unchanged full TRAIN annotation/graph files and original native
tokenizer/map functions. Enumerate actual root-relation and other-entity token
intersections, with annotations and scenes as denominators. No prediction,
VAL or test selection, new dataset, labels, seed or training schedule.

Matched controls: disjoint token spans and constructed identical spans passed
through the same original mapper. Negative control must detect a deliberately
shared span. Empty populations are not evidence of a repeatability PASS.

If native TRAIN intersections exist, next inspect the original semantic loss
and capture the corresponding paired native gradient pathway before deriving a
structural intervention. If none exist and the overlap control is detected,
reject only this direct token-intersection premise. Do not infer parser
correctness, global semantic adequacy, native full-model backward or efficacy.

Diagnosis, controls, native_backward, resources, independence and constraints
remain unpassed until their actual tests. No admission follows a corpus audit.
