# Persistent wrong-context physical identity

Stable diagnosis `m95-sample-context-support`. Use the two frozen 128-row
independent TRAIN transforms in `m95_seed_exact_1999_20260927.json` and
`m95_seed_exact_2000_20260927.json` with hashes recorded in
`m95_context_error_repeat_prereg_20260927.md`. Check unique identical
expression identities, checkpoint/manifest bindings, changed input hashes,
and same target instance ID across transforms.

Among expressions that are selected wrong-context failures in both
transforms, count whether `selected_seed_instance` is the *same physical
non-target instance* in both. Negative control: expressions that fail in
both transforms but are not wrong-context in either, scored by the same
physical-instance repeat metric. Mixed transitions are reported separately.
Report expression and scene denominators, paired-scene comparisons only
when both arms occur within one scene. If persistence of the context-error
label rarely retains physical instance identity, a stable distractor
identity hypothesis fails; if identities persist but the negative control
is similar, context-role specificity is not established. This is an
observational TRAIN replay, not a relation mechanism or admission.
