# CLIP cache producer source audit

Stable candidate `m95-sample-context-support`; diagnosis only.
The cluster project's README names `image2point_clip.py` and a downloadable
preprocessed 2D-feature alternative, but this producer file is not present
in its Git worktree. A read-only, key-authenticated server-6 source lookup
found `/data3/songcl/Project/IPDN_baseline_project/IPDN/data/image2point_clip.py`
with SHA256 `e1271a5fec0012fa9aef07f962606e293486a60afd6387c6769fcef5af42c468`.

In that source, per-point accumulators start at zero (lines 63-64); frames
contribute projected CLIP tokens where image-to-point mapping is valid
(lines 69-90); division by the observation count is followed by NaN-to-zero
replacement (lines 92-93), superpoint averaging and `clip-feat` output
(lines 94-96). Its main loop samples every tenth image (lines 106-110).
Thus an unobserved point could map to zero in this *source implementation*.
This is not evidence that the physical `clip_feat` files in
`/data3/songcl/data/data_cluster` were produced by this exact source:
the folder spelling differs, and README permits downloaded features.
Cache provenance, source revision, raw frames and per-point observation
counts are unverified. The 64-scene physical screen found zero rows but
did not find target- or failure-specific enrichment. No intervention,
admission or launch follows from the source audit.
