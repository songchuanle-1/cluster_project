# M95 Decoder Assignment Stability Preregistration

- Tick: 498da58819f245158586bd649cd29a88; created 2026-10-09.
- Stable candidate: m95-decoder-assignment-churn; stage diagnosis.
- Hypothesis: repeated layer-specific assignment changes create inconsistent
  native referent targets across decoder depth.
- Independent of quality-target censorship: readout is query/target assignment,
  not loss magnitude, quality scores, gradient surgery or reweighting.
- Test: source audit plus capture the actual indices passed to loss_masks for
  final and auxiliary outputs on the existing frozen TRAIN cohort.
- Matched control: one native forward, identical geometry and target; compare
  layer assignment hashes against the final-layer assignment. Rotated query
  indices provide a deliberately changed negative control.
- Reject the layer-specific-rematching realization if all native assignments
  are identical across depth and no layer rematcher exists on the active path.
  This does not rule out mask changes, feature drift or future structural ideas.
- Report complete cohort/companions, input hashes, two seeded repeats and exact
  assignment agreement. Numeric readouts retain the existing 1e-6 repeat check.
- No optimizer, candidate deployment, training or effect/novelty claim.
- Only server-6 GPU7 for native capture, with live idleness and exclusive lock.
