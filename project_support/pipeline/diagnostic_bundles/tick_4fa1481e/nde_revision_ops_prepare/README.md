# Disabled NDE revision1 operational software

Reuses corrected tick71 active_v2 operations. Actual runtime stays
`Cluster_nsd_20261107` at f625. Candidate source is 0747f6. No old lease,
request, stage, manifest, active binding or release is copied.

The top-level adapter is deliberately DRAFT-disabled with native producer/hash
anchors NULL. It is not an execution packet. Default launcher and renderer
perform NOP only. All original deadline margins 360/420/1020, GPU0 overlay
free20000MiB/max1, project-slot guards, original three locks and reconciliation
remain unchanged. The sole eligibility extension checks the exact frozen
pending revision1 canonical digest, preregistration owner/hash and original
negative evidence; it does not allow another or completed revision.

When the actual new native producer and source independent review exist, root
can invoke `python -B -X utf8 render_disabled_ops.py --render-disabled
--native-dir <fresh native path> --source-review <actual passed review>
--output <absent path under current tick>`. This writes another DRAFT-disabled
software copy, never adapter_release.json or execution material. Root must
independently review and activate a distinct copy before existing operations.

Acyclic hash order: native packet actual hashes -> current_binding.json (remote
and launcher hashes only) -> adapter.py anchors -> release_template.json ->
preparation.json -> software independent review -> separately reviewed active
copy and byte-exact adapter_release.json -> external candidate anchors -> fresh
prepare/stage actual binding review. No old execution fields are filled.

These checks are AST/hash/source preparation only. Native/Torch/autograd/TRAIN2,
all resources, launch, efficacy and novelty are NOT_RUN/UNKNOWN.
