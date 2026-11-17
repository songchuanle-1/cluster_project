"""Native TRAIN same-physical-instance context-label control availability."""
import argparse
import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
    assign = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in ("type2class", "sem2nyu"):
                    assign[target.attr] = ast.literal_eval(node.value)
    if set(assign) != {"type2class", "sem2nyu"} or args.output.exists():
        raise ValueError("Native source contract or output differs")
    keys = assign["type2class"]
    nyu = assign["sem2nyu"]
    nyu_ids = {3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
               21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40}
    mapping = {}
    for line in tsv_path.read_text().splitlines()[1:]:
        cells = line.split("\t")
        if int(cells[4]) in nyu_ids:
            mapping[int(cells[4])] = keys.get(cells[7], keys["others"])
    annotations = defaultdict(list)
    for a in json.loads(ann_path.read_text()):
        annotations[a["scene_id"]].append(a)
    graphs = json.loads(graph_path.read_text())
    scenes = sorted(annotations)[:64]
    if len(scenes) != 64:
        raise ValueError("Frozen cohort differs")
    total_instances = eligible = toggles = no_class_on = 0
    examples = []
    per_scene = []
    for scene in scenes:
        path = root / "scannetv2/train" / (scene + "_refer.pth")
        data = torch.load(path, map_location="cpu", weights_only=False)
        if len(data) != 5:
            raise ValueError("Native physical schema differs")
        semantic = np.asarray(data[3], dtype=int)
        instance = np.asarray(data[4], dtype=int)
        if semantic.shape != instance.shape:
            raise ValueError("Native label axis differs")
        ann_rows = []
        for a in annotations[scene]:
            graph = graphs[scene][str(a["ann_id"])]
            text = " ".join(graph["utterance"].replace(",", " ,").split()) + " . not mentioned"
            cls = {keys[w] for w in text.split() if w in keys and w != "others"}
            targets = {int(x) for x in a.get("object_ids", [a.get("object_id")])}
            ann_rows.append((int(a["ann_id"]), targets, cls))
        scene_eligible = scene_toggles = 0
        for iid in np.unique(instance):
            if iid < 0:
                continue
            indices = np.flatnonzero(instance == iid)
            if len(indices) < 5:
                continue
            total_instances += 1
            s = int(semantic[indices[0]])
            cls = mapping.get(nyu[s]) if 0 <= s < len(nyu) else None
            rows = [(ann_id, cls in classes) for ann_id, targets, classes in ann_rows if iid not in targets]
            if len(rows) < 2:
                continue
            if cls is None or cls == keys["others"]:
                no_class_on += sum(on for _, on in rows)
                continue
            eligible += 1
            scene_eligible += 1
            on = [ann for ann, yes in rows if yes]
            off = [ann for ann, yes in rows if not yes]
            if on and off:
                toggles += 1
                scene_toggles += 1
                if len(examples) < 12:
                    examples.append({"scene": scene, "instance": int(iid), "class_id": cls,
                                     "context_on_ann": on[0], "context_off_ann": off[0],
                                     "on_count": len(on), "off_count": len(off)})
        per_scene.append({"scene": scene, "sha256": sha(path),
                          "eligible": scene_eligible, "toggles": scene_toggles})
    result = {"contract": "m95_context_instance_toggle_v1", "admission": False,
              "sources": {"annotations": sha(ann_path), "graphs": sha(graph_path),
                          "dataset": sha(args.dataset_source), "tsv": sha(tsv_path)},
              "summary": {"scenes": len(scenes), "instances_ge5": total_instances,
                          "eligible_non_target_instances": eligible, "toggles": toggles,
                          "toggle_scenes": sum(r["toggles"] > 0 for r in per_scene),
                          "no_class_context_on": no_class_on},
              "examples": examples, "scenes": per_scene,
              "limits": "Same physical instance across different expressions; not same-input native FPS or causal loss control."}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
