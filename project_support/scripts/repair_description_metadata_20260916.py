"""Repair text attribution using archived manifest identities, not loader order."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = ["same_target_native", "same_target_support", "scene_interchange"]
report = {}
for name in paths:
    source = root / f"pipeline/reports/{name}_20260916.json"
    data = json.loads(source.read_text())
    lookup = {(m["scene"], int(r["ann_id"])): (int(r["object_id"]), r["description"])
              for m in data["manifest"] for r in m["selected"]}
    rows = data.get("rows")
    if rows is None:
        rows = [r for b in data["batches"] for branch in b["branches"].values()
                for r in branch["rows"]]
    changes = []
    for row in rows:
        obj, text = lookup[(row["scene"], int(row["ann_id"]))]
        assert row["target_ids"] == [obj]
        if row["utterance"] != text:
            changes.append(dict(scene=row["scene"], ann_id=row["ann_id"],
                                previous=row["utterance"], corrected=text))
        row["utterance"] = text
    output = source.with_name(source.stem + "_metadata_corrected.json")
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    report[name] = dict(rows=len(rows), corrected=len(changes), changes=changes,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        output=str(output.relative_to(root)),
        output_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
(root / "pipeline/reports/description_metadata_repair_20260916.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({k: dict(rows=v["rows"], corrected=v["corrected"]) for k, v in report.items()}))
