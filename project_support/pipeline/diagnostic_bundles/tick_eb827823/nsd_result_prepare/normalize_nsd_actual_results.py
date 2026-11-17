"""Normalize only complete actual NSD results; never admit, enqueue or execute."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import math
import os
import re
import statistics
import sys
import yaml

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / ("results_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ"))
OWNER_KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
TICK = HERE.parent
EXECUTION = TICK / "nsd_execution"
ACTIVATION = TICK / "nsd_current_activation"
NATIVE = ACTIVATION / "native"
PROTOCOL = ROOT / "pipeline/diagnostic_bundles/tick_2e51495f/reserve_candidate/native_protocol.md"
PROOF = ROOT / "pipeline/diagnostic_bundles/tick_c706ca80/nsd_compatible_source/compatible_source_version.json"
SOURCE_REVIEW = ROOT / "pipeline/diagnostic_bundles/tick_c706ca80/nsd_compatible_source_independent_review.json"
TOKEN = "eb827823f30543d8aa8609643034f996"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CID = "hierarchy-native-spatial-dirichlet-composition"
SOURCE = "f6257de79148581334ee495e6e2d60ccb525457c"
PARENT = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
GOAL = "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
PAIRS = (("smoke", "champion"), ("smoke", "candidate"), ("resources", "champion"), ("resources", "candidate"))
CHECKS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def check(name, condition):
    CHECKS.append({"name": name, "passed": bool(condition)})
    if not condition:
        raise ValueError("Actual result validation refused: " + name)


def guard():
    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_eb827823/nsd_result_prepare"
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert os.environ.get("CODEX_THREAD_ID") == THREAD
    assert sys.dont_write_bytecode and os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert OUTPUT.resolve().is_relative_to(HERE.resolve())
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return owner


def save(name, value):
    guard()
    path = OUTPUT / name
    assert path.parent == OUTPUT and Path(name).name == name
    OUTPUT.mkdir(exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return ref(path)


def finite(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def percentile90(values):
    ordered = sorted(values)
    index = (len(ordered) - 1) * 0.9
    lo = math.floor(index)
    return ordered[lo] + (ordered[math.ceil(index)] - ordered[lo]) * (index - lo)


def source_function(path, name):
    text = path.read_text(encoding="utf-8")
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(text, node)



def preserve_partial(status, missing=None, error=None):
    guard()
    entries = {}
    for mode, target in PAIRS:
        path = EXECUTION / (mode + "_" + target + "_execution.json")
        if path.is_file():
            try:
                value = read(path)
                entries[mode + "_" + target] = {"evidence": ref(path), "actual_raw_wrapper": value}
            except Exception as malformed:
                entries[mode + "_" + target] = {"evidence": ref(path), "parse_error": str(malformed)}
    return save("partial_actual_results.json", {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": status, "candidate_id": CID, "source_commit": SOURCE,
        "runtime_code_commit": PARENT, "owner_provenance_only": {
            key: read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")[key] for key in OWNER_KEYS},
        "missing": missing or [], "error_type": type(error).__name__ if error else None,
        "error": str(error) if error else None, "checks_before_refusal": CHECKS,
        "actual_results_preserved": entries, "PASS_artifacts_written": False,
        "native_pass_claimed": False, "resources_pass_claimed": False,
        "shared_or_raw_files_written": False, "GPU_SSH_model_execution": False,
        "failure_scope": "Observed implementation/data/resource evidence only; no whole-mechanism rejection.",
        "conditional_memory_rule": "Above15% requires actual trained +0.003mIoU retention evidence; never synthesized.",
        "unrelated_parent_runtime_root_causes": "UNKNOWN; not a NSD scientific gate.",
    })


def validate_external_arm_identity(result, mode, target):
    package = "framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort" + ("_nsd" if target == "candidate" else "")
    expected = {"candidate_id": "hierarchy-native-spatial-dirichlet-composition", "code_commit": "f6257de79148581334ee495e6e2d60ccb525457c",
                "experiment_id": "M232-NSD", "goal_sha256": GOAL,
                "config": "configs/Quard/ctf_hcg_csort_nsd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nsd.yaml",
                "mode": mode, "target": target, "model_package": package}
    check("external_literal_NSD_arm_identity_" + mode + "_" + target,
          mode in ("smoke", "resources") and target in ("champion", "candidate")
          and isinstance(result, dict) and all(result.get(k) == v for k, v in expected.items()))


def validate_nsd_path(observation):
    step = str(observation["forward"])
    check("NSD_original_native_coordinate_encoder_refs_" + step,
          observation["exact_original_decoder_padded_positions_reference"] is True
          and observation["exact_original_encoder_feature_and_mask_references"] is True
          and observation["actual_three_LN_calls"] == [1, 1, 1]
          and observation["native_positions"]["finite"] is True
          and observation["native_positions"]["shape"][-1] == 3
          and observation["per_parameter_nonzero_FP32_minimum_effect_gate_added"] is False)
    active = [scene for scene in observation["scene_observations"] if scene["true_supported_nodes_by_scale"][0] > 0]
    check("NSD_original_supported_scene_count_" + step, len(active) == observation["actual_supported_scene_count"])
    for index, scene in enumerate(active):
        suffix = step + "_scene" + str(index)
        counts = scene["true_supported_nodes_by_scale"]
        check("NSD_original_single_call_topology_" + suffix,
              scene["actual_original_support_builder_calls"] == 1
              and scene["actual_original_valid_coordinate_and_feature_mask_reference"] is True
              and all(scene[k] == 3 for k in ("actual_chain_energy_calls", "actual_chain_builder_calls",
                  "actual_analysis_calls", "actual_synthesis_calls", "actual_final_index_copy_calls")))
        energies = scene["energy_observations"]
        check("NSD_original_three_chain_levels_" + suffix,
              len(energies) == 3 and [x["level"] for x in energies] == [0, 1, 2])
        for level, energy in enumerate(energies):
            has_edges = energy["actual_edge_count"] > 0
            channels = energy["output"]["shape"][-1]
            check("NSD_original_coordinate_chain_tie_mean_squared_contrast_" + suffix + "_" + str(level),
                  energy["original_calls"] == 1 and energy["returned_original_object_unchanged"] is True
                  and energy["energy_arithmetic_replayed"] is False
                  and all(energy[k]["finite"] is True for k in ("input", "native_coordinates", "output"))
                  and energy["output"]["shape"] == [counts[level], channels]
                  and energy["actual_coordinate_mean_and_contrast_mean_calls"] == (2 if has_edges else 0)
                  and energy["original_empty_chain_zero_branch"] is (not has_edges)
                  and energy["optional_boundary_coverage_is_not_a_new_nonzero_or_resampling_gate"] is True)
            if has_edges:
                square = energy["actual_squared_pair_contrast"]
                check("NSD_original_square_native_dtype_" + suffix + "_" + str(level),
                      square["original_calls"] == 1 and square["input_dtype_equals_output_dtype"] is True
                      and square["extra_FP32_cast_added"] is False
                      and square["input"]["finite"] is True and square["output"]["finite"] is True)
        check("NSD_six_original_center_calls_plus_optional_chain_means_" + suffix,
              scene["actual_group_mean_calls"] == 6 + sum(x["actual_coordinate_mean_and_contrast_mean_calls"] for x in energies)
              and len(scene["mean_observations"]) == scene["actual_group_mean_calls"]
              and all(x["original_calls"] == 1 and x["returned_original_object_unchanged"] is True
                      and x["input"]["finite"] is True and x["output"]["finite"] is True for x in scene["mean_observations"]))
        for kind, order, width in (("analysis", [0, 1, 2], 3), ("synthesis", [2, 1, 0], 2)):
            stages = scene[kind + "_observations"]
            check("NSD_original_shared_" + kind + "_" + suffix,
                  len(stages) == 3 and [x["level"] for x in stages] == order
                  and all(x["original_calls"] == 1 and x["actual_original_shared_module"] is True
                          and x["no_replay_or_replacement"] is True
                          and x["input"]["finite"] is True and x["output"]["finite"] is True
                          and x["input"]["shape"] == [counts[x["level"]], width * x["output"]["shape"][-1]] for x in stages))
        restored = scene["restoration_observations"]
        check("NSD_original_supported_id_restoration_" + suffix,
              len(restored) == 3 and [x["level"] for x in restored] == [0, 1, 2]
              and all(x["original_calls"] == 1 and x["actual_synthesis_delta_ref"] is True
                      and x["zero_initialized_destination"] is True and x["returned_original_object_unchanged"] is True
                      and x["original_node_ids"] == scene["nodes"][x["level"]] and x["output"]["finite"] is True for x in restored))
    for level in range(3):
        for key in ("native_normalized_level" + str(level) + "_gradients", "native_output_level" + str(level) + "_gradients"):
            check("NSD_original_finite_observed_backward_" + step + "_" + key,
                  bool(observation[key]) and all(x["finite"] is True for x in observation[key]))



def main():
    owner = guard()
    missing = [mode + "_" + target + "_execution.json" for mode, target in PAIRS
               if not (EXECUTION / (mode + "_" + target + "_execution.json")).is_file()]
    if missing:
        partial = preserve_partial("WAITING_ACTUAL_EXECUTION_FILES", missing=missing)
        print(json.dumps({"status": "WAITING_ACTUAL_EXECUTION_FILES", "missing": missing, "partial": partial, "PASS_artifacts_written": False}))
        return
    manifest = read(EXECUTION / "native_manifest.json")
    binding = read(EXECUTION / "execution_binding.json")
    lease = read(EXECUTION / "execution_lease.json")
    proof = read(PROOF)
    config = manifest["config"]
    base = {"id": "M232-NSD", "candidate_id": CID, "config": config, "code_commit": SOURCE,
            "goal_sha256": GOAL, "recorded_at": datetime.now(timezone.utc).isoformat()}
    input_paths = [EXECUTION / name for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    raw = {}
    check("manifest_exact_identity_source_runtime_goal", manifest["candidate_id"] == CID and manifest["code_commit"] == SOURCE
          and manifest["runtime_code_commit"] == PARENT and manifest["goal_sha256"] == GOAL
          and manifest["root"] == "/data/songcl/Project/Cluster_project/Cluster_psc_20261106")
    check("goal_unchanged", sha(ROOT / "pipeline/goal.json") == GOAL)
    check("binding_manifest_lease_match", binding["native_manifest_sha256"] == sha(EXECUTION / "native_manifest.json")
          == lease["native_manifest_sha256"] and binding["execution_lease_sha256"] == sha(EXECUTION / "execution_lease.json")
          and binding["code_commit"] == SOURCE and binding["runtime_code_commit"] == PARENT)
    owner_keys = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
    check("execution_actual_current_owner", binding["owner"] == {k: owner[k] for k in owner_keys}
          and manifest["current_token"] == lease["token"] == TOKEN)
    check("source_compatible_proof_and_review", proof["source_commit"] == SOURCE and proof["parent_commit"] == PARENT
          and read(SOURCE_REVIEW)["passed"] is True and len(proof["source_files_exact9"]) == 9)
    for mode, target in PAIRS:
        name = mode + "_" + target
        path, request_path = EXECUTION / (name + "_execution.json"), EXECUTION / (name + "_request.json")
        entry, request = read(path), read(request_path)
        result = entry.get("result") or {}
        validate_external_arm_identity(result, mode, target)
        raw[(mode, target)] = result
        input_paths.extend((path, request_path))
        expected = {"project": "cluster_project", "candidate_id": CID, "code_commit": SOURCE,
                    "stage": binding["stage"], "token": TOKEN, "request_id": request["request_id"],
                    "operation": "run", "physical_gpu": 0, "gpu_uuid": binding["gpu_uuid"],
                    "native_manifest_sha256": binding["native_manifest_sha256"]}
        check(name + "_wrapper_identity", entry["identity"] == expected and request == {**expected, "mode": mode, "target": target})
        check(name + "_actual_terminal_success", entry.get("certainty") == "terminal"
              and entry.get("returncode") == 0 and result.get("execution_completed") is True)
        check(name + "_original_command", entry["command"] == [
            "/home/songcl/.conda/envs/project_cluster/bin/python", "-B", binding["stage"] + "/worker.py",
            "--lease", binding["stage"] + "/execution_lease.json", "--mode", mode, "--target", target])
        identity = {"candidate_id": CID, "experiment_id": "M232-NSD", "code_commit": SOURCE,
                    "goal_sha256": GOAL, "config": config, "mode": mode, "target": target,
                    "stage": binding["stage"], "physical_gpu": 0, "gpu_uuid": binding["gpu_uuid"],
                    "current_token": TOKEN, "native_manifest_sha256": binding["native_manifest_sha256"],
                    "diagnostic_worker_sha256": sha(NATIVE / "worker.py"),
                    "runtime_sha256": sha(NATIVE / "native_runtime.py"),
                    "context_sha256": owner["context_sha256"], "pending_sha256": owner["pending_sha256"],
                    "tick_generated_at": owner["generated_at"], "deadline_at": owner["deadline_at"]}
        check(name + "_raw_identity", all(result.get(k) == v for k, v in identity.items()))
        expected_sources = manifest["candidate_source_hashes"] if target == "candidate" else manifest["assets"]["source_hashes"]
        check(name + "_source_and_YAML_exact", result.get("source_hashes") == expected_sources
              and result.get("config_sha256") == result.get("original_config_sha256") == manifest["candidate_config_sha256"]
              and result.get("native_train_source_sha256") == manifest["assets"]["native_train_source_sha256"]
              and result.get("native_model_and_yaml_unchanged") is True)
        check(name + "_native_pretrain_seed", result.get("initialization", {}).get("kind") == "native_train_pretrain"
              and result["initialization"]["seed"] == 1999 and result["initialization"]["trained_m95_checkpoint_loaded"] is False
              and result["initialization"]["sha256"] == manifest["assets"]["pretrain_sha256"])

    check("manifest_exact_activation_template_projection", manifest == {
        **read(NATIVE / "manifest_template.json"),
        "current_token": TOKEN, "stage": "/data/songcl/Project/Cluster_project/pipeline/nsd_" + TOKEN[:8] + "_gpu0",
        "tick_generated_at": owner["generated_at"], "deadline_at": owner["deadline_at"],
        "physical_gpu": 0, "gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c", "allowed_gpus": [0],
        "context_sha256": owner["context_sha256"], "pending_sha256": owner["pending_sha256"], "runtime_code_commit": PARENT})
    check("NSD_source_proof_and_review_hashes", sha(PROOF) == "e1a03ed4f1631d78f427fedc153d54bf7a3a0a94bcb2272e11c7caf19c1e3302"
          and sha(SOURCE_REVIEW) == "32609b8720b466713911a3d93650272f5ba4e376218253ef5dd261e5992758d2"
          and sha(PROTOCOL) == "ab5675efd2d72432c827d60095d3bddbd6fef53fa3b0a2764af5a9f9ba61dee4")
    check("exact_reviewed_worker_and_runtime", sha(NATIVE / "worker.py") == "cd1cb8b000b7109db99b7bb44b69867d1c3bb5e63466a749b51bb4d35fd09112"
          and sha(NATIVE / "native_runtime.py") == "8ca969c6b4d7099fcf4e407d27ef979e93070a2be06f5f9784f3eed8a29c48f9")
    for (mode, target), actual in raw.items():
        for boundary in ("before", "after"):
            observed = actual[boundary]
            row = [value.strip() for value in observed["gpu"].split(",")]
            check(mode + "_" + target + "_" + boundary + "_actual_authorized_boundary",
                  row[:2] == ["0", binding["gpu_uuid"]]
                  and observed["resource_authorization"] == manifest["resource_authorization"]
                  and observed["resource_memory_policy"] == manifest["resource_memory_policy"]
                  and observed["measurement_scope"] == manifest["resource_memory_policy"]["measurement_scope"]
                  and observed["exclusive_measurement_claimed"] is False
                  and observed["cooperative_project_locks_held"] == (0 if boundary == "before" else 3)
                  and datetime.fromisoformat(owner["generated_at"]) <= datetime.fromisoformat(observed["observed_at"]) < datetime.fromisoformat(owner["deadline_at"]))
        check(mode + "_" + target + "_before_original20000MiB_budget",
              actual["before"]["memory_free_mib"] >= 20000
              and actual["before"]["usable_under_current_overlay_policy"] is True)
        if mode == "resources":
            check(target + "_original121_predict_calls_no_optimizer_or_loss",
                  actual["native_predict_calls"] == 121 and actual["optimizer_steps"] == actual["native_loss_forwards"] == actual["native_criterion_backwards"] == 0)
    input_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in input_paths}
    champion, candidate = raw["smoke", "champion"], raw["smoke", "candidate"]
    for target, result in (("champion", champion), ("candidate", candidate)):
        check(target + "_two_natural_original_loss_steps", result.get("optimizer_steps") == result.get("native_loss_forwards")
              == result.get("native_criterion_backwards") == 2
              and len(result.get("losses", [])) == len(result.get("batches", [])) == len(result.get("steps", [])) == 2
              and all(finite(x) for x in result["losses"]) and result.get("native_data_loaded") is True
              and result.get("native_train_function_executed") is True and result.get("backward_finite") is True
              and result.get("native_smoke_checks_passed") is True and result.get("intended_path_observed") is True)
        check(target + "_no_extra_backward_or_training", result.get("auxiliary_autograd_grad_or_backward_used") is False
              and result.get("training_checkpoint_saved") is False and result.get("new_training") == 0)
        check(target + "_finite_original_backward", all(s.get("all_observed_gradients_finite") is True
              and not s.get("nonfinite_parameter_names") and s.get("optimizer_step_completed") is True for s in result["steps"]))
        check(target + "_single_inst_mask_path", len(result.get("inst_to_mask_path_observations", [])) == 2
              and all(x.get("single_native_inst_update_exact") is True and x.get("new_extra_injection") is False
                      for x in result["inst_to_mask_path_observations"]))
    common_c, common_b = candidate["common_initialized_parameters"], champion["common_initialized_parameters"]
    check("paired835_common_named_tensors_shapes_and_values", common_c == common_b
          and common_c["tensor_count"] == len(common_c["names"]) == len(common_c["shapes"]) == 835
          and re.fullmatch(r"[0-9a-f]{64}", common_c["sha256"]) is not None) 
    check("original_common_initialization_exclusions_only", common_c["excluded_name_prefixes"] == [
          "dec.cluster_att.cluster_ffn.0.", "dec.cluster_att.cluster_ffn.1.",
          "dec.cluster_att.cluster_ffn.2.", "dec.cluster_att.spatial_dirichlet."])
    check("paired_two_complete_natural_batch_fingerprints", candidate["batches"] == champion["batches"])
    check("paired_native_initialization_data_optimizer_schedule", candidate["initialization"] == champion["initialization"]
          and candidate["data_source"] == champion["data_source"]
          and candidate["native_dataloader_config"] == champion["native_dataloader_config"]
          and candidate["optimizer_type"] == champion["optimizer_type"] == "AdamW"
          and candidate["scheduler_type"] == champion["scheduler_type"] == "PolyLR")
    gradient_summary = []
    for step in candidate["steps"]:
        gradient = step["whole_spatial_dirichlet_weight_gradient"]
        weight_changed = step["weight_before_step_hash"]["spatial_dirichlet"] != step["weight_after_step_hash"]["spatial_dirichlet"]
        module_changed = step["module_before_step_hash"]["spatial_dirichlet"] != step["module_after_step_hash"]["spatial_dirichlet"]
        check("whole_core_gradient_and_update_step" + str(step["forward"]),
              gradient["finite"] is True and finite(gradient["abs_max"]) and gradient["abs_max"] > 0
              and step["whole_spatial_dirichlet_weight_updated"] is weight_changed and weight_changed
              and step["whole_spatial_dirichlet_module_updated"] is module_changed and module_changed)
        gradient_summary.append({"forward": step["forward"], "aggregate_weight_gradient": gradient,
                                 "aggregate_weight_updated": weight_changed, "aggregate_module_updated": module_changed})
    observations = candidate["NSD_spatial_dirichlet_observations"]
    check("two_actual_NSD_path_observations", len(observations) == 2)
    check("original_three_raw_skips_and_exact_HCG_inputs",
          len(candidate["hcg_readbacks"]) == 2
          and all(x["NSD_original_three_skips_and_exact_HCG_inputs"] == [True, True, True]
                  for x in candidate["hcg_readbacks"]))
    path_summary = []
    for observation in observations:
        count = observation["actual_supported_scene_count"]
        check("actual_production_NSD_path_step" + str(observation["forward"]),
              observation["actual_true_fine_paths"] > 0 and count > 0
              and all(observation[k] == 3 * count for k in ("actual_chain_energy_calls", "actual_chain_builder_calls",
                  "actual_analysis_calls", "actual_synthesis_calls", "actual_final_index_copy_calls"))
              and observation["actual_production_NSDirichlet_path_observed"] is True
              and observation["no_feature_energy_or_model_replay"] is True
              and ((observation["actual_internal_backward_callbacks"] > 0
                    and observation["all_observed_internal_gradients_finite"] is True)
                   or (observation["actual_internal_backward_callbacks"] == 0
                       and observation["all_observed_internal_gradients_finite"] is None)))
        validate_nsd_path(observation)
        path_summary.append({key: value for key, value in observation.items() if isinstance(value, (str, int, float, bool))})
    values = yaml.safe_load((NATIVE / "candidate.yaml").read_text(encoding="utf-8"))
    check("original_data_seed_schedule_saved_YAML", values["train"]["seed"] == 1999 and values["train"]["epochs"] == 50
          and values["lr_scheduler"]["max_iters"] == 70 and values["dataloader"]["train"]["batch_size"] == 2
          and values["dataloader"]["train"]["num_workers"] == 4 and values["dataloader"]["train"]["persistent_workers"] is True)
    rb, rc = raw["resources", "champion"], raw["resources", "candidate"]
    check("matched_resource_fixture", all(rb[k] == rc[k] for k in (
        "input_sha256", "scan_ids", "ann_ids", "batch_size", "lang_num_max", "warmup", "repeat", "initialization", "data_source"))
        and rc["batch_size"] == rc["lang_num_max"] == 1 and rc["warmup"] == 20 and rc["repeat"] == 100)
    check("same_original_profiler_handlers", rb["profile"]["profiler_file_sha256"] == rc["profile"]["profiler_file_sha256"]
          == {"flop_count": "b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba",
              "jit_analysis": "110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31",
              "jit_handles": "ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129"})
    producer = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native/worker.py"
    check("complete_original_resource_function_byte_exact", source_function(NATIVE / "worker.py", "resources") == source_function(producer, "resources"))
    for target, result in (("champion", rb), ("candidate", rc)):
        times = result["measurements_ms"]
        check(target + "_all100_resource_measurements_recomputed", len(times) == 100 and all(finite(x) and x > 0 for x in times)
              and math.isclose(statistics.median(times), result["median_ms"], rel_tol=1e-12)
              and math.isclose(percentile90(times), result["p90_ms"], rel_tol=1e-12)
              and result["parameter_flags_preserved"] is True and result["source_body_executed_without_replacement"] is True
              and result["validation_accuracy_evaluated_for_selection"] is False
              and isinstance(result["profile"]["unsupported_ops"], dict) and bool(result["profile"]["by_operator"]))
    over_memory = rc["peak_allocated_bytes"] > rb["peak_allocated_bytes"] * 1.15
    check("original_whole_model10G_gate", finite(rc["profile"]["flops_g"]) and rc["profile"]["flops_g"] <= 10
          and rc["profile"]["within10G"] is True)
    check("original_conditional15percent_memory_policy", not over_memory)
    # An above15% result requires the existing measured +0.003mIoU retention
    # evidence. This normalizer never invents trained gain or rejects a mechanism.
    check("raw_input_files_preserved", all(sha(ROOT / name) == digest for name, digest in input_hashes.items()))
    failures = [item["name"] for item in CHECKS if not item["passed"]]
    evidence = [ref(EXECUTION / (mode + "_" + target + "_execution.json")) for mode, target in PAIRS]
    evidence += [ref(EXECUTION / name) for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    evidence += [ref(PROOF), ref(SOURCE_REVIEW), ref(PROTOCOL), ref(NATIVE / "worker.py"), ref(NATIVE / "native_runtime.py")]
    audit = {**base, "passed": not failures, "checks": CHECKS, "check_count": len(CHECKS), "failed_checks": failures,
             "actual_input_files": input_hashes, "original_thresholds_only": True,
             "per_row_map_bias_positivity_or_FP32_minimum_effect_gates_added": False,
             "root_or_independent_actual_review_completed_by_this_author": False,
             "shared_state_or_raw_result_written": False, "GPU_model_execution_by_normalizer": False}
    if failures:
        audit["status"] = "ACTUAL_FAILURE_OR_UNVERIFIED_GATE_PRESERVED_NO_ADMISSION_DRAFT"
        result_ref = save("normalization_audit.json", audit)
        print(json.dumps({"status": audit["status"], "failed_checks": failures, "evidence": result_ref}))
        return
    smoke = {**base, "passed": True, "steps": 2, "losses": candidate["losses"], "champion_losses": champion["losses"],
             "native_data_loaded": True, "backward_finite": True, "intended_path_observed": True,
             "split": "train", "command": candidate["actual_train_command"], "data_source": candidate["data_source"],
             "paired_TRAIN_batches": {"shared_initialization_verified": True, "two_natural_train_batches": True,
                 "common_tensor_count": 835, "common_parameter_count": common_c["parameter_count"],
                 "common_sha256": common_c["sha256"], "excluded_name_prefixes": common_c["excluded_name_prefixes"],
                 "batches": candidate["batches"]},
             "whole_NSD_core_original_loss_gradient_and_update": gradient_summary,
             "actual_NSD_path_observations": path_summary, "evidence": evidence,
             "limitations": ["Two natural TRAIN steps establish technical execution only, not trained efficacy or novelty.",
                 "Smoke memory includes observer hooks and snapshots; it is not pure optimizer TRAIN memory.",
                 "Individual rows/maps/biases/statistic components may be zero; no additional coverage or positivity gate was added."]}
    smoke_ref = save("native_smoke.json", smoke)
    metrics = {"flops_g": (rb["profile"]["flops_g"], rc["profile"]["flops_g"])}
    metrics.update({key: (rb[key], rc[key]) for key in ("median_ms", "p90_ms", "peak_allocated_bytes", "peak_reserved_bytes", "parameters")})
    resources = {**base, "schema_version": 1, "experiment_id": "M232-NSD", "passed": True,
                 "decision": "ORIGINAL_RESOURCE_GATE_PASSED_ACTUAL_MATCHED_SAME_OWNER_FIXTURE",
                 "champion_actual": evidence[2], "candidate_actual": evidence[3],
                 "pairing": {key: rc[key] for key in ("input_sha256", "scan_ids", "ann_ids", "batch_size", "lang_num_max", "warmup", "repeat")},
                 "runtime_code_commit": PARENT, "runtime_root": manifest["root"], "physical_gpu": 0, "gpu_uuid": binding["gpu_uuid"],
                 "measured": {key: {"champion": pair[0], "candidate": pair[1]} for key, pair in metrics.items()},
                 "delta": {key: {"absolute": pair[1] - pair[0], "percent": (pair[1] / pair[0] - 1) * 100} for key, pair in metrics.items()},
                 "full_profile": {"champion": rb["profile"], "candidate": rc["profile"]},
                 "all100_times_each_and_statistics_recomputed": True,
                 "original_gates": {"whole_model_counted_FLOPs_at_most10G": True,
                     "peak_prediction_allocated_memory_increase_above15percent": over_memory,
                     "conditional_retention_gain_requirement_triggered": over_memory,
                     "trained_mIoU_gain_measured": False, "new_latency_cutoff_added": False},
                 "resource_boundary_observations": {target: {key: result[key] for key in ("before", "after", "measurement_scope", "exclusive_measurement_claimed")}
                                                    for target, result in (("champion", rb), ("candidate", rc))},
                 "evidence": evidence, "limitations": [
                     "Sequential authorized-overlay measurements; not exclusive timing or a causal speed claim.",
                     "Complete original profiler unsupported-op counts are retained; counted FLOPs use the original standard.",
                     "Full optimizer TRAIN peak and no-cluster baseline delta remain UNKNOWN.",
                     "Memory increase is below15%; no trained +0.003 mIoU condition is triggered. Efficacy/novelty remain UNKNOWN."]}
    resource_ref = save("resources.json", resources)
    constraints = {**base, "experiment_id": "M232-NSD", "parent_commit": PARENT, "passed": True,
                   "actual_git_source_hashes": proof["source_files_exact9"], "exact_nine_paths_only": True,
                   "source_version": ref(PROOF), "independent_source_review": ref(SOURCE_REVIEW),
                   "native_smoke": smoke_ref, "resources": resource_ref, "protocol": ref(PROTOCOL),
                   "source_unchanged_from_tested_bytes": True, "config_is_independent_native_YAML": True,
                   "fixed_original_data_seed_schedule_loss_precision": True,
                   "native_yaml_record": {"seed": 1999, "epochs": 50, "max_iters": 70,
                                          "precision_intervention": False, "optimizer": candidate["optimizer_type"],
                                          "scheduler": candidate["scheduler_type"], "data_source": candidate["data_source"]},
                   "mainline": "Actual original native coordinate-chain spatial Dirichlet energy/shared analysis/synthesis core replaces original three FFNs and reaches original HCG/rawskip/single inst_feats/ILA/mask path.",
                   "no_goal_server_bans_holds_or_protocol_changes": True,
                   "efficacy": "UNKNOWN", "novelty": "UNKNOWN", "scientific_admission": False,
                   "review_status": "PENDING_ROOT_AND_INDEPENDENT_ACTUAL_GATE_REVIEW", "evidence": evidence}
    constraints_ref = save("constraints_independence.json", constraints)
    authorization = {"path": "pipeline/authorizations/experiment_first_20261021.json",
                     "sha256": "2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8"}
    draft = {**base, "profile": "experiment_first", "authorization": authorization,
             "native_smoke": smoke_ref, "decision": None, "draft": True, "canonical_receipt": False,
             "admission_granted": False, "requires_root_and_independent_actual_review": True,
             "independent_reviews": [], "gates": {
                 "native_backward": {"passed": True, "evidence": [smoke_ref]},
                 "resources": {"passed": True, "evidence": [resource_ref]},
                 "independence": {"passed": True, "evidence": [constraints_ref]},
                 "constraints": {"passed": True, "evidence": [constraints_ref]}},
             "efficacy": "UNKNOWN; technical checks do not establish training gain or novelty."}
    # Validate only the existing read-only canonical smoke interface, not admission.
    sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
    import experiment_first
    experiment_first.validate_smoke(ROOT, draft)
    audit["canonical_validate_smoke_actual_passed"] = True
    audit["status"] = "ACTUAL_RESULTS_NORMALIZED_PENDING_ROOT_AND_INDEPENDENT_REVIEW"
    audit_ref = save("normalization_audit.json", audit)
    draft["normalization_audit"] = audit_ref
    # This is only a local non-admitting draft, with no decision or root review.
    draft_ref = save("draft_receipt.json", draft)
    print(json.dumps({"status": audit["status"], "check_count": len(CHECKS), "native_smoke": smoke_ref,
                      "resources": resource_ref, "constraints_independence": constraints_ref,
                      "draft_receipt": draft_ref, "normalization_audit": audit_ref,
                      "candidate_losses": candidate["losses"], "resource_measured": resources["measured"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        partial = preserve_partial("ACTUAL_PARTIAL_FAILURE_OR_UNVERIFIED_NO_PASS", error=error)
        print(json.dumps({"status": "ACTUAL_PARTIAL_FAILURE_OR_UNVERIFIED_NO_PASS",
                          "error_type": type(error).__name__, "error": str(error),
                          "partial": partial, "PASS_artifacts_written": False}))
        raise SystemExit(2)
