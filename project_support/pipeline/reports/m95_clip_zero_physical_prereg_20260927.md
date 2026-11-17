# Native CLIP zero-row physical support test

Stable diagnosis `m95-sample-context-support`. The independent physical
cache audit found exact zero feature rows in 54 of 64 TRAIN scenes; zero
alone does not imply a defect. Freeze those first 64 scenes, the original
ScanNet superpoint labels, CLIP cache and first annotation per scene.

Map each zero cache row to the physical superpoint with the same raw ID.
For every valid superpoint (at least five points), compare zero versus
nonzero rows on point count, physical target membership, majority semantic
class and target annotation support. Pre-register the negative control:
nonzero rows in the same scenes. Report denominators and scene-stratified
target exposure; do not assume that zero encodes missingness, nor infer
target failure from a prediction-blind observation. If target support is
never zero, this realization cannot explain target-specific missing 2D
features in the frozen cohort. Any nonzero target exposure requires a
producer provenance check and matched native behavior control, not a new
model variant by itself.
