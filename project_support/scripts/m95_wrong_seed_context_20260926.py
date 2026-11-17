"""Physical query-seed context upper bound from frozen M95 TRAIN capture."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from m95_physical_semantic_contract_20260926 import native_mapping

CAPTURE_SHA = "9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd"
GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
DATASET_SHA = "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
LABELS_SHA = "9c17c0da2061beea889edc9f49ff14e8218f4cd040ab241fc70186e03b32a744"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(capture, graphs, type2class, sem_to_class):
    if (capture.get("capture_mode") != "full_train_scan"
            or not capture.get("native_match_cause_completed")):
        raise ValueError("Native capture incomplete")
    rows = []
    for item in capture["rows"]:
        graph = graphs[item["scene"]][str(item["ann_id"])]
        text = " ".join(graph["utterance"].replace(",", " ,").split()) + " . not mentioned"
        classes = {type2class[word] for word in text.split()
                   if word in type2class and word != "others"}
        seeds = item["sampled_seed_indices"]
        fps = item["fps_superpoints"]
        physical = item["physical_instance_labels"]
        semantics = item["semantic_labels"]
        positive = item["native_match_cause"]["native_positive"]
        if (len(seeds) != len(positive) or len(physical) != len(semantics)
                or positive != item["native_positive"]):
            raise ValueError("Native query/point axes differ")
        target = set(map(int, item["target_instances"]))
        query = []
        for index, seed in enumerate(seeds):
            if not 0 <= int(seed) < len(fps) or not 0 <= int(fps[int(seed)]) < len(physical):
                raise ValueError("Native FPS seed index differs")
            point = int(fps[int(seed)])
            instance = int(physical[point])
            semantic = sem_to_class.get(int(semantics[point]))
            unresolved = instance < 0 or semantic is None
            context = not unresolved and instance not in target and semantic in classes
            query.append({
                "query": index, "positive": bool(positive[index]),
                "seed_instance": instance, "semantic_class": semantic,
                "unresolved": unresolved, "non_target": instance not in target,
                "context_upper_bound": bool(context and not positive[index]),
            })
        selected = int(item["selected_query"])
        if selected < 0 or selected >= len(query):
            raise ValueError("Selected query axis differs")
        eligible = [q for q in query if not q["unresolved"] and q["non_target"] and not q["positive"]]
        rows.append({
            "manifest_index": int(item["manifest_index"]), "scene": item["scene"],
            "ann_id": int(item["ann_id"]), "stratum": item["stratum"],
            "failed": float(item["ious"][selected]) <= 0.5,
            "selected_query": selected,
            "selected_unresolved": query[selected]["unresolved"],
            "selected_exposed": query[selected]["context_upper_bound"],
            "non_target_unmatched": len(eligible),
            "context_upper_bound_count": sum(q["context_upper_bound"] for q in query),
            "matched_positive_queries": sum(q["positive"] for q in query),
            "context_classes": sorted(classes),
            "selected_seed_instance": query[selected]["seed_instance"],
        })
    rows.sort(key=lambda x: x["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen row coverage differs")

    def tally(group):
        return {
            "rows": len(group), "scenes": len({r["scene"] for r in group}),
            "failures": sum(r["failed"] for r in group),
            "selected_unresolved": sum(r["selected_unresolved"] for r in group),
            "selected_exposed": sum(r["selected_exposed"] for r in group),
            "selected_exposed_failures": sum(r["selected_exposed"] and r["failed"] for r in group),
            "non_target_unmatched": sum(r["non_target_unmatched"] for r in group),
            "context_upper_bound_queries": sum(r["context_upper_bound_count"] for r in group),
            "matched_positive_queries": sum(r["matched_positive_queries"] for r in group),
        }
    pairs = [(a, b) for i, a in enumerate(rows) for b in rows[i + 1:]
             if a["scene"] == b["scene"] and a["stratum"] == b["stratum"]
             and not a["selected_unresolved"] and not b["selected_unresolved"]
             and a["selected_exposed"] != b["selected_exposed"]]
    return {
        "contract": "m95_wrong_seed_context_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "graph_sha256": GRAPH_SHA,
        "summary": {
            "all": tally(rows),
            "ambiguous": tally([r for r in rows if r["stratum"] == "ambiguous"]),
            "class_unique": tally([r for r in rows if r["stratum"] == "class_unique"]),
            "same_scene_discordant_pairs": len(pairs),
            "same_scene_exposed_failures": sum(
                a["failed"] if a["selected_exposed"] else b["failed"] for a, b in pairs),
            "same_scene_control_failures": sum(
                b["failed"] if a["selected_exposed"] else a["failed"] for a, b in pairs),
        },
        "rows": rows,
    }


def main():
    p = argparse.ArgumentParser()
    for key in ("capture", "graphs", "dataset-code", "labels", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or any(
            sha(path) != expected for path, expected in (
                (args.capture, CAPTURE_SHA), (args.graphs, GRAPH_SHA),
                (args.dataset_code, DATASET_SHA), (args.labels, LABELS_SHA))):
        raise ValueError("Frozen input hash differs or output exists")
    type2class, sem_to_class = native_mapping(
        args.dataset_code.read_text(encoding="utf-8"),
        args.labels.read_text(encoding="utf-8"))
    result = audit(
        json.loads(args.capture.read_text(encoding="utf-8")),
        json.loads(args.graphs.read_text(encoding="utf-8")),
        type2class, sem_to_class)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
