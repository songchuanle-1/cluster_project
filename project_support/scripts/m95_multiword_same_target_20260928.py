"""Same-target controls for a frozen multiword context-key exposure."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def target(ann):
    values = ann.get("object_ids", [ann.get("object_id")])
    if not values or any(x is None for x in values):
        raise ValueError("Missing target identity")
    return tuple(sorted(int(x) for x in values))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--physical-report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = json.loads(args.physical_report.read_text())
    if (report["contract"] != "m95_multiword_context_v1"
            or sha(args.physical_report) !=
            "331718c7181f176197502e74ea0cf271025096cc0bd9c464348c8944674caaf0"
            or len(report["exposed_rows"]) != 11):
        raise ValueError("Physical report contract differs")
    ann_path = args.data_root / "scanrefer/ScanRefer_train_new.json"
    graph_path = args.data_root / "scanrefer/scene_graphs_new_train.json"
    if (sha(ann_path) != report["inputs"]["annotations"]
            or sha(graph_path) != report["inputs"]["graphs"]):
        raise ValueError("Native source hashes differ")
    anns = defaultdict(list)
    for ann in json.loads(ann_path.read_text()):
        anns[ann["scene_id"]].append(ann)
    graphs = json.loads(graph_path.read_text())
    rows = []
    for exposed in report["exposed_rows"]:
        scene = exposed["scene"]
        aid = int(exposed["ann_id"])
        selected = [a for a in anns[scene] if int(a["ann_id"]) == aid]
        if len(selected) != 1:
            raise ValueError("Exposed identity missing or duplicate")
        target_ids = target(selected[0])
        controls = []
        for other in anns[scene]:
            oid = int(other["ann_id"])
            if oid == aid or target(other) != target_ids:
                continue
            text = (" ".join(graphs[scene][str(oid)]["utterance"]
                             .replace(",", " ,").split()) + " . not mentioned")
            tokens = text.split()
            phrase = any(tokens[i:i + 2] == ["shower", "curtain"]
                         for i in range(len(tokens) - 1))
            if not phrase:
                controls.append({"ann_id": oid, "text": text})
        rows.append({
            "scene": scene, "ann_id": aid, "target_instances": target_ids,
            "controls": sorted(controls, key=lambda c: c["ann_id"]),
        })
    summary = {
        "exposed_expressions": len(rows),
        "exposed_scene_targets": len({
            (r["scene"], tuple(r["target_instances"])) for r in rows}),
        "with_same_target_phrase_absent": sum(bool(r["controls"]) for r in rows),
        "absent_same_target_controls": sum(not r["controls"] for r in rows),
        "pairs": sum(len(r["controls"]) for r in rows),
        "control_scenes": len({r["scene"] for r in rows if r["controls"]}),
    }
    result = {
        "contract": "m95_multiword_same_target_v1", "admission": False,
        "physical_report_sha256": sha(args.physical_report),
        "annotation_sha256": sha(ann_path), "graph_sha256": sha(graph_path),
        "summary": summary, "rows": rows,
        "limits": "Language differs, outcome not captured, no same-input intervention or admission.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
