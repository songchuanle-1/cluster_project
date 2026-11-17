"""Read-only remote CPU audit of exact native caption/target equivalence."""
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path

ROOT = Path("/data3/songcl/Project/Cluster_project")
DATA = Path("/data3/songcl/data/data_cluster/scanrefer")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    ap = DATA / "ScanRefer_train_new.json"
    gp = DATA / "scene_graphs_new_train.json"
    mp = ROOT / "pipeline/point_detail_population_20261009/result.manifest.json"
    assert sha(ap) == "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
    assert sha(gp) == "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
    assert sha(mp) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    annotations = json.loads(ap.read_text())
    graphs = json.loads(gp.read_text())
    manifest = json.loads(mp.read_text())
    frozen = {(r["scene"], int(a["ann_id"])) for r in manifest
              for a in r["annotations"]}
    groups = defaultdict(list)
    for a in annotations:
        scene, aid = a["scene_id"], int(a["ann_id"])
        g = graphs[scene][str(aid)]
        native_text = " ".join(g["utterance"].replace(",", " ,").split()) + " . not mentioned"
        groups[(scene, native_text)].append({
            "ann_id": aid,
            "target_ids": sorted(map(int, a.get("object_ids", [a.get("object_id")]))),
            "graph_sha256": hashlib.sha256(json.dumps(
                g, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "in_frozen_cohort": (scene, aid) in frozen,
        })
    counts, rows, frozen_rows = Counter(), [], []
    for (scene, text), group in groups.items():
        if len(group) <= 1:
            continue
        unique = {tuple(r["target_ids"]) for r in group}
        conflict = any(set(a).isdisjoint(b) for a in unique for b in unique if a != b)
        item = {"scene": scene, "text": text, "annotations": group,
                "disjoint_labels": conflict, "unique_target_sets": len(unique),
                "graph_identical": len({r["graph_sha256"] for r in group}) == 1}
        counts["repeated_input_groups"] += 1
        counts["annotations_in_repeated_groups"] += len(group)
        counts["disjoint_label_groups" if conflict else "same_target_or_overlap_groups"] += 1
        if conflict:
            counts["annotations_in_disjoint_groups"] += len(group)
        rows.append(item)
        selected = [r for r in group if r["in_frozen_cohort"]]
        if selected:
            frozen_rows.append(item)
            counts["frozen_expressions_with_repeat_anywhere"] += len(selected)
            if conflict:
                counts["frozen_expressions_in_disjoint_groups"] += len(selected)
            if len(selected) > 1:
                counts["groups_with_at_least_two_frozen_expressions"] += 1
    result = {"contract": "native_caption_equivalence_audit_v1",
              "annotation_count": len(annotations), "unique_native_inputs": len(groups),
              "frozen_expression_count": len(frozen), "counts": dict(counts),
              "all_repeated_groups": rows, "frozen_groups": frozen_rows,
              "input_hashes": {"annotations": sha(ap), "graphs": sha(gp), "manifest": sha(mp)},
              "script_sha256": sha(Path(__file__)), "cpu_only": True, "admission": False,
              "limits": "Exact observable caption/scene grouping only. Does not prove tensors/gradients identical, native masks erroneous, multi-target labels correct, or trained benefit."}
    output = ROOT / "pipeline/caption_equivalence_audit_20261012.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps({"output": str(output), "sha256": sha(output),
                      "counts": result["counts"], "frozen_groups": frozen_rows}, indent=2))


if __name__ == "__main__":
    main()
