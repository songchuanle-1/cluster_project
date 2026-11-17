"""Summarize partial identification without choosing a convenient anchor."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "pipeline/reports/vertical_relation_bounds_20260916.json"
data = json.loads(source.read_text())
rows = []
for row in data["rows"]:
    bounds = {}
    for role in ("target", "winner"):
        values = [e[role]["signed_center_height"] for e in row.get("evaluations", [])
                  if e.get(role) is not None and not e[role]["same_as_anchor"]]
        bounds[role] = dict(
            eligible=len(values), minimum=min(values) if values else None,
            maximum=max(values) if values else None,
            all_positive=all(v > 0 for v in values) if values else None,
            any_positive=any(v > 0 for v in values) if values else None)
    common = [e for e in row.get("evaluations", [])
              if e.get("target") and e.get("winner")
              and not e["target"]["same_as_anchor"] and not e["winner"]["same_as_anchor"]]
    distinguishing = [e["anchor"] for e in common
                      if e["target"]["signed_center_height"] > 0
                      and e["winner"]["signed_center_height"] <= 0]
    rows.append(dict(scene=row["scene"], ann_id=row["ann_id"], bounds=bounds,
                     common_anchors=len(common), distinguishing_anchors=distinguishing,
                     confident_wrong=row.get("confident_wrong", False)))
report = dict(
    rows=rows,
    summary=dict(
        edges=len(rows),
        target_all_positive=sum(r["bounds"]["target"]["all_positive"] is True for r in rows),
        target_ambiguous=sum(r["bounds"]["target"]["any_positive"] is True
                             and r["bounds"]["target"]["all_positive"] is False for r in rows),
        no_target_candidates=sum(r["bounds"]["target"]["eligible"] == 0 for r in rows)),
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    limitations="Common-anchor analysis excludes self-reference for either candidate; "
    "it is diagnostic and uses GT identities, never an inference rule. Signed centroid "
    "height is only a geometric proxy. Existential satisfaction does not identify "
    "the mentioned anchor. No scene truth or native efficacy claim.")
out = root / "pipeline/reports/vertical_relation_summary_20260916.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
