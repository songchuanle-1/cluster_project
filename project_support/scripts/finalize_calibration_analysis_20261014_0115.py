"""Bind final diagnostic facts and post-hoc scene-level associations."""
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import runpy

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "pipeline/reports"
TOKEN = "3aabc8207fea49ffb20003340e9bdfb9"
library = runpy.run_path(str(ROOT / "scripts/summarize_calibration_20261014_0115.py"),
                        run_name="calibration_analysis")
read, ref, cohort, heads = (library[name] for name in ("read", "ref", "cohort", "heads"))
owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
summary = read(P / "native_calibration_summary_20261014_0115.json")
extension = read(P / ("native_calibration_extension_" + TOKEN + ".json"))
head_path = P / ("native_extension_head_" + TOKEN + ".json")
head = read(head_path)
expected = {r["selection"]["group"]: r["input_sha256"] for r in extension["rows"]}
assert all(r["input_sha256"] == expected[r["selection"]["group"]] for r in head["rows"])
summary["extension_head_input_fingerprints_match"] = True
summary["extension_fixed_head"] = heads(head)
summary["cohorts"]["native_extension_head"] = cohort(head)
summary["successful_gpu_runs"] += 1
summary["completed_group_readouts"] += len(head["rows"])
summary["evidence"].append(ref(head_path))
summary["summarized_at"] = datetime.now(timezone.utc).isoformat()
summary["sampler_original_mapper_reads"] = 34647
summary["sampler_scope"] = "New prediction-blind frozen manifest, not repeated independent population evidence"
unique_groups, unique_expressions, unique_scenes = set(), set(), set()
for evidence in summary["evidence"]:
    capture = read(ROOT / evidence["path"])
    for row in capture["rows"]:
        unique_groups.add(row["selection"]["group"])
        unique_scenes.add(row["selection"]["scene"])
        unique_expressions.update((row["selection"]["scene"], e["ann_id"])
                                  for e in row["calibration_readout"]["expressions"])
summary["unique_native_groups"] = len(unique_groups)
summary["unique_native_expressions"] = len(unique_expressions)
summary["unique_native_scenes"] = len(unique_scenes)
summary["maximum_allocator_peak_allocated_mib"] = max(
    c["peak_allocated_mib"] for c in summary["cohorts"].values())
summary["maximum_allocator_peak_reserved_mib"] = max(
    c["peak_reserved_mib"] for c in summary["cohorts"].values())

# Pair exposure groups inside the same frozen scene, without causal attribution.
scenes = defaultdict(lambda: {"exposed": [], "unexposed": []})
all_exposed, all_unexposed = [], []
for row in extension["rows"]:
    if row["selection"]["group"] == 4804:
        continue
    for expression in row["calibration_readout"]["expressions"]:
        exposed = "fractional_repelling" in expression["role_task_alignment"]
        failed = int(expression["selected_support_iou"] < .5)
        scenes[row["selection"]["scene"]]["exposed" if exposed else "unexposed"].append(failed)
        (all_exposed if exposed else all_unexposed).append(failed)
paired = [
    sum(values["exposed"]) / len(values["exposed"]) -
    sum(values["unexposed"]) / len(values["unexposed"])
    for values in scenes.values() if values["exposed"] and values["unexposed"]]
rng = random.Random(1999)
bootstrap = sorted(sum(rng.choices(paired, k=len(paired))) / len(paired)
                   for _ in range(10000)) if paired else []
summary["posthoc_descriptive_association"] = {
    "bridge_control_excluded": True,
    "exposed_expressions": len(all_exposed), "exposed_failed": sum(all_exposed),
    "unexposed_expressions": len(all_unexposed), "unexposed_failed": sum(all_unexposed),
    "within_scene_comparison_scenes": len(paired),
    "equal_scene_mean_failure_risk_difference": sum(paired) / len(paired) if paired else None,
    "scene_resampling_95_interval": [bootstrap[249], bootstrap[9749]] if bootstrap else None,
    "bootstrap_replicates": 10000, "bootstrap_seed": 1999,
    "scope": "Explicitly post-hoc descriptive association in a role-selected fixed TRAIN cohort. Scene pairing does not match captions, roles or objects; no causal effect, population generalization, efficacy or evaluation noise-floor claim."}
summary["closure_limitation"] = (
    "Three stable candidates remain validation; no independent structural intervention or training admission. "
    "No real external resource block and no two independently rejected routes justify validated early cooldown. "
    "Do not fabricate no_information_gain or wait merely to pass a deadline. Actual finish/abort outcome is not yet known.")
summary["evidence"].extend([
    ref(P / ("native_calibration_extension_" + TOKEN + ".manifest.json")),
    ref(ROOT / "pipeline/designs/native_extension_head_addendum_20261014_0139.md"),
    ref(Path(__file__))])
output = P / "native_calibration_final_summary_20261014_0115.json"
with output.open("x", encoding="utf-8") as stream:
    json.dump(summary, stream, indent=2, allow_nan=False)
    stream.write("\n")
print(json.dumps({
    "summary": str(output), "sha256": ref(output)["sha256"],
    "successful_gpu_runs": summary["successful_gpu_runs"],
    "completed_group_readouts": summary["completed_group_readouts"],
    "unique_native_groups": summary["unique_native_groups"],
    "unique_native_expressions": summary["unique_native_expressions"],
    "unique_native_scenes": summary["unique_native_scenes"],
    "extension_repelling_head": summary["extension_fixed_head"]["conditions"]["fractional_repelling"],
    "posthoc_descriptive_association": summary["posthoc_descriptive_association"]
}, indent=2))
