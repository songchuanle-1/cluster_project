# Prediction-Blind Calibration Cohorts

- Preserve primary25groups/97expressions and head readouts unchanged.
- Supplement: use the five already frozen remaining MAIN-overwrite cases and
  original control4804. Same source audit hash and original dataset/TRAIN/graph
  hashes; complete calibration/task reads for13of13original source cases.
- Extension: sort original TRAIN annotations by(scene_id, numeric ann_id),
  exclude ALL primary scenes and the five supplementary scenes. Use original
  token mapper, not model predictions, to classify half-mass secondary tokens.
  Choose each eligible scene's first half-mass expression, then first64scenes;
  choose first16other scenes whose every TRAIN expression lacks half-mass tokens.
  Include every expression in each selected native group. Add original control
  group4804 as an explicitly repeated bridge, not an independent new scene.
- Enumerating the original mapper here constructs a new frozen sampling
  manifest, not a repeated population scientific claim. Manifest is saved
  before any forward. Missing requested scenes are unknown/shortfalls, not
  filled with prediction-selected replacements.
- Report denominators, scenes, cases, support IoUs and calibration/direction
  comparisons separately for supplement and extension. No-half scene groups
  are population comparators, NOT exchangeable or matched causal controls.
  Scene/category differences and small subgroups preclude causal harm claims.
- Same model, seed1999, unchanged masks/matching/temperature, strict1e-6,
  no new trainable tensor, optimizer or training. Original full-forward FAILs
  and missing original disjoint controls remain. Shared guards unchanged.
