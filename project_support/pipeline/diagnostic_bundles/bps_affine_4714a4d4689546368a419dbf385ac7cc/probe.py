"""CPU-only supplemental geometry audit; never modify training artifacts."""
import argparse
import ast
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "2"

import numpy as np
import torch
import torch_scatter

torch.set_num_threads(2)

PACKAGE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps"
DATASET_SHA = "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
SUPPORT_SHA = "18e2a35e3df74c2823b2af36457dbbb7944c3b3697616f480b234d172797ce74"
CATALOG_SHA = "9ddcddeff3629c50c50054a9eaadb0828f5dfcb8541defd16705341c0dc567f2"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native_methods(path):
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "ScanNetDataset_sample_graph_edge")
    names = {"data_aug", "get_sp_label", "get_ref_mask"}
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)
               and n.name in names]
    assert {n.name for n in methods} == names
    module = ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[]))
    env = dict(np=np, torch=torch, torch_scatter=torch_scatter, math=math)
    exec(compile(module, str(path), "exec"), env)
    return env


def columns(support):
    result = {}
    for cost, descriptors in zip(support["costs"], support["pairs"]):
        assert cost.shape[1] == len(descriptors)
        for index, descriptor in enumerate(descriptors):
            key = tuple(descriptor[k] for k in ("left_node", "right_node", "a", "b"))
            if key in result:
                assert torch.equal(result[key], cost[:, index])
            result[key] = cost[:, index]
    return result


def compare(first, second, gt):
    left, right = columns(first), columns(second)
    matched = sorted(left.keys() & right.keys())
    if not matched:
        return dict(matched_columns=0, removed_columns=len(left.keys() - right.keys()),
                    added_columns=len(right.keys() - left.keys()), field_max_abs_delta=None,
                    gt_expectation_max_abs_delta=None, pass1e6=None)
    counts = first["counts"]
    weight = gt.double() * counts
    weight = weight / weight.sum().clamp_min(1)
    field_delta = max((float((left[k] - right[k]).abs().max()) for k in matched),
                      default=0.0)
    gt_delta = max((float(((left[k] - right[k]) * weight).sum().abs())
                    for k in matched), default=0.0)
    return dict(matched_columns=len(matched), removed_columns=len(left.keys() - right.keys()),
                added_columns=len(right.keys() - left.keys()), field_max_abs_delta=field_delta,
                gt_expectation_max_abs_delta=gt_delta,
                pass1e6=not (left.keys() ^ right.keys()) and field_delta <= 1e-6)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    root, data = Path(args.code_root), Path(args.data_root)
    dataset = root / "framework/dataset/scannetv2.py"
    support_path = root / "framework/model/Quard_model" / PACKAGE / "between_support.py"
    assert digest(dataset) == DATASET_SHA
    assert digest(support_path) == SUPPORT_SHA
    assert digest(args.catalog) == CATALOG_SHA
    functions = native_methods(dataset)
    spec = importlib.util.spec_from_file_location("bps_affine_native_support", support_path)
    support_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support_module)
    selected = json.loads(Path(args.selection).read_text())["cases"]
    annotations = json.loads((data / "scanrefer/ScanRefer_train_new.json").read_text())
    annotation_by_key = {(r["scene_id"], int(r["ann_id"])): r for r in annotations}
    np.random.seed(1999)
    rows, raw_hashes, matrices = [], {}, {}
    for scene in sorted({case["scene"] for case in selected}):
        scene_cases = sorted((case for case in selected if case["scene"] == scene),
                             key=lambda case: case["ann_id"])
        raw_file = data / "scannetv2/train" / (scene + "_refer.pth")
        raw_hashes[scene] = digest(raw_file)
        xyz, rgb, sp_raw, semantic, instance = torch.load(raw_file, map_location="cpu",
                                                        weights_only=False)
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
            objects.append(list(map(int, annotation.get("object_ids",
                               [int(annotation.get("object_id", -1))]))))
        gt_masks = [functions["get_ref_mask"](None, None, instance, sp, obj)[1]
                    for obj in objects]
        matrix = functions["data_aug"](None, np.eye(3), True, True, True)
        u, singular, vh = np.linalg.svd(matrix)
        conformal = (u @ vh) * float(np.sqrt(np.mean(singular ** 2)))
        matrices[scene] = dict(native=matrix.tolist(), conformal=conformal.tolist(),
                               singular_values=singular.tolist(), points=len(xyz),
                               supports=len(labels), expressions=len(ann_ids))
        for precision in ("native_float32", "auxiliary_float64"):
            dtype = torch.float32 if precision == "native_float32" else torch.float64
            catalog = support_module.BetweenSupportCatalog(args.catalog, CATALOG_SHA)
            coords = torch.as_tensor(xyz, dtype=dtype)
            original_coords = coords.clone()
            offsets = torch.tensor([0, len(labels)])

            def prepare(value):
                return catalog.prepare(ann_ids, [scene], [len(ann_ids)], objects,
                                       sp, value, offsets, [labels])

            baseline = prepare(coords)
            native = prepare(torch.as_tensor(xyz @ matrix, dtype=dtype))
            control = prepare(torch.as_tensor(xyz @ conformal, dtype=dtype))
            restored = prepare(coords)
            assert torch.equal(coords, original_coords)
            for i, aid in enumerate(ann_ids):
                repeat = compare(baseline[i], restored[i], gt_masks[i])
                assert repeat["field_max_abs_delta"] in (None, 0)
                assert repeat["added_columns"] == repeat["removed_columns"] == 0
                row = dict(scene=scene, ann_id=aid, precision=precision,
                           available_events=len(baseline[i]["costs"]),
                           native_affine=compare(baseline[i], native[i], gt_masks[i]),
                           conformal_control=compare(baseline[i], control[i], gt_masks[i]),
                           repeat_exact=True, input_restored_exact=True)
                rows.append(row)
        print("completed " + scene, flush=True)
    results = dict(token=args.token, remote_observed_at=datetime.datetime.now(
                   datetime.timezone.utc).isoformat(), script_sha256=digest(__file__),
                   dataset_sha256=DATASET_SHA, support_sha256=SUPPORT_SHA,
                   catalog_sha256=CATALOG_SHA, selection_sha256=digest(args.selection),
                   raw_file_sha256=raw_hashes, matrices=matrices, rows=rows,
                   scope="Raw TRAIN geometry plus exact native methods; no collated "
                         "model input, native model forward, optimizer, task harm or efficacy.",
                   cuda_visible_devices=os.environ["CUDA_VISIBLE_DEVICES"],
                   cpu_threads=torch.get_num_threads())
    destination = Path(args.output)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(results, indent=2) + "\n")
    temporary.replace(destination)
    print(json.dumps(dict(rows=len(rows), scenes=len(raw_hashes), output=str(destination),
                          sha256=digest(destination))), flush=True)


if __name__ == "__main__":
    main()
