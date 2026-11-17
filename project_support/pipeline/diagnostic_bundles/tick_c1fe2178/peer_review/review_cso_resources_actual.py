"""Independent recorded-resource validation; stdlib only, no execution replay."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
HERE = TICK / "cso_native_bound"
EXEC = TICK / "cso_native_execution"
OUT = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
owner = read(TICK / "current_owner_binding.json")
actual = EXEC / "run_resources_candidate_actual.json"
assert sha(actual) == "fb07add58260f2f1ca309c8e174aa1eb6bf72ae284e26567ea6ce4f766d08450"
wrapper = read(actual); observation = wrapper["observation"]; result = observation["result"]
assert wrapper["owner"] == result["owner"] == owner
assert wrapper["certainty"] == observation["certainty"] == "terminal"
assert wrapper["returncode"] == observation["returncode"] == 0
assert read(EXEC / "run_resources_candidate_transport.stdout.partial") == json.loads(wrapper["stdout"]) == observation
raw_result_hash = hashlib.sha256(json.dumps(result, indent=2, allow_nan=False).encode()).hexdigest()
assert raw_result_hash == observation["result_sha256"]
request = read(EXEC / "run_resources_candidate_request.json"); intent = read(EXEC / "run_resources_candidate_intent.json")
assert sha(EXEC / "run_resources_candidate_request.json") == wrapper["request_sha256"] == intent["request_sha256"]
assert sha(EXEC / "run_resources_candidate_intent.json") == wrapper["intent_sha256"]
assert request["owner"] == intent["owner"] == owner
assert intent["no_replay"] and intent["action"] == request["action"] == "run"
assert request["independent_review_sha256"] == sha(OUT / "cso_native_bound_independent_review.json")
assert request["transport_sha256"] == sha(HERE / "run_native_once.py")
manifest = read(EXEC / "native_manifest.json"); binding = read(EXEC / "source_binding.json")
assert manifest["owner"] == binding["owner"] == owner
assert result["native_manifest_sha256"] == request["native_manifest_sha256"] == sha(EXEC / "native_manifest.json")
assert result["source_binding_sha256"] == manifest["source_binding_sha256"] == sha(EXEC / "source_binding.json")
assert binding["source_version_proof"] == read(HERE / "source_version.json")
assert result["diagnostic_worker_sha256"] == sha(HERE / "worker.py")
assert result["runtime_sha256"] == sha(HERE / "native_runtime.py")
for name, value in manifest["diagnostic_files"].items(): assert sha(HERE / name) == value
assert result["code_commit"] == "af45707d7b6089f764843337c5f88af285383f88"
assert result["stage"] == intent["remote_stage"] == manifest["stage"] == "/data/songcl/Project/Cluster_project/pipeline/cso_c1fe2178_gpu0"
assert result["experiment_id"] == "M236-CSO" and result["candidate_id"] == manifest["candidate_id"]
assert result["config"] == manifest["config"] and result["goal_sha256"] == manifest["goal_sha256"]
assert result["source_hashes"] == manifest["candidate_source_hashes"]
assert result["config_sha256"] == manifest["candidate_config_sha256"]
assert result["physical_gpu"] == 0 and result["gpu_uuid"] == manifest["gpu_uuid"]
assert result["mode"] == request["mode"] == "resources" and result["target"] == request["target"] == "candidate"
assert result["execution_completed"] and result["native_model_and_yaml_unchanged"]
assert result["optimizer_steps"] == result["native_loss_forwards"] == result["native_criterion_backwards"] == result["new_training"] == 0
assert result["native_predict_calls"] == 121
assert (result["batch_size"], result["lang_num_max"], result["warmup"], result["repeat"]) == (1, 1, 20, 100)
assert result["parameter_flags_preserved"] and result["source_body_executed_without_replacement"]
assert result["validation_accuracy_evaluated_for_selection"] is False
assert result["scientific_admission"] is False and result["efficacy"] == result["novelty"] == "UNKNOWN"
assert "UNKNOWN" in result["full_optimizer_training_peak"] and "UNKNOWN" in result["original_no_cluster_resource_delta"]
assert datetime.fromisoformat(owner["generated_at"]) < datetime.fromisoformat(result["observed_at"]) < datetime.fromisoformat(owner["deadline_at"])
times = result["measurements_ms"]
assert len(times) == 100 and all(isinstance(value, (int, float)) and math.isfinite(value) and value > 0 for value in times)
median = statistics.median(times); ordered = sorted(times); p90 = ordered[89] * 0.9 + ordered[90] * 0.1
assert math.isclose(median, result["median_ms"], rel_tol=1e-12)
assert math.isclose(p90, result["p90_ms"], rel_tol=1e-12)
profile = result["profile"]
assert profile["flops"] == 9645764684.0 <= 10e9 and profile["within10G"] is True
assert profile["flops_g"] == profile["flops"] / 1e9
assert math.isclose(sum(profile["by_operator"].values()), profile["flops"], rel_tol=1e-12)
baseline_path = ROOT / "pipeline/diagnostic_bundles/tick_5287cf71/nde_execution/resources_champion_execution.json"
assert sha(baseline_path) == "ba47706b17f694cf868b75f83844aa314d5e1f2fe74e3ad4417e65d070b5c7f8"
baseline = read(baseline_path)["result"]
assert result["input_sha256"] == baseline["input_sha256"] == "526079d667505fce5957a69797f328cf23fe42c34e1e9ddeca5a5deedbbccf90"
assert result["scan_ids"] == baseline["scan_ids"] and result["ann_ids"] == baseline["ann_ids"]
assert profile["profiler_file_sha256"] == baseline["profile"]["profiler_file_sha256"]
assert profile["fvcore_version"] == baseline["profile"]["fvcore_version"]
assert all(result[key] == baseline[key] for key in ("batch_size", "lang_num_max", "warmup", "repeat"))
assert 0 < result["peak_allocated_bytes"] <= 1.15 * baseline["peak_allocated_bytes"]
assert 0 < result["peak_reserved_bytes"] <= 1.15 * baseline["peak_reserved_bytes"]
before = result["before"]
assert [(item["kind"], item["device"], item["inode"]) for item in before["original_lock_identities"]] == [
    ("training", 66308, 92537152), ("diagnostic", 66308, 92537153), ("exclusive", 66308, 92537154)]
for record, locks in ((before, 0), (before["post_acquisition_observation"], 3), (before["last_pre_Torch_observation"], 3)):
    assert record["memory_free_queried_directly"] and record["memory_free_mib"] >= 20000
    assert record["cooperative_project_locks_held"] == locks and record["exclusive_measurement_claimed"] is False
assert result["exclusive_measurement_claimed"] is False
assert result["measurement_scope"] == "authorized_overlay_potentially_contended_not_exclusive"
deltas = {key: {"candidate": result[key], "historical_M95": baseline[key], "absolute_delta": result[key] - baseline[key],
                "relative_delta_percent": (result[key] / baseline[key] - 1) * 100}
          for key in ("parameters", "median_ms", "p90_ms", "peak_allocated_bytes", "peak_reserved_bytes")}
deltas["standard_counted_flops_g"] = {"candidate": profile["flops_g"], "historical_M95": baseline["profile"]["flops_g"],
    "absolute_delta": profile["flops_g"] - baseline["profile"]["flops_g"],
    "relative_delta_percent": (profile["flops_g"] / baseline["profile"]["flops_g"] - 1) * 100}
review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True, "material_concerns": [],
    "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer", "kind": "ACTUAL_NATIVE_RESOURCES_RESULT_INDEPENDENT_REVIEW",
    "actual_sha256": sha(actual), "remote_result_sha256": raw_result_hash, "resource_gate_passed": True,
    "source_commit": result["code_commit"], "source_binding_sha256": result["source_binding_sha256"],
    "native_manifest_sha256": result["native_manifest_sha256"], "source_review_sha256": sha(OUT / "cso_native_bound_independent_review.json"),
    "input_sha256": result["input_sha256"], "batch_size": 1, "lang_num_max": 1, "warmup": 20, "repeat": 100, "native_predict_calls": 121,
    "parameters": result["parameters"], "standard_counted_flops_g": profile["flops_g"],
    "recomputed_100_timings_median_ms": median, "recomputed_100_timings_p90_ms": p90,
    "peak_allocated_bytes": result["peak_allocated_bytes"], "peak_reserved_bytes": result["peak_reserved_bytes"],
    "standard_10G_passed": True, "peak_memory_plus15pct_threshold_passed": True,
    "historical_M95_comparator": {"path": baseline_path.relative_to(ROOT).as_posix(), "sha256": sha(baseline_path), "simultaneous_comparison": False},
    "observed_deltas_to_historical_M95": deltas,
    "timing_interpretation": "Historical, non-simultaneous timing comparison only. The large observed latency difference cannot establish architectural acceleration; environment/driver/cache/temporal differences remain uncontrolled.",
    "standard_profiler_handlers_unchanged": True, "standard_profiler_unsupported_ops_retained": profile["unsupported_ops"],
    "supplementary_complete_op_accounting_or_no_cluster_comparison_performed": False,
    "pre_Torch_last_direct_free_mib": before["last_pre_Torch_observation"]["memory_free_mib"], "original_three_lock_identities_verified": True,
    "measurement_scope": result["measurement_scope"], "exclusive_measurement_claimed": False,
    "full_optimizer_training_peak": result["full_optimizer_training_peak"], "original_no_cluster_resource_delta": result["original_no_cluster_resource_delta"],
    "validation_accuracy_evaluated_for_selection": False, "scientific_admission": False, "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
    "review_scope": "Source-bound af457 predict-only resource result; exact historical M95 input and original profiler handlers, bs1/lang1/warmup20/repeat100 preserved. All100 wall timings recomputed. Standard counted FLOPs<=10G and measured predict peak memory satisfy current thresholds. Training peak, no-cluster delta, efficacy and architectural speedup remain unknown. This review does not authorize production launch.",
    "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False,
    "prepared_module_execution_or_test_replay_performed": False, "shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits": False}
target = OUT / "cso_resources_actual_independent_review.json"
with target.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(review, stream, indent=2); stream.write("\n")
print(json.dumps({"path": str(target), "sha256": sha(target), "resource_gate_passed": True}))
