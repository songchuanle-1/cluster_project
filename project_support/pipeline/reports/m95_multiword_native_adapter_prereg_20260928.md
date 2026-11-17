# Frozen 31-expression native capture adapter readiness

Before staging any GPU diagnostic, compare the immutable two-scene
`m95_multiword_capture_manifest_v1` against the existing M95 native
manifest producer's input contract. Bind both file hashes and inspect
the producer's declared manifest contract, cardinality, required row
fields, GPU guard, model class and output behavior.

Predeclared failure criterion: the producer expects the historic
256-expression identity manifest, whereas the new outcome-blind cohort
has 31 unique expressions and a distinct schema. If so, do not modify
or silently coerce the frozen 256-row producer. Require a separately
reviewed adapter preserving original text, target IDs, checkpoint,
native model and seed, with explicit scene/annotation parity before
any GPU execution.

This is a local static compatibility test, not an M95 outcome, native
backward pass or admission gate PASS. External GPU occupation remains
a separate blocker to actual capture.
