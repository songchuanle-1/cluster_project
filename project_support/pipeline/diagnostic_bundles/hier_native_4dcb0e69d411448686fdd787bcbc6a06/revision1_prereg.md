# Implementation Revision 1: Preserve the Canonical Bank Axis

Same stable candidate and SAME disjoint-support hypothesis. Failure scope is
implementation/inconclusive, not a failed trained hypothesis. The original
grouped/compacted SDPA realization has12strictfloat32FAILs on frozen fixtures;
native-input explicit compacted reference has4/16first-point strict failures.
Target torch1.12 has no functional SDPA. Preserve every original result.

One local realization change: retain the full, bounded fine/middle/coarse bank
axis and apply the geometric support masks BEFORE softmax, instead of compacting
each selected support into a different key length. Use existing plain PyTorch
matmul/softmax operations matching the frozen dense-reference definition, with
an independently vectorized support predicate. Do not select a backend, change
precision, threshold, sample, heads, seed, scale, projection or learned weight.
Abandon the original grouped/chunk/checkpoint memory optimization claim for
this realization; N by at most328 keys is not N by N, but it computes masked
edges too and may cost more memory/FLOPs than the grouped realization and M95.

Prediction BEFORE tests: the frozen original16/4/2 and64/16/4 constructed
fixtures and all16native expressions should match the unchanged original dense
reference for float32 output, fixed-query readout and each input gradient
within1e-6; float64 remains an independent1e-10 test. No chunk/checkpoint PASS
will be claimed for an implementation that does not execute those paths.
Also freeze empty/single-tree, padded keys/points, included/excluded support
edges and genuine zero-path controls. Failure remains FAIL, not retuned.

After correctness, test the SAME native suffix with this realization and measure
actual readout cost; no resource gate promotion from a microbenchmark. Independent
model/config, full native backward and matched whole-model efficiency are still
needed before admission. No training/new ID/old-route reopening is authorized.
