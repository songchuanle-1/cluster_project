# M229-MIC frozen native protocol (NOT RUN)

Use original M95 YAML bytes a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a. No data/pretrain/loss/optimizer/seed1999/epochs50/max_iters70 changes. Compare original M95 and MIC on the same two natural original TRAIN batches with original loss.backward and optimizer.step, no auxiliary backward, resampling or extra coverage gate.

Preserve original FFN+three LN construction prefix, then construct only the new C-to-C core in a CPU RNG fork and replace original three FFNs with Identity. Common initializer dynamically pairs all actual surviving original names/shapes/hashes, excludes removed three FFN groups and the new mobius_interaction core, and retains three LN parameter groups; no hard parameter count.

Observe actual original three LN outputs, true-support plans, eight global subset input blocks (8F rows), one shared Linear and one original GELU invocation, actual eight output slices and q inclusion-exclusion, two transparent original direct-path mean calls and original three raw skips/HCG/singleinst/mask/loss. No learned/mean replays. Nonempty true fine path is the core prerequisite; missing core support is INCONCLUSIVE without resampling. Optional unequal degree/multi-root/zero-input boundaries unexercised remain NOT_EXERCISED, never mandatory extra gates.

Only new core original-loss aggregate weight-gradient finite/nonzero and real aggregate weight/module update over each of the two original optimizer steps are the new trainability conditions. Individual map/node/row/column/bias/subset outputs may be zero. No FP32 cancellation/zero/symmetry/finite-difference residual, Jacobian, conservation or per-branch positivity gate. All claimed captures must be finite but no new threshold.

Original resource function and handlers unchanged: same paired input, bs1/lang1, warmup20/repeat100 synchronized whole-call median/P90, full unsupported counts retained; original counted total FLOPs <=10G. Original prediction peak allocation +15% requires >=+0.003 mIoU for retention; no new latency cutoff. Source parameter/MAC arithmetic is not a pass. Pure TRAIN peak, accuracy and novelty remain UNKNOWN.

Raw/native/autograd/resources NOT_RUN. No admission, queue, remote request, lease, GPU permission or actual source commit is supplied by this prototype.
