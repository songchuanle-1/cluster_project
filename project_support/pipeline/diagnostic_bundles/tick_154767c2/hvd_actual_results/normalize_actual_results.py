"""Normalize only complete actual HVD results; never admit, enqueue or execute."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import math
import os
import statistics
import sys
import yaml

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
EXECUTION = TICK / "hvd_execution"
ACTIVATION = TICK / "hvd_current_activation"
NATIVE = ROOT / "pipeline/diagnostic_bundles/tick_c7451cf1/hvd_native_prepare/native"
PROTOCOL = ROOT / "pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare/native_protocol.md"
PROOF = ROOT / "pipeline/diagnostic_bundles/tick_1138a3fc/hvd_compatible_source_version.json"
SOURCE_REVIEW = PROOF.with_name("hvd_compatible_source_independent_review.json")
TOKEN = "154767c278664ba4a7b666c69f12abaa"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CID = "hierarchy-native-variance-decomposition-composition"
SOURCE = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
PARENT = "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
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


def guard():
    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_154767c2/hvd_actual_results"
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert os.environ.get("CODEX_THREAD_ID") != THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return owner


def save(name, value):
    guard()
    path = HERE / name
    assert path.parent == HERE and Path(name).name == name
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


def main():
    owner = guard()
    missing = [mode + "_" + target + "_execution.json" for mode, target in PAIRS
               if not (EXECUTION / (mode + "_" + target + "_execution.json")).is_file()]
    if missing:
        print(json.dumps({"status": "WAITING_ACTUAL_EXECUTION_FILES", "missing": missing, "PASS_artifacts_written": False}))
        return
    manifest = read(EXECUTION / "native_manifest.json")
    binding = read(EXECUTION / "execution_binding.json")
    lease = read(EXECUTION / "execution_lease.json")
    proof = read(PROOF)
    config = manifest["config"]
    base = {"id": "M230-HVD", "candidate_id": CID, "config": config, "code_commit": SOURCE,
            "goal_sha256": GOAL, "recorded_at": datetime.now(timezone.utc).isoformat()}
    input_paths = [EXECUTION / name for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    raw = {}
    check("manifest_exact_identity_source_runtime_goal", manifest["candidate_id"] == CID and manifest["code_commit"] == SOURCE
          and manifest["runtime_code_commit"] == PARENT and manifest["goal_sha256"] == GOAL
          and manifest["root"] == "/data/songcl/Project/Cluster_project/Cluster_mic_20261105")
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
        identity = {"candidate_id": CID, "experiment_id": "M230-HVD", "code_commit": SOURCE,
                    "goal_sha256": GOAL, "config": config, "mode": mode, "target": target,
                    "stage": binding["stage"], "physical_gpu": 0, "gpu_uuid": binding["gpu_uuid"],
                    "current_token": TOKEN, "native_manifest_sha256": binding["native_manifest_sha256"],
                    "diagnostic_worker_sha256": sha(NATIVE / "worker.py"),
                    "runtime_sha256": sha(ACTIVATION / "native_runtime.py"),
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
          and common_c["tensor_count"] == len(common_c["names"]) == len(common_c["shapes"]) == 835)
    check("paired_two_complete_natural_batch_fingerprints", candidate["batches"] == champion["batches"])
    check("paired_native_initialization_data_optimizer_schedule", candidate["initialization"] == champion["initialization"]
          and candidate["data_source"] == champion["data_source"]
          and candidate["native_dataloader_config"] == champion["native_dataloader_config"]
          and candidate["optimizer_type"] == champion["optimizer_type"] == "AdamW"
          and candidate["scheduler_type"] == champion["scheduler_type"] == "PolyLR")
    gradient_summary = []
    for step in candidate["steps"]:
        gradient = step["whole_variance_decomposition_weight_gradient"]
        weight_changed = step["weight_before_step_hash"]["variance_decomposition"] != step["weight_after_step_hash"]["variance_decomposition"]
        module_changed = step["module_before_step_hash"]["variance_decomposition"] != step["module_after_step_hash"]["variance_decomposition"]
        check("whole_core_gradient_and_update_step" + str(step["forward"]),
              gradient["finite"] is True and finite(gradient["abs_max"]) and gradient["abs_max"] > 0
              and step["whole_variance_decomposition_weight_updated"] is weight_changed and weight_changed
              and step["whole_variance_decomposition_module_updated"] is module_changed and module_changed)
        gradient_summary.append({"forward": step["forward"], "aggregate_weight_gradient": gradient,
                                 "aggregate_weight_updated": weight_changed, "aggregate_module_updated": module_changed})
    observations = candidate["HVD_variance_decomposition_observations"]
    check("two_actual_HVD_path_observations", len(observations) == 2)
    path_summary = []
    for observation in observations:
        count = observation["actual_supported_scene_count"]
        check("actual_production_HVD_path_step" + str(observation["forward"]),
              observation["actual_true_fine_paths"] > 0 and count > 0
              and all(observation[k] == count for k in ("actual_stats_calls", "actual_pack_calls", "actual_factor_calls", "actual_GELU_calls"))
              and observation["actual_group_mean_calls"] == 8 * count
              and observation["actual_linear_calls"] == 2 * count and observation["actual_final_index_copy_calls"] == 3 * count
              and observation["statistics_and_packing_from_actual_production_calls"] is True
              and observation["no_feature_or_statistic_replay"] is True
              and observation["all_observed_internal_gradients_finite"] is True)
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
    check("raw_input_files_preserved", all(sha(ROOT / name) == digest for name, digest in input_hashes.items()))
    failures = [item["name"] for item in CHECKS if not item["passed"]]
    evidence = [ref(EXECUTION / (mode + "_" + target + "_execution.json")) for mode, target in PAIRS]
    evidence += [ref(EXECUTION / name) for name in ("native_manifest.json", "execution_binding.json", "execution_lease.json")]
    evidence += [ref(PROOF), ref(SOURCE_REVIEW), ref(PROTOCOL), ref(NATIVE / "worker.py"), ref(ACTIVATION / "native_runtime.py")]
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
             "whole_HVD_core_original_loss_gradient_and_update": gradient_summary,
             "actual_HVD_path_observations": path_summary, "evidence": evidence,
             "limitations": ["Two natural TRAIN steps establish technical execution only, not trained efficacy or novelty.",
                 "Smoke memory includes observer hooks and snapshots; it is not pure optimizer TRAIN memory.",
                 "Individual rows/maps/biases/statistic components may be zero; no additional coverage or positivity gate was added."]}
    smoke_ref = save("native_smoke.json", smoke)
    metrics = {"flops_g": (rb["profile"]["flops_g"], rc["profile"]["flops_g"])}
    metrics.update({key: (rb[key], rc[key]) for key in ("median_ms", "p90_ms", "peak_allocated_bytes", "peak_reserved_bytes", "parameters")})
    resources = {**base, "schema_version": 1, "experiment_id": "M230-HVD", "passed": True,
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
    constraints = {**base, "experiment_id": "M230-HVD", "parent_commit": PARENT, "passed": True,
                   "actual_git_source_hashes": proof["source_files_exact9"], "exact_nine_paths_only": True,
                   "source_version": ref(PROOF), "independent_source_review": ref(SOURCE_REVIEW),
                   "native_smoke": smoke_ref, "resources": resource_ref, "protocol": ref(PROTOCOL),
                   "source_unchanged_from_tested_bytes": True, "config_is_independent_native_YAML": True,
                   "fixed_original_data_seed_schedule_loss_precision": True,
                   "native_yaml_record": {"seed": 1999, "epochs": 50, "max_iters": 70,
                                          "precision_intervention": False, "optimizer": candidate["optimizer_type"],
                                          "scheduler": candidate["scheduler_type"], "data_source": candidate["data_source"]},
                   "mainline": "Actual variance-decomposition hierarchy core replaces original three FFNs and reaches original HCG/single inst_feats/ILA/mask path.",
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
    draft_ref = save("draft_receipt.json", draft)
    print(json.dumps({"status": audit["status"], "check_count": len(CHECKS), "native_smoke": smoke_ref,
                      "resources": resource_ref, "constraints_independence": constraints_ref,
                      "draft_receipt": draft_ref, "normalization_audit": audit_ref,
                      "candidate_losses": candidate["losses"], "resource_measured": resources["measured"]}))


if __name__ == "__main__":
    main()
