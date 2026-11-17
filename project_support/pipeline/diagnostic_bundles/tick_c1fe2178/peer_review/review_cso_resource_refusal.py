"""Independent local verification of the recorded resource refusal; no SSH/query/rerun."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
PACKET = TICK / "cso_production_prepare_v2"
DISPATCH = TICK / "cso_dispatch_execution_v2"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def value_sha(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
actual_path = TICK / "cso_resource_refusal.actual.json"
assert sha(actual_path) == "8538672b504c65d634c4eab5fde4ad39326d38dc383a675246544af553f42fff"
actual = read(actual_path); observed = actual["observation"]; owner = read(TICK / "current_owner_binding.json")
assert actual["owner"] == observed["owner"] == owner
assert actual["certainty"] == "terminal" and actual["ssh_returncode"] == 0 and actual["stderr"] == ""
assert json.loads(actual["stdout"]) == observed
assert actual["collector_thread_id"] == "/root/cso_sync_peer"
assert actual["probe_sha256"] == sha(actual["probe_path"]) == "730adec7d44b7a808e202c3b2293ccc48186e5cec4eeb46ece18b333559cfc6f"
probe = Path(actual["probe_path"]).read_text(encoding="utf-8")
ast.parse(probe); compile(probe, 'resource_refusal_probe_static', 'exec')
assert "memory.free,memory.used,memory.total,utilization.gpu" in probe
assert "no_project_trainer_proven':not trainers and not inventory_errors" in probe
assert "original_locks_metadata_only" in probe and "'locks_acquired':False" in probe
for path, expected in actual["local_files_sha256"].items(): assert sha(path) == expected, path
assert {path.name:sha(path) for path in DISPATCH.iterdir() if path.is_file()} == actual["dispatch_files_sha256"]
assert (DISPATCH / "cso_dispatch_ssh_00.stdout").read_bytes() == b""
assert sha(actual["known_prelaunch_refusal"]["stderr_path"]) == actual["known_prelaunch_refusal"]["stderr_sha256"]
assert "ResourceRefused: Direct memory.free below unchanged 20000 MiB gate" in (DISPATCH / "cso_dispatch_ssh_00.stderr").read_text(encoding="utf-8")
for name in ("cso_dispatch_intent.json", "cso_dispatch_result.json", "cso_prelaunch_actual_resources.json"):
    assert not (DISPATCH / name).exists()
for key in ("dispatch_intent_absent", "dispatch_result_absent", "prelaunch_result_absent"):
    assert actual["known_prelaunch_refusal"][key] is True
assert observed["hostname"] == "dl04-MS-7E06" and observed["uid"] == 1001
assert observed["runtime_HEAD"] == "5413102c57b526035f3920b5e7a81f3b58ad764d"
gpu = observed["gpu"]
fields = [value.strip() for value in observed["gpu_raw_row"].split(',')]
assert len(fields) == 6 and fields[:2] == ["0", "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
assert list(map(int,fields[2:])) == [gpu["memory_free_mib"],gpu["memory_used_mib"],gpu["memory_total_mib"],gpu["utilization_percent"]]
assert gpu["free_queried_directly"] is True and gpu["below_unchanged_gate"] is True
assert actual["resource_gate_required_free_mib"] == gpu["required_free_memory_mib"] == 20000
assert isinstance(gpu["memory_free_mib"],int) and 0 <= gpu["memory_free_mib"] == 10848 < 20000
assert observed["one_shot_marker_absent_before_after"] is True
assert observed["one_shot_marker"] == "/data/songcl/Project/Cluster_project/pipeline/runtime/cso_path_prod_c1fe2178_v2/train-consumed.json"
assert observed["project_trainers_or_testers"] == observed["same_uid_inventory_errors"] == []
assert observed["no_project_trainer_proven"] is True
assert observed["contexts"] and all(value["gpu_uuid"] == gpu["uuid"] and value["uid"] != 1001 for value in observed["contexts"])
assert [(item["dev"],item["ino"]) for item in observed["original_locks_metadata_only"]] == [(66308,92537152),(66308,92537153),(66308,92537154)]
assert all(item["uid"] == 1001 and item["kernel_lock_lines"] == [] for item in observed["original_locks_metadata_only"])
assert observed["kernel_locks_read"] is True and observed["locks_acquired"] is False
frozen = read(PACKET / "FROZEN.json")
assert actual["producer_FROZEN_sha256"] == sha(PACKET / "FROZEN.json")
assert observed["producer_files_sha256"] == {name:frozen["files"][name] for name in ("production_controller.py","lock_core.py","entry_factory.py")}
render = read(TICK / "cso_setup_execution_v2/render_result.json")
assert observed["production_files_sha256"] == render["files"]
assert observed["producer"] == render["binding"]["producer"] and observed["production"] == render["binding"]["stage"]
proof = read(ROOT / "pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json")
assert observed["source8_sha256"] == {name:value for name,value in proof["files_exact9_sha256"].items() if name.endswith('.py')}
assert observed["runtime_config_sha256"] == proof["files_exact9_sha256"][read(ROOT / "pipeline/admissions/M236-CSO.json")["config"]]
queue = read(ROOT / "pipeline/queue.json")
tasks = [task for group in queue["gpu_queues"].values() for task in group]
task = next(task for task in tasks if task.get("id") == "M236-CSO")
assert value_sha(task) == actual["M236_queue"]["canonical_task_sha256"]
assert task["status"] == "waiting" and not task.get("pid") and task.get("launch_verified") is not True
old_tasks = [task for group in read(TICK / "queue.json.before")["gpu_queues"].values() for task in group]
for name, record in actual["protected_paused_tasks"].items():
    current = next(task for task in tasks if task.get("id") == name)
    original = next(task for task in old_tasks if task.get("id") == name)
    assert current == original and value_sha(current) == record["canonical_task_sha256"] and record["unchanged_from_tick_before"]
assert actual["no_launch_in_this_attempt"] is True
assert all(actual[key] is False for key in ("prior_native_resource_checks_reclassified","threshold_lowered","automatic_retry_or_dispatch_performed","remote_writes_or_signals"))
assert all(observed[key] is False for key in ("signals_sent","remote_writes","GPU1_or_other_servers_queried","Torch_imported","training_launched_by_observer"))
assert datetime.fromisoformat(owner["generated_at"]) < datetime.fromisoformat(observed["recorded_at"]) < datetime.fromisoformat(owner["deadline_at"])
review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True, "material_concerns": [],
    "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer", "kind": "ACTUAL_RESOURCE_REFUSAL_AND_NO_LAUNCH_INDEPENDENT_REVIEW",
    "actual_sha256": sha(actual_path), "resource_block_confirmed": True,
    "actual_free_mib": gpu["memory_free_mib"], "original_minimum_free_mib": 20000,
    "marker_absent": True, "no_project_training_launched": True,
    "no_project_training_launched_scope": "This M236 prelaunch attempt; no same-user project trainer/tester was observed and no M236 PID/dispatch intent/marker exists.",
    "source_commit": observed["runtime_HEAD"], "new_production_entry_unchanged": True,
    "original_three_lock_inodes_unchanged_and_unheld_at_observation": True,
    "dispatch_intent_result_and_prelaunch_result_absent": True,
    "M236_queue_waiting_without_pid_or_verified_launch": True,
    "M206_M227_preserved_byte_exact_tasks": True,
    "observed_external_GPU_contexts": [{"pid":value["pid"],"uid":value["uid"],"used_gpu_memory_mib":value["used_gpu_memory_mib"]} for value in observed["contexts"]],
    "native_smoke_and_measured_resource_PASS_reclassified": False,
    "deployment_resource_block_is_not_model_resource_test_failure": True,
    "threshold_lowered_or_external_jobs_signalled": False,
    "review_scope": "Fresh physical GPU0 direct-free observation confirms10848<20000 and a preserved other-UID GPU context. New entry/source/producers and original three inodes remain exact; marker is absent before/after, dispatch failed before intent/canonical launch, queue has no PID. This is a deployment availability block; successful native smoke and same-protocol model resource measurements remain valid. New owner binding and fresh resources are required before any later dispatch.",
    "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False,
    "prepared_module_import_or_execution_performed": False, "shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits": False}
target = OUT / "cso_resource_refusal_independent_review.json"
with target.open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(review,stream,indent=2);stream.write('\n')
print(json.dumps({"path":str(target),"sha256":sha(target),"resource_block_confirmed":True,"actual_free_mib":gpu["memory_free_mib"]}))
