"""Within-expression score control for native-negative physical seed classes."""
import argparse
import hashlib
import json
from pathlib import Path

from m95_physical_semantic_contract_20260926 import native_mapping

CAPTURE_SHA = "9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd"
GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
DATASET_SHA = "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
LABELS_SHA = "9c17c0da2061beea889edc9f49ff14e8218f4cd040ab241fc70186e03b32a744"


def analyze(capture, graphs, mapping, semantic_mapping):
    rows = []
    for item in capture["rows"]:
        graph = graphs[item["scene"]][str(item["ann_id"])]
        text = " ".join(graph["utterance"].replace(",", " ,").split()) + " . not mentioned"
        classes = {mapping[word] for word in text.split()
                   if word in mapping and word != "others"}
        query_scores = item["scores"]
        seeds = item["sampled_seed_indices"]
        fps = item["fps_superpoints"]
        positive = item["native_positive"]
        instances = item["physical_instance_labels"]
        semantics = item["semantic_labels"]
        if (len(query_scores) != len(seeds) or len(seeds) != len(positive)
                or len(instances) != len(semantics)):
            raise ValueError("Frozen native axes differ")
        target = set(map(int, item["target_instances"]))
        exposed, control = [], []
        for query, seed in enumerate(seeds):
            if not 0 <= int(seed) < len(fps) or not 0 <= int(fps[int(seed)]) < len(instances):
                raise ValueError("FPS seed axis differs")
            point = int(fps[int(seed)])
            instance = int(instances[point])
            category = semantic_mapping.get(int(semantics[point]))
            if positive[query] or instance < 0 or instance in target or category is None:
                continue
            (exposed if category in classes else control).append(float(query_scores[query]))
        rows.append({
            "manifest_index": int(item["manifest_index"]), "scene": item["scene"],
            "stratum": item["stratum"], "failed": float(item["ious"][int(item["selected_query"])]) <= 0.5,
            "exposed_queries": len(exposed), "control_queries": len(control),
            "score_delta": (sum(exposed) / len(exposed) - sum(control) / len(control))
            if exposed and control else None,
        })
    rows.sort(key=lambda r: r["manifest_index"])
    if len(rows) != 256 or [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Frozen cohort incomplete")

    def tally(group):
        paired = [r for r in group if r["score_delta"] is not None]
        return {"rows": len(group), "scenes": len({r["scene"] for r in group}),
                "paired_rows": len(paired), "paired_scenes": len({r["scene"] for r in paired}),
                "paired_failures": sum(r["failed"] for r in paired),
                "context_queries": sum(r["exposed_queries"] for r in group),
                "control_queries": sum(r["control_queries"] for r in group),
                "positive_deltas": sum(r["score_delta"] > 0 for r in paired),
                "mean_delta": sum(r["score_delta"] for r in paired) / len(paired)
                if paired else None}
    return {"contract": "m95_seed_context_score_control_v1", "admission": False,
            "capture_sha256": CAPTURE_SHA, "graph_sha256": GRAPH_SHA,
            "summary": {
                "all": tally(rows),
                "ambiguous": tally([r for r in rows if r["stratum"] == "ambiguous"]),
                "class_unique": tally([r for r in rows if r["stratum"] == "class_unique"]),
            }, "rows": rows}


def main():
    p = argparse.ArgumentParser()
    for key in ("capture", "graphs", "dataset-code", "labels", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or any(
        hashlib.sha256(path.read_bytes()).hexdigest() != expected
        for path, expected in (
            (args.capture, CAPTURE_SHA), (args.graphs, GRAPH_SHA),
            (args.dataset_code, DATASET_SHA), (args.labels, LABELS_SHA))
    ):
        raise ValueError("Frozen input differs or output exists")
    mapping, semantic_mapping = native_mapping(
        args.dataset_code.read_text(encoding="utf-8"),
        args.labels.read_text(encoding="utf-8"))
    result = analyze(json.loads(args.capture.read_text(encoding="utf-8")),
                     json.loads(args.graphs.read_text(encoding="utf-8")),
                     mapping, semantic_mapping)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
