# Standalone EQ optimizer harness fix, preparation only

The failed ec459714 EQ request is immutable terminal rc1: native YAML optimizer
selection expected full-model named groups on a standalone core. First-fixture
forward/gradient comparisons may have executed before construction failed; no
completed case/equivalence PASS was serialized. Preserve all negative evidence.

The new entry adds only a parameterless module carrier: four empty YAML groups,
then dec pointing to the SAME existing core. The unchanged native gorilla
optimizer builder receives the unchanged deepcopy of original YAML. Native
selection/configuration semantics and core parameter identity/order are retained;
no tensor/module weights are recreated, no random draw or model call occurs.
All compare_revision1 fixture/tolerance/RNG/gradient/update/control code is exact.

The captured installed build.py and original YAML are hash-bound. The local
stdlib-only mock executes exact native selection functions with annotation
expressions removed, reproduces the original missing-text_encoder error and
proves carrier groups equal full-model groups restricted to core parameters.
This is not a real AdamW, Torch, numerical-equivalence or GPU execution test.

This is harness repair only, not model revision2; candidate source0747 and model
revision1 remain pending. No old package/request/stage/lease is modified. The
old one-attempt EQ capability is consumed. Only preparation is allowed this owner;
future execution requires independent review and a fresh owner/capability/stage/
manifest/lease bound to the new entry SHA. Never replay the failed request.
No release, remote/GPU operation, normalizer execution, admission or shared write.
Normalizer and production stay unexecuted until fixed EQ actually passes/reviews.
