"""Ground annotation identities and record geometry without causal labels."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import time

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))


def mentions(label, description):
    label, text = tokens(label), tokens(description)
    return bool(label) and any(text[i:i + len(label)] == label
                               for i in range(len(text) - len(label) + 1))


def geometry(xyz):
    import numpy as np
    assert len(xyz) and np.isfinite(xyz).all()
    lo, hi = xyz.min(axis=0), xyz.max(axis=0)
    return dict(points=len(xyz), centroid=xyz.mean(axis=0).tolist(),
                bbox_min=lo.tolist(), bbox_max=hi.tolist(), extent=(hi - lo).tolist())


def separation(a, b):
    import numpy as np
    delta = np.asarray(a["centroid"]) - b["centroid"]
    gap = np.maximum(0, np.maximum(np.asarray(a["bbox_min"]) - b["bbox_max"],
                                  np.asarray(b["bbox_min"]) - a["bbox_max"]))
    return dict(centroid_delta=delta.tolist(), centroid_distance=float(np.linalg.norm(delta)),
                aabb_distance_lower_bound=float(np.linalg.norm(gap)),
                relation_truth="unknown_no_grounded_reference_frame_or_predicate")


def self_test():
    import numpy as np
    assert mentions("trash can", "blue trash_can next to box")
    assert not mentions("can", "candy")
    assert not mentions("chair", "chairs")
    assert not mentions("", "chair")
    a = geometry(np.array([[0., 0., 0.], [1., 1., 1.]]))
    b = geometry(np.array([[3., 0., 0.], [4., 1., 1.]]))
    assert a["extent"] == [1., 1., 1.]
    assert separation(a, b)["aabb_distance_lower_bound"] == 2
    assert separation(a, a)["centroid_distance"] == 0
    shift = np.array([11., -7., 3.])
    c = geometry(np.array([[0., 0., 0.], [1., 1., 1.]]) + shift)
    d = geometry(np.array([[3., 0., 0.], [4., 1., 1.]]) + shift)
    assert separation(a, b)["centroid_distance"] == separation(c, d)["centroid_distance"]
    print("SELF_TEST_PASS 8 checks")


def main():
    import numpy as np
    import resource
    import torch
    p = argparse.ArgumentParser()
    for name in ("protocol", "audit", "data-root", "out"):
        p.add_argument("--" + name, required=True)
    args = p.parse_args()
    output, data = Path(args.out), Path(args.data_root)
    assert not output.exists()
    protocol = json.loads(Path(args.protocol).read_text())
    assert sha(args.audit) == protocol["audit_sha256"]
    audit = json.loads(Path(args.audit).read_text())
    requested = {tuple(k) for k in protocol["ids"]}
    key = lambda r: (r["scene_id"], str(r["object_id"]), str(r["ann_id"]))
    rows = [r for r in audit["rows"] if key(r) in requested]
    assert len(rows) == 42 and len(requested) == 21
    expected_raw = {s["scene_id"]: s["sha256"] for s in audit["scene_checks"]}
    source = data / "scanrefer/ScanRefer_val_new.json"
    assert sha(source) == audit["source_sha256"]
    torch.set_num_threads(1)
    self_test()
    start = time.monotonic()
    scenes, result = {}, []
    for scene in sorted({k[0] for k in requested}):
        assert time.monotonic() - start < 480
        root = data / "scannetv2/val"
        paths = dict(raw=root / f"{scene}_refer.pth",
                     aggregation=root / f"{scene}.aggregation.json",
                     segmentation=root / f"{scene}_vh_clean_2.0.010000.segs.json")
        assert sha(paths["raw"]) == expected_raw[scene]
        xyz, _, _, _, instances = torch.load(paths["raw"], map_location="cpu", weights_only=False)
        xyz = np.asarray(xyz, dtype=np.float64)
        groups = json.loads(paths["aggregation"].read_text())["segGroups"]
        segments = np.asarray(json.loads(paths["segmentation"].read_text())["segIndices"])
        assert len(segments) == len(instances) == len(xyz)
        objects, seen = {}, set()
        for group in groups:
            oid = int(group["objectId"])
            assert oid not in seen
            seen.add(oid)
            mask = np.isin(segments, group["segments"])
            exact = bool(np.array_equal(mask, instances == oid))
            objects[str(oid)] = dict(label=group["label"], exact_mask_join=exact,
                                     raw_points=int((instances == oid).sum()),
                                     aggregation_points=int(mask.sum()),
                                     geometry=geometry(xyz[mask]) if exact and mask.any() else None)
        assert all(str(int(i)) in objects and objects[str(int(i))]["exact_mask_join"]
                   for i in np.unique(instances) if i >= 0), scene
        scenes[scene] = dict(hashes={k: sha(v) for k, v in paths.items()}, objects=objects)
        for row in [r for r in rows if r["scene_id"] == scene]:
            target = objects[str(row["object_id"])]
            assert target["exact_mask_join"] and target["geometry"] is not None
            winner_id = row["selected"]["best_instance"]
            winner = objects.get(str(winner_id))
            assert winner is not None and winner["exact_mask_join"] and winner["geometry"] is not None
            lexical = [oid for oid, obj in objects.items()
                       if obj["geometry"] is not None and mentions(obj["label"], row["description"])]
            result.append(dict(model=row["model"], scene_id=scene, object_id=row["object_id"],
                               ann_id=row["ann_id"], source_object_name=row["object_name"],
                               description=row["description"], selected_iou=row["selected_iou"],
                               overlap_label=row["selected"]["label"],
                               target_label=target["label"], winner_id=winner_id,
                               winner_label=winner["label"],
                               source_target_label_agrees=tokens(row["object_name"]) == tokens(target["label"]),
                               exact_label_equal=tokens(target["label"]) == tokens(winner["label"]),
                               target_winner_geometry=separation(target["geometry"], winner["geometry"]),
                               lexical_object_candidates=lexical,
                               target_to_lexical_candidates={
                                   oid: separation(target["geometry"], objects[oid]["geometry"])
                                   for oid in lexical if oid != str(row["object_id"])},
                               relation_cause="unknown", boundary_cause="unknown"))
        print("SCENE", scene, "objects", len(objects), flush=True)
    assert not torch.cuda.is_initialized()
    output.mkdir()
    payload = dict(status="complete", protocol_sha256=sha(args.protocol),
                   worker_sha256=sha(__file__), audit_sha256=sha(args.audit),
                   rows=result, scenes=scenes, cuda_initialized=False,
                   elapsed_seconds=time.monotonic() - start,
                   peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                   limits=protocol["limits"])
    (output / "identity_geometry.json").write_text(json.dumps(payload, indent=2))
    print("COMPLETE", len(result), "rows", len(scenes), "scenes")


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    else:
        main()
