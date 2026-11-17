"""Independent local-only validation of the already-recorded read-only observation."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

owner = read(TICK / "current_owner_binding.json")
live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
assert {key: live[key] for key in owner} == owner
for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
    assert sha(ROOT / "pipeline/headless" / name) == owner[key]
actual_path = TICK / "runtime_readiness.actual.json"
assert sha(actual_path) == "419acac969100b44b95b5187b63587ea96ecb720a9ff4d2fa65c7512fec62b94"
actual = read(actual_path)
assert actual["owner"] == owner and actual["passed"] is True
assert actual["certainty"] == "terminal" and actual["returncode"] == 0
assert actual["completed_before_deadline"] is True
assert datetime.fromisoformat(owner["generated_at"]) <= datetime.fromisoformat(actual["started_at"])
assert datetime.fromisoformat(actual["completed_at"]) < datetime.fromisoformat(owner["deadline_at"])
for key in ("Torch_imported", "GPU_compute", "signals_sent", "remote_mutations"):
    assert actual[key] is False
for item in actual["historical_binding_inputs"] + list(actual["historical_provenance"].values()):
    assert sha(ROOT / item["path"]) == item["sha256"]
assert sha(ROOT / actual["producer"]["path"]) == actual["producer"]["sha256"]
assert sha(TICK / "runtime_readiness_probe.py.txt") == actual["body_sha256"]
assert sha(TICK / "runtime_readiness.packet.json") == actual["packet_sha256"]
assert sha(TICK / "runtime_readiness.transport.stdout") == actual["stdout_sha256"]
assert sha(TICK / "runtime_readiness.transport.stderr") == actual["stderr_sha256"]
assert (TICK / "runtime_readiness.transport.stderr").read_bytes() == b""
observation = actual["observation"]
assert read(TICK / "runtime_readiness.transport.stdout") == observation
assert observation["owner"] == owner
assert observation["hostname"] == "dl04-MS-7E06" and observation["uid"] == 1001
assert observation["runtime_root"] == "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
assert observation["runtime_HEAD"] == "b1e639b3ceb14bb5c65d9f81a084d41c834b951c"
packet = read(TICK / "runtime_readiness.packet.json")
assert packet["owner"] == owner
env, manifest = packet["environment"], packet["manifest"]
assert env == read(ROOT / actual["historical_provenance"]["environment"]["path"])
assert manifest == read(ROOT / actual["historical_provenance"]["manifest"]["path"])
assets = manifest["assets"]
runtime = manifest["root"]
expected = {
    env["base_conda_source"]: env["base_conda_sha256"], env["python_path"]: env["python_sha256"],
    env["compatible_extension_path"]: env["compatible_extension_sha256"],
    env["torch"]["module"]["path"]: env["torch"]["module"]["sha256"],
    env["torch"]["extension"]["path"]: env["torch"]["extension"]["sha256"],
    runtime + "/tools/train.py": assets["native_train_source_sha256"],
    runtime + "/framework/dataset/scannetv2.py": assets["dataset_source_sha256"],
    assets["config_path"]: assets["config_sha256"], assets["annotation_path"]: assets["annotation_sha256"],
    assets["checkpoint"]: assets["checkpoint_sha256"], assets["pretrain"]: assets["pretrain_sha256"]}
expected.update({runtime + "/framework/model/Quard_model/" + manifest["name"] + "/" + name: value
                 for name, value in assets["source_hashes"].items()})
assert len(expected) == len(observation["files"]) == observation["source_environment_assets_verified_count"] == 18
assert {item["path"]: item["expected_sha256"] for item in observation["files"]} == expected
assert all(item["matches"] and item["read_stable"] and item["sha256"] == expected[item["path"]]
           for item in observation["files"])
assert [(item["kind"], item["device"], item["inode"]) for item in observation["original_locks"]] == [
    ("training", 66308, 92537152), ("diagnostic", 66308, 92537153), ("exclusive", 66308, 92537154)]
assert all(item["matching_kernel_lock_rows"] == [] for item in observation["original_locks"])
assert observation["project_trainers"] == observation["project_workers"] == []
gpu = observation["gpu0"]
assert gpu["index"] == 0 and gpu["uuid"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
assert gpu["memory_free_queried_directly"] is True and gpu["memory_free_mib"] == 32016 >= 20000
assert observation["lock_observation_method"] == "metadata_and_proc_locks_only_no_acquisition"
assert observation["old_consumed_entry"]["executed"] is False
assert observation["old_lease_or_shim_executed"] is False
assert observation["resource_ready_at_observation"] is observation["readiness_passed"] is True
for name in ("run_runtime_readiness.py", "runtime_readiness_probe.py.txt"):
    raw = (TICK / name).read_text(encoding="utf-8")
    ast.parse(raw, filename=name)
    compile(raw, name, "exec")
body = (TICK / "runtime_readiness_probe.py.txt").read_text(encoding="utf-8")
assert "memory.free,memory.used,memory.total,utilization.gpu" in body
assert "resource_ready = gpu['memory_free_mib'] >= 20000 and not trainers and not workers" in body
assert "total - used" not in body
assert "utilization_percent'] == 0" not in body

review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
    "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer",
    "passed": True, "material_concerns": [],
    "kind": "CURRENT_OWNER_READ_ONLY_READINESS_RESULT_REVIEW",
    "status": "OBSERVATION_REVIEW_PASSED_NATIVE_AND_RESOURCES_NOT_RUN",
    "actual_sha256": sha(actual_path), "producer_sha256": actual["producer"]["sha256"],
    "probe_body_sha256": actual["body_sha256"], "packet_sha256": actual["packet_sha256"],
    "observation_at": observation["observed_at"], "direct_memory_free_mib": gpu["memory_free_mib"],
    "verified": {
        "current_owner_six_context_pending_exact": True,
        "producer_packet_body_stdout_stderr_historical_inputs_hashes_exact": True,
        "expected18_fresh_stable_observed_hashes_exact": True,
        "runtime_b1_host_uid_gpu0_physical_UUID_exact": True,
        "direct_free20000_threshold_without_empty_or_utilization_requirement": True,
        "original_three_inode_metadata_and_proc_locks_rows_no_acquisition": True,
        "project_trainers_workers_absent_at_observation": True,
        "historical_environment_inputs_preserved_no_fresh_import_claim": True,
        "old_consumed_marker_read_only_not_executed": True,
        "producer_and_probe_static_compile_only_by_reviewer": True},
    "review_scope": "Independent local verification of root's fresh read-only remote observation and source/hash closure. Readiness holds only at its observed time; actual native TRAIN2/backward/resource measurements, current last-moment locked guards and production authorization remain separate.",
    "native_TRAIN2": "NOT_RUN", "native_backward": "NOT_RUN", "resources": "NOT_RUN",
    "actual_native_gate_passed": False, "actual_resource_gate_passed": False,
    "scientific_admission": False, "execution_authorized_by_this_review": False,
    "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False,
    "GPU_use_by_reviewer": False, "prepared_module_execution_performed": False,
    "shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits": False}
target = OUT / "runtime_readiness_actual_independent_review.json"
with target.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(review, stream, indent=2)
    stream.write("\n")
print(json.dumps({"path": str(target), "sha256": sha(target), "passed": True}))
