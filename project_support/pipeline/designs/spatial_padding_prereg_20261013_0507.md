# Native Spatial Padding Loss Isolation

- Tick: f3d67c69338443d28eee4349fd8576ab.
- Stable ID: m95-native-spatial-padding-loss-isolation.
- Hypothesis ID: padded-superpoint-columns-contribute-to-native-mask-loss-and-gradient.
- Unlike text padding, main-role maps, short input-group transport or sentinel
  identity, this concerns the geometry axis inside the actual mask loss.
- Source inspection suggests explicit valid-support filtering; establish its
  behavior using original native augmented getter masks and collations rather
  than treating inspection alone as experimental disconfirmation.
- Population: first eight groups of the unchanged original frozen 32/128 TRAIN
  manifest; actual native paired collations, seed 1999 twice.
- Test the original Criterion.get_layer_loss with match_last_layer=True and
  original native configuration loss weights. Inject deterministic decoder-shaped
  tensors only at the loss boundary. Native model forward/FPS is NOT executed.
- Predeclared intervention changes only padded spatial logits. Read loss change,
  valid-gradient change and padded-gradient magnitude for BCE/Dice/score/indication
  paths. proj_tokens=None, so language alignment is not evaluated.
- Matched negative control removes valid-support filtering and appends zero
  target columns; it must produce nonzero padded gradients. No production repair.
- A zero test is interpretable only if actual collations contain padding and the
  broken-filter control is positive. Empty cohorts are inconclusive.
- If the actual mask-loss path has zero padded gradient and unchanged valid loss
  and gradient, reject only spatial padding contamination at this loss boundary.
  This does not certify decoder attention padding, whole-model backward,
  population efficacy, reference supervision or a new architecture.
- Remote server-6 CPU only, no additional data, label changes or training.
