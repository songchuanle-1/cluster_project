"""Existing TRAIN lexical negation inventory; no new semantic labels."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

root = Path("/data3/songcl/Project/Cluster_project")
data = Path("/data3/songcl/data/data_cluster/scanrefer")
annotations_path = data/"ScanRefer_train_new.json"
graphs_path = data/"scene_graphs_new_train.json"
annotations = json.loads(annotations_path.read_text())
graphs = json.loads(graphs_path.read_text())
pattern = re.compile(r"\b(?:no|not|without|neither|nor|except)\b", re.I)
rows, keys = [], set()
for annotation in annotations:
    scene, ann = annotation["scene_id"], str(annotation["ann_id"])
    assert (scene, ann) not in keys
    keys.add((scene, ann))
    graph = graphs[scene][ann]
    caption = " ".join(graph["utterance"].replace(",", " ,").split())
    cues = []
    for match in pattern.finditer(caption):
        covered = []
        for node in graph["graph_node"]:
            for kind in ("target_char_span", "mod_char_span", "pron_char_span", "rel_char_span"):
                for start, end in node.get(kind, []):
                    if int(start) <= match.start() and match.end() <= int(end):
                        covered.append(dict(node=node["node_id"], kind=kind))
        cues.append(dict(text=match.group().lower(), span=list(match.span()),
                         covered=covered))
    if cues:
        rows.append(dict(scene=scene, ann_id=ann, target=int(annotation["object_id"]),
                         caption=caption, cues=cues, edges=graph["graph_edge"]))
summary = dict(
    train_annotations=len(annotations), scenes=len({s for s, _ in keys}),
    cue_expressions=len(rows), cue_scenes=len({r["scene"] for r in rows}),
    cues=sum(len(r["cues"]) for r in rows),
    token_counts=dict(Counter(c["text"] for r in rows for c in r["cues"])),
    cues_covered_any_node=sum(bool(c["covered"]) for r in rows for c in r["cues"]),
    cues_covered_target_node=sum(any(n["node"] == 0 for n in c["covered"])
                                  for r in rows for c in r["cues"]),
)
out = root/"pipeline/negation_training_inventory_20260916"
out.mkdir(exist_ok=True)
(out/"result.json").write_text(json.dumps(dict(
    summary=summary, rows=rows,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), annotations_path, graphs_path)},
    limitations="TRAIN lexical cues only. Scope, double negation, not-only idioms "
    "and referential truth not labeled. Counts are not model failure rates. "
    "Uncovered parser span does not remove a token from the contextual encoder. "
    "No novel mechanism, effect or admission claim."
), indent=2))
print(json.dumps(summary, indent=2), flush=True)
