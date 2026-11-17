"""Prediction-blind physical TRAIN context versus target superpoint audit."""
import argparse
import ast
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--dataset-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    import torch

    root = args.data_root
    annotations = root / "scanrefer/ScanRefer_train_new.json"
    graph_path = root / "scanrefer/scene_graphs_new_train.json"
    label_path = root / "scannetv2-labels.combined.tsv"
    source = args.dataset_source.read_text()
    if not all(s in source for s in ("point_ref_mask[point_context_mask > 0] = 0.5",
                                    "point_ref_mask[instance_label == object_id] = 1",
                                    "sp_ref_mask = torch_scatter.scatter_mean",
                                    "gt_spmask = (gt_spmask > 0.5).float()")):
        raise ValueError("Native target source contract differs")
    values = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in (
                        "type2class", "sem2nyu", "nyu40ids"):
                    values[target.attr] = ast.literal_eval(node.value) if target.attr != "nyu40ids" else None
    if set(values) != {"type2class", "sem2nyu", "nyu40ids"}:
        raise ValueError("Native class mapping missing")
    type2class = values["type2class"]
    sem2nyu = values["sem2nyu"]
    nyu40ids = {3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40}
    if "self.nyu40ids = np.array([3, 4, 5" not in source:
        raise ValueError("Native nyu mapping changed")
    nyu_to_class = {}
    for line in label_path.read_text().splitlines()[1:]:
        cells = line.split("\t")
        nyu = int(cells[4])
        if nyu in nyu40ids:
            nyu_to_class[nyu] = type2class.get(cells[7], type2class["others"])
    anns = defaultdict(list)
    for row in json.loads(annotations.read_text()):
        anns[row["scene_id"]].append(row)
    scenes = sorted(anns)[:64]
    graphs = json.loads(graph_path.read_text())
    if len(scenes) != 64 or args.output.exists():
        raise ValueError("Frozen cohort or output differs")
    totals = Counter()
    rows = []
    for scene in scenes:
        scene_path = root / "scannetv2/train" / (scene + "_refer.pth")
        data = torch.load(scene_path, map_location="cpu", weights_only=False)
        if len(data) != 5:
            raise ValueError("Scene schema differs")
        _, _, sp, sem, ins = [np.asarray(x) for x in data]
        sp = sp.astype(int)
        sem = sem.astype(int)
        ins = ins.astype(int)
        ids = np.unique(sp)
        if not np.array_equal(ids, np.arange(len(ids))):
            raise ValueError("Noncontiguous superpoint IDs")
        nsp = len(ids)
        counts = np.bincount(sp, minlength=nsp)
        if (counts == 0).any():
            raise ValueError("Empty superpoint")
        physical = {}
        for instance_id in np.unique(ins):
            idx = np.flatnonzero(ins == instance_id)
            first = int(sem[idx[0]])
            if first < 0:
                continue
            if first >= len(sem2nyu):
                raise ValueError("Semantic mapping out of range")
            nyu = sem2nyu[first]
            if nyu in nyu40ids:
                physical[int(instance_id)] = nyu_to_class[nyu]
        scene_totals = Counter()
        for ann in anns[scene]:
            target = {int(x) for x in ann.get("object_ids", [ann.get("object_id")])}
            if any(x is None for x in target):
                raise ValueError("Missing target")
            graph = graphs[scene][str(ann["ann_id"])]
            utterance = " ".join(graph["utterance"].replace(",", " ,").split()) + " . not mentioned"
            classes = {type2class[w] for w in utterance.split()
                       if w in type2class and w != "others"}
            target_point = np.isin(ins, list(target))
            context_point = np.isin(ins, [iid for iid, cls in physical.items() if cls in classes])
            target_fraction = np.bincount(sp, weights=target_point, minlength=nsp) / counts
            soft_point = context_point.astype(float) * 0.5
            soft_point[target_point] = 1
            soft = np.bincount(sp, weights=soft_point, minlength=nsp) / counts
            gt = target_fraction > 0.5
            row = Counter({
                "target_rows": int(gt.sum()),
                "nontarget_rows": int((~gt).sum()),
                "target_below_half": int((gt & (soft < 0.5)).sum()),
                "nontarget_at_least_half": int(((~gt) & (soft >= 0.5)).sum()),
                "fractional_target": int((gt & (soft < 1)).sum()),
                "fractional_nontarget": int(((~gt) & (soft > 0) & (soft < 1)).sum()),
                "target_minority": int(((~gt) & (target_fraction > 0)).sum()),
            })
            scene_totals.update(row)
            scene_totals["annotations"] += 1
        totals.update(scene_totals)
        rows.append({"scene": scene, "sha256": sha(scene_path), "counts": dict(scene_totals)})
    result = {"contract": "m95_context_superpoint_v1", "admission": False,
              "inputs": {"annotations": sha(annotations), "graphs": sha(graph_path),
                         "dataset_source": sha(args.dataset_source), "labels": sha(label_path)},
              "totals": dict(totals), "rows": rows,
              "limits": "Native source-reconstructed unaugmented TRAIN targets, not gradients, loss defect, or efficacy."}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
