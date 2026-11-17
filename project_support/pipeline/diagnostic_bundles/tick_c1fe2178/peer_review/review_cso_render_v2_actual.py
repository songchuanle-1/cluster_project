"""Independent actual render/entry binding verification; no import, remote operation or launch."""
import ast
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
HERE = TICK / "cso_production_prepare_v2"
EXEC = TICK / "cso_setup_execution_v2"
OUT = Path(__file__).resolve().parent
def digest(raw): return hashlib.sha256(raw).hexdigest()
def sha(path): return digest(Path(path).read_bytes())
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
owner = read(TICK / "current_owner_binding.json")
actual_path, result_path = EXEC / "render_actual.json", EXEC / "render_result.json"
assert sha(actual_path) == "9c33ccd5ddf9dbccbf3524cb7d035df109d16b259d9fe138cbf552c108c39496"
assert sha(result_path) == "58fd9d475ee1928ae587d0140b38e1aa8dbd7fb84ea78d5e78a0adbef02beca2"
wrapper = read(actual_path); remote = wrapper["observation"]; result = read(result_path)
assert wrapper["owner"] == remote["owner"] == result["owner"] == owner
assert wrapper["certainty"] == remote["certainty"] == "terminal" and wrapper["ssh_returncode"] == remote["returncode"] == 0
assert wrapper["action"] == remote["action"] == "render"
assert json.loads(wrapper["stdout"]) == read(EXEC / "render_transport.stdout.partial") == remote
raw = base64.b64decode(remote["remote_result_bytes_base64"], validate=True)
assert digest(raw) == remote["remote_result_sha256"] == sha(result_path)
assert json.loads(raw) == remote["result"] == result
assert wrapper["training_launch_or_GPU_use"] is remote["training_launch_or_GPU_use"] is result["training_launch_or_GPU_use"] is False
assert result["one_shot_consumed"] is False and result["kind"] == "PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED"
intent = read(EXEC / "render_intent.json"); request = read(EXEC / "render_request.json")
assert sha(EXEC / "render_intent.json") == wrapper["intent_sha256"] and intent["no_replay"] is True
assert intent["owner"] == request["owner"] == owner and intent["action"] == "render"
assert intent["request"]["sha256"] == sha(EXEC / "render_request.json")
assert remote["command"][-1] == sha(EXEC / "render_request.json")
assert intent["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
assert intent["review_sha256"] == sha(OUT / "cso_production_v2_independent_review.json")
assert intent["current_verification_sha256"] == sha(TICK / "cso_deployment_execution/sync.actual.json")
admission_path = ROOT / "pipeline/admissions/M236-CSO.json"
assert intent["admission_sha256"] == sha(admission_path)
assert request["training_launch_authorized"] is False and request["execution_authorized"] is True
for key in ("admission_receipt", "activation_receipt", "observation_independent_review"):
    item = request[key]; data = base64.b64decode(item["bytes_base64"], validate=True)
    assert digest(data) == item["sha256"] == sha(ROOT / item["path"])
activation = read(ROOT / request["activation_receipt"]["path"])
assert sha(ROOT / request["activation_receipt"]["path"]) == "5fd8ec2e6582d88e8f4a4c10e1ea242242ef91690b86532fbf61677624e28f1c"
assert activation["owner"] == owner and activation["decision"] == "ALLOW_PRODUCTION_PATH_RENDER"
assert activation["training_launch_authorized"] is False
collect_peer = read(ROOT / request["observation_independent_review"]["path"])
assert collect_peer["owner"] == owner and collect_peer["passed"] is True and collect_peer["material_concerns"] == []
assert request["observation_independent_review"]["sha256"] == "80043c4b7e6396155f5c8dff7b9eb49928d6ad30c05c8c23d49f6bd572dae7b3"
collect = read(EXEC / "collect_actual.json"); facts = read(EXEC / "collect_result.json")
assert request["actual_observation_sha256"] == collect["observation"]["remote_result_sha256"] == collect_peer["actual_observation_sha256"]
assert collect_peer["collect_actual_sha256"] == sha(EXEC / "collect_actual.json")
assert activation["actual_observation_sha256"] == request["actual_observation_sha256"]
assert activation["admission_receipt_sha256"] == sha(admission_path)
assert activation["independent_observation_review_sha256"] == request["observation_independent_review"]["sha256"]
binding = result["binding"]; artifact = result["artifact"]
assert binding["owner"] == owner and binding["owner_deadline_at"] == owner["deadline_at"]
assert binding["kind"] == artifact["kind"] == "production"
assert binding["source_commit"] == facts["source_commit"] == "5413102c57b526035f3920b5e7a81f3b58ad764d"
assert binding["producer"] == remote["stage"] == "/data/songcl/Project/Cluster_project/pipeline/runtime/cso_path_prepare_c1fe2178_v2"
assert binding["stage"] == artifact["stage"] == facts["production_stage"] == "/data/songcl/Project/Cluster_project/pipeline/runtime/cso_path_prod_c1fe2178_v2"
assert binding["entry"] == artifact["entry"] == binding["stage"] + "/bin/python"
assert binding["one_shot_marker"] == binding["stage"] + "/train-consumed.json"
assert result["shim"] == binding["stage"] + "/conda_source.sh"
assert binding["runtime_root"] == facts["runtime_root"]
assert binding["hostname"] == "dl04-MS-7E06" and binding["uid"] == 1001
assert binding["physical_gpu"] == 0 and binding["expected_gpu_uuid"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
assert binding["max_project_tasks"] == 1 and binding["required_free_memory_mib"] == 20000
assert binding["resource_values_are_contract_not_current_GPU_observation"] is True
assert binding["activation_receipt_sha256"] == request["activation_receipt"]["sha256"]
assert binding["runtime_config_sha256"] == facts["runtime_config_canonical_preview"]["sha256"] == "f744372291ca7f4e930d0f4bb1c98f6cf58312e8ccb47a5f98d92ab5c33305de"
for key in ("python", "python_realpath", "python_sha256", "source_files", "normal_CPU_environment", "required_asset_sha256", "trainable_core_parameter_count", "trainable_core_parameter_names", "trainable_core_prefix", "lock_files"):
    assert binding[key] == facts[key], key
assert binding["argv"] == ["tools/train.py", read(admission_path)["config"], "--gpu_ids", "0", "--num_gpus", "1"]
assert [(x["dev"],x["ino"]) for x in binding["lock_files"]] == [(66308,92537152),(66308,92537153),(66308,92537154)]
assert binding["normal_CPU_environment"]["Torch_imported"] is binding["normal_CPU_environment"]["GPU_use"] is False
assert result["actual_conda_PATH_resolution"] == ["file", binding["entry"]]
assert result["diagnostic"]["prefix"] == binding["conda_prefix"] and result["diagnostic"]["python"] == binding["python"]
binding_raw = (json.dumps(binding, sort_keys=True, indent=2) + "\n").encode()
assert digest(binding_raw) == artifact["binding_sha256"] == result["files"]["binding.json"]
core_raw = (HERE / "lock_core.py").read_bytes()
assert digest(core_raw) == artifact["core_sha256"] == result["files"]["lock_core.py"] == "ac2938f3258b2b215e1858f6c255b48f1ca3086c3b572a72a37a212701cb015d"
factory = ast.parse((HERE / "entry_factory.py").read_text(encoding="utf-8"))
entry_template = next(node.value for node in ast.walk(factory) if isinstance(node, ast.Assign) and isinstance(node.value, ast.JoinedStr) and any(isinstance(target, ast.Name) and target.id == "entry" for target in node.targets))
values = {"str(stage / 'bin/python')": binding["entry"], "str(stage)": binding["stage"], "expected_kind": "production", "binding['uid']": 1001, "digest(core_bytes)": digest(core_raw), "digest(raw)": digest(binding_raw)}
entry = "".join(node.value if isinstance(node, ast.Constant) else repr(values[ast.unparse(node.value)]) for node in entry_template.values)
assert digest(entry.encode()) == artifact["entry_sha256"] == result["files"]["bin/python"]
ast.parse(entry); compile(entry, 'actual_bound_entry_static', 'exec')
assert set(result["files"]) == {"bin/python", "binding.json", "lock_core.py", "conda_source.sh"}
assert result["files"]["conda_source.sh"] == result["shim_sha256"]
assert datetime.fromisoformat(owner["generated_at"]) < datetime.fromisoformat(result["recorded_at"]) < datetime.fromisoformat(owner["deadline_at"])
review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True, "material_concerns": [],
    "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer", "kind": "ACTUAL_CSO_V2_PRODUCTION_RENDER_AND_ENTRY_BINDING_REVIEW",
    "production_result_sha256": sha(result_path), "production_result_path": result_path.relative_to(ROOT).as_posix(),
    "actual_sha256": sha(actual_path), "render_actual_sha256": sha(actual_path), "remote_raw_result_sha256": digest(raw),
    "source_commit": binding["source_commit"], "admission_sha256": sha(admission_path),
    "source_packet_review_sha256": sha(OUT / "cso_production_v2_independent_review.json"),
    "collect_actual_sha256": sha(EXEC / "collect_actual.json"), "collect_independent_review_sha256": request["observation_independent_review"]["sha256"],
    "activation_receipt_sha256": request["activation_receipt"]["sha256"],
    "production_entry_sha256": artifact["entry_sha256"], "binding_sha256": artifact["binding_sha256"], "lock_core_sha256": artifact["core_sha256"],
    "production_render_passed": True, "production_transport_review_passed": True,
    "actual_entry_hash_reconstructed_from_original_factory_AST_and_exact_binding_core": True,
    "original_conda_PATH_file_resolution_and_original_interpreter_CPU_diagnostic_verified": True,
    "original_three_inode_bindings_and_directfree_cap1_contract_verified": True,
    "one_shot_consumed": False, "training_launch_or_GPU_use": False,
    "actual_locked_marker_directfree_cap1_launch_verified": False,
    "review_scope": "Actual new v2 CPU render succeeded with exact current collect peer/root activation/receipt/source and raw transport closure. Reconstructed entry bytes from immutable original factory AST plus exact binding/core match the observed entry SHA. Only new production path is rendered; marker is absent and no trainer was launched. Fresh locked source/cap1/direct-free checks and actual marker/native increasing steps are still required for launch success.",
    "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False,
    "prepared_module_import_or_execution_performed": False, "shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits": False}
target = OUT / "cso_render_v2_actual_independent_review.json"
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(review, stream, indent=2); stream.write('\n')
print(json.dumps({"path": str(target), "sha256": sha(target), "production_result_sha256": sha(result_path), "passed": True}))
