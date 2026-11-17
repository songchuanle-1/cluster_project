"""Matched min-placement intervention on all eligible physical masks."""
import argparse
from collections import defaultdict
import datetime
import importlib.util
import json
import os
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "2"
import numpy as np
import torch

torch.set_num_threads(2)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--population", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    helper = load("frozen_population_helpers", Path(__file__).parent / "probe.py")
    assert helper.digest(Path(__file__).parent / "probe.py") == (
        "a9fa39e9ca705e038fb525b909492181e6ceee9b7f42d6ac3c5841354c2fbbd0")
    assert helper.digest(args.population) == (
        "e930143cfd9476c6336ba4f0a89278a86280d6d15d70450c1de30c7bb73a01c5")
    population = json.loads(Path(args.population).read_text())
    assert population["complete"]
    chosen = [r for r in population["rows"] if r["status"] == "physical_masks_evaluated"]
    assert len(chosen) == 49
    grouped = defaultdict(list)
    for row in chosen:
        grouped[row["scene"]].append(row)
    root, data = Path(args.code_root), Path(args.data_root)
    dataset = root / "framework/dataset/scannetv2.py"
    assert helper.digest(dataset) == helper.DATASET_SHA
    methods = helper.native_methods(dataset)
    support_path = root / "framework/model/Quard_model" / (
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps/between_support.py")
    assert helper.digest(support_path) == helper.SUPPORT_SHA
    native = load("population_coherence_native", support_path)
    catalog = native.BetweenSupportCatalog(args.catalog, helper.CATALOG_SHA)
    fixed = catalog.catalog
    rows = []
    for scene in sorted(grouped):
        expression_rows = sorted(grouped[scene], key=lambda row: row["ann_id"])
        path = data / "scannetv2/train" / (scene + "_refer.pth")
        assert helper.digest(path) == fixed["raw_scene_sha256"][scene]
        xyz, rgb, sp_raw, semantic, instance = torch.load(
            path, map_location="cpu", weights_only=False)
        _, sp = np.unique(np.asarray(sp_raw), return_inverse=True)
        sp = torch.as_tensor(sp, dtype=torch.long)
        instance = torch.as_tensor(np.asarray(instance), dtype=torch.long)
        semantic = torch.as_tensor(np.asarray(semantic), dtype=torch.long)
        labels, _ = methods["get_sp_label"](None, sp, instance, semantic)
        ann_ids = [row["ann_id"] for row in expression_rows]
        objects = [row["target_ids"] for row in expression_rows]
        supports = catalog.prepare(ann_ids, [scene], [len(ann_ids)], objects, sp,
                                   torch.as_tensor(np.asarray(xyz), dtype=torch.float32),
                                   torch.tensor([0, len(labels)]), [labels])
        masks = {}

        def physical(ids):
            key = tuple(sorted(map(int, ids)))
            if key not in masks:
                masks[key] = methods["get_ref_mask"](None, None, instance, sp, list(key))[1]
            return masks[key]

        for i, original in enumerate(expression_rows):
            teacher = physical(original["target_ids"])

            def evaluate(mask, fragmented):
                logits = torch.where(mask > 0, 100.0, -100.0).unsqueeze(0)
                value = native.support_excess(
                    [logits], [{"masks": teacher.unsqueeze(0)}],
                    [(torch.tensor([0]), torch.tensor([0]))], 1, [supports[i]],
                    fragmented=fragmented)
                assert bool(torch.isfinite(value))
                return float(value)

            readouts = []
            for prior in original["physical_readouts"]:
                mask = physical([prior["object_id"]])
                if prior["loss"] is None:
                    assert int(mask.sum()) == 0
                    continue
                coherent, fragmented = evaluate(mask, False), evaluate(mask, True)
                assert coherent == prior["loss"], "Original arm failed exact reproduction"
                readouts.append(dict(object_id=prior["object_id"], coherent=coherent,
                                     fragmented=fragmented, delta=coherent-fragmented))
            rows.append(dict(scene=scene, ann_id=original["ann_id"], readouts=readouts,
                             gt_self_coherent=evaluate(teacher, False),
                             gt_self_fragmented=evaluate(teacher, True)))
        print("completed " + scene, flush=True)
    result = dict(token=args.token, complete=True, remote_observed_at=datetime.datetime.now(
                  datetime.timezone.utc).isoformat(), script_sha256=helper.digest(__file__),
                  population_sha256=helper.digest(args.population), rows=rows,
                  cuda_visible_devices=os.environ["CUDA_VISIBLE_DEVICES"],
                  cpu_threads=torch.get_num_threads(),
                  scope="Same actual physical mask/GT/source inputs; native min-placement "
                        "intervention only. Not model predictions, task benefit or witness labels.")
    destination = Path(args.output)
    helper.save(destination, result)
    print(json.dumps(dict(expressions=len(rows),
                          readouts=sum(len(r["readouts"]) for r in rows),
                          sha256=helper.digest(destination))), flush=True)


if __name__ == "__main__":
    main()
