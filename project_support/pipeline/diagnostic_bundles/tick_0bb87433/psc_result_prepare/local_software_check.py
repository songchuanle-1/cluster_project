"""Check normalizer software only; this cannot supply a native/resource result."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import importlib.util
import json
import math
import statistics
import sys

HERE = Path(__file__).resolve().parent
path = HERE / "normalize_psc_actual_results.py"
source = path.read_text(encoding="utf8")
compile(source, str(path), "exec")
spec = importlib.util.spec_from_file_location("psc_result_normalizer_software_checked", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checks = []


def record(name, condition):
    assert condition, name
    checks.append({"name": name, "passed": True})


record("normalizer_compile_and_import_no_main_or_result_output", not list(HERE.glob("results_*")))
record("only_current_tick_PSC_sources_and_owner", module.TOKEN == "0bb874337dde412e98bbbaac369f3370"
       and module.SOURCE == "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
       and module.PARENT == "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
       and module.CID == "hierarchy-native-position-feature-cross-scatter-composition")
record("original_four_required_arms", module.PAIRS == (
    ("smoke", "champion"), ("smoke", "candidate"), ("resources", "champion"), ("resources", "candidate")))
for value in (None, True, "1", float("nan"), float("inf"), -float("inf")):
    record("nonfinite_or_nonnumeric_refused:" + repr(value), module.finite(value) is False)
record("finite_numeric_values_accepted", module.finite(0) and module.finite(-1.5))
record("median_and_original_linear_P90_recompute", statistics.median(list(range(1, 101))) == 50.5
       and math.isclose(module.percentile90(list(range(1, 101))), 90.1))
try:
    module.check("software_negative_integrity_control", False)
except ValueError:
    record("failed_actual_check_refuses_immediately", True)
else:
    raise AssertionError("Failed native evidence could continue")
module.CHECKS.clear()
record("certain_terminal_zero_and_completed_required", all(text in source for text in (
    'entry.get("certainty") == "terminal"', 'entry.get("returncode") == 0',
    'result.get("execution_completed") is True', 'check(name + "_raw_identity"',
    '"manifest_exact_activation_template_projection"')))
record("original_PSC_observation_keys_present", all(text in source for text in (
    "whole_position_feature_scatter_weight_gradient", "whole_position_feature_scatter_weight_updated",
    "whole_position_feature_scatter_module_updated", "PSC_position_feature_scatter_observations",
    'actual_group_mean_calls"] == 11', 'actual_centered_cross_calls"] == 3',
    "packing_blocks_C_3C_3C_3C", "exact_original_decoder_padded_positions_reference")))
record("conditional_memory_and_whole_model10G_only", all(text in source for text in (
    'rc["profile"]["flops_g"] <= 10', 'rb["peak_allocated_bytes"] * 1.15',
    '"trained_mIoU_gain_measured": False', '"new_latency_cutoff_added": False')))
record("internal_callbacks_zero_legal_no_new_completeness_gate", 'actual_internal_backward_callbacks"] == 0' in source)
record("partial_raw_preserved_and_no_self_admission", "actual_raw_wrapper" in source
       and '"admission_granted": False' in source and '"canonical_receipt": False' in source)
record("no_process_transport_or_torch_import", not any(name == "torch" or name.startswith("torch.") for name in sys.modules)
       and not any(isinstance(node, (ast.Import, ast.ImportFrom)) and
                   any(alias.name in ("subprocess", "paramiko", "torch") for alias in node.names)
                   for node in ast.walk(ast.parse(source))))
result = {
    "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
    "status": "ACTUAL_LOCAL_NORMALIZER_SOFTWARE_CHECKS_PASSED_NOT_NATIVE_RESULTS",
    "check_count": len(checks), "checks": checks,
    "normalizer_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "native": "NOT_EVALUATED_BY_SOFTWARE_CHECK", "resources": "NOT_EVALUATED_BY_SOFTWARE_CHECK",
    "native_or_resources_pass_artifacts_created": False, "raw_results_or_shared_state_written": False,
}
with (HERE / "software_validation.json").open("x", encoding="utf8", newline="\n") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps({"status": result["status"], "check_count": len(checks), "normalizer_sha256": result["normalizer_sha256"]}))
