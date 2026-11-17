# Affine Follow-Up: Pullback And Physical-Mask Readouts

- Continue the same supplemental BPS diagnostic, not a new training candidate.
  First probe result SHA256:
  0dc181a9fbb8065f78bdbb1d0a093c3963c00530d82e4b3af50ade9fa7cef118.
- Frozen first-probe source, 12 scenes/48 expressions, matrices and native
  source/catalog identities remain unchanged. Do not overwrite its results.
- New question: do the large individual-field deltas survive the actual
  event minimum and GT subtraction? An individual worst pair is not the
  trained loss and must not be represented as such.
- Freeze before outcomes: evaluate original/native-affine fields on every
  actual same-physical-class distractor instance in those scenes. Obtain
  masks with the unmodified native get_ref_mask function; no prediction or
  outcome selection. Empty/unknown classes are unavailable, not negative.
- Readouts: exact native support_excess on finite +/-100 mask logits encoding
  those actual instance masks, original GT teacher, original matched-query
  normalization1; GT-self control in both branches; each event's minimum GT
  expected cost. These are physical-mask counterfactuals, not model logits,
  native full forward, trained task harm or efficacy.
- Separate numerical controls: exact float64 affine transform followed by its
  inverse, and float32-rounded affine coordinates followed by the inverse.
  Keep absolute1e-6. Primary float32 conformal failures stay failures; the
  auxiliary control cannot overwrite native precision or earlier records.
- No assumed universal loss direction or ranking inequality. Report
  denominators, no-event bypasses, unavailable classes, zero masks, actual
  operators, scalar loss deltas and pair/ranking changes without cherry picking.
- CPU-only server-6, two threads, CUDA hidden only in this diagnostic process,
  timeout600; no optimizer, model/package/config/admission/queue change.
