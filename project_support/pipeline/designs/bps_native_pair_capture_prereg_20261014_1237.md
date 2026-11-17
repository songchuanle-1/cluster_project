# Same-Forward Native BPS Pair-Selection Capture

- Resume BPS diagnosis, not a new training variant. Fixed eligible cohort:
  all49 expressions/all40 scenes in the complete population audit, with all
  ordinary native four-expression companion groups retained and deduplicated.
- Use a frozen copy of the current M201-BPS best checkpoint. Bind file SHA,
  meta, source stat before/after copying and all native package source hashes.
  Do not change or restart the original training.
- Native TRAIN dataset/config, seed1999, batch1 diagnostic and model.train().
  Restore original checkpoint model/buffer state before each of two identical
  input forwards. No optimizer or model-parameter backward.
- Capture the unchanged native support_excess arguments: actual decoder mask
  logits, original matched src/tgt indices, original GT masks/num_insts and
  native geometry. Return the original component to the native criterion.
- Diagnostic intervention only: for each matched query, compare unchanged
  fields with all exact GT-minimum-cost pair columns. Original per-query
  decomposition must reproduce the original batch-normalized component at
  absolute1e-6. No GT-conditioned field enters the actual model loss.
- Check unchanged full native loss and captured mask logits between repeats
  at original absolute1e-6, and original CPU input identity before/after.
  Retain failures; no threshold/precision/schedule repair in this diagnostic.
- Report all groups/expressions, absent events, actual matched-query
  denominators, component/oracle deltas and finite/repeat/decomposition
  checks. Oracle is not a true witness label, deployable repair or task benefit.
- Shared GPU7 only: verify das/UUID, live free>=32768MiB and project slots;
  acquire all three existing cluster_project GPU7 lock files, use allocator
  fraction.25 and two CPU threads, timeout600. Preserve every foreign process.
- Lock paths observed read-only on this server:
  /tmp/cluster_project_gpu7_exclusive.lock,
  /tmp/cluster_project_gpu7_diagnostic.lock,
  /tmp/cluster_project_gpu7_slot2_diagnostic.lock.
  These fence diagnostics; holding a named lock does not imply GPU exclusivity.
