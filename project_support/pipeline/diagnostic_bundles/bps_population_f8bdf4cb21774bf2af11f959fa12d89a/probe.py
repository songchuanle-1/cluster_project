"""Audit fixed TRAIN ideal physical-mask readouts without model execution."""
import argparse
import ast
from collections import Counter, defaultdict
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

DATASET_SHA = "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
SUPPORT_SHA = "18e2a35e3df74c2823b2af36457dbbb7944c3b3697616f480b234d172797ce74"
CATALOG_SHA = "9ddcddeff3629c50c50054a9eaadb0828f5dfcb8541defd16705341c0dc567f2"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native_methods(path):
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "ScanNetDataset_sample_graph_edge")
    names = {"get_sp_label", "get_ref_mask"}
    nodes = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == names
    env = dict(np=np, torch=torch, torch_scatter=torch_scatter, math=math)
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, str(path), "exec"), env)
    return env


def save(path, payload):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    root, data = Path(args.code_root), Path(args.data_root)
    source = root / "framework/dataset/scannetv2.py"
    support_path = root / "framework/model/Quard_model" / (
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps/between_support.py")
    assert digest(source) == DATASET_SHA
    assert digest(support_path) == SUPPORT_SHA
    assert digest(args.catalog) == CATALOG_SHA
    methods = native_methods(source)
    spec = importlib.util.spec_from_file_location("native_population_bps", support_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    catalog = module.BetweenSupportCatalog(args.catalog, CATALOG_SHA)
    fixed = catalog.catalog
    grouped = defaultdict(list)
    for key, record in fixed["records"].items():
        scene, aid = key.split("/")
        grouped[scene].append((int(aid), record))
    assert len(grouped) == 416
    assert sum(len(group) for group in grouped.values()) == 1498
    rows, scenes, counts = [], [], Counter()
    outfile = Path(args.output)

    def payload(complete):
        return dict(token=args.token, complete=complete,
                    remote_observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    script_sha256=digest(__file__), dataset_sha256=DATASET_SHA,
                    support_sha256=SUPPORT_SHA, catalog_sha256=CATALOG_SHA,
                    planned_scenes=len(grouped), planned_expressions=1498,
                    counts=dict(counts), scenes=scenes, rows=rows,
                    cuda_visible_devices=os.environ["CUDA_VISIBLE_DEVICES"],
                    cpu_threads=torch.get_num_threads(),
                    scope="Unaugmented raw TRAIN geometry with ideal native physical masks; "
                          "not model logits, native full forward/backward, task harm or efficacy.")

    for scene in sorted(grouped):
        records = sorted(grouped[scene], key=lambda row: row[0])
        raw_file = data / "scannetv2/train" / (scene + "_refer.pth")
        raw_sha = digest(raw_file)
        assert raw_sha == fixed["raw_scene_sha256"][scene]
        xyz, rgb, sp_raw, semantic, instance = torch.load(
            raw_file, weights_only=False, map_location="cpu")
        _, sp = np.unique(np.asarray(sp_raw), return_inverse=True)
        sp = torch.as_tensor(sp, dtype=torch.long)
        instance = torch.as_tensor(np.asarray(instance), dtype=torch.long)
        semantic = torch.as_tensor(np.asarray(semantic), dtype=torch.long)
        labels, _ = methods["get_sp_label"](None, sp, instance, semantic)
        coords = torch.as_tensor(np.asarray(xyz), dtype=torch.float32)
        offsets = torch.tensor([0, len(labels)])
        ann_ids = [aid for aid, record in records]
        objects = [record["target_ids"] for aid, record in records]
        supports = catalog.prepare(ann_ids, [scene], [len(records)], objects,
                                   sp, coords, offsets, [labels])
        physical_mask_cache = {}

        def physical_mask(ids):
            key = tuple(sorted(map(int, ids)))
            if key not in physical_mask_cache:
                physical_mask_cache[key] = methods["get_ref_mask"](
                    None, None, instance, sp, list(key))[1]
            return physical_mask_cache[key]

        categories = fixed["instances"][scene]
        scene_counts = Counter()
        for i, (aid, record) in enumerate(records):
            support = supports[i]
            teacher = physical_mask(record["target_ids"])
            scene_counts["expressions"] += 1
            scene_counts["events"] += len(record["events"])
            scene_counts["available_events"] += len(support["costs"])
            row = dict(scene=scene, ann_id=aid, target_ids=record["target_ids"],
                       events=len(record["events"]), available_events=len(support["costs"]),
                       unknowns=support["unknowns"], native_gt_positive_supports=int(teacher.sum()),
                       status="geometry_unavailable", physical_readouts=[])
            if not support["costs"]:
                scene_counts["geometry_unavailable_expressions"] += 1
                rows.append(row)
                continue
            scene_counts["geometry_available_expressions"] += 1
            if not bool(teacher.sum() > 0):
                row["status"] = "empty_original_gt"
                scene_counts["empty_original_gt"] += 1
                rows.append(row)
                continue

            def loss(mask):
                logits = torch.where(mask > 0, 100.0, -100.0).unsqueeze(0)
                value = module.support_excess(
                    [logits], [{"masks": teacher.unsqueeze(0)}],
                    [(torch.tensor([0]), torch.tensor([0]))], 1, [support])
                assert bool(torch.isfinite(value))
                return float(value)

            self_loss = loss(teacher)
            row["gt_self_loss"] = self_loss
            scene_counts["gt_self_checked"] += 1
            scene_counts["gt_self_nonzero"] += self_loss != 0
            target_classes = {categories.get(str(oid)) for oid in record["target_ids"]}
            target_classes.discard(None)
            if not target_classes:
                row["status"] = "unknown_target_category"
                scene_counts["unknown_target_category"] += 1
                rows.append(row)
                continue
            alternatives = sorted(int(oid) for oid, category in categories.items()
                                  if category in target_classes and int(oid) not in record["target_ids"])
            if not alternatives:
                row["status"] = "no_same_class_alternative"
                scene_counts["no_same_class_alternative"] += 1
                rows.append(row)
                continue
            row["status"] = "physical_masks_evaluated"
            nonempty = 0
            for oid in alternatives:
                mask = physical_mask([oid])
                positive = int(mask.sum())
                if not positive:
                    scene_counts["empty_alternative_masks"] += 1
                    row["physical_readouts"].append(dict(object_id=oid, supports=0, loss=None))
                    continue
                nonempty += 1
                value = loss(mask)
                row["physical_readouts"].append(dict(object_id=oid, supports=positive, loss=value))
                scene_counts["nonempty_alternative_readouts"] += 1
                scene_counts["exact_zero_alternative_losses"] += value == 0
                scene_counts["nonzero_alternative_losses"] += value != 0
                scene_counts["alternative_losses_above1e6"] += value > 1e-6
            if nonempty:
                scene_counts["expressions_with_nonempty_alternatives"] += 1
            else:
                scene_counts["expressions_without_nonempty_alternatives"] += 1
            rows.append(row)
        counts.update(scene_counts)
        scenes.append(dict(scene=scene, raw_sha256=raw_sha, points=len(coords),
                           supports=len(labels), counts=dict(scene_counts),
                           native_prepare_work=catalog.last_work))
        counts["scenes_completed"] += 1
        if len(scenes) % 20 == 0:
            save(outfile, payload(False))
            print(json.dumps(dict(scenes_completed=len(scenes), counts=dict(counts))), flush=True)
    assert counts["expressions"] == 1498 and counts["events"] == 1502
    save(outfile, payload(True))
    print(json.dumps(dict(complete=True, counts=dict(counts), sha256=digest(outfile))), flush=True)


if __name__ == "__main__":
    main()
