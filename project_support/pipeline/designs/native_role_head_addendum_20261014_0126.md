# Role-Local Fixed-Head Response

- The calibration test found26repelling fractional sites in4expressions; all4
  original selected support IoUs were>=.5. This is an observed association,
  not evidence for benefit, harm, correct supervision or a scientific rejection.
- Keep the same original25groups and every97expression. Freeze decoder head,
  instance features, padding, native matches/targets and every model weight.
  No new seed, optimizer, head update, gradient surgery or prediction filtering.
- At the unchanged final query, compare original weighted semantic direction,
  identity, each role-local subset, and its exact original-minus-subset
  complement. Fixed epsilon.001, the same preregistered readout scale as the
  previous head-only diagnostic; never select or scan epsilon.
- Record mask/indicator/composite loss deltas, central derivatives and
  analytic derivative errors, selected support IoU and native indicator margin
  (best matched query score minus best unmatched query score) per expression.
  Require original head replay agreement1e-6 and exact two head repeats.
- Zero-gradient subsets remain unknown. Tiny float32 changes or central
  derivative discrepancies are not a strict derivative PASS, meaningful harm,
  whole-network intervention, official mIoU change or training outcome.
- Preserve failed v1 and successful v2 calibration. V3 is a new source/output;
  repairs only the already documented GT repetition assumption and adds head
  readouts. It does not replace previous outputs or change frozen thresholds.
