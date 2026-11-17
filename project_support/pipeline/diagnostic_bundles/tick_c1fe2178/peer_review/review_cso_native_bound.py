"""Independent local AST/hash review; never imports or executes prepared sources."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
HERE = TICK / "cso_native_bound"
OLD = ROOT / "pipeline/diagnostic_bundles/tick_7caf419d/cso_native_bound"
OUT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def dump(node):
    return ast.dump(node, include_attributes=False)

owner = read(TICK / "current_owner_binding.json")
old_owner = read(OLD / "FROZEN.json")["owner"]
live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
assert {key: live[key] for key in owner} == owner
for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
    assert sha(ROOT / "pipeline/headless" / name) == owner[key]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
frozen = read(HERE / "FROZEN.json")
assert sha(HERE / "FROZEN.json") == "16b3a117cf2f3a42fb9a214618ebdb7dd13ccefc8d9c832d95ee736c559439dd"
assert frozen["owner"] == owner
for directory in (OLD, HERE):
    record = read(directory / "FROZEN.json")
    for name, expected in record["files"].items():
        assert sha(directory / name) == expected, (directory, name)
    for item in record["anchors"].values():
        assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
for name in ["worker.py", "candidate.yaml", "protocol_validation.json", "historical_cso_commit_proof.json", "historical_sinc_source_version.json"]:
    assert (HERE / name).read_bytes() == (OLD / name).read_bytes(), name
assert sha(HERE / "worker.py") == "767c54233635c95e16d32f3e8330b16dca2ec76b76967beecf02f9da9fda6343"
for path in (HERE / "candidate_model").iterdir():
    assert path.is_file() and path.suffix == ".py"
    assert path.read_bytes() == (OLD / "candidate_model" / path.name).read_bytes()
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
assert len(list((HERE / "candidate_model").iterdir())) == 8
guard_source = ROOT / "pipeline/diagnostic_bundles/tick_7caf419d/cso_ops_source_draft/direct_memory_free_guard.py"
assert (HERE / "direct_memory_free_guard.py").read_bytes() == guard_source.read_bytes()
assert sha(guard_source) == "1d48570e42ee34e012194ccf412e475a12608396f946e0eac27902907006c111"

def normalized(text):
    for key in old_owner:
        text = text.replace(old_owner[key], owner[key])
    return text.replace("cso_7caf419d_gpu0", "cso_c1fe2178_gpu0")

old_runtime = ast.parse(normalized((OLD / "native_runtime.py").read_text(encoding="utf-8")))
new_runtime = ast.parse((HERE / "native_runtime.py").read_text(encoding="utf-8"))
old_functions = {node.name: node for node in old_runtime.body if isinstance(node, ast.FunctionDef)}
new_functions = {node.name: node for node in new_runtime.body if isinstance(node, ast.FunctionDef)}
assert old_functions.keys() == new_functions.keys()
for name in old_functions.keys() - {"observe", "acquire"}:
    assert dump(old_functions[name]) == dump(new_functions[name]), name
expected_acquire = copy.deepcopy(new_functions["acquire"])
last_observation = []
for node in ast.walk(expected_acquire):
    if isinstance(node, ast.Try):
        for statement in list(node.body):
            if isinstance(statement, ast.Assign) and "last_pre_Torch_observation" in ast.unparse(statement):
                last_observation.append(statement)
                node.body.remove(statement)
assert len(last_observation) == 1
assert dump(expected_acquire) == dump(old_functions["acquire"])
new_global = [node for node in new_runtime.body if not isinstance(node, ast.FunctionDef)
              and not (isinstance(node, ast.ImportFrom) and node.module == "direct_memory_free_guard")]
old_global = [node for node in old_runtime.body if not isinstance(node, ast.FunctionDef)]
assert [dump(node) for node in new_global] == [dump(node) for node in old_global]
observe_source = ast.get_source_segment((HERE / "native_runtime.py").read_text(encoding="utf-8"), new_functions["observe"])
assert "measured = require_direct_free_memory()" in observe_source
assert "memory.free,memory.used,memory.total,utilization.gpu" in observe_source
assert "total - used" not in observe_source
assert "free >= 20000" in observe_source and "if require_usable:" in observe_source
assert "assert not external" not in observe_source and "utilization ==" not in observe_source
acquire_source = ast.get_source_segment((HERE / "native_runtime.py").read_text(encoding="utf-8"), new_functions["acquire"])
assert acquire_source.count("observe(True)") == 3
assert acquire_source.index('before["post_acquisition_observation"] = observe(True)') < acquire_source.index("verify()")
assert acquire_source.index("verify()") < acquire_source.index('before["last_pre_Torch_observation"] = observe(True)')
assert acquire_source.index('before["last_pre_Torch_observation"] = observe(True)') < acquire_source.index("os.environ.update")
assert "release()" in acquire_source and "except BaseException:" in acquire_source

old_transport_source = normalized((OLD / "run_native_once.py").read_text(encoding="utf-8"))
new_transport_source = (HERE / "run_native_once.py").read_text(encoding="utf-8")
expected_transport_source = old_transport_source.replace(
    '(OWNER["thread_id"], "/root", "/root/fresh_ops", "/root/sinc_prod")',
    '(OWNER["thread_id"], "/root", "/root/fresh_ops", "/root/sinc_prod", "/root/cso_native_ops")')
expected_transport_source = expected_transport_source.replace(
    '    assert review["source_and_native_protocol_review_passed"] is True\n',
    '    assert review["source_and_native_protocol_review_passed"] is True\n    assert review["direct_memory_free_guard_integration_review_passed"] is True\n')
assert dump(ast.parse(expected_transport_source)) == dump(ast.parse(new_transport_source))
transport_tree = ast.parse(new_transport_source)
bootstrap = next(ast.literal_eval(node.value) for node in transport_tree.body
                 if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "BOOTSTRAP" for target in node.targets))
old_bootstrap = next(ast.literal_eval(node.value) for node in ast.parse(old_transport_source).body
                     if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "BOOTSTRAP" for target in node.targets))
assert bootstrap == old_bootstrap
ast.parse(bootstrap)
compile(bootstrap, "BOOTSTRAP", "exec")
assert bootstrap.index("assert not result.exists() and not attempt.exists()") < bootstrap.index("with attempt.open('x')") < bootstrap.index("process=subprocess.Popen")
assert new_transport_source.index("assert not occupied") < new_transport_source.index("process = subprocess.Popen(command")
for filename in ("native_runtime.py", "run_native_once.py", "worker.py", "direct_memory_free_guard.py"):
    raw = (HERE / filename).read_text(encoding="utf-8")
    ast.parse(raw, filename=filename)
    compile(raw, filename, "exec")

manifest = read(HERE / "manifest_template.json")
source = read(HERE / "source_version.json")
binding = read(HERE / "source_binding.template.json")
environment = read(HERE / "environment_binding.json")
lease = read(HERE / "execution_lease.template.json")
for value in (manifest, source, binding, environment, lease):
    assert value["owner"] == owner
assert manifest["stage"] == "/data/songcl/Project/Cluster_project/pipeline/cso_c1fe2178_gpu0"
assert manifest["environment_binding_sha256"] == sha(HERE / "environment_binding.json")
assert manifest["source_snapshot_sha256"] == binding["source_snapshot_sha256"] == sha(HERE / "source_version.json")
assert frozen["source_version_sha256"] == sha(HERE / "source_version.json")
assert source["source_files_exact9"] == binding["source_files"]
assert source["source_commit"] == manifest["code_commit"] == "af45707d7b6089f764843337c5f88af285383f88"
assert source["source_parent_commit"] == manifest["source_parent_commit"] == "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
assert source["runtime_original_parent_commit"] == manifest["runtime_code_commit"] == "b1e639b3ceb14bb5c65d9f81a084d41c834b951c"
for key in ("assets", "candidate_source_hashes", "candidate_config_sha256", "private_candidate_loading", "resource_authorization", "resource_memory_policy", "root", "gpu_uuid", "allowed_gpus"):
    assert manifest[key] == read(OLD / "manifest_template.json")[key]
for name, expected in manifest["diagnostic_files"].items():
    assert sha(HERE / name) == expected
assert manifest["diagnostic_files"]["direct_memory_free_guard.py"] == sha(guard_source)
assert lease["draft_template_not_an_actual_execution_lease"] is True
for filename in ("source_version.json", "environment_binding.json"):
    value = read(HERE / filename)
    historical = value["previous_tick7caf_execution_binding"]
    assert historical["owner_preserved"] == old_owner
    assert sha(ROOT / historical["path"]) == historical["sha256"]
    value = {key: part for key, part in value.items() if key != "previous_tick7caf_execution_binding"}
    value["owner"] = old_owner
    assert value == read(OLD / filename)

git = "C:/Program Files (x86)/Git/cmd/git.exe"
worktree = ROOT / "pipeline/isolated_versions/m236_cso_1aa2d994"
git_env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
def git_output(*args):
    return subprocess.check_output([git, "--no-optional-locks", "-c", "core.fsmonitor=false", "-c", "safe.directory=" + worktree.as_posix(), "-C", str(worktree), *args], env=git_env, timeout=30)
assert git_output("show", "-s", "--format=%P", source["source_commit"]).decode().strip() == source["source_parent_commit"]
integration = read(ROOT / "pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json")
assert integration["commit"] == "5413102c57b526035f3920b5e7a81f3b58ad764d"
assert git_output("show", "-s", "--format=%P", integration["commit"]).decode().strip() == source["runtime_original_parent_commit"]
for name, expected in source["source_files_exact9"].items():
    raw = git_output("show", source["source_commit"] + ":" + name)
    assert hashlib.sha256(raw).hexdigest() == expected
    assert git_output("show", integration["commit"] + ":" + name) == raw
    prepared = HERE / "candidate.yaml" if name.endswith(".yaml") else HERE / "candidate_model" / Path(name).name
    assert prepared.read_bytes() == raw
assert source["source_files_exact9"] == integration["files_exact9_sha256"]

worker_source = (HERE / "worker.py").read_text(encoding="utf-8")
worker_tree = ast.parse(worker_source)
resources = next(node for node in worker_tree.body if isinstance(node, ast.FunctionDef) and node.name == "resources")
old_worker = (OLD / "worker.py").read_text(encoding="utf-8")
old_resources = next(node for node in ast.parse(old_worker).body if isinstance(node, ast.FunctionDef) and node.name == "resources")
assert ast.get_source_segment(worker_source, resources) == ast.get_source_segment(old_worker, old_resources)
resources_ast_sha = hashlib.sha256(dump(resources).encode()).hexdigest()
assert resources_ast_sha == read(HERE / "protocol_validation.json")["resources_AST_sha256"]

review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
    "passed": True, "material_concerns": [], "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer",
    "FROZEN_sha256": sha(HERE / "FROZEN.json"), "source_version_sha256": sha(HERE / "source_version.json"),
    "worker_sha256": sha(HERE / "worker.py"), "runtime_sha256": sha(HERE / "native_runtime.py"),
    "transport_sha256": sha(HERE / "run_native_once.py"), "direct_memory_free_guard_sha256": sha(guard_source),
    "source_and_native_protocol_review_passed": True, "source_preparation_review_passed": True,
    "direct_memory_free_guard_integration_review_passed": True, "semantic_model_code_changes": False,
    "status": "CURRENT_OWNER_SOURCE_PROTOCOL_AND_DIRECT_FREE_CALLER_REVIEW_PASSED_ACTUAL_NATIVE_AND_RESOURCES_PENDING",
    "experiment_id": "M236-CSO", "candidate_id": source["candidate_id"],
    "source_commit": source["source_commit"], "source_parent_commit": source["source_parent_commit"],
    "runtime_expected_HEAD": source["runtime_original_parent_commit"], "runtime_root": manifest["root"],
    "retained_distinct_integration_commit": integration["commit"], "new_private_stage": manifest["stage"], "GPU0_UUID": manifest["gpu_uuid"],
    "native_TRAIN2": "NOT_RUN", "native_backward": "NOT_RUN", "resources": "NOT_RUN",
    "actual_native_gate_passed": False, "actual_resource_gate_passed": False,
    "scientific_admission": False, "execution_authorized_by_this_review": False,
    "verified": {
        "frozen_files_exact": len(frozen["files"]), "anchors_exact": len(frozen["anchors"]),
        "current_owner_six_fields_context_pending_deadline_exact": True,
        "old_packet_and_anchors_immutable": True,
        "source9_worker_native_yaml_historical_protocol_byte_identical": True,
        "af457_parent_d214_and_5413102_parent_b1_git_objects_verified_read_only": True,
        "source9_bytes_equal_both_distinct_native_and_integrated_commits": True,
        "resources_function_source_and_AST_unchanged": True,
        "runtime_other_functions_AST_only_owner_stage_and_acquire_final_observation_change": True,
        "transport_AST_only_owner_stage_distinct_reviewer_and_helper_review_guard_changes": True,
        "BOOTSTRAP_byte_exact_except_owner_token_and_new_stage": True,
        "conservative_native_attempt_position_no_replay_default_NOP_unchanged": True,
        "source_binding_manifest_environment_producer_hash_closure": True,
        "helper_byte_exact_to_historical_independent_static_review": True,
        "observe_true_direct_free20000_before_locks_after_locks_and_after_verify_before_Torch": True,
        "observe_false_actual_direct_free_no_postrun20000_gate": True,
        "no_empty_GPU_context_or_utilization_gate": True,
        "original_cap1_three_lock_inode_GPU0_UUID_host_UID_overlay_policy_preserved": True,
        "local_busy_queue_before_SSH_remote_project_trainers_before_Torch_guards_preserved": True,
        "draft_lease_template_not_actual_lease": True,
        "static_compile_only_no_prepared_import_or_execution": True},
    "resources_AST_sha256": resources_ast_sha,
    "readiness_independent_review": {"path": "pipeline/diagnostic_bundles/tick_c1fe2178/peer_review/runtime_readiness_actual_independent_review.json", "sha256": sha(OUT / "runtime_readiness_actual_independent_review.json")},
    "review_scope": "Independent current-owner source/protocol and direct memory.free caller integration review. Worker/model/YAML/data/seed/loss/TRAIN2/common841/core9/resources protocol is unchanged. Native attempt remains conservatively consumed at the original BOOTSTRAP position. This does not review a production caller or declare actual native/resource/scientific gates passed. Root must execute fresh checked arms and submit actual results for distinct review; uncertain attempts remain immutable and unreplayed.",
    "future_actual_result_requirements": [
        "Measure actual M95 versus candidate common names/shapes/dtypes/hash equality and actual tensor_count841, never only derived_expected_count841.",
        "Verify original two natural TRAIN2 input hashes, finite task losses and native backward, all nine core gradients and parameter updates, and untouched full HCG/instance/ILA/mask path.",
        "Independently review actual resources with original retained sample, unchanged fvcore handlers, standard10G, bs1/lang1/warmup20/repeat100 and measured wall/peak-memory data.",
        "Any later production packet requires its own lock-held final direct-free and cap1 checks before its marker and distinct version/activation/deployment/launch reviews."],
    "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False,
    "candidate_or_prepared_module_execution_performed": False,
    "shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits": False}
target = OUT / "cso_native_bound_independent_review.json"
with target.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(review, stream, indent=2)
    stream.write("\n")
print(json.dumps({"path": str(target), "sha256": sha(target), "passed": True}))

