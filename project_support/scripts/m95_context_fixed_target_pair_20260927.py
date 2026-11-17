"""Fixed-target same-physical-instance context toggle availability."""
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
    graph_path = root / "scanrefer/scene_graphs_new_train.json"
    tsv_path = root / "scannetv2-labels.combined.tsv"
    source = args.dataset_source.read_text()
    assignments = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in ("type2class", "sem2nyu"):
                    assignments[target.attr] = ast.literal_eval(node.value)
    if set(assignments) != {"type2class", "sem2nyu"} or args.output.exists():
        raise ValueError("Native source or output differs")
    classes = assignments["type2class"]
    sem2nyu = assignments["sem2nyu"]
    nyu_ids = {3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
               21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40}
    nyu_to_class = {}
    for line in tsv_path.read_text().splitlines()[1:]:
        cells = line.split("\t")
        n = int(cells[4])
        if n in nyu_ids:
            nyu_to_class[n] = classes.get(cells[7], classes["others"])
    anns = defaultdict(list)
    for ann in json.loads(ann_path.read_text()):
        anns[ann["scene_id"]].append(ann)
    graphs = json.loads(graph_path.read_text())
    scenes = sorted(anns)[:64]
    if len(scenes) != 64:
        raise ValueError("Frozen scene cohort differs")
    candidates = 0
    toggles = 0
    scenes_toggled = set()
    identical_text_toggles = 0
    examples = []
    physical_hashes = {}
    for scene in scenes:
        path = root / "scannetv2/train" / (scene + "_refer.pth")
        data = torch.load(path, map_location="cpu", weights_only=False)
        if len(data) != 5:
            raise ValueError("Native scene schema differs")
        sem, ins = np.asarray(data[3]), np.asarray(data[4])
        physical_hashes[scene] = sha(path)
        groups = defaultdict(list)
        for ann in anns[scene]:
            targets = tuple(sorted(int(x) for x in ann.get("object_ids", [ann.get("object_id")])))
            graph = graphs[scene][str(ann["ann_id"])]
            text = " ".join(graph["utterance"].replace(",", " ,").split()) + " . not mentioned"
            keys = {classes[w] for w in text.split() if w in classes and w != "others"}
            groups[targets].append((int(ann["ann_id"]), keys, text))
        for iid in np.unique(ins):
            if iid < 0:
                continue
            indices = np.flatnonzero(ins == iid)
            if len(indices) < 5:
                continue
            sem_first = int(sem[indices[0]])
            if not 0 <= sem_first < len(sem2nyu):
                continue
            cls = nyu_to_class.get(sem2nyu[sem_first])
            if cls is None or cls == classes["others"]:
                continue
            for target, expressions in groups.items():
                if iid in target or len(expressions) < 2:
                    continue
                candidates += 1
                on = [x for x in expressions if cls in x[1]]
                off = [x for x in expressions if cls not in x[1]]
                if not on or not off:
                    continue
                toggles += 1
                scenes_toggled.add(scene)
                identical_text_toggles += int(on[0][2] == off[0][2])
                if len(examples) < 12:
                    examples.append({"scene": scene, "target": target, "other_instance": int(iid),
                                     "class_id": cls, "on_ann": on[0][0], "off_ann": off[0][0],
                                     "on": len(on), "off": len(off), "identical_text": on[0][2] == off[0][2]})
    result = {
        "contract": "m95_context_fixed_target_pair_v1", "admission": False,
        "inputs": {"annotations": sha(ann_path), "graphs": sha(graph_path),
                   "labels": sha(tsv_path), "dataset_source": sha(args.dataset_source),
                   "physical": physical_hashes},
        "summary": {"scenes": len(scenes), "eligible_fixed_target_units": candidates,
                    "toggle_units": toggles, "toggle_scenes": len(scenes_toggled),
                    "identical_text_toggle_units": identical_text_toggles},
        "examples": examples,
        "limits": "Target and geometry matched, language differs; source-only feasibility, no native FPS/gradients or efficacy.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
