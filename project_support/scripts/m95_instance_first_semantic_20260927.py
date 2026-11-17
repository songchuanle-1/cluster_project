"""CPU-only frozen native instance/semantic provenance audit."""
import argparse
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ("data-root", "code", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    import torch

    root = args.data_root
    annotations_path = root / "scanrefer/ScanRefer_train_new.json"
    graphs_path = root / "scanrefer/scene_graphs_new_train.json"
    annotations = json.loads(annotations_path.read_text())
    graphs = json.loads(graphs_path.read_text())
    chosen = {}
    for item in annotations:
        scene = item["scene_id"]
        if scene not in chosen or int(item["ann_id"]) < int(chosen[scene]["ann_id"]):
            chosen[scene] = item
    scenes = sorted(chosen)[:64]
    if len(scenes) != 64:
        raise ValueError("Insufficient native TRAIN scenes")
    values = {}
    for node in ast.walk(ast.parse(args.code.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in ("type2class", "sem2nyu"):
                    if target.attr in values:
                        raise ValueError("Duplicate native mapping")
                    values[target.attr] = ast.literal_eval(node.value)
    if set(values) != {"type2class", "sem2nyu"}:
        raise ValueError("Native mapping unavailable")
    type2class = dict(values["type2class"])
    type2class.pop("others")
    sem2nyu = values["sem2nyu"]
    tsv = root / "scannetv2-labels.combined.tsv"
    names = {}
    for line in tsv.read_text().splitlines()[1:]:
        cells = line.split("\t")
        nyu = int(cells[4])
        names.setdefault(nyu, set()).add(cells[7])
    def context_class(semantic):
        if semantic < 0 or semantic >= len(sem2nyu):
            return None
        nyu = sem2nyu[semantic]
        labels = names.get(nyu, set())
        classes = {type2class.get(name) for name in labels}
        return next(iter(classes)) if len(classes) == 1 else None

    totals = Counter()
    rows = []
    inputs = []
    for scene in scenes:
        path = root / "scannetv2/train" / (scene + "_refer.pth")
        data = torch.load(path, map_location="cpu", weights_only=False)
        if len(data) != 5:
            raise ValueError(f"Scene schema differs: {scene}")
        semantic = np.asarray(data[3])
        instance = np.asarray(data[4])
        if semantic.shape != instance.shape:
            raise ValueError(f"Label shape differs: {scene}")
        ann = chosen[scene]
        graph = graphs[scene][str(ann["ann_id"])]
        utterance = " ".join(graph["utterance"].replace(",", " ,").split()) + " . not mentioned"
        classes = {type2class[word] for word in utterance.split() if word in type2class}
        target = {int(x) for x in ann.get("object_ids", [ann.get("object_id")])}
        counts = {}
        first = {}
        for semantic_id, instance_id in zip(semantic, instance):
            key = int(instance_id)
            counts.setdefault(key, Counter())[int(semantic_id)] += 1
            first.setdefault(key, int(semantic_id))
        summary = Counter()
        examples = []
        for instance_id, count in counts.items():
            n = sum(count.values())
            if instance_id < 0 or n < 5:
                continue
            totals["eligible_instances"] += 1
            summary["eligible_instances"] += 1
            majority, majority_n = count.most_common(1)[0]
            if majority_n * 2 <= n:
                totals["no_strict_majority"] += 1
                continue
            if len(count) > 1:
                totals["mixed_instances"] += 1
            mismatch = first[instance_id] != majority
            flip = ((context_class(first[instance_id]) in classes)
                    != (context_class(majority) in classes))
            referred = instance_id in target
            arm = "target" if referred else "nontarget"
            totals[arm + "_eligible"] += 1
            if mismatch:
                totals[arm + "_mismatch"] += 1
                summary[arm + "_mismatch"] += 1
            if mismatch and flip:
                totals[arm + "_context_flip"] += 1
                summary[arm + "_context_flip"] += 1
                examples.append({
                    "instance": instance_id, "points": n, "first": first[instance_id],
                    "majority": majority, "first_class": context_class(first[instance_id]),
                    "majority_class": context_class(majority), "referred": referred,
                })
        rows.append({"scene": scene, "ann_id": int(ann["ann_id"]), "summary": dict(summary),
                     "context_flip_examples": examples})
        inputs.append({"scene": scene, "sha256": sha(path)})
    result = {
        "contract": "m95_instance_first_semantic_v1", "admission": False,
        "input_sha256": {"annotations": sha(annotations_path), "graphs": sha(graphs_path),
                         "labels": sha(tsv), "dataset_code": sha(args.code)},
        "scene_inputs": inputs, "totals": dict(totals), "rows": rows,
        "limits": "CPU native TRAIN data-path screen; no inference mechanism or training efficacy.",
    }
    if args.output.exists():
        raise ValueError("Output exists")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
