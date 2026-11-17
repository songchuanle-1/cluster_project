"""Join existing frozen evidence by full identity; no new oracle or model run."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
paths = [root / "contact_intervention_20260914.json",
         root / "boundary_cardinality_probe_20260914.json"]
key = lambda r: (r["scene_id"], r["object_id"], r["ann_id"])
tables = [{key(r): r for r in json.loads(p.read_text())["rows"]} for p in paths]
assert all(len(t) == 284 for t in tables) and tables[0].keys() == tables[1].keys()
rows = []
for identity, contact in tables[0].items():
    boundary = tables[1][identity]
    assert abs(contact["before"] - boundary["before"]) < 1e-8
    if contact["before"] > .5:
        continue
    rows.append(dict(identity=identity, before=contact["before"],
        boundary_count_rescue=boundary["after"] > .5,
        completion_rescue=contact["touched_target_completion_iou"] > .5,
        false_island_rescue=contact["false_island_oracle_iou"] > .5,
        any_inversion=boundary["inverted_edges"] > 0,
        seed_outside=not contact["seed_in_gt"],
        zero_overlap=contact["before"] == 0))
summary = dict(failures=len(rows), scenes=len({r["identity"][0] for r in rows}))
for name in ("boundary_count_rescue", "completion_rescue", "false_island_rescue",
             "any_inversion", "seed_outside", "zero_overlap"):
    take = [r for r in rows if r[name]]
    summary[name] = dict(n=len(take), scenes=len({r["identity"][0] for r in take}))
summary["completion_not_count"] = sum(r["completion_rescue"] and not r["boundary_count_rescue"] for r in rows)
summary["unrescued_by_all_three"] = sum(not any(r[n] for n in (
    "boundary_count_rescue", "completion_rescue", "false_island_rescue")) for r in rows)
report = dict(summary=summary,rows=rows,sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    scope="Mined frozen VAL identities;GT oracles and correlations only. Not proof that a deployable completion method exists.")
(root/"boundary_error_partition_20260915.json").write_text(json.dumps(report,indent=2))
print(json.dumps(summary))
