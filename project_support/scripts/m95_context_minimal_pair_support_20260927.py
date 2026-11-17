"""Physical superpoint support for one preregistered context minimal pair."""
import argparse
import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--dataset-source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    import numpy as np
    import torch

    root = args.data_root
    ann_path = root / "scanrefer/ScanRefer_train_new.json"
    graphs_path = root / "scanrefer/scene_graphs_new_train.json"
    tsv_path = root / "scannetv2-labels.combined.tsv"
    scene_path = root / "scannetv2/train/scene0035_00_refer.pth"
    assignments = {}
    source = args.dataset_source.read_text()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in ("type2class", "sem2nyu"):
                    assignments[target.attr] = ast.literal_eval(node.value)
    if set(assignments) != {"type2class", "sem2nyu"} or args.output.exists():
        raise ValueError("Native source contract or output differs")
    keys, sem2nyu = assignments["type2class"], assignments["sem2nyu"]
    nyu_ids = {3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
               21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40}
    nyu_to_class = {}
    for line in tsv_path.read_text().splitlines()[1:]:
        cells = line.split("\t")
        nyu = int(cells[4])
        if nyu in nyu_ids:
            nyu_to_class[nyu] = keys.get(cells[7], keys["others"])
    graph = json.loads(graphs_path.read_text())["scene0035_00"]
    annotations = [a for a in json.loads(ann_path.read_text())
                   if a["scene_id"] == "scene0035_00" and int(a["ann_id"]) in (21, 31)]
    if len(annotations) != 2 or any(
            tuple(sorted(int(x) for x in a.get("object_ids", [a.get("object_id")]))) != (9,)
            for a in annotations):
        raise ValueError("Frozen target identity differs")
    data = torch.load(scene_path, map_location="cpu", weights_only=False)
    if len(data) != 5:
        raise ValueError("Native physical schema differs")
    sp, sem, ins = [np.asarray(x, dtype=int) for x in data[2:]]
    nsp = int(sp.max()) + 1
    if not np.array_equal(np.unique(sp), np.arange(nsp)):
        raise ValueError("Superpoint axis differs")
    counts = np.bincount(sp, minlength=nsp)
    physical_classes = {}
    for iid in np.unique(ins):
        idx = np.flatnonzero(ins == iid)
        first = int(sem[idx[0]])
        if first < 0:
            continue
        if first >= len(sem2nyu):
            raise ValueError("Semantic class out of range")
        nyu = sem2nyu[first]
        if nyu in nyu_ids:
            physical_classes[int(iid)] = nyu_to_class[nyu]
    if physical_classes.get(3) != keys["desk"]:
        raise ValueError("Preregistered physical instance class differs")
    support = {}
    texts = {}
    for a in annotations:
        ann = int(a["ann_id"])
        text = " ".join(graph[str(ann)]["utterance"].replace(",", " ,").split()) + " . not mentioned"
        classes = {keys[w] for w in text.split() if w in keys and w != "others"}
        context = np.isin(ins, [iid for iid, cls in physical_classes.items() if cls in classes])
        soft = context.astype(float) * 0.5
        soft[ins == 9] = 1
        support[ann] = np.bincount(sp, weights=soft, minlength=nsp) / counts
        texts[ann] = text
    tokens21, tokens31 = texts[21].split(), texts[31].split()
    shorter, longer = (tokens21, tokens31) if len(tokens21) < len(tokens31) else (tokens31, tokens21)
    if len(longer) - len(shorter) != 1 or not any(
            token == "desk" and longer[:i] + longer[i + 1:] == shorter
            for i, token in enumerate(longer)):
        raise ValueError("Pair no longer strict minimal contrast")
    on, off = (21, 31) if "desk" in tokens21 else (31, 21)
    changed = np.flatnonzero(np.abs(support[on] - support[off]) > 1e-7)
    target_rows = np.flatnonzero(np.bincount(sp, weights=(ins == 9), minlength=nsp) > 0)
    other_rows = np.flatnonzero(np.bincount(sp, weights=(ins == 3), minlength=nsp) > 0)
    result = {
        "contract": "m95_context_minimal_pair_support_v1", "admission": False,
        "input_sha256": {"annotations": sha(ann_path), "graphs": sha(graphs_path),
                         "labels": sha(tsv_path), "dataset": sha(args.dataset_source),
                         "scene": sha(scene_path)},
        "identity": {"scene": "scene0035_00", "target": 9, "other_instance": 3,
                     "on_ann": on, "off_ann": off, "on_text": texts[on], "off_text": texts[off]},
        "summary": {
            "points": len(sp), "superpoints": nsp, "other_instance_points": int((ins == 3).sum()),
            "target_instance_points": int((ins == 9).sum()),
            "other_instance_rows": len(other_rows), "target_rows": len(target_rows),
            "changed_rows": len(changed),
            "changed_other_rows": int(np.isin(changed, other_rows).sum()),
            "changed_target_rows": int(np.isin(changed, target_rows).sum()),
            "changed_nonother_rows": int((~np.isin(changed, other_rows)).sum()),
            "other_support_on_mean": float(support[on][other_rows].mean()),
            "other_support_off_mean": float(support[off][other_rows].mean()),
            "max_target_support_difference": float(np.max(np.abs(
                support[on][target_rows] - support[off][target_rows]))),
        },
        "limits": "One strict lexical pair, source-level masks only, no FPS or native loss intervention.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
