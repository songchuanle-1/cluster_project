"""Persist executed diagnostic evidence without changing queue state."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "pipeline/research_work.json"
work = json.loads(path.read_text(encoding="utf-8"))
context = json.loads((root / "pipeline/headless/.tick_context.json").read_text(encoding="utf-8"))
feature_ids = {"modality-identity-preservation", "instance-identity-representation",
               "input-modality-distinguishability"}
for candidate in work["candidates"]:
    if candidate["id"] not in context["research_work"]["due_ids"]:
        continue
    feature = candidate["id"] in feature_ids
    names = (["pipeline/reports/native_feature_contrasts_20260916-1615.json",
              "scripts/native_feature_contrasts_20260916.py",
              "scripts/test_native_feature_contrasts_20260916.py"] if feature else
             ["pipeline/reports/native_query_summary_20260916-1615.json",
              "scripts/native_query_summary_20260916.py"])
    for name in names + ["pipeline/decisions/20260916-161803_other.md"]:
        if not any(e["path"] == name for e in candidate["evidence"]):
            candidate["evidence"].append(dict(
                path=name, sha256=hashlib.sha256((root / name).read_bytes()).hexdigest()))
    candidate["feature_tick_progress"] = dict(
        stage_completed=("CPU support-bound all-instance leave-one-superpoint-out retrieval"
                         if feature else "Exact query contingency and repeated-target inventory"),
        scientific_validation_complete=False,
        finding=("Four-scene target retrieval raw3D .9301,raw2D .6879,final .9430;5 tests pass."
                 if feature else
                 "259 seed-out maskOK queries,1positive;top5 .8125;one physical same-target pair,not seven controls."),
        limitations="No expanded predefined sample, language-grounding inference or terminal PIRS comparison.")
    if feature:
        candidate["next_action"] = (
            "Extend native capture with semantic class and selected-mask physical instance overlap; "
            "predefine recoverable same-class stratum, then compare paired feature stages. "
            "Do not infer language grounding from all-instance retrieval.")
path.write_text(json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
print("Persisted evidence for eight due diagnosis records; stages unchanged.")
