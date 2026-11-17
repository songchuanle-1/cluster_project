# Prediction-blind zero-feature geometry diagnosis

Stable candidate `m95-sample-context-support`, diagnosis only. Freeze the same
first 64 lexicographically sorted TRAIN scenes from `ScanRefer_train_new.json`
and use their native, unaugmented point and CLIP-cache files. A zero CLIP row
could indicate a missing 2D observation, but the cache producer is not present
in the project and this hypothesis is unverified.

Before looking at the outcome, compare zero versus nonzero cache rows on
superpoint size, semantic unknown fraction, and strict-majority semantic
purity. Match each zero row to a nonzero row in the same scene with nearest
point-count rank, without replacement where possible. Report the full and
paired denominators, scene-level differences, and hashes of inputs. This
control separates a size/composition association from the already counted
zero-row frequency; it cannot establish cache provenance, failure causality,
or a trainable mechanism. If there is no consistent within-scene association,
do not promote missing-view repair. No model edits, GPU, admission or launch.
