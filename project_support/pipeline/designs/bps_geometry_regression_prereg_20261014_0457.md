# Native Geometry Transformation And Invocation Isolation

- Same v3 loss/package/catalog; no new candidate or optimizer.
- Use the original frozen eight native groups, stress5743/7787, genuine
  nonevent0, nonevent batch[0,44] and mixed[0,452]. Selection is from existing
  manifests, not the new outcomes.
- On each actual augmented TRAIN input, compare original geometry with signed
  coordinate reflection, axis permutation, uniform scale2 and translation
  [1,-2,4]. These transformations change neither ownership nor event metadata.
- Normalized physical gap cost should be invariant; compare every cost column
  at absolute1e-6, keep unknown/readout categories and pair ordering unchanged.
  Do not claim arbitrary semantic spatial relations are invariant.
- Re-evaluate untransformed input after each transformed call. Require exact
  original costs/counts/centers/readouts, detecting accidental cross-call reuse.
- Compare v2 and v3 on each transformed input at strict absolute1e-6 as a
  separate implementation regression. No threshold relaxation on failure.
- CPU-only on authorized server-6 after resource timings, bounded180seconds.
  No local native behavior tests, no CUDA forward or optimizer.
