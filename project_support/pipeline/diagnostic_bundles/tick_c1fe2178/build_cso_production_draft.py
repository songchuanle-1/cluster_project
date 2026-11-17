"""Prepare only new CSO operational source drafts; no packet import, SSH or GPU query."""
from datetime import datetime, timezone
import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path('D:/project/cluster_project')
TICK = Path(__file__).resolve().parent
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_9573f1fc/m235_production_prepare'
NEW = TICK / 'cso_production_prepare'
OWNER = json.loads((TICK / 'current_owner_binding.json').read_text())
SOURCE = '5413102c57b526035f3920b5e7a81f3b58ad764d'
PARENT = 'b1e639b3ceb14bb5c65d9f81a084d41c834b951c'
AUTHOR = '/root/cso_native_ops'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(name, value):
    path = NEW / name
    if isinstance(value, str):
        path.write_text(value, encoding='utf8', newline='\n')
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')


assert sys.dont_write_bytecode and os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
assert os.environ['GIT_OPTIONAL_LOCKS'] == '0'
assert OWNER['token'] == 'c1fe217800894083b65baac45f79aa83'
live = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
assert {key: live[key] for key in OWNER} == OWNER
assert not (NEW / 'FROZEN.json').exists(), 'Never revise a frozen/currently executing packet'
old_frozen = read(OLD / 'FROZEN.json')
old_owner = old_frozen['owner']
assert all(sha(OLD / name) == expected for name, expected in old_frozen['files'].items())
NEW.mkdir(exist_ok=True)
binding = read(TICK / 'cso_native_bound/source_binding.template.json')
source9 = binding['source_files']
code8 = {name: value for name, value in source9.items() if name.endswith('.py')}
assert len(source9) == 9 and len(code8) == 8
guard_source = (TICK / 'cso_native_bound/direct_memory_free_guard.py').read_bytes()
assert hashlib.sha256(guard_source).hexdigest() == '1d48570e42ee34e012194ccf412e475a12608396f946e0eac27902907006c111'
core_names = ['input_norm.weight', 'input_norm.bias', 'project.weight', 'readout.0.weight', 'readout.0.bias',
              'readout.2.weight', 'readout.2.bias', 'readout.3.weight', 'readout.3.bias']


def adapt(text):
    for key, value in OWNER.items():
        text = text.replace(old_owner[key], value)
    return (text.replace('9573f1fc', 'c1fe2178').replace('M235-SINC', 'M236-CSO')
        .replace('M235', 'M236').replace('m235', 'cso').replace('SINC', 'CSO')
        .replace('sinc_path_', 'cso_path_').replace('_sinc', '_cso')
        .replace('fine-leaf-geometric-simplex-incidence-composition', 'fine-leaf-full-covariance-shape-composition')
        .replace('b1e639b3ceb14bb5c65d9f81a084d41c834b951c', SOURCE)
        .replace('d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e', PARENT)
        .replace('"/root/sinc_prod")', '"/root/sinc_prod", "/root/cso_native_ops")'))


def replace_assignment(text, name, value):
    tree = ast.parse(text)
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
    lines = text.splitlines(True)
    lines[node.lineno - 1:node.end_lineno] = [name + ' = ' + repr(value) + '\n']
    return ''.join(lines)


shutil.copyfile(OLD / 'entry_factory.py', NEW / 'entry_factory.py')
shutil.copyfile(TICK / 'cso_native_bound/direct_memory_free_guard.py', NEW / 'direct_memory_free_guard.py')
core = (OLD / 'lock_core.py').read_text()
core = core.replace('import sys\n', 'import sys\nfrom datetime import datetime, timezone\nfrom types import ModuleType\n', 1)
core = core.replace('\ndef refuse(', '\nEXPECTED_OWNER = ' + repr(OWNER) + '\nDIRECT_FREE_GUARD_SOURCE = ' + repr(guard_source) +
    '\nDIRECT_FREE_GUARD_SHA256 = ' + repr(hashlib.sha256(guard_source).hexdigest()) + '\n\ndef refuse(', 1)
extra = '''
def require_project_cap1():
    project = Path(BINDING["runtime_root"]).parent
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            if proc.stat().st_uid != BINDING["uid"]:
                continue
            raw = (proc / "cmdline").read_bytes()
            argv = [value.decode(errors="replace") for value in raw.split(b"\\0") if value]
            # Handle direct scripts, -m and short option clusters using the reviewed parser.
            trainer = bool(argv) and (is_training(script_target(argv[1:])) or
                any(value == "tools/train.py" or value.endswith("/tools/train.py") for value in argv))
            cwd = os.readlink(proc / "cwd")
            same_project = cwd == str(project) or cwd.startswith(str(project) + "/")
            if trainer and same_project:
                refuse("Existing same-project trainer occupies cap1; preserve every job", 75)
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            refuse("Uncertain same-user process identity; preserve and refuse", 75)


def require_locked_direct_free():
    if hashlib.sha256(DIRECT_FREE_GUARD_SOURCE).hexdigest() != DIRECT_FREE_GUARD_SHA256:
        refuse("Direct-free helper source identity mismatch")
    module = ModuleType("cso_locked_direct_free_guard")
    exec(compile(DIRECT_FREE_GUARD_SOURCE, "reviewed_direct_memory_free_guard.py", "exec"), module.__dict__)
    measured = module.require_direct_free_memory()
    if measured["index"] != 0 or measured["uuid"] != BINDING["expected_gpu_uuid"]:
        refuse("Direct-free physical GPU0 identity mismatch")
    if measured["memory_free_mib"] < BINDING["required_free_memory_mib"]:
        refuse("Direct memory.free below unchanged 20000 MiB gate", 75)
    if datetime.now(timezone.utc) >= datetime.fromisoformat(EXPECTED_OWNER["deadline_at"]):
        refuse("Current foreground owner expired during direct-free query")
    return measured

'''
core = core.replace('\ndef validate_training(args):', '\n' + extra + '\ndef validate_training(args):', 1)
core = core.replace('    # No proof/test/override environment is read by this branch.\n',
    '    # No proof/test/override environment is read by this branch.\n'
    '    if BINDING["owner"] != EXPECTED_OWNER or BINDING["owner_deadline_at"] != EXPECTED_OWNER["deadline_at"]:\n'
    '        refuse("Current six-field owner binding mismatch")\n'
    '    generated, deadline = (datetime.fromisoformat(EXPECTED_OWNER[key]) for key in ("generated_at", "deadline_at"))\n'
    '    if not generated <= datetime.now(timezone.utc) < deadline:\n'
    '        refuse("Current foreground execution owner expired")\n'
    '    if BINDING["physical_gpu"] != 0 or BINDING["max_project_tasks"] != 1 or BINDING["required_free_memory_mib"] != 20000:\n'
    '        refuse("GPU0 cap1/direct-free resource contract mismatch")\n'
    '    if BINDING["expected_gpu_uuid"] != "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c":\n'
    '        refuse("GPU0 UUID binding mismatch")\n', 1)
core = core.replace('        # A failed/uncertain exec consumes this artifact too.',
    '        # Revalidate source/interpreter/owner under all three retained original locks.\n'
    '        validate_training(args)\n'
    '        require_project_cap1()\n'
    '        last_moment_direct_free = require_locked_direct_free()\n'
    '        # A failed/uncertain exec consumes this artifact too.', 1)
core = core.replace('                "activation_receipt_sha256": BINDING["activation_receipt_sha256"],\n',
    '                "activation_receipt_sha256": BINDING["activation_receipt_sha256"],\n'
    '                "owner": EXPECTED_OWNER, "last_moment_direct_free": last_moment_direct_free,\n'
    '                "same_project_cap1_verified_with_three_original_locks_held": True,\n', 1)
core = core.replace('    validate_training(args)\n    locked_exec(args)\n',
    '    validate_training(args)\n    require_project_cap1()\n    locked_exec(args)\n', 1)
core = core.replace('except (OSError, ValueError, KeyError) as error:', 'except (OSError, ValueError, KeyError, RuntimeError) as error:')
write('lock_core.py', core)

controller = adapt((OLD / 'production_controller.py').read_text())
controller = replace_assignment(controller, 'EXPECTED_SOURCES', code8)
controller = replace_assignment(controller, 'CORE_SHA', sha(NEW / 'lock_core.py'))
controller = controller.replace('d479b53c7874d2515f91af32acdf908a884c91ebb24bcec42d53d12c39c74369', binding['candidate_config_sha256'])
controller = controller.replace('dec.cluster_att.fine_simplex.', 'dec.cluster_att.fine_covariance.')
controller = controller.replace('["point_weight", "factor_weight", "receiver_weight", "output_weight", "point_bias", "message_bias", "output_bias"]', repr(core_names))
controller = controller.replace('"trainable_core_parameter_count": 33536', '"trainable_core_parameter_count": 41856')
write('production_controller.py', controller)
receiver = adapt((OLD / 'remote_receiver.py.txt').read_text())
write('remote_receiver.py.txt', receiver)
setup = adapt((OLD / 'run_setup_once.py').read_text())
write('run_setup_once.py', setup)
resolver = adapt((OLD / 'source_resolver.py').read_text())
resolver = resolver.replace('pipeline/isolated_versions/cso_cso_79656807', 'pipeline/isolated_versions/m236_cso_integrated_7caf419d')
write('source_resolver.py', resolver)
packet = adapt((OLD / 'packet_runtime.py').read_text())
packet = packet.replace('VERIFICATION = TICK / "cso_runtime_verification/runtime_verification.actual.json"',
                        'VERIFICATION = TICK / "cso_deployment_execution/sync.actual.json"')
start = packet.index('HISTORICAL_SYNC = {')
end = packet.index('OWNER = {', start)
packet = packet[:start] + packet[end:]
packet = packet.replace('    # A fresh read-only runtime observation binds the immutable historical sync.\n    # It is never relabelled as a new canonical sync or another owner\'s result.\n',
    '    # Require the new owner\'s real canonical safe_sync outcome; no historical sync relabel.\n')
packet = packet.replace('    assert proof["kind"] == "READ_ONLY_RUNTIME_SOURCE_VERIFICATION"\n', '')
packet = packet.replace('    assert proof["certainty"] == "terminal" and proof["ssh_returncode"] == 0\n',
    '    assert proof["certainty"] == "terminal" and proof["canonical_safe_sync"] is True\n')
start = packet.index('    assert proof["historical_canonical_sync"] == HISTORICAL_SYNC')
end = packet.index('    actual = proof["actual"]', start)
packet = packet[:start] + '''    assert proof["runtime_before"] == PARENT
    assert proof["training_started"] is False and proof["GPU_compute"] is False
    assert proof["signals_sent"] is False and proof["automatic_retry"] is False
''' + packet[end:]
start = packet.index('    assert actual["gpu0"]["index"] == 0')
end = packet.index('    receipt_path = Path(args.admission).resolve()', start)
packet = packet[:start] + '''    assert [(item["kind"], item["device"], item["inode"]) for item in actual["original_locks"]] == [
        ("training", 66308, 92537152), ("diagnostic", 66308, 92537153), ("exclusive", 66308, 92537154),
    ]
''' + packet[end:]
packet = packet.replace('    assert peer["source_review_passed"] is True and peer["production_transport_review_passed"] is True\n',
    '    assert peer["source_review_passed"] is True and peer["production_transport_review_passed"] is True\n'
    '    assert peer["locked_direct_memory_free_and_cap1_integration_review_passed"] is True\n'
    '    assert peer["lock_core_sha256"] == sha(HERE / "lock_core.py")\n')
write('packet_runtime.py', packet)
dispatch = adapt((OLD / 'dispatch_m235_once.py').read_text())
dispatch = dispatch.replace('"d479b53c7874d2515f91af32acdf908a884c91ebb24bcec42d53d12c39c74369"', repr(binding['candidate_config_sha256']))
start = dispatch.index('row=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu"')
end = dispatch.index('contexts=subprocess.check_output(', start)
dispatch = dispatch[:start] + '''from types import ModuleType
helper_source=P["direct_free_source"]
assert hashlib.sha256(helper_source).hexdigest()==P["direct_free_sha256"]
helper=ModuleType("cso_prelaunch_direct_free")
exec(compile(helper_source,"reviewed_direct_memory_free_guard.py","exec"),helper.__dict__)
direct=helper.require_direct_free_memory()
row=", ".join(map(str,(direct["index"],direct["uuid"],direct["memory_free_mib"],direct["memory_used_mib"],direct["memory_total_mib"],direct["utilization_percent"])))
''' + dispatch[end:]
dispatch = dispatch.replace('"free_memory_mib":int(v[3])-int(v[2])', '"free_memory_mib":direct["memory_free_mib"],"memory_free_queried_directly":True')
dispatch = dispatch.replace('"locks": production["binding"]["lock_files"]}',
    '"locks": production["binding"]["lock_files"],\n'
    '                      "direct_free_source": (HERE / "direct_memory_free_guard.py").read_bytes(),\n'
    '                      "direct_free_sha256": sha(HERE / "direct_memory_free_guard.py")}')
write('dispatch_cso_once.py', dispatch)
write('clear_cso_hold_once.py', adapt((OLD / 'clear_m235_hold_once.py').read_text()))

baseline = copy.deepcopy(read(OLD / 'baseline.json'))
baseline['owner'] = OWNER
baseline['source_files_exact9'] = source9
baseline['source_commit'] = SOURCE
baseline['source_parent_commit'] = PARENT
baseline['runtime_original_parent_commit'] = PARENT
baseline['detached_checkout'] = str(ROOT / 'pipeline/isolated_versions/m236_cso_integrated_7caf419d')
baseline.pop('historical_sync_owner_token', None)
baseline.pop('new_sync_performed', None)
baseline['new_sync_required'] = True
baseline['original_conda_source'] = read(ROOT / 'pipeline/diagnostic_bundles/tick_c1fe2178/integrity_before.json').get('original_conda_source', baseline['original_conda_source'])
assert sha(ROOT / 'SERVERS.yaml') == baseline['SERVERS_sha256']
assert sha(ROOT / 'pipeline/goal.json') == baseline['goal_sha256']
assert all(sha(ROOT / 'Cluster' / name) == expected for name, expected in {**baseline['dirty_files_exact28'], **baseline['working_tree_r0_files_exact9']}.items())
write('baseline.json', baseline)
for name in ('collect_request.draft.json', 'render_request.draft.json'):
    request = json.loads(adapt((OLD / name).read_text()))
    request['owner'] = OWNER
    request.pop('fresh_admission_sha256', None)
    request['files'] = {n: sha(NEW / n) for n in ('production_controller.py', 'lock_core.py', 'entry_factory.py')}
    request['historical_CPU_lock_proof_does_not_cover_new_direct_free_integration'] = True
    write(name, request)
contract = json.loads(adapt((OLD / 'independent_review_contract.json').read_text()))
contract.pop('admission_sha256', None)
contract['admission_binding'] = 'Root must finalize against actual pipeline/admissions/M236-CSO.json after genuine gates'
contract['required_fields'] += ['lock_core_sha256', 'locked_direct_memory_free_and_cap1_integration_review_passed']
contract['expected_file_hashes'] = {key: sha(NEW / name) for key, name in (
    ('controller_sha256', 'production_controller.py'), ('transport_sha256', 'run_setup_once.py'),
    ('resolver_sha256', 'source_resolver.py'), ('guard_sha256', 'packet_runtime.py'),
    ('receiver_sha256', 'remote_receiver.py.txt'), ('lock_core_sha256', 'lock_core.py'))}
contract['current_verification_interface'] = str(TICK / 'cso_deployment_execution/sync.actual.json')
contract['scope'] = 'CSO current-owner stage/collect/render/canonical-dispatch caller integration; new actual canonical sync required; original scientific protocol/source unchanged'
write('independent_review_contract.json', contract)
write('activation_receipt.contract.json', {'owner': OWNER, 'source_commit': SOURCE, 'draft_not_an_actual_receipt': True,
    'decision': 'ALLOW_PRODUCTION_PATH_RENDER', 'training_launch_authorized': False,
    'required_real_sha256_fields': ['actual_observation_sha256', 'admission_receipt_sha256', 'independent_observation_review_sha256']})
write('sync_actual_contract.json', {'owner': OWNER, 'source_commit': SOURCE, 'source_parent_commit': PARENT,
    'path': str(TICK / 'cso_deployment_execution/sync.actual.json'),
    'required': ['passed:true', 'certainty:terminal', 'canonical_safe_sync:true', 'runtime_code_commit:source_commit',
                 'source_verified:true', 'source_integrity_before_after:true', 'source_files_exact9:CSO9',
                 'runtime_before:source_parent_commit', 'training_started:false', 'GPU_compute:false', 'signals_sent:false',
                 'automatic_retry:false', 'actual.hostname:dl04-MS-7E06', 'actual.uid:1001', 'actual.runtime_HEAD:source_commit',
                 'actual.original_locks:original device/inodes']})
write('README.md', '''# CSO prospective production source

This is a non-executable source draft until root binds a real M236-CSO admission in FROZEN.json and a distinct reviewer passes the exact frozen packet. No native or resource PASS is claimed. No SSH, resource query, GPU/native action, queue, source, goal or inventory mutation was performed by this author.

Reuse the retained clean detached integration5413102c (parentb1) without a new commit. The eight candidate code files and native YAML are the exact source9 tested through the private native packet; seed/data/schedule/loss/optimizer are unchanged. Root first performs the separately reviewed canonical safe_sync in cso_deployment_prepare, producing cso_deployment_execution/sync.actual.json under the current owner. Its real proof is mandatory at every setup/dispatch guard; no historical synchronization receipt is relabelled.

The 9573 stage/CPU collect/render flow, immutable base conda activation, entry_factory bytes, and scoped server-copy/source resolver are reused. Main SERVERS.yaml keeps its existing consumed shim and is never called as an active training entry: only a temporary server copy receives the new cso_path_prod_c1fe2178/conda_source.sh, restoring the canonical loader afterwards. All operational entrypoints default to NOP and preserve exclusive no-replay intents.

The new lock_core repeats full source/owner/interpreter verification with all three original inode FDs held, scans all same-user project trainers again for cap1, then invokes the exact historical direct-memory.free helper immediately before the one-shot marker. Unknown/low memory or cap1 failure refuses without marker or exec. Three original dev66308 inodes92537152/53/54 remain jointly held and inheritable across original interpreter exec. External GPU contexts remain allowed and untouched; only physical GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c and memory.free>=20000 MiB are accepted. No idle or utilization gate is introduced.

After actual native/resource/independence/constraint gates and canonical M236-CSO admission, root finalizes the packet against that real receipt, obtains the distinct packet review, then runs: run_setup_once.py --execute-root --action stage/collect with --admission/--admission-sha256, --review/--review-sha256, --current-verification/--current-verification-sha256. Independent actual collect review and a genuine ALLOW_PRODUCTION_PATH_RENDER receipt precede render. Independent actual render review precedes clear_cso_hold_once.py (only if the newly admitted task is held), then dispatch_cso_once.py through canonical monitor/closure/safe_launch. Root must confirm actual increasing native optimizer steps after launch. Actual runtime, collect, render, marker, source deployment and trained efficacy remain pending.
''')
for path in NEW.glob('*.py'):
    compile(path.read_bytes(), str(path), 'exec')
compile(receiver, 'remote_receiver.py.txt', 'exec')
assert (NEW / 'entry_factory.py').read_bytes() == (OLD / 'entry_factory.py').read_bytes()
assert 'total - used' not in core and 'int(v[3])-int(v[2])' not in dispatch
assert 'm235_sinc_79656807' not in resolver and 'm236_cso_integrated_7caf419d' in resolver
assert core.index('        validate_training(args)') < core.index('        require_project_cap1()') < core.index('        last_moment_direct_free = require_locked_direct_free()') < core.index('        descriptor = os.open(marker')
helper_assignment = next(n for n in ast.parse(core).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'DIRECT_FREE_GUARD_SOURCE' for t in n.targets))
assert ast.literal_eval(helper_assignment.value) == guard_source
for name, old_name in [('lock_core.py', 'lock_core.py'), ('production_controller.py', 'production_controller.py'),
                       ('packet_runtime.py', 'packet_runtime.py'), ('source_resolver.py', 'source_resolver.py'),
                       ('dispatch_cso_once.py', 'dispatch_m235_once.py'), ('remote_receiver.py.txt', 'remote_receiver.py.txt')]:
    diff = ''.join(difflib.unified_diff((OLD / old_name).read_text().splitlines(True), (NEW / name).read_text().splitlines(True),
                                     fromfile='tick9573/' + old_name, tofile='tickc1fe/' + name))
    write(name + '.diff', diff)
write('draft_validation.json', {'owner': OWNER, 'recorded_at': datetime.now(timezone.utc).isoformat(), 'author_thread_id': AUTHOR,
    'AST_compile_only_no_prepared_import_execution_or_query': True, 'entry_factory_byte_exact': True,
    'direct_free_helper_embedded_source_byte_exact': True, 'three_original_lock_FDs_and_inodes_preserved': True,
    'locked_source_verify_then_same_project_cap1_then_direct_free_then_marker_order': True,
    'one_shot_no_replay_and_original_safe_launch_dispatch_flow_retained': True,
    'new_safe_sync_actual_required_not_old_sync_anchor': True, 'source5413_parentb1_retained_no_commit': True,
    'candidate_source9': source9, 'source_commit': SOURCE, 'source_parent_commit': PARENT,
    'SSH_GPU_Torch_native_queue_or_source_mutation': False, 'native_resources_admission': 'NOT_CLAIMED',
    'frozen_or_executable': False})
anchors = [
    {'path': str((OLD / 'FROZEN.json').relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(OLD / 'FROZEN.json')},
    {'path': 'pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json',
     'sha256': sha(ROOT / 'pipeline/diagnostic_bundles/tick_7caf419d/cso_integration_commit/commit_proof.json')},
    {'path': 'pipeline/diagnostic_bundles/tick_4a0ed3c1/peer_review/guard_source_independent_review.json',
     'sha256': sha(ROOT / 'pipeline/diagnostic_bundles/tick_4a0ed3c1/peer_review/guard_source_independent_review.json')},
    {'path': 'pipeline/diagnostic_bundles/tick_c1fe2178/cso_native_bound/FROZEN.json',
     'sha256': sha(TICK / 'cso_native_bound/FROZEN.json')},
]
write('SOURCE_MANIFEST.NOT_EXECUTABLE.json', {'owner': OWNER, 'author_thread_id': AUTHOR,
    'status': 'SOURCE_DRAFT_PENDING_ACTUAL_ADMISSION_BINDING_AND_DISTINCT_CURRENT_PACKET_REVIEW',
    'source_commit': SOURCE, 'source_parent_commit': PARENT, 'native_commit': binding.get('source_commit', 'af45707d7b6089f764843337c5f88af285383f88'),
    'admission_not_yet_bound': True, 'author_executed': False, 'anchors': anchors,
    'files': {p.name: sha(p) for p in sorted(NEW.iterdir()) if p.is_file() and p.name != 'SOURCE_MANIFEST.NOT_EXECUTABLE.json'}})
assert all(sha(OLD / name) == expected for name, expected in old_frozen['files'].items())
assert not (NEW / 'FROZEN.json').exists()
print(json.dumps({'packet': str(NEW), 'source_manifest_sha256': sha(NEW / 'SOURCE_MANIFEST.NOT_EXECUTABLE.json'),
                  'lock_core_sha256': sha(NEW / 'lock_core.py'), 'status': 'DRAFT_NOT_EXECUTABLE'}, indent=2))
