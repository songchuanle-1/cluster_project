"""Independent frozen production source review; stdlib-only local AST/hash checks."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TICK = Path(__file__).resolve().parents[1]
HERE = TICK / "cso_production_prepare"
OLD = ROOT / "pipeline/diagnostic_bundles/tick_9573f1fc/m235_production_prepare"
OUT = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def source(path): return Path(path).read_text(encoding="utf-8")
def dump(tree): return ast.dump(tree, include_attributes=False)
def functions(text): return {node.name: node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}
owner = read(TICK / "current_owner_binding.json")
frozen = read(HERE / "FROZEN.json")
assert sha(HERE / "FROZEN.json") == "319eefb852aa8a9a47dea65fd449ab983dca7f571499d6a5fa0b79139428c213"
assert frozen["owner"] == owner
for name, expected in frozen["files"].items(): assert sha(HERE / name) == expected, name
for item in frozen["anchors"]: assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
admission_path = ROOT / "pipeline/admissions/M236-CSO.json"
assert sha(admission_path) == frozen["admission_sha256"] == "07b56b16948f7f7e1a4a0682fd6abc81d3eda586e05ae4424f89d16005d8be09"
admission = read(admission_path)
assert admission["owner"] == owner and admission["code_commit"] == frozen["source_commit"] == "5413102c57b526035f3920b5e7a81f3b58ad764d"
for key in ("authorization", "native_smoke", "decision", "version_association", "version_association_review"):
    item = admission[key]; assert sha(ROOT / item["path"]) == item["sha256"]
for value in admission["gates"].values():
    assert value["passed"] is True
    for item in value["evidence"]: assert sha(ROOT / item["path"]) == item["sha256"]
assert read(HERE / "finalization_validation.json")["canonical_closure_admission_validated"] is True
live = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
assert {key: live[key] for key in owner} == owner
for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
    assert sha(ROOT / "pipeline/headless" / name) == owner[key]
old_owner = read(OLD / "FROZEN.json")["owner"]
def normalized(text):
    text = text.replace("pipeline/isolated_versions/m235_sinc_79656807", "pipeline/isolated_versions/m236_cso_integrated_7caf419d")
    for key in owner: text = text.replace(old_owner[key], owner[key])
    text = text.replace("9573f1fc", "c1fe2178").replace("M235-SINC", "M236-CSO").replace("M235", "M236").replace("m235_", "cso_")
    text = text.replace("sinc_path_", "cso_path_").replace("ctf_hcg_csort_sinc", "ctf_hcg_csort_cso")
    text = text.replace("fine-leaf-geometric-simplex-incidence-composition", "fine-leaf-full-covariance-shape-composition")
    text = text.replace("b1e639b3ceb14bb5c65d9f81a084d41c834b951c", "5413102c57b526035f3920b5e7a81f3b58ad764d")
    text = text.replace('"/root/sinc_prod")', '"/root/sinc_prod", "/root/cso_native_ops")')
    return text
for new_name, old_name in (("source_resolver.py", "source_resolver.py"), ("remote_receiver.py.txt", "remote_receiver.py.txt"), ("run_setup_once.py", "run_setup_once.py"), ("clear_cso_hold_once.py", "clear_m235_hold_once.py")):
    assert dump(ast.parse(normalized(source(OLD / old_name)))) == dump(ast.parse(source(HERE / new_name))), new_name
assert (HERE / "entry_factory.py").read_bytes() == (OLD / "entry_factory.py").read_bytes()
assert sha(HERE / "entry_factory.py") == "0a8ed26bd62327314de89f4228b53c8c633fdd73e4e1867d674df94b24d073dd"
guard_raw = (HERE / "direct_memory_free_guard.py").read_bytes()
assert hashlib.sha256(guard_raw).hexdigest() == "1d48570e42ee34e012194ccf412e475a12608396f946e0eac27902907006c111"
core_text = source(HERE / "lock_core.py"); old_core = source(OLD / "lock_core.py")
core_tree = ast.parse(core_text); core_functions = functions(core_text); old_functions = functions(old_core)
embedded = {target.id: ast.literal_eval(node.value) for node in core_tree.body if isinstance(node, ast.Assign)
            for target in node.targets if isinstance(target, ast.Name) and target.id in ("DIRECT_FREE_GUARD_SOURCE", "DIRECT_FREE_GUARD_SHA256", "EXPECTED_OWNER")}
assert embedded["DIRECT_FREE_GUARD_SOURCE"] == guard_raw
assert embedded["DIRECT_FREE_GUARD_SHA256"] == sha(HERE / "direct_memory_free_guard.py") and embedded["EXPECTED_OWNER"] == owner
for name in ("refuse", "sha", "script_target", "is_training", "checked_file", "check_lock_inode"):
    assert dump(core_functions[name]) == dump(old_functions[name]), name
assert dump(core_functions['run']) == dump(functions(old_core.replace('except (OSError, ValueError, KeyError)', 'except (OSError, ValueError, KeyError, RuntimeError)'))['run'])
assert core_text.count('[BINDING["python"], "-B", *args]') == 2
new_validate = copy.deepcopy(core_functions["validate_training"])
first_old = dump(old_functions["validate_training"].body[0])
index = next(i for i, node in enumerate(new_validate.body) if dump(node) == first_old)
assert index == 5
new_validate.body = new_validate.body[index:]
assert dump(new_validate) == dump(old_functions["validate_training"])
locked = ast.get_source_segment(core_text, core_functions["locked_exec"])
assert locked.index("validate_training(args)") < locked.index("require_project_cap1()") < locked.index("require_locked_direct_free()") < locked.index("descriptor = os.open(marker") < locked.index("os.execve")
assert locked.index("check_lock_inode(descriptor, specification)") < locked.index("validate_training(args)")
assert 'os.set_inheritable(descriptor, True)' in locked and 'os.O_EXCL' in locked and 'os.O_NOFOLLOW' in locked
assert '"last_moment_direct_free": last_moment_direct_free' in locked and '"same_project_cap1_verified_with_three_original_locks_held": True' in locked
cap1 = ast.get_source_segment(core_text, core_functions["require_project_cap1"])
assert 'except PermissionError:' in cap1 and 'preserve and refuse' in cap1 and 'is_training(script_target(argv[1:]))' in cap1
free = ast.get_source_segment(core_text, core_functions["require_locked_direct_free"])
assert free.index('module.require_direct_free_memory()') < free.index('datetime.now(timezone.utc)') < free.index('return measured')
assert 'total - used' not in core_text
baseline = read(HERE / "baseline.json")
exact9 = read(ROOT / "pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json")["files_exact9_sha256"]
assert baseline["source_files_exact9"] == exact9
assert sha(ROOT / "pipeline/goal.json") == baseline["goal_sha256"] and sha(ROOT / "SERVERS.yaml") == baseline["SERVERS_sha256"]
for name, expected in {**baseline["dirty_files_exact28"], **baseline["working_tree_r0_files_exact9"]}.items(): assert sha(ROOT / "Cluster" / name) == expected
for name, expected in exact9.items(): assert sha(ROOT / "pipeline/isolated_versions/m236_cso_integrated_7caf419d" / name) == expected
controller_text = source(HERE / "production_controller.py")
controller_tree = ast.parse(controller_text)
constants = {target.id: ast.literal_eval(node.value) for node in controller_tree.body if isinstance(node, ast.Assign)
             for target in node.targets if isinstance(target, ast.Name) and target.id in ("CORE_SHA", "FACTORY_SHA", "EXPECTED_SOURCES", "EXACT_ARGS", "EXPECTED_OWNER", "COMMIT")}
assert constants["CORE_SHA"] == sha(HERE / "lock_core.py") == "ac2938f3258b2b215e1858f6c255b48f1ca3086c3b572a72a37a212701cb015d"
assert constants["EXPECTED_OWNER"] == owner and constants["COMMIT"] == frozen["source_commit"]
assert constants["FACTORY_SHA"] == sha(HERE / "entry_factory.py")
assert constants["EXPECTED_SOURCES"] == {name: value for name, value in exact9.items() if name.endswith('.py')}
assert constants["EXACT_ARGS"] == ["tools/train.py", admission["config"], "--gpu_ids", "0", "--num_gpus", "1"]
for filename in ("collect_request.draft.json", "render_request.draft.json"):
    draft = read(HERE / filename)
    assert draft["owner"] == owner
    assert draft["files"]["lock_core.py"] == constants["CORE_SHA"]
packet_text = source(HERE / "packet_runtime.py")
assert 'proof["runtime_before"] == PARENT' in packet_text and 'proof["canonical_safe_sync"] is True' in packet_text
assert 'proof["source_integrity_before_after"] is True' in packet_text and 'proof["automatic_retry"] is False' in packet_text
assert 'peer["locked_direct_memory_free_and_cap1_integration_review_passed"] is True' in packet_text
assert 'peer["lock_core_sha256"] == sha(HERE / "lock_core.py")' in packet_text
assert 'closure.admission(ROOT, task)' in packet_text
dispatch_text = source(HERE / "dispatch_cso_once.py")
assert 'helper.require_direct_free_memory()' in dispatch_text and 'int(v[3])-int(v[2])' not in dispatch_text
assert 'len(eligible) == 1 and eligible[0]["id"] == "M236-CSO"' in dispatch_text
assert 'monitor._process_queue(' in dispatch_text
compiled = []
for path in HERE.iterdir():
    if path.suffix == '.py' or path.name == 'remote_receiver.py.txt':
        text = source(path); ast.parse(text, filename=path.name); compile(text, path.name, 'exec'); compiled.append(path.name)
compile(guard_raw, 'embedded_reviewed_free_guard', 'exec')
sync_path = TICK / 'cso_deployment_execution/sync.actual.json'
assert sha(sync_path) == 'd04ac71ed5f62a3a65d60b613cdee137476355cc9c2dc4575678a0de61bcdec1'
sync = read(sync_path)
assert sync['owner'] == owner and sync['passed'] and sync['canonical_safe_sync'] and sync['source_commit'] == frozen['source_commit']
contract = read(HERE / 'independent_review_contract.json')
review = {
    'owner': owner, 'recorded_at': datetime.now(timezone.utc).isoformat(), 'passed': True, 'material_concerns': [],
    'reviewer_thread_id': '/root/cso_peer', 'reviewer_agent': '/root/cso_peer', 'kind': 'CURRENT_OWNER_COMPLETE_CSO_PRODUCTION_SOURCE_AND_CALLER_REVIEW',
    'FROZEN_sha256': sha(HERE / 'FROZEN.json'), 'source_commit': frozen['source_commit'], 'source_parent_commit': frozen['source_parent_commit'],
    'admission_sha256': sha(admission_path), **{key: value for key, value in contract['expected_file_hashes'].items()},
    'dispatch_sha256': sha(HERE / 'dispatch_cso_once.py'), 'clear_hold_sha256': sha(HERE / 'clear_cso_hold_once.py'),
    'source_review_passed': True, 'production_transport_review_passed': True,
    'locked_direct_memory_free_and_cap1_integration_review_passed': True, 'scoped_resolver_canonical_dispatch_review_passed': True,
    'verified': {'frozen_files_exact': len(frozen['files']), 'anchors_exact': len(frozen['anchors']),
        'owner6_context_pending_deadline_new_stages_exact': True, 'actual_canonical_M236_admission_and_all_evidence_hashes_bound': True,
        'new_current_canonical_safe_sync541_required_and_present': True, 'source9_exact_tested_native_and_clean_integrated_bytes': True,
        'entry_factory_original_byte_exact': True, 'resolver_receiver_transport_clear_AST_normalized_exact': True,
        'three_original_inode_FDs_no_create_nonblocking_and_inheritable_preserved': True,
        'locked_source_owner_interpreter_reverify_then_cap1_then_direct_free_then_deadline_before_marker': True,
        'helper_embedded_source_byte_exact_hash_verified_no_total_minus_used': True,
        'no_external_context_or_utilization_gate_and_no_signals': True,
        'two_final_original_interpreter_execve_argv_explicit_B': True,
        'new_stage_collect_render_intents_requests_exclusive_no_replay_and_distinct_current_reviews_required': True,
        'render_requires_new_collect_peer_and_root_activation_before_one_shot_production_stage': True,
        'clear_only_new_M236_then_only_eligible_M236_canonical_dispatch': True,
        'protected37_main_bytes_goal_SERVERS_unchanged': True, 'all_python_sources_and_embedded_helper_static_compiled': compiled},
    'current_sync_actual_sha256': sha(sync_path),
    'historical_CPU_proof_scope': 'Old proof remains lineage for retained factory/original lock propagation only; newly integrated lock core has static review here, not a claim of new CPU/GPU execution.',
    'review_scope': 'Complete final frozen source/caller packet bound to genuine current canonical M236 admission and new safe_sync541. Source/static integration PASS only. Root must still obtain current stage/CPU collect, distinct observation review, activation, real render, distinct render review, last-moment lock-held marker data and increasing native training steps. No model/data/seed/loss/schedule/resource protocol change or actual production success is inferred.',
    'actual_runtime_collect_or_render_reviewed': False, 'last_moment_locked_free_cap1_execution_verified': False,
    'training_started_or_verified_by_this_review': False, 'execution_authorized_by_this_review': False,
    'SSH_performed_by_reviewer': False, 'Torch_imported_by_reviewer': False, 'GPU_use_by_reviewer': False,
    'prepared_module_import_or_execution_performed': False, 'shared_work_queue_memory_ledger_SERVERS_goal_or_source_edits': False}
for key in contract['required_fields']: assert key in review
for key, expected in contract['expected_file_hashes'].items(): assert review[key] == expected
target = OUT / 'cso_production_independent_review.json'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(review, stream, indent=2); stream.write('\n')
print(json.dumps({'path': str(target), 'sha256': sha(target), 'passed': True}))
