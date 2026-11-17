"""Summarize the preregistered native same-target capture."""
import hashlib
import json
from pathlib import Path
from target_equivalence_audit_20260916 import audit

root = Path(__file__).resolve().parents[1]
source = root / "pipeline/reports/same_target_native_20260916.json"
native = json.loads(source.read_text())
result = audit(native["rows"])
lookup = {(r["scene"], r["ann_id"]): r for r in native["rows"]}
for pair in result["pairs"]:
    pair["candidate_covered"] = [
        lookup[(pair["scene"], a)]["layers"][-1]["best"] > .5 for a in pair["ann_ids"]]
    pair["sampled_target"] = [
        lookup[(pair["scene"], a)]["sampled_instance_target"] for a in pair["ann_ids"]]
result["summary"]["disagreements_both_covered"] = sum(
    p["success_disagreement"] and all(p["candidate_covered"]) for p in result["pairs"])
result["summary"]["correct_both"] = sum(all(v > .5 for v in p["ious"]) for p in result["pairs"])
result["summary"]["wrong_both"] = sum(all(v <= .5 for v in p["ious"]) for p in result["pairs"])
result["limitations"][0] = "32fixedTRAINscenes;2objects/scene selected by ID,not outcome;not population-random."
result["evidence"] = [dict(path=str(p.relative_to(root)),
    sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (source, Path(__file__))]
(root / "pipeline/reports/same_target_summary_20260916.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result["summary"]))
for pair in result["pairs"]:
    if pair["success_disagreement"]:
        print(json.dumps(pair))
