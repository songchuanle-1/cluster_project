"""Freeze outcome-blind native scene/annotation pairs for later diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path


PHYSICAL_SHA = "331718c7181f176197502e74ea0cf271025096cc0bd9c464348c8944674caaf0"
CONTROL_SHA = "11051e83414960ff1bdafb1220c2ff9b1d855c147b56b54bea73f0782d489ca1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def edit_distance(left, right):
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--physical-report", type=Path, required=True)
    p.add_argument("--control-report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or sha(args.physical_report) != PHYSICAL_SHA or sha(args.control_report) != CONTROL_SHA:
        raise ValueError("Source reports differ or output exists")
    physical = json.loads(args.physical_report.read_text())
    controls = json.loads(args.control_report.read_text())
    graph_path = args.data_root / "scanrefer/scene_graphs_new_train.json"
    if (physical["contract"] != "m95_multiword_context_v1"
            or controls["contract"] != "m95_multiword_same_target_v1"
            or physical["inputs"]["graphs"] != sha(graph_path)
            or controls["graph_sha256"] != sha(graph_path)):
        raise ValueError("Graph contract differs")
    graphs = json.loads(graph_path.read_text())
    physical_by_id = {(r["scene"], int(r["ann_id"])): r
                      for r in physical["exposed_rows"]}
    if len(physical_by_id) != 11 or len(controls["rows"]) != 11:
        raise ValueError("Frozen exposed identities differ")
    manifest = {}
    pair_rows = []
    for row in controls["rows"]:
        scene, aid = row["scene"], int(row["ann_id"])
        source = physical_by_id.pop((scene, aid))
        target = tuple(int(x) for x in row["target_instances"])
        text = (" ".join(graphs[scene][str(aid)]["utterance"]
                         .replace(",", " ,").split()) + " . not mentioned")
        tokens = text.split()
        if not any(tokens[i:i + 2] == ["shower", "curtain"]
                   for i in range(len(tokens) - 1)):
            raise ValueError("Exposed phrase differs")
        manifest[(scene, aid)] = {
            "scene": scene, "ann_id": aid, "text": text,
            "target_instances": target, "arm": "phrase",
            "nontarget_curtain_instances": source["nontarget_curtain_instances"],
        }
        ranked = []
        for control in row["controls"]:
            cid = int(control["ann_id"])
            control_text = (" ".join(graphs[scene][str(cid)]["utterance"]
                                     .replace(",", " ,").split()) + " . not mentioned")
            if control["text"] != control_text:
                raise ValueError("Control text differs")
            distance = edit_distance(tokens, control_text.split())
            ranked.append({"ann_id": cid, "edit_distance": distance})
            key = scene, cid
            record = {"scene": scene, "ann_id": cid, "text": control_text,
                      "target_instances": target, "arm": "phrase_absent"}
            if key in manifest and manifest[key] != record:
                raise ValueError("Conflicting control target")
            manifest[key] = record
        ranked.sort(key=lambda r: (r["edit_distance"], r["ann_id"]))
        if not ranked:
            raise ValueError("No controls for exposed expression")
        pair_rows.append({
            "scene": scene, "ann_id": aid, "target_instances": target,
            "all_controls": ranked, "nearest_control": ranked[0]["ann_id"],
            "nearest_edit_distance": ranked[0]["edit_distance"],
        })
    if physical_by_id:
        raise ValueError("Missing exposed expressions")
    records = sorted(manifest.values(), key=lambda r: (r["scene"], r["ann_id"]))
    summary = {
        "scenes": len({r["scene"] for r in records}),
        "scene_targets": len({(r["scene"], r["target_instances"]) for r in pair_rows}),
        "exposed": len(pair_rows),
        "unique_controls": sum(r["arm"] == "phrase_absent" for r in records),
        "pairs": sum(len(r["all_controls"]) for r in pair_rows),
        "nearest_edit_distances": [r["nearest_edit_distance"] for r in pair_rows],
    }
    result = {
        "contract": "m95_multiword_capture_manifest_v1", "admission": False,
        "physical_sha256": PHYSICAL_SHA, "control_sha256": CONTROL_SHA,
        "graph_sha256": sha(graph_path),
        "summary": summary, "records": records, "pairs": pair_rows,
        "limits": "Outcome-blind but text-confounded paired descriptions; capture is pending, no inference-time mechanism or training admission.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
