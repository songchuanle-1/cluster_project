# Source clarification

The initial preregistration's incidental phrase "axis-aligned hierarchy" was inaccurate. The actual admitted PointCloudPartitioner uses native FurthestPointSampling.apply plus Euclidean nearest-center assignment;its source fingerprint is frozen in manifest.json. This audit isolates the fine metric exchange with memberships held fixed and makes no whole-hierarchy rotation-invariance claim. No hierarchy implementation or preregistered control was changed. Exact native TRAIN memberships still require the original CUDA FPS,not an artificial CPU substitute.
