# Native instance semantic origin screen

Stable candidate `m95-sample-context-support`, diagnosis only. Native
`scannetv2.py` assigns each physical instance a context class using the first
retained point's semantic label. This screen asks whether that label differs
from the instance majority in independently selected TRAIN scenes. No model
prediction or validation outcome enters the exposure definition.

Freeze the first 64 lexicographically sorted distinct ScanNet TRAIN scenes
from `ScanRefer_train_new.json`, one annotation per scene (lowest numeric
`ann_id`), the native scene tensor and native `scene_graphs_new_train.json`.
For every physical instance with at least five retained points and a unique
strict semantic majority, compare the first-point semantic to majority.
Report denominators, mixed-label instances, first/majority mismatches,
and, for the frozen annotation, whether a mismatch flips exact-key context
membership. Use same-scene unmismatched instances as a rate control and
separate referred instances from nonreferred ones. Hash input/code files.

Primary defect screen: at least one mismatch that changes native context
membership in a referred instance and more such exposures than the
same-scene unmismatched control (whose flip count is necessarily zero).
If none, reject first-point semantic instability as a causal realization
in this cohort. This test does not establish training benefit, independence,
native backward, or admission. Do not modify dataset or launch training.
