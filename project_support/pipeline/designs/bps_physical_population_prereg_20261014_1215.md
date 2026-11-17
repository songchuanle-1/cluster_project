# Full Frozen TRAIN Physical-Mask Population Audit

- Continue stable m95-native-between-pair-support; supplemental diagnosis,
  not an admitted variant or a repeat of the completed affine comparison.
- Prior bounded observation: 67 same-class physical masks in eight eligible
  expressions had zero native support_excess. It is not a full-population
  result or trained-mask result. Determine its denominator and exceptions.
- Freeze before outcomes: all1498 records/all1502 stored events in the
  existing frozen TRAIN catalog, grouped by all416 stored native scenes.
  Do not select by loss outcome or add new scenes/annotations/datasets.
- Catalog SHA256:
  9ddcddeff3629c50c50054a9eaadb0828f5dfcb8541defd16705341c0dc567f2.
  Native dataset SHA256:
  2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d.
  BPS between_support SHA256:
  18e2a35e3df74c2823b2af36457dbbb7944c3b3697616f480b234d172797ce74.
- Use original unaugmented raw TRAIN points, unchanged native get_sp_label
  and get_ref_mask methods, original target IDs and catalog categories.
  Bind every loaded raw-file SHA to the catalog before use.
- For each geometry-eligible expression with an original nonempty GT mask
  and known target category, enumerate all distinct actual same-class
  physical instances, not model proposals or guessed true witnesses.
- Evaluate exact unchanged support_excess with finite +/-100 logits encoding
  each native physical mask, original GT teacher, one matched query and
  normalization1. Record exact zeros, finite nonzeros and >1e-6 values
  separately; 1e-6 is the inherited numerical reporting boundary, not a
  task-effect or admission threshold. GT-self remains a matched control.
- Report all scene/expression/event denominators, unavailable geometry,
  unknown categories, empty supports and missing alternatives. These are
  unavailable rather than negative evidence. Class names are not witness labels.
- This measures ideal physical-mask discrimination for fixed raw geometry.
  It does not measure augmented training prevalence, predicted-mask gradients,
  native full forward/backward, task harm, convergence or universal incapacity.
  Existing M201-BPS training and its six-gate receipt remain unchanged.
- CPU-only server-6; two threads; CUDA hidden in this diagnostic process;
  timeout900. Checkpoint partial records every20 scenes and retain them on
  timeout/failure. No local native behavior run or extra GPU process.
