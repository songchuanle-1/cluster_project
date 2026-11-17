"""CPU-only resolution and complement controls on frozen recorded diagnostics."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import struct
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
TOKEN = "2bbb4e0b9a814185a795b2ea2178483f"
owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
head_path, mask_path = BUNDLE / "task_head_result.json", BUNDLE / "mask_direction_result.json"
head, mask = tick.load(head_path), tick.load(mask_path)
assert head["complete"] and mask["status"] == "completed"


def spacing(value):
    assert value >= 0
    bits = struct.unpack("<I", struct.pack("<f", value))[0]
    rounded = struct.unpack("<f", struct.pack("<I", bits))[0]
    higher = struct.unpack("<f", struct.pack("<I", bits + 1))[0]
    return higher - rounded


measurements = []
complements = []
for row in head["rows"]:
    h = row["trials"][0]["task_calibration"]["fixed_head"]
    for name, condition in h["conditions"].items():
        if condition["effects"] is None:
            continue
        for objective, effect in condition["effects"].items():
            baseline = h["baseline"]["losses"][objective]
            descent = baseline + effect["descent_loss_delta"]
            ascent = baseline + effect["ascent_loss_delta"]
            budget = (.5 * spacing(descent) + .5 * spacing(ascent)) / (2 * h["epsilon"])
            measurements.append({
                "kind": "head", "group": row["selection"]["group"], "condition": name,
                "objective": objective, "error": effect["central_absolute_error"],
                "rounding_budget": budget, "primary_failed1e6": effect["central_absolute_error"] > 1e-6,
                "within_final_scalar_rounding_budget": effect["central_absolute_error"] <= budget,
            })
    for role in ("main_secondary", "relation_other", "fractional_secondary", "fractional_repelling", "fractional_attracting"):
        part = h["conditions"][role]
        complement = h["conditions"]["complement_" + role]
        full = h["conditions"]["original"]
        if part["effects"] is None or complement["effects"] is None:
            continue
        for objective in ("mask", "indicator", "mask_plus_indicator"):
            def dot(condition):
                return -condition["effects"][objective]["analytic_unit_descent_derivative"] * condition["gradient_norm"]
            total, role_dot, complement_dot = dot(full), dot(part), dot(complement)
            complements.append({
                "group": row["selection"]["group"], "role": role, "objective": objective,
                "original_dot": total, "role_dot": role_dot, "complement_dot": complement_dot,
                "sum_identity_error": abs(total - role_dot - complement_dot),
                "partial_opposed_but_total_aligned": role_dot < 0 and total > 0,
            })
for index, row in enumerate(mask["rows"][::2]):
    for name, condition in row["conditions"].items():
        if not condition["gradient_norm"]:
            continue
        baseline = row["task_loss"]
        budget = (.5 * spacing(baseline + condition["descent_task_delta"]) +
                  .5 * spacing(baseline + condition["ascent_task_delta"])) / (2 * row["epsilon"])
        measurements.append({
            "kind": "mask", "group_offset": index, "condition": name, "objective": "mask",
            "error": condition["finite_difference_abs_error"], "rounding_budget": budget,
            "primary_failed1e6": condition["pass_derivative1e6"] is False,
            "within_final_scalar_rounding_budget": condition["finite_difference_abs_error"] <= budget,
        })
result = {
    "token": TOKEN, "recorded_at": datetime.now().astimezone().isoformat(),
    "script_sha256": tick.digest(Path(__file__)),
    "head_sha256": tick.digest(head_path), "mask_sha256": tick.digest(mask_path),
    "measured_derivatives": len(measurements),
    "primary_failed1e6": sum(row["primary_failed1e6"] for row in measurements),
    "failed_within_final_scalar_rounding_budget": sum(
        row["primary_failed1e6"] and row["within_final_scalar_rounding_budget"] for row in measurements),
    "complement_comparisons": len(complements),
    "complement_identity_max_error": max(row["sum_identity_error"] for row in complements),
    "complement_identity_failures1e6": sum(row["sum_identity_error"] > 1e-6 for row in complements),
    "partial_opposed_but_total_aligned": sum(
        row["partial_opposed_but_total_aligned"] and row["objective"] == "mask_plus_indicator"
        for row in complements),
    "measurements": measurements, "complement_rows": complements,
    "scope": "Descriptive final-scalar resolution and exact recorded decomposition; no primary1e-6 failure overwritten, no new pass, causal task harm, training efficacy or independent repair.",
}
tick.save(BUNDLE / "resolution_result.json", result)
print(json.dumps({key: value for key, value in result.items() if key not in ("measurements", "complement_rows")}, indent=2))
