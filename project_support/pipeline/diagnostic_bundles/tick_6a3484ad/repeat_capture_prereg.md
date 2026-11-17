# One Exact-Source Replication After A Strict Control Failure

The first native Q/F attribution attempt FAILED at scene9 (scene0028_00):
the UNCHANGED revision2 matched-radius solver exhausted64bisections.
Eight completed scenes and9nativeforwards are partial evidence, NOT32scene
attribution PASS. Same inputs match the earlier terminal run; normal Piou
agrees exactly on these8scenes, native loss differs by at most2.3842e-7.
Do not overwrite that result, hide failures or make numericalrevision3.

Run ONE separately staged replication of the IDENTICAL32scene runner,
helper/runtime/source/checkpoint/cohort/tolerances. The sole addition is a
pass-through wrapper around matched_radius that saves donor/recipient arrays
ONLY on its exception, then re-raises the original exception. The wrapper
must not alter tensors, call RNG, change returns or catch-and-continue.
Retain all original native1e-6 and fixture1e-12 controls.

If the failure repeats, retain exact operands and compare original solver
on these operands on CPU as a backend diagnostic; no replacement can enter
native attribution. If this repeat passes, retain BOTH attempts and report
run-to-run instability plus any valid complete readouts descriptively.
Neither outcome authorizes training, another arithmetic fix or repeated
trials until success. Never turn failed controls into a scientific null.

Before any CUDA execution again require fresh authorized GPU0 idleness,
verified server4 identity, all3lifetime locks and current original deadline.
