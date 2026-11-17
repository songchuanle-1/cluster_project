# M95 Selected-Algorithm Observation

Two fresh processes only, same frozen M95 weights, saved sparse input and native
cotangent from sparse_m95_1, native flags and two unchanged original SparseConv
calls/VJPs per process. Read existing CONV_CPP.get_tuned_algo before/after each
call using its documented forward key; do not set algorithms, backend flags or
cache contents, clear caches, profile alternatives or retry until a difference.
Preserve coordinate alignment, exact saved-output identity and zero VJP controls.
Record chosen descriptors, TF32/accumulation flags and actual outputs/gradients.
Different descriptors with different arithmetic would be association, not proof
of unique kernel causality. Same descriptors do not prove all execution choices
are the same. Retain unknowns; this is not a fix or trained noise estimate.
