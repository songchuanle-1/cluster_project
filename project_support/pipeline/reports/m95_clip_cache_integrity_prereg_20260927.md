# Physical CLIP cache integrity screen

Stable `m95-sample-context-support`, diagnosis only. Native 2D features are
loaded directly as `clip_feat/<scene>.pth` and indexed by superpoint ID.
The earlier index contract did not inspect physical feature content.

Freeze the same first 64 lexicographically sorted distinct TRAIN scenes used
by the instance-semantic audit. For each corresponding original scene and
CLIP tensor, count nonfinite and all-zero rows, exact duplicate 1024-vector
rows within scene, and entire cache tensors identical across distinct scenes.
Compare duplicate rate in observed rows with deterministic different-scene
row pairs as a negative control. Record file hashes, shapes, and denominator.
Reject this realization if no corruption/sentinel/duplicate pathology is
found; a passed shape check alone is not proof of semantic provenance.

No target prediction, GT oracle, new model intervention, admission, sync,
or training. A cache pathology would first need independent producer audit
and failure-linked matched native control.
