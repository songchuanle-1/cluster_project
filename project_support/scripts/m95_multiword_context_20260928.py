"""Physical exposure to a whitespace-unreachable class key."""
import argparse
import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--dataset-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    import torch

    if args.output.exists():
        raise ValueError("Output exists")
    source = args.dataset_source.read_text()
    if "for word in lang_utterance.split():" not in source:
        raise ValueError("Exact whitespace membership contract differs")
    assignments = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (isinstance(target, ast.Attribute)
                        and target.attr in ("type2class", "sem2nyu")):
                    assignments[target.attr] = ast.literal_eval(node.value)
    keys = assignments["type2class"]
    sem2nyu = assignments["sem2nyu"]
    if "shower curtain" not in keys:
        raise ValueError("Multiword key missing")
    root = args.data_root
    ann_path = root / "scanrefer/ScanRefer_train_new.json"
    graph_path = root / "scanrefer/scene_graphs_new_train.json"
    tsv_path = root / "scannetv2-labels.combined.tsv"
    nyu40ids = {3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40}
    nyu_to_class = {}
    for line in tsv_path.read_text().splitlines()[1:]:
        cells = line.split("\t")
        nyu = int(cells[4])
        if nyu in nyu40ids:
            nyu_to_class[nyu] = keys.get(cells[7], keys["others"])
    anns = defaultdict(list)
    for row in json.loads(ann_path.read_text()):
        anns[row["scene_id"]].append(row)
    graphs = json.loads(graph_path.read_text())
    scenes = sorted(anns)[:64]
    if len(scenes) != 64:
        raise ValueError("Frozen scene cohort differs")
    output = []
    physical_hashes = {}
    for scene in scenes:
        path = root / "scannetv2/train" / (scene + "_refer.pth")
        data = torch.load(path, map_location="cpu", weights_only=False)
        if len(data) != 5:
            raise ValueError("Physical scene schema differs")
        sp, sem, ins = [np.asarray(x, dtype=np.int64) for x in data[2:]]
        if not np.array_equal(np.unique(sp), np.arange(sp.max() + 1)):
            raise ValueError("Noncontiguous superpoints")
        nsp = sp.max() + 1
        counts = np.bincount(sp, minlength=nsp)
        physical_hashes[scene] = sha(path)
        curtain = []
        for iid in np.unique(ins):
            idx = np.flatnonzero(ins == iid)
            first = int(sem[idx[0]])
            if first < 0:
                continue
            if first >= len(sem2nyu):
                raise ValueError("Semantic class differs")
            nyu = sem2nyu[first]
            if nyu in nyu40ids and nyu_to_class[nyu] == keys["shower curtain"]:
                curtain.append(int(iid))
        for ann in anns[scene]:
            target = {int(x) for x in ann.get("object_ids", [ann.get("object_id")])}
            if None in target:
                raise ValueError("Target missing")
            text = (" ".join(graphs[scene][str(ann["ann_id"])]["utterance"]
                             .replace(",", " ,").split()) + " . not mentioned")
            tokens = text.split()
            phrase = any(tokens[i:i + 2] == ["shower", "curtain"]
                         for i in range(len(tokens) - 1))
            native_keys = {keys[w] for w in tokens if w in keys and w != "others"}
            if keys["shower curtain"] in native_keys:
                raise ValueError("Native producer unexpectedly matches multiword")
            others = [iid for iid in curtain if iid not in target]
            changed = np.zeros(nsp, dtype=np.int64)
            if phrase and others:
                added = np.isin(ins, others)
                changed = np.bincount(sp, weights=added, minlength=nsp)
            output.append({
                "scene": scene, "ann_id": int(ann["ann_id"]),
                "phrase": phrase, "physical_curtain_instances": curtain,
                "nontarget_curtain_instances": others,
                "target_is_curtain": any(iid in target for iid in curtain),
                "changed_superpoint_rows": int((changed > 0).sum()),
                "changed_nonzero_support_rows": int(((changed > 0) & (changed < counts)).sum()),
                "changed_curtain_points": int(changed.sum()),
            })
    exposed = [r for r in output if r["phrase"] and r["nontarget_curtain_instances"]]
    summary = {
        "scenes": len(scenes), "annotations": len(output),
        "phrase_expressions": sum(r["phrase"] for r in output),
        "phrase_scenes": len({r["scene"] for r in output if r["phrase"]}),
        "phrase_target_curtain": sum(r["phrase"] and r["target_is_curtain"] for r in output),
        "qualifying_expressions": len(exposed),
        "qualifying_scenes": len({r["scene"] for r in exposed}),
        "qualifying_physical_nontarget_instances": len({
            (r["scene"], iid) for r in exposed for iid in r["nontarget_curtain_instances"]}),
        "changed_superpoint_rows_repeated": sum(r["changed_superpoint_rows"] for r in exposed),
        "negative_control_changed_rows": sum(r["changed_superpoint_rows"] for r in output if not r["phrase"]),
    }
    result = {
        "contract": "m95_multiword_context_v1", "admission": False,
        "inputs": {"annotations": sha(ann_path), "graphs": sha(graph_path),
                   "dataset_source": sha(args.dataset_source), "labels": sha(tsv_path)},
        "physical_sha256": physical_hashes, "summary": summary,
        "exposed_rows": exposed,
        "limits": "Source-level tokenization audit, not native gradient, causal efficacy or a training admission.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
