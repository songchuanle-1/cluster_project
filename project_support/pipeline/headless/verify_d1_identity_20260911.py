"""Independent local identity/geometry accounting and readable fixed case report."""
from collections import Counter
import json
import math
from d1_identity_geometry_20260911 import sha
from run_d1_identity_geometry_20260911 import P, OUT
from close_tick_20260911_0707 import table

data = json.loads((OUT / "identity_geometry.json").read_text(encoding="utf-8"))
protocol = json.loads((OUT / "protocol.json").read_text(encoding="utf-8"))
old = json.loads((P / "reports/d1_instance_20260911-0810/instance_audit.json").read_text(encoding="utf-8"))
assert data["protocol_sha256"] == sha(OUT / "protocol.json")
assert data["audit_sha256"] == protocol["audit_sha256"]
assert data["worker_sha256"] == sha(P / "headless/d1_identity_geometry_20260911.py")
recovery = json.loads((OUT / "recovery_execution.json").read_text(encoding="utf-8"))
assert recovery["returncode"] == 0
assert all(v == data["worker_sha256"] for v in recovery["deployments"].values())
assert not data["cuda_initialized"] and len(data["rows"]) == 42
key = lambda r: (r["scene_id"], str(r["object_id"]), str(r["ann_id"]))
expected = set(map(tuple, protocol["ids"]))
by_model = {n: {key(r): r for r in data["rows"] if r["model"] == n} for n in ("baseline", "m95")}
assert all(set(rs) == expected for rs in by_model.values())
old_index = {(r["model"], key(r)): r for r in old["rows"]}
objects_checked = 0
for scene in data["scenes"].values():
    for obj in scene["objects"].values():
        assert obj["exact_mask_join"] and obj["raw_points"] == obj["aggregation_points"]
        g = obj["geometry"]
        if g is not None:
            assert g["points"] == obj["raw_points"]
            assert all(lo <= c <= hi for lo, c, hi in zip(g["bbox_min"], g["centroid"], g["bbox_max"]))
            assert all(abs(hi - lo - e) < 1e-12 for lo, hi, e in zip(g["bbox_min"], g["bbox_max"], g["extent"]))
        objects_checked += 1
for row in data["rows"]:
    original = old_index[(row["model"], key(row))]
    assert row["winner_id"] == original["selected"]["best_instance"]
    assert row["selected_iou"] == original["selected_iou"]
    objects = data["scenes"][row["scene_id"]]["objects"]
    a = objects[str(row["object_id"])]["geometry"]
    b = objects[str(row["winner_id"])]["geometry"]
    distance = math.sqrt(sum((u - v) ** 2 for u, v in zip(a["centroid"], b["centroid"])))
    gaps = [max(0, a["bbox_min"][j] - b["bbox_max"][j],
                b["bbox_min"][j] - a["bbox_max"][j]) for j in range(3)]
    box_distance = math.sqrt(sum(g * g for g in gaps))
    assert abs(distance - row["target_winner_geometry"]["centroid_distance"]) < 1e-12
    assert abs(box_distance - row["target_winner_geometry"]["aabb_distance_lower_bound"]) < 1e-12
    assert row["relation_cause"] == row["boundary_cause"] == "unknown"
    assert row["source_target_label_agrees"]
errors = [tuple(pair["error"]) for pair in protocol["pairs"]]
error_rows = [by_model["m95"][k] for k in errors]
counts = Counter(
    "target_best_partial" if int(r["object_id"]) == r["winner_id"] else
    "no_instance_pass50" if r["overlap_label"] == "no_instance_pass50" else
    "different_instance_equal_annotation_label" if r["exact_label_equal"] else
    "different_instance_different_annotation_label" for r in error_rows)
rows = [(i, "/".join(k), r["target_label"], r["winner_id"], r["winner_label"],
         f"{r['selected_iou']:.6f}", f"{r['target_winner_geometry']['centroid_distance']:.6f}",
         f"{r['target_winner_geometry']['aabb_distance_lower_bound']:.6f}")
        for i, k in enumerate(errors, 1) for r in [by_model["m95"][k]]]
report = f"""# D1 Exact Identity And Geometry Audit

## Protocol And Coverage
Frozen21descriptionIDs from the existing12errors/9controls, threecontrols missing
without replacement. 11physicalscenes, two models,42records. No new inference.
All{objects_checked} aggregation object masks exactly equal raw instance-ID masks.
Raw point SHA matches the prior audit; segmentation and aggregation SHA saved
per scene. All42 target names agree with source labels after case/underscore
token normalization. Zero missing ID joins, duplicateIDs or nonfinite geometry.
No label guessed from predicted appearance. No external annotation or new dataset.

## Fixed Error Evidence
{table(["Case", "Scene/object/ann", "Target label", "Winner ID", "Winner label", "M95 IoU", "Centroid distance", "AABB lower bound"], rows)}

M95 fixed12errors: {dict(counts)}.
These are outcome-selected examples, not prevalence estimates or causal effects.
The two pillow cases (scene0426 object22 and scene0591 object14) now have verified
same annotation labels despite unknown coarse semantics. Scene0249 object23
versus28 is trash can versus trash can, not merely equality of coarseID19.
Scene0652 cabinet6 versus dresser27 is different annotation labels; the wording
"taller of the two" does not license calling these the same semantic category.
Scene0334 coffee table5 best overlaps couch2 but no instance reachesIoU>.5:
do not upgrade this to a confident couch prediction. Scene0146 dispenser16
remains target-best partial mask, not demonstrated wrong-object selection.

## Geometry And Language Limits
For object point set X_i, c_i=mean(X_i), l_i=min(X_i), u_i=max(X_i).
d_ij=||c_i-c_j||2; g=max(0,l_i-u_j,l_j-u_i) coordinatewise;
||g||2 is the distance between enclosing axis-aligned boxes, hence a lower
bound on point-set distance, not contact or predicate truth.
Local independent scalar recomputation verifies all42 target/winner distances,
all object extents and centroid containment. Original point-coordinate frame
and numeric units retained; viewpoint/alignment/unit provenance not adjudicated.
No thresholds applied to infer near, on, behind, right, color or target height.
Exact token-subsequence noun matches produce object candidate lists and target
distances in JSON. Singular/plural variants and misspellings are not corrected.
These lists are incomplete lexical matches, not grounded anchors or parser recall.
All42 relation and boundary causal labels remain unknown.

## Controls And Interpretation
Nine original same-scene successful controls retained, three missing. These are
descriptive controls chosen by M95 outcomes, not matched randomized experiments.
Scene0046 object26 ann27 fails in bothmodels while ann34 succeeds: same target,
different descriptions, not a controlled paraphrase or proof of relation failure.
Do not impute these12 labels to remaining99 M95 recoverable errors. Earlier
284-ID coarse-semantic audit and its denominator remain unchanged.
The candidate-selection headroom evidence is stronger than any proposed cause.
No shared-anchor mechanism, novelty, generalization or efficacy claim admitted.

## Next Evidence Gate
Choose a concrete explanatory question only after addressing language ambiguity:
does the available description distinguish target from the verified same-name
alternative through an observable property, or is viewpoint/anchor ambiguous?
Freeze per-case text spans, alternative object IDs, anchor candidates and missing
frame evidence before evaluating a predicate; use existing scene assets only.
Then compare one candidate to primary papers and historical variants and derive
its objective, forward/loss, gradients, degeneracies and matched controls.
No automatic selector/pooling descendants or new training entry.

## Verification And Resources
8synthetic local/remote checks passed;42independent scalar distance checks and
{objects_checked} object geometry/identity records validated. AuditCPU
{data['elapsed_seconds']:.3f}s,peakRSS{data['peak_rss_mib']:.3f}MiB,CUDAuninitialized.
These costs exclude training/model inference and are not efficiency admission.
Initial Python3.10 hashlib API crash occurred before pointdata load; portable
SHA256 repair attempt1 succeeded. Initial logs preserved; no training interrupted.
Worker hash verified on server-4 and server-6; deployment diffs unchanged.
AuditSHA:{sha(OUT / 'identity_geometry.json')}.
"""
(OUT / "diagnostic_report.md").write_text(report, encoding="utf-8")
verification = dict(status="passed", rows=42, descriptions=21, scenes=11,
                    objects_checked=objects_checked, missing_joins=0,
                    error_counts=dict(counts), source_label_disagreements=0,
                    audit_sha256=sha(OUT / "identity_geometry.json"),
                    protocol_sha256=sha(OUT / "protocol.json"), helper_retries=1,
                    relation_cause_unknown=42, boundary_cause_unknown=42)
(OUT / "verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
print(json.dumps(verification, indent=2))
