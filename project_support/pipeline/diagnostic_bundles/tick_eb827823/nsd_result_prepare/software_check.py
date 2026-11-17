"""Synthetic parser tests only; never creates or represents native evidence."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import copy
import hashlib
import importlib.util
import json
import os
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "normalize_nsd_actual_results.py"
ROOT = Path("D:/project/cluster_project")
RESULTS = []


def require(name, condition):
    RESULTS.append({"name": name, "passed": bool(condition)})
    assert condition, name


def refuses(name, operation):
    try:
        operation()
    except (AssertionError, ValueError, KeyError):
        require(name, True)
    else:
        require(name, False)


assert sys.dont_write_bytecode and os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
assert os.environ.get("CODEX_THREAD_ID") == "01a1a5a9-7056-7c92-bc3b-ca205451add4"
before = sorted(p.name for p in HERE.iterdir())
text = SOURCE.read_text(encoding="utf-8")
compile(text, str(SOURCE), "exec")
require("syntax_compiles_in_memory_without_bytecode", True)
spec = importlib.util.spec_from_file_location("nsd_actual_parser_software_test", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
require("import_has_no_output_or_native_artifacts", before == sorted(p.name for p in HERE.iterdir()))
require("no_torch_import_or_model_execution", "torch" not in sys.modules)
refuses("actual_child_is_refused_by_root_only_guard_without_spoofing", module.guard)
require("original_four_arms_only", module.PAIRS == (("smoke", "champion"), ("smoke", "candidate"),
                                                 ("resources", "champion"), ("resources", "candidate")))
for mode, target in module.PAIRS:
    fixture = {"candidate_id": module.CID, "code_commit": module.SOURCE, "experiment_id": "M232-NSD",
               "goal_sha256": module.GOAL, "mode": mode, "target": target,
               "config": "configs/Quard/ctf_hcg_csort_nsd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nsd.yaml",
               "model_package": "framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
                                + ("_nsd" if target == "candidate" else "")}
    module.validate_external_arm_identity(fixture, mode, target)
    require("synthetic_literal_NSD_identity_accepted_" + mode + "_" + target, True)
    for field, wrong in (("candidate_id", "hierarchy-native-position-feature-cross-scatter-composition"),
                         ("code_commit", module.PARENT), ("config", fixture["config"].replace("_nsd", "_psc")),
                         ("model_package", fixture["model_package"] + "_psc"), ("experiment_id", "M231-PSC")):
        corrupt = {**fixture, field: wrong}
        refuses("synthetic_wrong_" + field + "_refused_" + mode + "_" + target,
                lambda c=corrupt, m=mode, t=target: module.validate_external_arm_identity(c, m, t))


def summary(shape):
    return {"shape": shape, "finite": True}


def path_fixture(edges):
    energies = []
    for level in range(3):
        item = {"level": level, "actual_edge_count": int(edges), "input": summary([1, 2]),
                "native_coordinates": summary([1, 3]), "output": summary([1, 2]), "original_calls": 1,
                "returned_original_object_unchanged": True, "energy_arithmetic_replayed": False,
                "actual_coordinate_mean_and_contrast_mean_calls": 2 if edges else 0,
                "original_empty_chain_zero_branch": not edges,
                "optional_boundary_coverage_is_not_a_new_nonzero_or_resampling_gate": True}
        if edges:
            item["actual_squared_pair_contrast"] = {
                "original_calls": 1, "input_dtype_equals_output_dtype": True, "extra_FP32_cast_added": False,
                "input": summary([1, 2]), "output": summary([1, 2])}
        energies.append(item)
    means = [{"original_calls": 1, "returned_original_object_unchanged": True,
              "input": summary([1, 2]), "output": summary([1, 2])} for _ in range(12 if edges else 6)]
    scene = {"nodes": [[0], [0], [0]], "true_supported_nodes_by_scale": [1, 1, 1],
             "actual_original_support_builder_calls": 1,
             "actual_original_valid_coordinate_and_feature_mask_reference": True,
             "energy_observations": energies, "actual_group_mean_calls": len(means), "mean_observations": means}
    for key in ("actual_chain_energy_calls", "actual_chain_builder_calls", "actual_analysis_calls",
                "actual_synthesis_calls", "actual_final_index_copy_calls"):
        scene[key] = 3
    for kind, order, width in (("analysis", [0, 1, 2], 3), ("synthesis", [2, 1, 0], 2)):
        scene[kind + "_observations"] = [{"level": level, "original_calls": 1,
            "actual_original_shared_module": True, "no_replay_or_replacement": True,
            "input": summary([1, 2 * width]), "output": summary([1, 2])} for level in order]
    scene["restoration_observations"] = [{"level": level, "original_calls": 1,
        "actual_synthesis_delta_ref": True, "zero_initialized_destination": True,
        "returned_original_object_unchanged": True, "original_node_ids": [0],
        "output": summary([1, 2])} for level in range(3)]
    observation = {"forward": 1, "exact_original_decoder_padded_positions_reference": True,
        "exact_original_encoder_feature_and_mask_references": True, "actual_three_LN_calls": [1, 1, 1],
        "native_positions": summary([1, 3]), "per_parameter_nonzero_FP32_minimum_effect_gate_added": False,
        "scene_observations": [scene], "actual_supported_scene_count": 1}
    for level in range(3):
        for stem in ("native_normalized_level", "native_output_level"):
            observation[stem + str(level) + "_gradients"] = [{"finite": True, "abs_max": 0}]
    return observation


for edges in (False, True):
    module.validate_nsd_path(path_fixture(edges))
    require("synthetic_original_path_accepts_" + ("edge" if edges else "empty_chain_zero_branch"), True)
fixture = path_fixture(True)
for name, mutate in (
    ("nonfinite_energy", lambda x: x["scene_observations"][0]["energy_observations"][0]["output"].update(finite=False)),
    ("extra_FP32_cast", lambda x: x["scene_observations"][0]["energy_observations"][0]["actual_squared_pair_contrast"].update(extra_FP32_cast_added=True)),
    ("replayed_energy", lambda x: x["scene_observations"][0]["energy_observations"][0].update(energy_arithmetic_replayed=True)),
    ("wrong_synthesis_order", lambda x: x["scene_observations"][0]["synthesis_observations"].reverse()),
    ("wrong_restoration_id", lambda x: x["scene_observations"][0]["restoration_observations"][0].update(original_node_ids=[999])),
    ("extra_positivity_gate", lambda x: x.update(per_parameter_nonzero_FP32_minimum_effect_gate_added=True)),
):
    corrupt = copy.deepcopy(fixture)
    mutate(corrupt)
    refuses("synthetic_path_" + name + "_refused", lambda c=corrupt: module.validate_nsd_path(c))
worker = module.NATIVE / "worker.py"
producer = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native/worker.py"
require("complete_original_resources_function_byte_exact",
        module.source_function(worker, "resources") == module.source_function(producer, "resources"))
require("current_runtime_and_stage_literals_correct",
        'manifest["root"] == "/data/songcl/Project/Cluster_project/Cluster_psc_20261106"' in text
        and '"/data/songcl/Project/Cluster_project/pipeline/nsd_"' in text
        and "Cluster_hvd_20261106" not in text and "/pipeline/psc_" not in text)
require("original_resource_thresholds_retained",
        'actual["before"]["memory_free_mib"] >= 20000' in text
        and 'rc["profile"]["flops_g"] <= 10' in text
        and 'rb["peak_allocated_bytes"] * 1.15' in text
        and 'rc["warmup"] == 20 and rc["repeat"] == 100' in text)
require("whole_core_not_per_parameter_controls_retained",
        'gradient["abs_max"] > 0' in text and '"spatial_dirichlet"' in text
        and "original_three_raw_skips_and_exact_HCG_inputs" in text)
require("native_execution_directory_absent_no_actual_results_synthesized", not module.EXECUTION.exists())
require("normalization_output_not_created", not module.OUTPUT.exists())
require("no_bytecode_directory", not (HERE / "__pycache__").exists())
record = {"schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
          "author_actual_child_thread": os.environ["CODEX_THREAD_ID"], "software_checks_passed": True,
          "check_count": len(RESULTS), "checks": RESULTS, "fixtures": "CLEARLY_SYNTHETIC_PARSER_TESTS_ONLY",
          "normalizer_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "independent_review": False, "native_status": "NOT_RUN", "resources_status": "NOT_RUN",
          "GPU_SSH_model_execution": False, "native_or_resource_PASS_artifact_created": False,
          "root_guard_spoofed": False, "raw_results_or_shared_ledgers_modified": False}
with (HERE / "software_validation.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"software_checks_passed": True, "check_count": len(RESULTS),
                  "normalizer_sha256": record["normalizer_sha256"]}))
