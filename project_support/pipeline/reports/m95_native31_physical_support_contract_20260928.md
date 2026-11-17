# Frozen native support reconstruction contract

Candidate: `m95-sample-context-support` (diagnosis). This is a prospective CPU
boundary check, not an observed native effect or training admission.

`scripts/m95_native31_physical_support_20260928.py` reconstructs the native
dataset's point support: target instance = 1, source-recognized context class =
0.5, otherwise 0; superpoint support is the pointwise mean. It verifies the
original `sp_ref_mask` before assigning 0.5 to physically labeled non-target
shower-curtain points that lacked source context. It rejects mismatched native
support, missing/cropped physical instances, inconsistent instance classes,
invalid superpoint axes, and unchanged treatment. Mixed-instance superpoints
are reported for later final-FPS parity checks, not silently treated as pure
curtain instances. The candidate placebo pool is only a pre-outcome inventory;
the preregistered final focal-target and same-forward invariants still govern
placebo eligibility.

20 synthetic CPU tests pass across this boundary, the frozen native-31 adapter,
and final-support replay contract. The initial fixture incorrectly assigned
one physical instance conflicting classes; correction made the intended
boundary test valid. No native TRAIN capture, gradient, placebo result, gate
PASS, queue admission or training follows from these tests. The native adapter
must explicitly capture transformed instance and semantic labels at dataset
production before collate drops them, and fail on any source/support hash
or identity mismatch. Server-6 GPU7 was occupied by foreign PID 709354 at
09:09 Beijing time; an exclusive diagnostic lease was not obtained.
