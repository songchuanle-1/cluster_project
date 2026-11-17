"""Full TRAIN physical scope of the unreachable shower-curtain key."""
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
    p.add_argument("--first64", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    import numpy as np
    import torch
    if args.output.exists():
        raise ValueError("Output exists")
    first = json.loads(args.first64.read_text())
    if (first["contract"] != "m95_multiword_context_v1"
            or sha(args.first64) !=
            "331718c7181f176197502e74ea0cf271025096cc0bd9c464348c8944674caaf0"):
        raise ValueError("Frozen 64-scene audit differs")
    root = args.data_root
    ann_path = root / "scanrefer/ScanRefer_train_new.json"
    graph_path = root / "scanrefer/scene_graphs_new_train.json"
    label_path = root / "scannetv2-labels.combined.tsv"
    source = args.dataset_source.read_text()
    actual = {"annotations": sha(ann_path), "graphs": sha(graph_path),
              "dataset_source": sha(args.dataset_source), "labels": sha(label_path)}
    if actual != first["inputs"] or "for word in lang_utterance.split():" not in source:
        raise ValueError("Native source inputs differ")
    values = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in ("type2class", "sem2nyu"):
                    values[target.attr] = ast.literal_eval(node.value)
    keys, sem2nyu = values["type2class"], values["sem2nyu"]
    nyu40ids = {3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40}
    nyu_to_class = {}
    for line in label_path.read_text().splitlines()[1:]:
        cells = line.split("\t")
        nyu = int(cells[4])
        if nyu in nyu40ids:
            nyu_to_class[nyu] = keys.get(cells[7], keys["others"])
    anns = defaultdict(list)
    all_annotations = json.loads(ann_path.read_text())
    for row in all_annotations:
        anns[row["scene_id"]].append(row)
    graphs = json.loads(graph_path.read_text())
    phrase_rows = defaultdict(list)
    for scene, rows in anns.items():
        for ann in rows:
            aid = int(ann["ann_id"])
            text = (" ".join(graphs[scene][str(aid)]["utterance"]
                             .replace(",", " ,").split()) + " . not mentioned")
            tokens = text.split()
            if any(tokens[i:i + 2] == ["shower", "curtain"]
                   for i in range(len(tokens) - 1)):
                phrase_rows[scene].append(ann)
    output = []
    physical_hashes = {}
    for scene in sorted(phrase_rows):
        path = root / "scannetv2/train" / (scene + "_refer.pth")
        data = torch.load(path, map_location="cpu", weights_only=False)
        if len(data) != 5:
            raise ValueError("Physical scene schema differs")
        sp, sem, ins = [np.asarray(x, dtype=np.int64) for x in data[2:]]
        if not np.array_equal(np.unique(sp), np.arange(sp.max() + 1)):
            raise ValueError("Noncontiguous superpoints")
        counts = np.bincount(sp)
        physical_hashes[scene] = sha(path)
        curtains = []
        for iid in np.unique(ins):
            idx = np.flatnonzero(ins == iid)
            label = int(sem[idx[0]])
            if label < 0:
                continue
            if label >= len(sem2nyu):
                raise ValueError("Semantic label out of range")
            nyu = sem2nyu[label]
            if nyu in nyu40ids and nyu_to_class[nyu] == keys["shower curtain"]:
                curtains.append(int(iid))
        for ann in phrase_rows[scene]:
            targets = {int(x) for x in ann.get("object_ids", [ann.get("object_id")])}
            if None in targets:
                raise ValueError("Missing target")
            other = [iid for iid in curtains if iid not in targets]
            changed = (np.bincount(sp, weights=np.isin(ins, other), minlength=len(counts))
                       if other else np.zeros(len(counts)))
            output.append({
                "scene": scene, "ann_id": int(ann["ann_id"]),
                "target_instances": sorted(targets),
                "other_curtain_instances": other,
                "target_is_curtain": any(iid in targets for iid in curtains),
                "changed_rows": int((changed > 0).sum()),
            })
    first_scenes = set(sorted(anns)[:64])
    first_rows = [r for r in output if r["scene"] in first_scenes]
    overlap = {
        "phrase_expressions": len(first_rows),
        "qualifying_expressions": sum(bool(r["other_curtain_instances"]) for r in first_rows),
        "changed_superpoint_rows_repeated": sum(r["changed_rows"] for r in first_rows),
    }
    if any(overlap[k] != first["summary"][k] for k in overlap):
        raise ValueError("Frozen 64-scene parity check failed")
    exposed = [r for r in output if r["other_curtain_instances"]]
    summary = {
        "train_scenes": len(anns), "train_annotations": len(all_annotations),
        "phrase_scenes": len(phrase_rows), "phrase_expressions": len(output),
        "target_curtain_expressions": sum(r["target_is_curtain"] for r in output),
        "qualifying_scenes": len({r["scene"] for r in exposed}),
        "qualifying_expressions": len(exposed),
        "physical_nontarget_curtain_instances": len({
            (r["scene"], iid) for r in exposed for iid in r["other_curtain_instances"]}),
        "changed_superpoint_rows_repeated": sum(r["changed_rows"] for r in exposed),
    }
    result = {"contract": "m95_multiword_population_v1", "admission": False,
              "inputs": actual, "first64_sha256": sha(args.first64),
              "first64_overlap": overlap, "physical_sha256": physical_hashes,
              "summary": summary, "rows": output,
              "limits": "TRAIN physical source scope, no native model outcome, causal loss intervention or admission."}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
