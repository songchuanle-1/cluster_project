"""Validate recorded native result locally; no Torch, imports, remote operations or rerun."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
HERE = TICK / "cso_native_bound"
EXEC = TICK / "cso_native_execution"
OUT = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
owner = read(TICK / "current_owner_binding.json")
actual = EXEC / "run_smoke_candidate_actual.json"
assert sha(actual) == "5742aefcb821789ec3778b56f82ffe9a970808c51d45875f71ba9e58995e6753"
wrapper = read(actual)
observation = wrapper["observation"]
result = observation["result"]
assert wrapper["owner"] == result["owner"] == owner
assert wrapper["certainty"] == observation["certainty"] == "terminal"
assert wrapper["returncode"] == observation["returncode"] == 0
assert read(EXEC / "run_smoke_candidate_transport.stdout.partial") == observation
assert json.loads(wrapper["stdout"]) == observation
raw_result_hash = hashlib.sha256(json.dumps(result, indent=2, allow_nan=False).encode()).hexdigest()
assert raw_result_hash == observation["result_sha256"] == "05e490e5c218524bfaaed8a38e6c5b065c138cf8b3356499227697ee66ac419a"
request, intent = read(EXEC / "run_smoke_candidate_request.json"), read(EXEC / "run_smoke_candidate_intent.json")
assert sha(EXEC / "run_smoke_candidate_request.json") == wrapper["request_sha256"]
assert sha(EXEC / "run_smoke_candidate_intent.json") == wrapper["intent_sha256"] == intent.get("intent_sha256", wrapper["intent_sha256"])
assert request["owner"] == intent["owner"] == owner
assert intent["no_replay"] is True and intent["action"] == request["action"] == "run"
assert intent["request_sha256"] == wrapper["request_sha256"]
source_review = read(OUT / "cso_native_bound_independent_review.json")
assert request["independent_review_sha256"] == sha(OUT / "cso_native_bound_independent_review.json")
assert source_review["passed"] and source_review["direct_memory_free_guard_integration_review_passed"]
assert request["transport_sha256"] == sha(HERE / "run_native_once.py")
manifest, binding, lease = (read(EXEC / name) for name in ("native_manifest.json", "source_binding.json", "execution_lease.json"))
assert manifest["owner"] == binding["owner"] == lease["owner"] == owner
assert result["native_manifest_sha256"] == request["native_manifest_sha256"] == sha(EXEC / "native_manifest.json")
assert result["source_binding_sha256"] == manifest["source_binding_sha256"] == sha(EXEC / "source_binding.json")
assert lease["native_manifest_sha256"] == result["native_manifest_sha256"]
assert binding["source_version_proof"] == read(HERE / "source_version.json")
assert result["diagnostic_worker_sha256"] == sha(HERE / "worker.py")
assert result["runtime_sha256"] == sha(HERE / "native_runtime.py")
for name, value in manifest["diagnostic_files"].items(): assert sha(HERE / name) == value
assert result["code_commit"] == "af45707d7b6089f764843337c5f88af285383f88"
assert result["stage"] == intent["remote_stage"] == "/data/songcl/Project/Cluster_project/pipeline/cso_c1fe2178_gpu0"
assert result["experiment_id"] == "M236-CSO" and result["candidate_id"] == manifest["candidate_id"]
assert result["config"] == manifest["config"] and result["goal_sha256"] == manifest["goal_sha256"]
assert result["source_hashes"] == manifest["candidate_source_hashes"]
assert result["config_sha256"] == manifest["candidate_config_sha256"]
assert result["native_train_source_sha256"] == manifest["assets"]["native_train_source_sha256"]
assert result["physical_gpu"] == 0 and result["gpu_uuid"] == manifest["gpu_uuid"]
assert result["mode"] == request["mode"] == "smoke" and result["target"] == request["target"] == "candidate"
assert datetime.fromisoformat(owner["generated_at"]) < datetime.fromisoformat(result["observed_at"]) < datetime.fromisoformat(owner["deadline_at"])
assert result["scientific_admission"] is False and result["efficacy"] == result["novelty"] == "UNKNOWN"
assert result["data_source"]["train"]["prefix"] == "train" and result["data_source"]["train"]["training"] is True
assert result["initialization"]["seed"] == 1999 and result["initialization"]["trained_m95_checkpoint_loaded"] is False
assert result["initialization"]["sha256"] == manifest["assets"]["pretrain_sha256"]
assert result["native_dataloader_config"] == {"batch_size": 2, "num_workers": 4, "persistent_workers": True}
for key in ("execution_completed", "native_model_and_yaml_unchanged", "native_data_loaded", "native_train_function_executed", "backward_finite", "intended_path_observed", "observer_readout_complete", "native_smoke_checks_passed", "wrappers_and_hooks_restored", "native_tracked_each_parameter_updated"):
    assert result[key] is True, key
assert result["optimizer_steps"] == result["native_loss_forwards"] == result["native_criterion_backwards"] == 2
assert result["auxiliary_autograd_grad_or_backward_used"] is False
assert result["training_checkpoint_saved"] is False
assert result["new_training"] == 0
assert len(result["losses"]) == len(result["batches"]) == len(result["steps"]) == 2
assert all(math.isfinite(item["loss"]) for item in result["losses"])
baseline_path = ROOT / "pipeline/diagnostic_bundles/tick_71e15360/nde_execution/smoke_champion_execution.json"
baseline = read(baseline_path)["result"]
assert result["batches"] == baseline["batches"]
reference, common, comparison = (result[key] for key in ("original_common_reference", "common_initialized_parameters", "original_common_initialization_comparison"))
assert reference["tensor_count"] == common["tensor_count"] == comparison["candidate_tensor_count"] == comparison["reference_tensor_count"] == 841
assert len(reference["names"]) == len(common["names"]) == len(comparison["candidate_names"]) == 841
assert reference["names"] == common["names"] == comparison["candidate_names"]
assert reference["shapes"] == common["shapes"] == comparison["candidate_shapes"]
assert reference["dtypes"] == comparison["candidate_dtypes"]
assert reference["sha256"] == common["sha256"] == comparison["candidate_sha256"] == comparison["reference_sha256"]
assert all(comparison[key] is True for key in ("passed", "same_names", "same_shapes", "same_dtypes", "candidate_source_initialization_untouched"))
assert all(comparison[key] == [] for key in ("different_parameter_names", "only_candidate_names", "only_reference_names"))
assert comparison["copied_common_weights"] is comparison["post_reference_rng_substituted"] is False
assert reference["reference_measurement_entry_RNG_restored_exact"] is True
alias = result["baseline_constructor_loss_alias"]
assert alias["actual_same_module_object"] is alias["actual_same_Criterion_class"] is alias["identical_source_verified"] is True
assert alias["registry_force_clear_or_edit"] is alias["class_mutation"] is False
expected_core = set(read(HERE / "protocol_validation.json")["core_parameter_tensor_names"])
assert len(expected_core) == 9
for step in result["steps"]:
    assert step["all_observed_parameter_gradients_finite"] is True and step["nonfinite_parameter_names"] == []
    assert step["original_optimizer_step_completed"] is True and step["actual_same_leaf_ordered_point_pairs"] > 0
    assert set(step["tracked_gradients"]) == set(step["actual_parameter_updated"]) == expected_core
    assert all(value["finite"] is True and math.isfinite(value["abs_max"]) and value["abs_max"] > 0 for value in step["tracked_gradients"].values())
    assert all(step["actual_parameter_updated"].values())
    assert all(step["before_hash"][name] != step["after_hash"][name] for name in expected_core)
assert result["steps"][0]["after_hash"] == result["steps"][1]["before_hash"]
assert result["native_tracked_initial_hash"] == result["steps"][0]["before_hash"]
assert result["native_tracked_after_hash"] == result["steps"][1]["after_hash"]
assert len(result["core_calls"]) == len(result["inst_to_mask_path_observations"]) == len(result["raw_bank_observations"]) == 2
for record in result["core_calls"]:
    assert record["actual_source_forward"] is record["actual_fine_message_delivered_to_HCG"] is True
    assert record["actual_covariance_core_observation"]["rank"] == 8
    assert record["actual_covariance_core_observation"]["matrix_iterations"] == 6
    for key in ("native_input_gradients", "native_output_gradients", "native_HCG_output_gradients"):
        assert record[key] and all(item["finite"] for item in record[key])
for record in result["inst_to_mask_path_observations"]:
    assert record["single_original_inst_writeback_exact"] is True and record["extra_injection"] is False
    for key in ("native_post_cluster_inst_gradients", "native_post_ILA_inst_gradients", "native_final_mask_gradients"):
        assert record[key] and all(item["finite"] for item in record[key])
for record in result["raw_bank_observations"]: assert record["raw_unchanged"] and record["ids_unchanged"] and record["maps_unchanged"]
assert len(result["csort_observations"]) == 4 and all(item["raw_object_identity_preserved"] for item in result["csort_observations"])
for record in result["covariance_support_observations"]:
    assert record["covariance_finite"] and record["same_leaf_ordered_point_pairs"] > 0 and record["offdiagonal_covariance_abs_max"] > 0
    assert record["cross_leaf_pairs"] == record["receiver_donor_edges"] == 0
before = result["before"]
assert [(item["kind"], item["device"], item["inode"]) for item in before["original_lock_identities"]] == [
    ("training", 66308, 92537152), ("diagnostic", 66308, 92537153), ("exclusive", 66308, 92537154)]
assert all(item["opened_existing_NOFOLLOW_no_create"] and item["nonblocking_acquired"] for item in before["original_lock_identities"])
for record, locks in ((before, 0), (before["post_acquisition_observation"], 3), (before["last_pre_Torch_observation"], 3)):
    assert record["memory_free_queried_directly"] and record["memory_free_mib"] >= 20000
    assert record["cooperative_project_locks_held"] == locks
    assert record["exclusive_measurement_claimed"] is False
    assert record["resource_memory_policy"] == manifest["resource_memory_policy"]
assert result["exclusive_measurement_claimed"] is False
review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True, "material_concerns": [],
    "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer", "kind": "ACTUAL_NATIVE_TRAIN2_RESULT_INDEPENDENT_REVIEW",
    "actual_sha256": sha(actual), "remote_result_sha256": raw_result_hash,
    "source_commit": result["code_commit"], "source_binding_sha256": result["source_binding_sha256"],
    "native_manifest_sha256": result["native_manifest_sha256"], "source_review_sha256": sha(OUT / "cso_native_bound_independent_review.json"),
    "native_smoke_passed": True, "native_backward_passed": True, "intended_path_observed": True,
    "actual_common_initialization_equality_passed": True, "actual_common_parameter_tensor_count": 841,
    "actual_common_parameter_sha256": common["sha256"], "optimizer_steps": 2,
    "losses": [item["loss"] for item in result["losses"]], "core_parameter_tensor_count": 9,
    "core_each_step_finite_nonzero_and_updated": True,
    "natural_TRAIN2_batch_hashes": [item["sha256"] for item in result["batches"]],
    "historical_M95_batch_comparator": {"path": str(baseline_path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(baseline_path), "simultaneous_comparison": False},
    "pre_Torch_last_direct_free_mib": before["last_pre_Torch_observation"]["memory_free_mib"],
    "original_three_lock_identities_verified": True,
    "source9_native_yaml_seed1999_schedule_data_loss_optimizer_unchanged": True,
    "native_HCG_instance_ILA_mask_backward_and_raw_bank_csort_integrity_verified": True,
    "transport_request_intent_stdout_remote_result_source_producer_hash_closure_verified": True,
    "resource_gate_passed": False, "resources": "NOT_RUN", "scientific_admission": False,
    "full_training_started_or_efficacy_demonstrated": False,
    "pure_training_peak_memory": result["pure_training_peak_memory"],
    "review_scope": "Two genuine natural original TRAIN batches through native task loss and optimizer, source-bound af457 private-stage model. Common841 names/shapes/dtypes/hash were actually compared to unchanged M95 constructor/pretrain and matched without weight copying/RNG substitution. Core9 and full HCG/instance/ILA/mask gradients passed. This is a smoke result, not whole training, efficacy, production launch or resource admission. Separate actual resource measurement remains required.",
    "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False,
    "prepared_module_execution_or_test_replay_performed": False, "shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits": False}
target = OUT / "cso_native_smoke_actual_independent_review.json"
with target.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(review, stream, indent=2); stream.write("\n")
print(json.dumps({"path": str(target), "sha256": sha(target), "native_smoke_passed": True}))
