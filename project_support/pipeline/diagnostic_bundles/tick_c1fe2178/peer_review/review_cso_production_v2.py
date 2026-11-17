"""Independent exact-delta frozen v2 review; never imports prepared modules."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
HERE = TICK / "cso_production_prepare_v2"
OLD = TICK / "cso_production_prepare"
OUT = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def source(path): return Path(path).read_text(encoding="utf-8")
def dump(tree): return ast.dump(tree, include_attributes=False)
owner = read(TICK / "current_owner_binding.json")
frozen = read(HERE / "FROZEN.json")
assert len(sys.argv) == 2 and sha(HERE / "FROZEN.json") == sys.argv[1]
assert frozen["owner"] == owner and frozen["admission_sha256"] == "07b56b16948f7f7e1a4a0682fd6abc81d3eda586e05ae4424f89d16005d8be09"
assert sha(ROOT / "pipeline/admissions/M236-CSO.json") == frozen["admission_sha256"]
assert sha(OLD / "FROZEN.json") == "319eefb852aa8a9a47dea65fd449ab983dca7f571499d6a5fa0b79139428c213"
for directory in (OLD, HERE):
    record = read(directory / "FROZEN.json")
    for name, value in record["files"].items(): assert sha(directory / name) == value, (directory, name)
    for item in record["anchors"]: assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
assert read(HERE / "SOURCE_MANIFEST.NOT_EXECUTABLE.json")["author_thread_id"] == "/root/cso_readiness"
assert sha(HERE / "SOURCE_MANIFEST.NOT_EXECUTABLE.json") == "fed03e1566cd88b6f175940156c5ca23737073f6e4a19b601133e9294937358f"
def new_names(text):
    for name in ("cso_path_prepare_c1fe2178", "cso_path_prod_c1fe2178", "cso_setup_execution", "cso_dispatch_execution", "cso_pointer_execution"):
        text = text.replace(name, name + "_v2")
    return text
for name in ("lock_core.py", "entry_factory.py", "direct_memory_free_guard.py", "baseline.json", "finalize_packet.py", "activation_receipt.contract.json", "sync_actual_contract.json"):
    assert (HERE / name).read_bytes() == (OLD / name).read_bytes(), name
assert sha(HERE / "lock_core.py") == "ac2938f3258b2b215e1858f6c255b48f1ca3086c3b572a72a37a212701cb015d"
for name in ("packet_runtime.py", "run_setup_once.py", "source_resolver.py", "remote_receiver.py.txt", "clear_cso_hold_once.py", "dispatch_cso_once.py"):
    expected = new_names(source(OLD / name))
    if name in ("packet_runtime.py", "run_setup_once.py"):
        expected = expected.replace('"/root/cso_native_ops")', '"/root/cso_native_ops", "/root/cso_readiness")')
    assert dump(ast.parse(expected)) == dump(ast.parse(source(HERE / name))), name
controller = source(HERE / "production_controller.py")
tree = ast.parse(controller)
blob_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "git_blob")
blob = ast.get_source_segment(controller, blob_node)
assert "subprocess.Popen(" in blob and '"cat-file", "blob", COMMIT + ":" + relative' in blob
assert 'text=' not in blob and 'encoding=' not in blob and 'return stdout' in blob
assert 'except subprocess.TimeoutExpired:' in blob and 'preserve PID' in blob
assert 'process.returncode' in blob and 'raise RuntimeError' in blob
without_blob = ast.Module(body=[node for node in tree.body if node is not blob_node], type_ignores=[])
expected_controller = new_names(source(OLD / "production_controller.py"))
expected_controller = expected_controller.replace('git("show", COMMIT + ":tools/train.py").encode("utf-8")', 'git_blob("tools/train.py")')
expected_controller = expected_controller.replace('git("show", COMMIT + ":" + CONFIG).encode("utf-8")', 'git_blob(CONFIG)')
assert dump(without_blob) == dump(ast.parse(expected_controller))
assert sha(HERE / "production_controller.py") == "14cea59d1f0ad44d2657d34d003919cb9b10f5ba034856d4269573e74378209f"
failure_path = TICK / "cso_setup_execution/collect_actual.json"
assert sha(failure_path) == "cc6df05a874e8a522cea69ed8f5b77e7e4cd4ca3be9d2d7fde86b6cf77248ea3"
failure = read(failure_path)
assert failure["owner"] == owner and failure["certainty"] == "terminal" and failure["ssh_returncode"] == 0
assert failure["observation"]["returncode"] == 1 and failure["observation"]["remote_result_sha256"] is None
assert 'digest(original)' in failure["observation"]["stderr"] and 'AssertionError' in failure["observation"]["stderr"]
assert failure["training_launch_or_GPU_use"] is False
git = "C:/Program Files (x86)/Git/cmd/git.exe"
worktree = ROOT / "pipeline/isolated_versions/m236_cso_integrated_7caf419d"
config = read(ROOT / "pipeline/admissions/M236-CSO.json")["config"]
def git_blob(relative):
    return subprocess.check_output([git, "--no-optional-locks", "-c", "core.fsmonitor=false", "-c", "safe.directory=" + worktree.as_posix(), "-C", str(worktree), "cat-file", "blob", frozen["source_commit"] + ":" + relative], env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"), timeout=30)
yaml = git_blob(config); train = git_blob("tools/train.py")
assert len(yaml) == 2791 and yaml.count(b"\r\n") == 134 and hashlib.sha256(yaml).hexdigest() == "908bc08a4d78dcc2723588abb7a6e3adeb169a79e788ce74ee5afbd78c991081"
assert hashlib.sha256(yaml.replace(b"\r\n", b"\n")).hexdigest() == "ba4982b74347efe04c386c2417d9519cce456af8231fa837b4ec49fe0527ffc5"
assert len(train) == 23368 and hashlib.sha256(train).hexdigest() == "4e870e9d24a184e59878c3bca2d70dfc1cc1c5cc66fe8ce6edf96fa364c10e40"
contract = read(HERE / "independent_review_contract.json")
for name in ("collect_request.draft.json", "render_request.draft.json"):
    request = read(HERE / name)
    assert request["owner"] == owner and request["files"]["production_controller.py"] == sha(HERE / "production_controller.py")
    assert request["files"]["lock_core.py"] == sha(HERE / "lock_core.py")
compiled = []
for path in HERE.iterdir():
    if path.suffix == '.py' or path.name == 'remote_receiver.py.txt':
        raw = source(path); ast.parse(raw, filename=path.name); compile(raw, path.name, 'exec'); compiled.append(path.name)
prior_review = OUT / "cso_production_independent_review.json"
assert sha(prior_review) == "e6be4cdeb7272605064daa17ead9155bab0b5ac61a6d22733e2d228985c3bc4f"
review = {
    "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True, "material_concerns": [],
    "reviewer_thread_id": "/root/cso_peer", "reviewer_agent": "/root/cso_peer", "kind": "CSO_PRODUCTION_V2_RAW_GIT_BLOB_CORRECTION_SOURCE_REVIEW",
    "FROZEN_sha256": sha(HERE / "FROZEN.json"), "source_commit": frozen["source_commit"], "source_parent_commit": frozen["source_parent_commit"],
    "admission_sha256": frozen["admission_sha256"], **contract["expected_file_hashes"],
    "source_review_passed": True, "production_transport_review_passed": True,
    "locked_direct_memory_free_and_cap1_integration_review_passed": True, "scoped_resolver_canonical_dispatch_review_passed": True,
    "verified": {"frozen_files_exact": len(frozen["files"]), "anchors_exact": len(frozen["anchors"]),
        "old_frozen_packet_review_and_terminal_failure_immutable": True,
        "controller_delta_exactly_new_v2_paths_raw_git_blob_function_and_two_blob_reads": True,
        "HEAD_remains_text_blob_identity_reads_remain_binary_no_newline_normalization": True,
        "independent_local_real_git_YAML2791_CRLF134_hash908bc_train23368_hash4e870_verified": True,
        "other_operational_modules_AST_only_new_namespaces_and_new_author_exclusion": True,
        "core_B_inheritable_original_3FD_directfree_cap1_entryfactory_helper_byte_identical": True,
        "model9_native_yaml_seed_data_loss_schedule_protocol_admission_sync_unchanged": True,
        "new_intents_and_stages_prevent_old_attempt_replay": True,
        "all_python_source_static_compiled": compiled},
    "prior_source_review": {"path": prior_review.relative_to(ROOT).as_posix(), "sha256": sha(prior_review)},
    "preserved_failed_collect": {"path": failure_path.relative_to(ROOT).as_posix(), "sha256": sha(failure_path), "SSH_returncode": 0, "controller_returncode": 1, "collect_gate_passed": False},
    "failure_scope": "operational byte-identity adapter; not native/model/scientific failure or scientific revision",
    "review_scope": "New operational v2 binding after known terminal CPU collect failure. Root must collect from the new producer and submit actual collect/render/launch evidence; no old stage/intent is replayed. Immutable source541/nativeaf457/YAML CRLF bytes and actual smoke/resources/admission/sync remain unchanged. Original v1 source review did not establish operational correctness and is preserved alongside its real failure.",
    "actual_runtime_collect_or_render_reviewed": False, "last_moment_locked_free_cap1_execution_verified": False,
    "training_started_or_verified_by_this_review": False, "execution_authorized_by_this_review": False,
    "SSH_performed_by_reviewer": False, "Torch_imported_by_reviewer": False, "GPU_use_by_reviewer": False,
    "prepared_module_import_or_execution_performed": False, "shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits": False}
for key in contract["required_fields"]: assert key in review
target = OUT / "cso_production_v2_independent_review.json"
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(review, stream, indent=2); stream.write('\n')
print(json.dumps({"path": str(target), "sha256": sha(target), "passed": True}))
