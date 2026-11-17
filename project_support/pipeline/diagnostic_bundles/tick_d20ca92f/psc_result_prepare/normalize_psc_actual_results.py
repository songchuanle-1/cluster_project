"""Normalize historical validated PSC smoke plus fresh current-owner resources; never execute."""
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
EXECUTION = TICK / "psc_execution"
ACTIVATION = TICK / "psc_current_activation"
NATIVE = ACTIVATION / "native"
PROTOCOL = ROOT / "pipeline/diagnostic_bundles/tick_0f3c54ec/reserve_candidate_prepare/native_protocol.md"
PROOF = ROOT / "pipeline/diagnostic_bundles/tick_12e364dc/psc_compatible_source/compatible_source_version.json"
SOURCE_REVIEW = ROOT / "pipeline/diagnostic_bundles/tick_12e364dc/psc_compatible_source_independent_review.json"
TOKEN = "d20ca92f1b654e24ba9cf29f634307b7"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CID = "hierarchy-native-position-feature-cross-scatter-composition"
SOURCE = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
PARENT = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
GOAL = "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
PAIRS = (("smoke", "champion"), ("smoke", "candidate"), ("resources", "champion"), ("resources", "candidate"))
CHECKS = []
HISTORICAL_TICK = ROOT / "pipeline/diagnostic_bundles/tick_0bb87433"
HISTORICAL_EXECUTION = HISTORICAL_TICK / "psc_execution"
HISTORICAL_ACTIVATION = HISTORICAL_TICK / "psc_current_activation"
HISTORICAL_REVIEW = HISTORICAL_TICK / "psc_partial_actual_independent_review.json"
OWNER_PROVENANCE = {}


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
    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_d20ca92f/psc_result_prepare"
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert os.environ.get("CODEX_THREAD_ID") in (THREAD, "01a1b166-dcbf-7d01-b0cb-c85fff644605")
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
        path = arm_execution(mode) / (mode + "_" + target + "_execution.json")
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
        "evidence_owner_provenance_by_mode": OWNER_PROVENANCE,
        "missing": missing or [], "error_type": type(error).__name__ if error else None,
        "error": str(error) if error else None, "checks_before_refusal": CHECKS,
        "actual_results_preserved": entries, "PASS_artifacts_written": False,
        "native_pass_claimed": False, "resources_pass_claimed": False,
        "shared_or_raw_files_written": False, "GPU_SSH_model_execution": False,
        "failure_scope": "Observed implementation/data/resource evidence only; no whole-mechanism rejection.",
        "conditional_memory_rule": "Above15% requires actual trained +0.003mIoU retention evidence; never synthesized.",
        "unrelated_HVD_root_cause": "UNKNOWN; not a PSC scientific gate.",
    })


def validate_psc_path(observation):
    step = str(observation["forward"])
    check("PSC_original_coordinate_and_encoder_references_step" + step,
          observation["exact_original_decoder_padded_positions_reference"] is True
          and observation["exact_original_encoder_feature_and_mask_references"] is True
          and observation["actual_three_LN_calls"] == [1, 1, 1]
          and observation["native_positions"]["finite"] is True
          and observation["native_positions"]["shape"][-1] == 3)
    scenes = observation["scene_observations"]
    active = [scene for scene in scenes if scene["true_supported_nodes_by_scale"][0] > 0]
    check("PSC_supported_scene_counts_step" + step, len(active) == observation["actual_supported_scene_count"])
    for index, scene in enumerate(active):
        suffix = step + "_scene" + str(index)
        counts = scene["true_supported_nodes_by_scale"]
        check("PSC_original_call_counts_" + suffix,
              all(scene[key] == 1 for key in ("actual_original_builder_calls", "actual_stats_calls",
                  "actual_pack_calls", "actual_factor_concat_calls", "actual_factor_calls",
                  "actual_GELU_calls", "actual_split_calls", "actual_within_between_add_calls"))
              and scene["actual_group_mean_calls"] == 11 and scene["actual_centered_cross_calls"] == 3
              and scene["actual_linear_calls"] == 2 and scene["actual_final_index_copy_calls"] == 3)
        stats, pack = scene["stats_observations"], scene["pack_observations"]
        check("PSC_original_stats_pack_single_calls_" + suffix, len(stats) == len(pack) == 1)
        stats, pack = stats[0], pack[0]
        channels = pack["semantic_inputs"][0]["shape"][-1]
        check("PSC_native_coordinates_and_original_five_moments_" + suffix,
              all(stats[key] is True for key in ("actual_native_mask_selection_observed",
                  "native_coordinate_dtype_cast_observed", "equal_supported_child_center_and_covariance_objects_verified",
                  "coarse_within_input_is_actual_middle_within_plus_between", "returned_original_tuple_unchanged"))
              and stats["moment_arithmetic_replayed"] is False and stats["statistic_nonzero_or_minimum_effect_gate"] is False
              and stats["moment_names"] == ["fine_cross_scatter", "middle_within", "middle_between",
                                           "coarse_within", "coarse_between"]
              and stats["native_coordinate_input"]["finite"] is True
              and stats["native_coordinate_input"]["shape"] == [scene["point_count"], 3]
              and stats["native_coordinate_input"]["dtype"] == stats["point_input"]["dtype"]
              and [value["shape"] for value in stats["outputs"]] == [
                  [counts[0], 3 * channels], [counts[1], 3 * channels], [counts[1], 3 * channels],
                  [counts[2], 3 * channels], [counts[2], 3 * channels]]
              and all(value["finite"] is True for value in stats["outputs"]))
        means, crosses = scene["group_mean_observations"], scene["centered_cross_observations"]
        check("PSC_eleven_actual_means_and_three_signed3xC_crosses_" + suffix,
              len(means) == 11 and [item["ordinal"] for item in means] == list(range(1, 12))
              and len(crosses) == 3 and [item["level"] for item in crosses] == [0, 1, 2]
              and all(item["original_calls"] == 1 and item["input"]["finite"] is True
                      and item["output"]["finite"] is True for item in means)
              and all(item["original_calls"] == 1 and item["arithmetic_replayed"] is False
                      and item["signed_outer_product_width"] == 3 * channels
                      and item["output"]["shape"] == [counts[level], 3 * channels]
                      and all(item[key]["finite"] is True for key in ("positions", "features", "position_center", "feature_center", "output"))
                      for level, item in enumerate(crosses)))
        check("PSC_actual_C_3C_3C_3C_to10C_pack_" + suffix,
              all(pack[key] is True for key in ("moment_inputs_are_actual_returned_objects",
                  "packing_blocks_C_3C_3C_3C", "returned_original_list_unchanged"))
              and pack["packing_replayed"] is False and pack["actual_ancestor_index_select_calls"] == 3
              and [value["shape"] for value in pack["outputs"]] == [[count, 10 * channels] for count in counts]
              and all(value["finite"] is True for value in pack["outputs"]))
        factor, restore = scene["factor_observations"], scene["restoration_observations"]
        check("PSC_original_shared_factor_and_restoration_" + suffix,
              [item["kind"] for item in factor] == ["first_linear", "original_GELU", "second_linear"]
              and factor[0]["input"]["shape"] == [sum(counts), 10 * channels]
              and all(item["input"]["finite"] is True and item["output"]["finite"] is True for item in factor)
              and len(restore) == 3 and [item["level"] for item in restore] == [0, 1, 2]
              and all(item["source_is_actual_factor_split"] is True and item["zero_initialized_destination"] is True
                      and item["returned_original_object_unchanged"] is True and item["output"]["finite"] is True for item in restore))
    for level in range(3):
        for key in ("native_normalized_level" + str(level) + "_gradients", "native_output_level" + str(level) + "_gradients"):
            check("PSC_original_finite_observed_backward_" + step + "_" + key,
                  bool(observation[key]) and all(item["finite"] is True for item in observation[key]))



def arm_execution(mode):
    if mode not in ("smoke", "resources"):
        raise ValueError("Unknown original PSC mode")
    return HISTORICAL_EXECUTION if mode == "smoke" else EXECUTION


def historical_smoke_provenance():
    check("historical_actual_smoke_review181_hash",
          sha(HISTORICAL_REVIEW) == "371d6354e24c8db8806b518e279b293341f36ee457fcdf8d92b4b9400088168c")
    review = read(HISTORICAL_REVIEW)
    check("historical_actual_smoke_pair_independently_validated",
          review["passed"] is True and review["actual_check_count"] == 181
          and review["paired_smoke"]["status"] == "ACTUAL_PAIRED_NATIVE_SMOKE_CHECKS_PASSED")
    for target in ("champion", "candidate"):
        entry = review["actual_arm_evidence"]["smoke_" + target]
        check("historical_smoke_" + target + "_exact_reviewed_wrapper",
              (ROOT / entry["path"]).resolve() == (HISTORICAL_EXECUTION / ("smoke_" + target + "_execution.json")).resolve()
              and sha(ROOT / entry["path"]) == entry["sha256"])
    needed = ("native_manifest.json", "execution_binding.json", "execution_lease.json",
              "smoke_champion_request.json", "smoke_candidate_request.json")
    for name in needed:
        path = HISTORICAL_EXECUTION / name
        original_hash = next(digest for name_, digest in review["inputs_unchanged_after_review"].items()
                             if (ROOT / name_).resolve() == path.resolve())
        check("historical_provenance_file_unchanged:" + name, sha(path) == original_hash)
    manifest, binding, lease = (read(HISTORICAL_EXECUTION / name) for name in needed[:3])
    owner = review["owner_provenance_only"]
    check("historical_smoke_exact_historical_owner_binding",
          binding["owner"] == owner and owner["token"] == "0bb874337dde412e98bbbaac369f3370"
          and binding["native_manifest_sha256"] == lease["native_manifest_sha256"] == sha(HISTORICAL_EXECUTION / "native_manifest.json")
          and binding["execution_lease_sha256"] == sha(HISTORICAL_EXECUTION / "execution_lease.json")
          and lease["token"] == manifest["current_token"] == owner["token"]
          and manifest["code_commit"] == SOURCE and manifest["runtime_code_commit"] == PARENT
          and manifest["goal_sha256"] == GOAL and manifest["candidate_id"] == CID)
    expected = read(HISTORICAL_ACTIVATION / "native/manifest_template.json")
    expected.update(current_token=owner["token"], stage=binding["stage"],
                    tick_generated_at=owner["generated_at"], deadline_at=owner["deadline_at"],
                    physical_gpu=0, gpu_uuid=binding["gpu_uuid"], allowed_gpus=[0],
                    context_sha256=owner["context_sha256"], pending_sha256=owner["pending_sha256"], runtime_code_commit=PARENT)
    check("historical_smoke_original_manifest_projection", manifest == expected)
    OWNER_PROVENANCE["smoke"] = {
        "owner": owner, "execution_directory": HISTORICAL_EXECUTION.relative_to(ROOT).as_posix(),
        "independent_actual_review": ref(HISTORICAL_REVIEW), "reuse": "Immutable validated actual smoke only",
        "historical_expired_lease_used_for_new_execution": False, "copied_raw_into_current_execution": False}
    return {"owner": owner, "manifest": manifest, "binding": binding, "lease": lease}


def main():
    owner = guard()
    historical = historical_smoke_provenance()
    OWNER_PROVENANCE["resources"] = {"owner": {key: owner[key] for key in OWNER_KEYS},
        "execution_directory": EXECUTION.relative_to(ROOT).as_posix(),
        "reuse": "Fresh same-current-owner resource pair required"}
    missing = [mode + "_" + target + "_execution.json" for mode, target in PAIRS
               if not (arm_execution(mode) / (mode + "_" + target + "_execution.json")).is_file()]
    if missing:
        partial = preserve_partial("WAITING_ACTUAL_EXECUTION_FILES", missing=missing)
        print(json.dumps({"status": "WAITING_ACTUAL_EXECUTION_FILES", "missing": missing, "partial": partial, "PASS_artifacts_written": False}))
        return
    manifest = read(EXECUTION / "native_manifest.json")
    binding = read(EXECUTION / "execution_binding.json")
    lease = read(EXECUTION / "execution_lease.json")
    proof = read(PROOF)
    config = manifest["config"]
    base = {"id": "M231-PSC", "candidate_id": CID, "config": config, "code_commit": SOURCE,
            "goal_sha256": GOAL, "recorded_at": datetime.now(timezone.utc).isoformat()}
    input_paths = [EXECUTION / name for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    input_paths += [HISTORICAL_EXECUTION / name for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    input_paths.append(HISTORICAL_REVIEW)
    raw = {}
    check("manifest_exact_identity_source_runtime_goal", manifest["candidate_id"] == CID and manifest["code_commit"] == SOURCE
          and manifest["runtime_code_commit"] == PARENT and manifest["goal_sha256"] == GOAL
          and manifest["root"] == "/data/songcl/Project/Cluster_project/Cluster_hvd_20261106")
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
        arm_directory = arm_execution(mode)
        arm_owner = historical["owner"] if mode == "smoke" else owner
        arm_manifest = historical["manifest"] if mode == "smoke" else manifest
        arm_binding = historical["binding"] if mode == "smoke" else binding
        name = mode + "_" + target
        path, request_path = arm_directory / (name + "_execution.json"), arm_directory / (name + "_request.json")
        entry, request = read(path), read(request_path)
        result = entry.get("result") or {}
        raw[(mode, target)] = result
        input_paths.extend((path, request_path))
        expected = {"project": "cluster_project", "candidate_id": CID, "code_commit": SOURCE,
                    "stage": arm_binding["stage"], "token": arm_owner["token"], "request_id": request["request_id"],
                    "operation": "run", "physical_gpu": 0, "gpu_uuid": arm_binding["gpu_uuid"],
                    "native_manifest_sha256": arm_binding["native_manifest_sha256"]}
        check(name + "_wrapper_identity", entry["identity"] == expected and request == {**expected, "mode": mode, "target": target})
        check(name + "_actual_terminal_success", entry.get("certainty") == "terminal"
              and entry.get("returncode") == 0 and result.get("execution_completed") is True)
        check(name + "_original_command", entry["command"] == [
            "/home/songcl/.conda/envs/project_cluster/bin/python", "-B", arm_binding["stage"] + "/worker.py",
            "--lease", arm_binding["stage"] + "/execution_lease.json", "--mode", mode, "--target", target])
        identity = {"candidate_id": CID, "experiment_id": "M231-PSC", "code_commit": SOURCE,
                    "goal_sha256": GOAL, "config": config, "mode": mode, "target": target,
                    "stage": arm_binding["stage"], "physical_gpu": 0, "gpu_uuid": arm_binding["gpu_uuid"],
                    "current_token": arm_owner["token"], "native_manifest_sha256": arm_binding["native_manifest_sha256"],
                    "diagnostic_worker_sha256": sha(NATIVE / "worker.py"),
                    "runtime_sha256": sha(NATIVE / "native_runtime.py"),
                    "context_sha256": arm_owner["context_sha256"], "pending_sha256": arm_owner["pending_sha256"],
                    "tick_generated_at": arm_owner["generated_at"], "deadline_at": arm_owner["deadline_at"]}
        check(name + "_raw_identity", all(result.get(k) == v for k, v in identity.items()))
        expected_sources = arm_manifest["candidate_source_hashes"] if target == "candidate" else arm_manifest["assets"]["source_hashes"]
        check(name + "_source_and_YAML_exact", result.get("source_hashes") == expected_sources
              and result.get("config_sha256") == result.get("original_config_sha256") == arm_manifest["candidate_config_sha256"]
              and result.get("native_train_source_sha256") == arm_manifest["assets"]["native_train_source_sha256"]
              and result.get("native_model_and_yaml_unchanged") is True)
        check(name + "_native_pretrain_seed", result.get("initialization", {}).get("kind") == "native_train_pretrain"
              and result["initialization"]["seed"] == 1999 and result["initialization"]["trained_m95_checkpoint_loaded"] is False
              and result["initialization"]["sha256"] == arm_manifest["assets"]["pretrain_sha256"])

    check("manifest_exact_activation_template_projection", manifest == {
        **read(NATIVE / "manifest_template.json"),
        "current_token": TOKEN, "stage": "/data/songcl/Project/Cluster_project/pipeline/psc_" + TOKEN[:8] + "_gpu0",
        "tick_generated_at": owner["generated_at"], "deadline_at": owner["deadline_at"],
        "physical_gpu": 0, "gpu_uuid": "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c", "allowed_gpus": [0],
        "context_sha256": owner["context_sha256"], "pending_sha256": owner["pending_sha256"], "runtime_code_commit": PARENT})
    check("PSC_source_proof_and_review_hashes", sha(PROOF) == "9c6308fe6d166216123ef23e871eeacec5e8e3b2b3b9c02fb448364a44d13083"
          and sha(SOURCE_REVIEW) == "7098b020bc414f34eab9013f6f3b94a72ad0d842249ceff7c30a1310cd2bf6d8"
          and sha(PROTOCOL) == "98b12c011260550efd1a87a10dc834d80468ee3523cb3301ddb18c2a4671976a")
    check("exact_reviewed_worker_and_runtime", sha(NATIVE / "worker.py") == "530a5230021fad8d880c37a34c18973b4c556e7dc1536b6c4faaffdd6d6f93d8"
          and sha(NATIVE / "native_runtime.py") == "2468966c25ef12b0c1d06907b39c9f341daa07e2771c026c8920899f8acb72a7")
    for (mode, target), actual in raw.items():
        boundary_owner = historical["owner"] if mode == "smoke" else owner
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
                  and datetime.fromisoformat(boundary_owner["generated_at"]) <= datetime.fromisoformat(observed["observed_at"]) < datetime.fromisoformat(boundary_owner["deadline_at"]))
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
          "dec.cluster_att.cluster_ffn.2.", "dec.cluster_att.position_feature_scatter."])
    check("paired_two_complete_natural_batch_fingerprints", candidate["batches"] == champion["batches"])
    check("paired_native_initialization_data_optimizer_schedule", candidate["initialization"] == champion["initialization"]
          and candidate["data_source"] == champion["data_source"]
          and candidate["native_dataloader_config"] == champion["native_dataloader_config"]
          and candidate["optimizer_type"] == champion["optimizer_type"] == "AdamW"
          and candidate["scheduler_type"] == champion["scheduler_type"] == "PolyLR")
    gradient_summary = []
    for step in candidate["steps"]:
        gradient = step["whole_position_feature_scatter_weight_gradient"]
        weight_changed = step["weight_before_step_hash"]["position_feature_scatter"] != step["weight_after_step_hash"]["position_feature_scatter"]
        module_changed = step["module_before_step_hash"]["position_feature_scatter"] != step["module_after_step_hash"]["position_feature_scatter"]
        check("whole_core_gradient_and_update_step" + str(step["forward"]),
              gradient["finite"] is True and finite(gradient["abs_max"]) and gradient["abs_max"] > 0
              and step["whole_position_feature_scatter_weight_updated"] is weight_changed and weight_changed
              and step["whole_position_feature_scatter_module_updated"] is module_changed and module_changed)
        gradient_summary.append({"forward": step["forward"], "aggregate_weight_gradient": gradient,
                                 "aggregate_weight_updated": weight_changed, "aggregate_module_updated": module_changed})
    observations = candidate["PSC_position_feature_scatter_observations"]
    check("two_actual_PSC_path_observations", len(observations) == 2)
    path_summary = []
    for observation in observations:
        count = observation["actual_supported_scene_count"]
        check("actual_production_PSC_path_step" + str(observation["forward"]),
              observation["actual_true_fine_paths"] > 0 and count > 0
              and all(observation[k] == count for k in ("actual_stats_calls", "actual_pack_calls", "actual_factor_calls", "actual_GELU_calls"))
              and observation["actual_group_mean_calls"] == 11 * count
              and observation["actual_centered_cross_calls"] == 3 * count
              and observation["actual_within_between_add_calls"] == count
              and observation["actual_linear_calls"] == 2 * count and observation["actual_final_index_copy_calls"] == 3 * count
              and observation["statistics_and_packing_from_actual_production_calls"] is True
              and observation["no_feature_or_statistic_replay"] is True
              and ((observation["actual_internal_backward_callbacks"] > 0
                    and observation["all_observed_internal_gradients_finite"] is True)
                   or (observation["actual_internal_backward_callbacks"] == 0
                       and observation["all_observed_internal_gradients_finite"] is None)))
        validate_psc_path(observation)
        path_summary.append({key: value for key, value in observation.items() if isinstance(value, (str, int, float, bool))})

    new_version = read(NATIVE / "source_version_binding.json")
    old_version = read(HISTORICAL_ACTIVATION / "native/source_version_binding.json")
    check("identical_exact9_source_versions_across_evidence_owners",
          new_version["source_files"] == old_version["source_files"] == proof["source_files_exact9"]
          and new_version["code_commit"] == old_version["code_commit"] == SOURCE
          and new_version["parent_commit"] == old_version["parent_commit"] == PARENT)
    check("historical_and_current_same_native_YAML_bytes",
          sha(NATIVE / "candidate.yaml") == sha(HISTORICAL_ACTIVATION / "native/candidate.yaml") == manifest["candidate_config_sha256"])
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
    evidence = [ref(arm_execution(mode) / (mode + "_" + target + "_execution.json")) for mode, target in PAIRS]
    evidence += [ref(EXECUTION / name) for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    evidence += [ref(HISTORICAL_EXECUTION / name) for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    evidence.append(ref(HISTORICAL_REVIEW))
    evidence += [ref(PROOF), ref(SOURCE_REVIEW), ref(PROTOCOL), ref(NATIVE / "worker.py"), ref(NATIVE / "native_runtime.py")]
    audit = {**base, "passed": not failures, "evidence_owner_provenance_by_mode": OWNER_PROVENANCE, "checks": CHECKS, "check_count": len(CHECKS), "failed_checks": failures,
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
             "owner_provenance": OWNER_PROVENANCE["smoke"], "validated_historical_smoke_reused": True,
              "split": "train", "command": candidate["actual_train_command"], "data_source": candidate["data_source"],
             "paired_TRAIN_batches": {"shared_initialization_verified": True, "two_natural_train_batches": True,
                 "common_tensor_count": 835, "common_parameter_count": common_c["parameter_count"],
                 "common_sha256": common_c["sha256"], "excluded_name_prefixes": common_c["excluded_name_prefixes"],
                 "batches": candidate["batches"]},
             "whole_PSC_core_original_loss_gradient_and_update": gradient_summary,
             "actual_PSC_path_observations": path_summary, "evidence": evidence,
             "limitations": ["Two natural TRAIN steps establish technical execution only, not trained efficacy or novelty.",
                 "Smoke memory includes observer hooks and snapshots; it is not pure optimizer TRAIN memory.",
                 "Individual rows/maps/biases/statistic components may be zero; no additional coverage or positivity gate was added."]}
    smoke_ref = save("native_smoke.json", smoke)
    metrics = {"flops_g": (rb["profile"]["flops_g"], rc["profile"]["flops_g"])}
    metrics.update({key: (rb[key], rc[key]) for key in ("median_ms", "p90_ms", "peak_allocated_bytes", "peak_reserved_bytes", "parameters")})
    resources = {**base, "schema_version": 1, "experiment_id": "M231-PSC", "passed": True,
                 "decision": "ORIGINAL_RESOURCE_GATE_PASSED_ACTUAL_MATCHED_SAME_OWNER_FIXTURE",
                 "champion_actual": evidence[2], "candidate_actual": evidence[3],
                 "pairing": {key: rc[key] for key in ("input_sha256", "scan_ids", "ann_ids", "batch_size", "lang_num_max", "warmup", "repeat")},
                 "owner_provenance": OWNER_PROVENANCE["resources"],
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
    constraints = {**base, "experiment_id": "M231-PSC", "parent_commit": PARENT, "passed": True, "evidence_owner_provenance_by_mode": OWNER_PROVENANCE,
                   "actual_git_source_hashes": proof["source_files_exact9"], "exact_nine_paths_only": True,
                   "source_version": ref(PROOF), "independent_source_review": ref(SOURCE_REVIEW),
                   "native_smoke": smoke_ref, "resources": resource_ref, "protocol": ref(PROTOCOL),
                   "source_unchanged_from_tested_bytes": True, "config_is_independent_native_YAML": True,
                   "fixed_original_data_seed_schedule_loss_precision": True,
                   "native_yaml_record": {"seed": 1999, "epochs": 50, "max_iters": 70,
                                          "precision_intervention": False, "optimizer": candidate["optimizer_type"],
                                          "scheduler": candidate["scheduler_type"], "data_source": candidate["data_source"]},
                   "mainline": "Actual position-feature signed cross-scatter hierarchy core replaces original three FFNs and reaches original HCG/single inst_feats/ILA/mask path.",
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
    audit["status"] = "ACTUAL_HISTORICAL_SMOKE_AND_FRESH_RESOURCES_NORMALIZED_PENDING_ROOT_AND_INDEPENDENT_REVIEW"
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
