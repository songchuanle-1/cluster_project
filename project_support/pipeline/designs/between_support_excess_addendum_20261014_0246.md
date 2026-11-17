# Consistent-Pair Support Distribution Excess

- The centroid strict-gap prototype returned loss/query-gradient0 on all8
  frozen native groups. Six expressions had resolved proxy events and2had
  unknown events. Preserve that exact no-op evidence; do not raise weights,
  change tolerance/cohort or claim a trained effect.
- Same stable BETWEEN candidate, same8groups/32expressions, same original
  checkpoint/seed/config/GT/matching/shared bounds. This new DIAGNOSTIC
  realization changes the supervision unit, not a numerical loss parameter.
- Let w_q(s)=n_s sigmoid(mask_qs)/sum_s n_s sigmoid(mask_qs), using native
  point count n_s; w_GT uses the unchanged native GT mask. For physical pair p,
  phi_p(x_s) is the squared normalized support-gap violation from the prior
  protocol. Define E_qp=sum_s w_q(s)phi_p(x_s), E_GTp similarly.
- Coherent per-event excess: min_p relu(E_qp-E_GTp), then mean over events.
  This requires one candidate pair for the whole predicted support measure.
  GT self-excess is exactly0 by construction, without a teacher-validity
  threshold. It does NOT certify the unknown physical witness identity.
- Matched fragmented-pair control: relu(sum_s w_q(s)min_p phi_p(x_s) -
  sum_s w_GT(s)min_p phi_p(x_s)). A point may choose its own pair here.
  No universal inequality between the two teacher-subtracted scores is assumed.
  Original center-only readout is also evaluated on the SAME native forward.
- Constructed same-center and fragmented-witness fixtures establish operator
  distinguishability only. Actual native positive-query mask and final-query
  gradients, original GT self-excess and all instance-mask controls decide
  whether the proposed path is active. Identity/two readout repeats1e-6;
  any zero/unknown path stays zero/unknown, no changed loss scale.
- Chain: dC_qp/dlogit_qs=w_q(s)(phi_p(x_s)-E_qp)(1-sigmoid(mask_qs)).
  Subgradients of relu/min are those of the actual Torch graph; ties and
  zero excess remain recorded. Complexity adds mask-support/pair coupling,
  not N^2 attention; no new trainable tensor or inference head in this probe.
- Jensen/expectation operations and ternary relations are not new primitives.
  Whole-mechanism difference, independent package/config, full native repeated
  backward, resources and efficacy remain unverified. No admission or training.
- Before execution add a count-matched disjoint physical-reference control:
  choose original native instance pairs outside all source reference candidate
  IDs and target IDs, sorted by ID, with the same valid-gap count per event.
  Insufficient disjoint pairs remain missing. Compare the original reference
  SUBSET and the disjoint control on the same eligible expressions/matches/
  num_boxes, never compare a partial-control aggregate to the full original.
