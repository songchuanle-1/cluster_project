"""Identity-aligned summary of symmetric native sampling controls."""
import hashlib
import json
from pathlib import Path
from target_equivalence_audit_20260916 import audit

root = Path(__file__).resolve().parents[1]
source = root / "pipeline/reports/same_target_support_20260916.json"
native = json.loads(source.read_text())
branches = {}
for name in ("base", "repeat", "shared_first", "shared_second"):
    rows = [r for b in native["batches"] for r in b["branches"][name]["rows"]]
    branches[name] = audit(rows)
base = {(p["scene"], tuple(p["ann_ids"])): p for p in branches["base"]["pairs"]}
survival = {}
for name in ("repeat", "shared_first", "shared_second"):
    pairs = {(p["scene"], tuple(p["ann_ids"])): p for p in branches[name]["pairs"]}
    assert pairs.keys() == base.keys()
    survival[name] = dict(base_disagreements=sum(p["success_disagreement"] for p in base.values()),
        still_disagree=sum(p["success_disagreement"] and pairs[k]["success_disagreement"]
                           for k, p in base.items()),
        resolved_both_success=sum(p["success_disagreement"] and all(v > .5 for v in pairs[k]["ious"])
                                  for k, p in base.items()),
        resolved_both_fail=sum(p["success_disagreement"] and all(v <= .5 for v in pairs[k]["ious"])
                               for k, p in base.items()),
        new_disagreements=sum(not p["success_disagreement"] and pairs[k]["success_disagreement"]
                              for k, p in base.items()))
noise = max(abs(x-y) for b in native["batches"]
            for a, c in zip(b["branches"]["base"]["logits"], b["branches"]["repeat"]["logits"])
            for x, y in zip(a, c))
stage_pairs = []
for batch in native["batches"]:
    rows = batch["branches"]["base"]["rows"]
    for i in range(0, len(rows), 2):
        a, b = rows[i:i+2]
        assert a["target_ids"] == b["target_ids"]
        stages = []
        for layer, (x, y) in enumerate(zip(a["layers"], b["layers"])):
            stages.append(dict(layer=layer, ious=[x["selected"], y["selected"]],
                disagree=(x["selected"] > .5) != (y["selected"] > .5),
                covered=[x["best"] > .5, y["best"] > .5]))
        stage_pairs.append(dict(scene=a["scene"], ann_ids=[a["ann_id"], b["ann_id"]],
                               target_ids=a["target_ids"], stages=stages))
stage_summary = [dict(layer=i,
    disagreements=sum(p["stages"][i]["disagree"] for p in stage_pairs),
    both_success=sum(all(v > .5 for v in p["stages"][i]["ious"]) for p in stage_pairs),
    both_fail=sum(all(v <= .5 for v in p["stages"][i]["ious"]) for p in stage_pairs))
    for i in range(len(stage_pairs[0]["stages"]))]
old_source = root / "pipeline/reports/same_target_summary_20260916.json"
old = json.loads(old_source.read_text())
previous = {(p["scene"], tuple(p["ann_ids"])): p for p in old["pairs"]}
assert previous.keys() == base.keys()
result = dict(branches=branches, survival=survival, repeat_max_logit_error=noise,
    stage_summary=stage_summary, stage_pairs=stage_pairs,
    previous_capture_success_disagreements=sum(p["success_disagreement"] for p in previous.values()),
    previous_disagreements_reproduced=sum(p["success_disagreement"] and base[k]["success_disagreement"]
                                          for k, p in previous.items()),
    evidence=[dict(path=str(p.relative_to(root)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
              for p in (source, old_source, Path(__file__))],
    limitations="Within-run controls freeze FPS;shared branches use each member's physical "
    "support symmetrically. Language conditioning remains at upstream encoding. "
    "Consistency alone permits jointly wrong outputs;not a novel mechanism or accuracy claim.")
(root / "pipeline/reports/same_target_support_summary_20260916.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(dict(summaries={k: v["summary"] for k, v in branches.items()},
    survival=survival, noise=noise,
    stage_summary=stage_summary,
    previous_disagreements_reproduced=result["previous_disagreements_reproduced"])))
