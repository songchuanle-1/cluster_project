"""Native TRAIN token-map availability, no training or annotation changes."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("coverage_stage_capture_20260916.py")
scope = {"__file__": str(parent)}
exec(compile(parent.read_text().split("\nmodel = importlib.import_module")[0],
             str(parent), "exec"), scope)
root = scope["ROOT"].parent / "pipeline"
source = root / "instance_feature_audit_20260916/result.json"
lookup = {(r["scene"], r["ann_id"]): r for r in json.loads(source.read_text())["rows"]}
rows = []
keys = ("positive_map", "modify_positive_map", "pron_positive_map",
        "rel_positive_map", "other_entity_map")
for batch in scope["batches"]:
    scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"]) for _ in range(int(n))]
    for i, maps in enumerate(batch["dense_maps"]):
        key = (scenes[i], int(batch["ann_ids"][i]))
        old = lookup[key]
        length = int(batch["lang_masks"][i].sum())
        counts = {k: int((maps[k][0, :length] > 0).sum()) for k in keys}
        outside = {k: int((maps[k][0, length:] > 0).sum()) for k in keys}
        rows.append(dict(scene=key[0], ann_id=key[1], length=length, counts=counts,
            outside_valid=outside, success=old["before"] > .5,
            confident_wrong=old["before"] <= .5 and old["winner_overlap"] > .5
                            and old["winner"] != old["target"]))
assert len(rows) == len({(r["scene"], r["ann_id"]) for r in rows}) == 123
summary = {}
for name, items in (
    ("success", [r for r in rows if r["success"]]),
    ("confident_wrong", [r for r in rows if r["confident_wrong"]]),
    ("other_failure", [r for r in rows if not r["success"] and not r["confident_wrong"]]),
):
    summary[name] = dict(expressions=len(items),
        empty={k: sum(r["counts"][k] == 0 for r in items) for k in keys},
        outside={k: sum(r["outside_valid"][k] > 0 for r in items) for k in keys})
out = root / "attribute_support_20260916"
out.mkdir(exist_ok=True)
(out / "result.json").write_text(json.dumps(dict(rows=rows, summary=summary,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), parent, source)},
    limitations="Native fixed16TRAIN batches123expressions. Empty map may reflect "
    "absence of an attribute phrase,not parser error. Presence is not semantic "
    "correctness or proof of effective gradient. Outcome strata descriptive only."
), indent=2))
print(json.dumps(summary), flush=True)
