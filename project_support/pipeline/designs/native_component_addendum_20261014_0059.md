# Native Semantic Component Attribution

- Keep the original25group final-projection capture, original loss coefficients,
  matching, model, checkpoint, seed1999 and all same-capture identity checks.
- Expose the existing box_to_token_loss/(2*num_boxes) and
  token_to_box_loss/(2*num_boxes) as separate diagnostic return values.
  Do not modify either computation, propose a new loss or fit weights.
- At every original matched role/token site, require the sum of component
  gradients to agree with original total gradient within1e-6.
  Record whether the26fractional-secondary positive derivatives arise from
  query-to-token competition, token-to-query competition or both.
- Full native original repeat FAIL and all task/finite-difference limits remain.
  Component attribution does not prove wrong labels, localization harm,
  trained efficacy, independence or new-core backward admission.
