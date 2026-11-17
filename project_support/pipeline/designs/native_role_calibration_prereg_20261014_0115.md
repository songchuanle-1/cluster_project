# Native Role Calibration Versus Task Error

- Tick 3aabc8207fea49ffb20003340e9bdfb9; continue the three stable validation
  IDs. Freeze the original 25-group/97-expression cohort, checkpoint, TRAIN,
  graphs, seed1999, native model/config and all historical failures.
  No outcome-selected samples, optimizer, new training variant or changed gate.
- Use exact final projected tensor identity and original GT/matching. Retain
  the prior strict full-forward repeat failures; a same-capture identity is
  not a repair. Missing disjoint controls remain missing.
- On original logits z, reconstruct the actual loss derivative:
  query-to-token = mask * ((1+OTHER) * softmax(z*(1+OTHER)) - a) / (2N);
  a = MAIN/n_main + .2*MOD/n_mod + .2*PRON/n_pron + .1*REL/n_rel.
  token-to-query = tmask * (softmax_query(z) - role_boolean_count/
  original_normalized_role_mass) / (2N), with original token support masking,
  unmatched EOS maps and ordered tmask assignments retained.
- Require analytic/autograd agreement1e-6 over ALL logits, exact identity and
  two same-capture readout repeats. Record role maps, effective probabilities,
  attraction coefficients and threshold a/(1+OTHER) at every frozen site.
  If repulsion occurs exactly above the actual calibration threshold, this
  explains its sign; it does not prove that the objective is useful or correct.
- Record every expression's selected native support IoU, best support IoU,
  matched query IoUs and whether original indication selects a matched query.
  These TRAIN augmented loss-mode readouts are not official validation mIoU
  or evidence of training benefit. Mask threshold remains native0.5.
- At the original final decoder query, differentiate the ORIGINAL weighted
  mask, indicator and composite objectives. Chain each of the three existing
  role-site derivative subsets, plus fractional repelling and attracting
  subsets, through the original semantic projection. Compare their task dots
  per expression and aggregated group. No gradient surgery or optimizer.
- Expected discrimination: calibration threshold can explain sign with no
  contradiction; task-opposing local derivatives can identify a specific
  diagnostic follow-up, but do not establish material harm or independent
  structure. No mandatory pretraining efficacy threshold is introduced.
- Shared server-6 GPU7 only; verify das/UUID/free>=32768MiB and acquire both
  project flocks. Allocator fraction.25, timeout600, preserve foreign jobs.
  New unique output names and source hashes; original sources stay unchanged.
