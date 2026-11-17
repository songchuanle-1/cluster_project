"""Native augmentation/frame exposure; no model or semantic relation labels."""
import ast
import hashlib
import json
from pathlib import Path
import types
import numpy as np

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
tree = ast.parse(base.read_text())
prefix = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name)
            and t.id == "batches" for t in node.targets):
        break
    prefix.append(node)
env = {"__file__": str(base)}
exec(compile(ast.Module(body=prefix, type_ignores=[]), str(base), "exec"), env)
dataset = env["dataset"]
original_aug, original_transform = dataset.data_aug, dataset.transform_train
state, scenes, expressions = {}, [], []


def observe_aug(self, xyz, jitter=False, flip=False, rot=False):
    rng = np.random.get_state()
    matrix = original_aug(np.eye(3), jitter, flip, rot)
    np.random.set_state(rng)
    result = original_aug(xyz, jitter, flip, rot)
    assert np.allclose(result, xyz @ matrix, atol=1e-8, rtol=1e-8)
    state["matrix"] = matrix
    return result


def observe_transform(self, xyz, rgb, superpoint, semantic, instance):
    raw = xyz.copy()
    result = original_transform(xyz, rgb, superpoint, semantic, instance)
    _, augmented, _, _, _, labels, _ = result
    matrix = state["matrix"]
    complete = len(labels) == len(instance) and np.array_equal(labels, instance)
    recovery = float(np.max(np.abs(augmented @ np.linalg.inv(matrix) - raw))) if complete else None
    ids = [int(i) for i in np.unique(instance) if i >= 0]
    raw_means = {i: raw[instance == i].mean(0) for i in ids}
    augmented_means = {i: augmented[labels == i].mean(0) for i in ids if np.any(labels == i)}
    pairs = []
    for a in ids:
        for b in ids:
            if a >= b or a not in augmented_means or b not in augmented_means:
                continue
            delta_raw = raw_means[a]-raw_means[b]
            delta_aug = augmented_means[a]-augmented_means[b]
            pairs.append(dict(a=a, b=b, raw=delta_raw.tolist(), augmented=delta_aug.tolist()))
    scenes.append(dict(matrix=matrix.tolist(), determinant=float(np.linalg.det(matrix)),
                       all_points_retained=complete, inverse_max_error=recovery,
                       pairs=pairs))
    return result


dataset.data_aug = types.MethodType(observe_aug, dataset)
dataset.transform_train = types.MethodType(observe_transform, dataset)
for step, batch in enumerate(env["loader"]):
    offset = 0
    for scene, count in zip(batch["scan_ids"], batch["scenes_len"]):
        for b in range(offset, offset+int(count)):
            graph = dataset.scene_graphs[scene][str(int(batch["ann_ids"][b]))]
            expressions.append(dict(batch=step, scene=scene, ann_id=int(batch["ann_ids"][b]),
                utterance=graph["utterance"], view_dependent=batch["view_dependents"][b],
                metadata=batch["meta_datas"][b]))
        offset += int(count)
    scenes[-2]["scene"], scenes[-1]["scene"] = batch["scan_ids"]
    print(json.dumps(dict(batch=step, scenes=len(scenes))), flush=True)
    if step == 15:
        break
counts = [dict(nonzero=0, sign_changed=0) for _ in range(3)]
for scene in scenes:
    for pair in scene["pairs"]:
        for axis in range(3):
            a, b = pair["raw"][axis], pair["augmented"][axis]
            if abs(a) > 1e-8 and abs(b) > 1e-8:
                counts[axis]["nonzero"] += 1
                counts[axis]["sign_changed"] += int(a*b < 0)
summary = dict(scenes=len(scenes), expressions=len(expressions),
               reflected=sum(s["determinant"] < 0 for s in scenes),
               complete_points=sum(s["all_points_retained"] for s in scenes),
               view_metadata_missing=sum(r["view_dependent"] is None and r["metadata"] is None
                                         for r in expressions),
               axis_signs=counts)
report = dict(summary=summary, scenes=scenes, expressions=expressions,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), base, env["ROOT"] / "framework/dataset/scannetv2.py")},
    scope="Native16TRAIN batches;actual augmentation matrix captured preserving NumPy RNG. "
          "Axis signs are coordinate facts,not language predicate truth or causal model failures. "
          "No inverse-transport model,augmentation removal,new labels or admission.")
out = env["ROOT"].parent / "pipeline/frame_exposure_20260916"
out.mkdir(parents=True, exist_ok=True)
(out / "result.json").write_text(json.dumps(report, indent=2))
print(json.dumps(summary))
