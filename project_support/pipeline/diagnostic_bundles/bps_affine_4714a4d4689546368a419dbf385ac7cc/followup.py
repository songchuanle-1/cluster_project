"""Interpret field drift without confusing it with trained model harm."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "2"

import numpy as np
import torch

torch.set_num_threads(2)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--first-result", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    bundle = Path(__file__).parent
    original = load_module("immutable_affine_helpers", bundle / "probe.py")
    assert original.digest(bundle / "probe.py") == (
        "f878b1938db96be80c200f1d06498e3284309adf56c7d403348e173958713c67")
    assert original.digest(args.first_result) == (
        "0dc181a9fbb8065f78bdbb1d0a093c3963c00530d82e4b3af50ade9fa7cef118")
    root, data = Path(args.code_root), Path(args.data_root)
    dataset = root / "framework/dataset/scannetv2.py"
    support_path = root / "framework/model/Quard_model" / original.PACKAGE / "between_support.py"
    assert original.digest(dataset) == original.DATASET_SHA
    assert original.digest(support_path) == original.SUPPORT_SHA
    functions = original.native_methods(dataset)
    support_module = load_module("native_affine_loss_readout", support_path)
    catalog = support_module.BetweenSupportCatalog(args.catalog, original.CATALOG_SHA)
    selected = json.loads(Path(args.selection).read_text())["cases"]
    first = json.loads(Path(args.first_result).read_text())
    annotations = json.loads((data / "scanrefer/ScanRefer_train_new.json").read_text())
    annotation_by_key = {(r["scene_id"], int(r["ann_id"])): r for r in annotations}
    rows = []
    for scene in sorted({case["scene"] for case in selected}):
        scene_cases = sorted((case for case in selected if case["scene"] == scene),
                             key=lambda case: case["ann_id"])
        raw_file = data / "scannetv2/train" / (scene + "_refer.pth")
        assert original.digest(raw_file) == first["raw_file_sha256"][scene]
        xyz, rgb, sp_raw, semantic, instance = torch.load(
            raw_file, weights_only=False, map_location="cpu")
        xyz = np.asarray(xyz)
        _, sp = np.unique(np.asarray(sp_raw), return_inverse=True)
        sp = torch.as_tensor(sp, dtype=torch.long)
        instance = torch.as_tensor(np.asarray(instance), dtype=torch.long)
        semantic = torch.as_tensor(np.asarray(semantic), dtype=torch.long)
        labels, _ = functions["get_sp_label"](None, sp, instance, semantic)
        ann_ids = [case["ann_id"] for case in scene_cases]
        objects = []
        for aid in ann_ids:
            annotation = annotation_by_key[(scene, aid)]
            objects.append(list(map(int, annotation.get(
                "object_ids", [int(annotation.get("object_id", -1))]))))
        gt_masks = [functions["get_ref_mask"](None, None, instance, sp, obj)[1]
                    for obj in objects]
        matrix = np.asarray(first["matrices"][scene]["native"])
        offsets = torch.tensor([0, len(labels)])

        def prepare(value, dtype):
            return catalog.prepare(ann_ids, [scene], [len(ann_ids)], objects, sp,
                                   torch.as_tensor(value, dtype=dtype), offsets, [labels])

        native_dtype = torch.float32
        raw = prepare(xyz, native_dtype)
        transformed = prepare(xyz @ matrix, native_dtype)
        raw64 = prepare(xyz, torch.float64)
        exact_pullback = prepare((xyz @ matrix) @ np.linalg.inv(matrix), torch.float64)
        rounded_pullback = prepare(
            (xyz @ matrix).astype(np.float32).astype(np.float64) @ np.linalg.inv(matrix),
            torch.float64)
        categories = catalog.catalog["instances"].get(scene, {})
        for i, aid in enumerate(ann_ids):
            teacher = gt_masks[i]

            def loss(mask, field):
                logits = torch.where(mask > 0, 100.0, -100.0).unsqueeze(0)
                return float(support_module.support_excess(
                    [logits], [{"masks": teacher.unsqueeze(0)}],
                    [(torch.tensor([0]), torch.tensor([0]))], 1, [field]))

            target_classes = {categories.get(str(oid)) for oid in objects[i]}
            target_classes.discard(None)
            distractors = sorted(int(oid) for oid, category in categories.items()
                                 if category in target_classes and int(oid) not in objects[i])
            physical = []
            for oid in distractors:
                mask = functions["get_ref_mask"](None, None, instance, sp, [oid])[1]
                original_loss, affine_loss = loss(mask, raw[i]), loss(mask, transformed[i])
                physical.append(dict(object_id=oid, native_positive_supports=int(mask.sum()),
                                     raw_loss=original_loss, affine_loss=affine_loss,
                                     loss_delta=affine_loss-original_loss))

            def teacher_minimum(support):
                weight = teacher.double() * support["counts"]
                if not support["costs"]:
                    return []
                weight = weight / weight.sum().clamp_min(1)
                return [float((weight @ cost).min()) for cost in support["costs"]]

            # Inactive bypasses carry empty counts; never multiply by a full mask.
            minima_raw = teacher_minimum(raw[i]) if raw[i]["costs"] else []
            minima_affine = teacher_minimum(transformed[i]) if transformed[i]["costs"] else []
            rows.append(dict(scene=scene, ann_id=aid, raw_events=len(raw[i]["costs"]),
                             affine_events=len(transformed[i]["costs"]),
                             gt_self_raw=loss(teacher, raw[i]),
                             gt_self_affine=loss(teacher, transformed[i]),
                             target_classes_known=len(target_classes),
                             distractors=physical, teacher_min_raw=minima_raw,
                             teacher_min_affine=minima_affine,
                             exact_pullback=original.compare(raw64[i], exact_pullback[i], teacher),
                             rounded_pullback=original.compare(raw64[i], rounded_pullback[i], teacher)))
        print("completed " + scene, flush=True)
    result = dict(token=args.token, remote_observed_at=datetime.datetime.now(
                  datetime.timezone.utc).isoformat(), script_sha256=original.digest(__file__),
                  first_result_sha256=original.digest(args.first_result),
                  selection_sha256=original.digest(args.selection), rows=rows,
                  scope="Actual raw-instance mask counterfactuals with native support_excess; "
                        "not captured model predictions, trained task harm or efficacy.",
                  cuda_visible_devices=os.environ["CUDA_VISIBLE_DEVICES"],
                  cpu_threads=torch.get_num_threads())
    destination = Path(args.output)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(destination)
    print(json.dumps(dict(rows=len(rows), output=str(destination),
                          sha256=original.digest(destination))), flush=True)


if __name__ == "__main__":
    main()
