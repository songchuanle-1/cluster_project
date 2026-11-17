# Exact Inactive And Symmetric-Pair Reuse

- Cost attribution found no-event batch2 geometry30.68ms and worst-pair
  geometry220.29ms. Instrumented/shared figures, not primary throughput.
- Original V2 copied verbatim to pipeline/reports/bps_package_v2_c9de23ffb1804f1eaa81cf54b94b9d6a;
  old remote staging/source/results unchanged. Same candidate, no new loss.
- Shortcut only actual missing-event or mismatched-target expressions/scenes;
  unknown stored events remain on the original geometry path. Inactive support
  containers have empty count/center tensors, never fake physical geometry.
  Valid native grouping checks and original no-event/mismatch readout retained.
- Reuse instance centers and physical pair geometry ONLY within one scene of
  one prepare invocation. Never reuse across augmentations, batches or GT IDs.
- BETWEEN gap costs are symmetric: reversal negates axis and exchanges/
  negates bounds; the two hinge terms swap, preserving squared field.
  Cache unordered physical pair, reconstruct ordered descriptor. Preserve all
  original pair columns/node IDs/order/multiplicity/minimum ties.
- Verify actual native costs/ordered descriptors/unknowns and component mask
  gradients against frozen V2 on eight original groups, two stress scenes,
  metadata-selected non-event batch1/batch2 and mixed event/non-event batch2.
  Strict1e-6 unchanged. Any discrepancy is an implementation regression,
  not permission to relax tolerance or reject the scientific mechanism.
- Then full native repeat/backward and standardized shared resource regression.
  Prediction/GT/catalog binding/numerical config unchanged. No optimizer.
