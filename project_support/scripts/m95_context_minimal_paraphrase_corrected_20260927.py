"""Exact one-class-token contrast among fixed-target TRAIN descriptions."""
import argparse
import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def one_class_token_pair(a, b, keys):
    if abs(len(a) - len(b)) != 1:
        return None
    shorter, longer = (a, b) if len(a) < len(b) else (b, a)
    for i, token in enumerate(longer):
        if token in keys and longer[:i] + longer[i + 1:] == shorter:
            return token
    return None


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
    graph_path = root / "scanrefer/scene_graphs_new_train.json"
    tsv_path = root / "scannetv2-labels.combined.tsv"
    source = args.dataset_source.read_text()
    assignment = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in ("type2class", "sem2nyu"):
                    assignment[target.attr] = ast.literal_eval(node.value)
    if set(assignment) != {"type2class", "sem2nyu"} or args.output.exists():
        raise ValueError("Native source contract or output differs")
    classes, sem2nyu = assignment["type2class"], assignment["sem2nyu"]
    nyu_ids = {3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
               21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40}
    nyu_to_class = {}
    for line in tsv_path.read_text().splitlines()[1:]:
        cells = line.split("\t")
        n = int(cells[4])
        if n in nyu_ids:
            nyu_to_class[n] = classes.get(cells[7], classes["others"])
    anns = defaultdict(list)
    for a in json.loads(ann_path.read_text()):
        anns[a["scene_id"]].append(a)
    graphs = json.loads(graph_path.read_text())
    scenes = sorted(anns)[:64]
    if len(scenes) != 64:
        raise ValueError("Frozen scene cohort differs")
    same_target_pairs = 0
    one_token_pairs = 0
    switch_units = set()
    examples = []
    physical_hashes = {}
    for scene in scenes:
        physical = root / "scannetv2/train" / (scene + "_refer.pth")
        data = torch.load(physical, map_location="cpu", weights_only=False)
        if len(data) != 5:
            raise ValueError("Native scene schema differs")
        sem, ins = np.asarray(data[3]), np.asarray(data[4])
        physical_hashes[scene] = sha(physical)
        instances = {}
        for iid in np.unique(ins):
            if iid < 0:
                continue
            idx = np.flatnonzero(ins == iid)
            if len(idx) < 5:
                continue
            semantic = int(sem[idx[0]])
            if 0 <= semantic < len(sem2nyu):
                cls = nyu_to_class.get(sem2nyu[semantic])
                if cls is not None and cls != classes["others"]:
                    instances[int(iid)] = cls
        groups = defaultdict(list)
        for ann in anns[scene]:
            target = tuple(sorted(int(x) for x in ann.get("object_ids", [ann.get("object_id")])))
            text = " ".join(graphs[scene][str(ann["ann_id"])]["utterance"].replace(",", " ,").split()) + " . not mentioned"
            groups[target].append((int(ann["ann_id"]), text.split()))
        for target, rows in groups.items():
            for i, left in enumerate(rows):
                for right in rows[i + 1:]:
                    same_target_pairs += 1
                    token = one_class_token_pair(left[1], right[1], set(classes) - {"others"})
                    if token is None:
                        continue
                    one_token_pairs += 1
                    for iid, cls in instances.items():
                        if iid in target or cls != classes[token]:
                            continue
                        if (cls in {classes[w] for w in left[1] if w in classes and w != "others"}) == (
                                cls in {classes[w] for w in right[1] if w in classes and w != "others"}):
                            continue
                        key = (scene, target, iid, left[0], right[0])
                        switch_units.add(key)
                        if len(examples) < 12:
                            examples.append({"scene": scene, "target": target,
                                             "instance": iid, "token": token,
                                             "annotations": [left[0], right[0]]})
    result = {
        "contract": "m95_context_minimal_paraphrase_v1", "admission": False,
        "input_sha256": {"annotations": sha(ann_path), "graphs": sha(graph_path),
                         "labels": sha(tsv_path), "dataset_source": sha(args.dataset_source),
                         "physical": physical_hashes},
        "summary": {"scenes": len(scenes), "same_target_annotation_pairs": same_target_pairs,
                    "one_class_token_pairs": one_token_pairs,
                    "context_switch_units": len(switch_units),
                    "context_switch_scenes": len({k[0] for k in switch_units})},
        "examples": examples,
        "limits": "Strict lexical minimal pairs only; no native transformed-input or training inference.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
