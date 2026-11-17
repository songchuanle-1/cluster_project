"""Join existing diagnostic edges to verified raw instance labels."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = [root/"pipeline/reports"/name for name in (
    "raw_semantic_identity_20260916.json", "vertical_relation_bounds_20260916.json",
    "entity_binding_20260916.json")]
raw, vertical, binding = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
lookup = {(r["scene"],r["ann_id"]):r for r in binding["rows"]}
rows = []
for row in vertical["rows"]:
    target = lookup[(row["scene"],row["ann_id"])]["target"]
    candidates = sorted(r["instance"] for r in raw["rows"]
                        if r["scene"] == row["scene"] and r["instance"] != target
                        and r["raw_label"] == row["anchor_name"])
    rows.append(dict(scene=row["scene"],ann_id=row["ann_id"],noun=row["anchor_name"],
                     previous=row["anchors"],raw_candidates=candidates,
                     added=sorted(set(candidates)-set(row["anchors"])),
                     removed=sorted(set(row["anchors"])-set(candidates))))
assert len(rows) == 11
summary = dict(edges=len(rows),changed=sum(r["previous"]!=r["raw_candidates"] for r in rows),
               missing=sum(not r["raw_candidates"] for r in rows))
result = dict(summary=summary,rows=rows,
              limitations="Exact strings only;no synonym/plural repair or anchor truth. "
              "All raw instance IDs already pointwise verified. No prediction or new labels.",
              sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [*paths,Path(__file__)]})
(root/"pipeline/reports/raw_anchor_join_20260916.json").write_text(
    json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
