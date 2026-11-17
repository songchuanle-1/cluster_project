"""Review retained genuine collect bytes locally; no SSH or model execution."""
import ast
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import yaml

ROOT = Path('D:/project/cluster_project')
TICK = ROOT / 'pipeline/diagnostic_bundles/tick_c1fe2178'
HERE = Path(__file__).resolve().parent
PACKET = TICK / 'cso_production_prepare_v2'
EXEC = TICK / 'cso_setup_execution_v2'
SOURCE = '5413102c57b526035f3920b5e7a81f3b58ad764d'
FROZEN = '03243749f480b986ebf6d5c8bfd52bd1dd3261df407a5b58475d272be1a9d2cc'
ADMISSION = '07b56b16948f7f7e1a4a0682fd6abc81d3eda586e05ae4424f89d16005d8be09'
COLLECT = 'eece27f8be47555e95b414044531bbc142ce913b2a9470583d81729172847c4d'
STAGE = '0300671b1c20aa002dc6aa46297fb5f0743918771ad6d0a056dccf12dfb3f5a3'
SOURCE_REVIEW = '1f9c9ed895f7a13b2942a2837a2408a6f2d025c3b5b10fc9529df3d23377d42b'
PRODUCER = '/data/songcl/Project/Cluster_project/pipeline/runtime/cso_path_prepare_c1fe2178_v2'
PRODUCTION = '/data/songcl/Project/Cluster_project/pipeline/runtime/cso_path_prod_c1fe2178_v2'
RUNTIME = '/data/songcl/Project/Cluster_project/Cluster_nsd_20261107'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
assert sys.dont_write_bytecode and not sys.flags.optimize
assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
os.environ['GIT_OPTIONAL_LOCKS'] = '0'
owner = read(TICK / 'current_owner_binding.json')
assert len(owner) == 6
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
assert sha(PACKET / 'FROZEN.json') == FROZEN
frozen = read(PACKET / 'FROZEN.json')
assert frozen['owner'] == owner and frozen['source_commit'] == SOURCE and frozen['admission_sha256'] == ADMISSION
for name, expected in frozen['files'].items(): assert sha(PACKET / name) == expected, name
for item in frozen['anchors']: assert sha(ROOT / item['path']) == item['sha256'], item['path']
source_peer_path = HERE / 'cso_production_v2_independent_review.json'
assert sha(source_peer_path) == SOURCE_REVIEW
peer = read(source_peer_path)
assert peer['owner'] == owner and peer['passed'] is True and peer['material_concerns'] == []
assert peer['reviewer_thread_id'] == '/root/cso_peer' and peer['reviewer_thread_id'] != frozen['author_thread_id']
assert peer['FROZEN_sha256'] == FROZEN and peer['controller_sha256'] == frozen['files']['production_controller.py']
assert sha(ROOT / 'pipeline/admissions/M236-CSO.json') == ADMISSION
sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import closure
receipt = closure.admission(ROOT, {'id':'M236-CSO','candidate_id':'fine-leaf-full-covariance-shape-composition',
    'config':'configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml',
    'code_commit':SOURCE,'profile':'experiment_first','admission_receipt':'pipeline/admissions/M236-CSO.json'})
collect_path = EXEC / 'collect_actual.json'
assert sha(collect_path) == COLLECT and sha(EXEC / 'stage_actual.json') == STAGE
actual, stage = read(collect_path), read(EXEC / 'stage_actual.json')
assert actual['owner'] == stage['owner'] == owner
assert actual['action'] == 'collect' and actual['certainty'] == 'terminal' and actual['ssh_returncode'] == 0
assert actual['training_launch_or_GPU_use'] is False and actual['stderr'] == ''
observed = actual['observation']
assert json.loads(actual['stdout']) == observed
assert observed['certainty'] == 'terminal' and observed['returncode'] == 0 and observed['result'] is not None
assert observed['owner'] == owner and observed['stage'] == PRODUCER and observed['action'] == 'collect'
assert observed['training_launch_or_GPU_use'] is False and observed['stderr'] == ''
raw_result = base64.b64decode(observed['remote_result_bytes_base64'], validate=True)
assert digest(raw_result) == observed['remote_result_sha256']
result = json.loads(raw_result)
assert result == observed['result'] == json.loads(observed['stdout']) == read(EXEC / 'collect_result.json')
expected_files = {name:frozen['files'][name] for name in ('production_controller.py','lock_core.py','entry_factory.py')}
assert stage['certainty'] == 'terminal' and stage['ssh_returncode'] == 0 and stage['action'] == 'stage'
assert stage['observation']['owner'] == owner and stage['observation']['stage'] == PRODUCER
assert stage['observation']['files'] == expected_files
request = read(EXEC / 'collect_request.json')
assert request['owner'] == owner and request['action'] == 'collect' and request['files'] == expected_files
assert request['execution_authorized'] is True and request['training_launch_authorized'] is False
assert request['prospective_producer'] == PRODUCER and request['prospective_production_stage'] == PRODUCTION
assert request['prospective_runtime'] == RUNTIME and request['prospective_source_commit'] == SOURCE
assert observed['command'] == ['/usr/bin/python3','-I','-B',PRODUCER+'/production_controller.py','collect','--request',PRODUCER+'/collect_request.json','--request-sha256',sha(EXEC/'collect_request.json')]
intent = read(EXEC / 'collect_intent.json')
assert actual['intent_sha256'] == sha(EXEC / 'collect_intent.json')
assert intent['owner'] == owner and intent['FROZEN_sha256'] == FROZEN and intent['review_sha256'] == SOURCE_REVIEW
assert intent['admission_sha256'] == ADMISSION and intent['no_replay'] is True
assert intent['request']['sha256'] == sha(EXEC / 'collect_request.json')
assert intent['current_verification_sha256'] == sha(TICK / 'cso_deployment_execution/sync.actual.json')
assert result['owner'] == owner and result['hostname'] == 'dl04-MS-7E06' and result['uid'] == 1001
assert result['kind'] == 'actual_CPU_observation_only' and result['runtime_root'] == RUNTIME
assert result['source_commit'] == SOURCE and result['production_stage'] == PRODUCTION
assert result['GPU_occupancy_or_resource_PASS'] is False
assert result['gpu_identity_only'] == '0, GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
baseline = read(TICK / 'cso_deployment_prepare/baseline.json')
source8 = {name:h for name,h in baseline['source_files_exact9'].items() if name.endswith('.py')}
assert len(source8) == 8 and result['source_files'] == source8
spec = importlib.util.spec_from_file_location('cso_sync_local_read_only', TICK / 'cso_deployment_prepare/deploy_cso_once.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.protected(); module.verify_checkout()
for name, expected in source8.items(): assert digest(module.git(module.MAIN,'cat-file','blob',SOURCE+':'+name)) == expected
config = module.git(module.MAIN, 'cat-file','blob', SOURCE+':'+module.CONFIG)
train = module.git(module.MAIN, 'cat-file','blob', SOURCE+':tools/train.py')
assert len(config) == 2791 and config.count(b'\r\n') == 134 and digest(config) == '908bc08a4d78dcc2723588abb7a6e3adeb169a79e788ce74ee5afbd78c991081'
assert result['runtime_config_current_sha256'] == digest(config)
assert len(train) == 23368 and digest(train) == result['tools_train_sha256'] == '4e870e9d24a184e59878c3bca2d70dfc1cc1c5cc66fe8ce6edf96fa364c10e40'
preview = result['runtime_config_canonical_preview']
preview_raw = base64.b64decode(preview['bytes_base64'], validate=True)
assert digest(preview_raw) == preview['sha256']
def adapt(value):
    if isinstance(value,dict):return {k:adapt(v) for k,v in value.items()}
    if isinstance(value,list):return [adapt(v) for v in value]
    if isinstance(value,str):
        for old,new in request['path_mappings']:value=value.replace(old,new)
    return value
expected_config = adapt(yaml.safe_load(config))
assert yaml.safe_load(preview_raw) == expected_config
assert yaml.safe_dump(expected_config,sort_keys=False).encode('utf-8') == preview_raw
assert result['python'] == '/home/songcl/.conda/envs/project_cluster/bin/python'
assert result['python_realpath'] == '/home/songcl/.conda/envs/project_cluster/bin/python3.10'
assert result['conda_prefix'] == '/home/songcl/.conda/envs/project_cluster'
assert result['python_sha256'] == '61ae9cdb79cb325d09a903fc05610369ee6488e954b19e165aad9dd6ba0e72f5'
assert result['original_conda_source'] == '/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh'
assert result['original_conda_source_sha256'] == '6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0'
environment = result['normal_CPU_environment']
assert environment['python'] == result['python'] and environment['user_site_enabled'] is True and environment['isolated'] is False
assert environment['Torch_imported'] is False and environment['GPU_use'] is False
assert environment['sha256'] == {'python':result['python_sha256'],'pointnet2_extension':'ef0daa5ccf7fe471a5d73528762f209ba6d2dd89a6c3b50c6371eb9e0edebcfe','torch_module':'2f0deb66d5dff6b9c02a62832c3bf3824c2ee031c462a3afeb9ca170466da5bf','torch_C':'7ebf704b024577720e8ace3c37bfff24fc333c8796d8655911c2af74984a0169'}
assert result['lock_files'] == [{'path':'/tmp/cluster_project_gpu0_'+kind+'.lock','dev':66308,'ino':ino} for kind,ino in [('training',92537152),('diagnostic',92537153),('exclusive',92537154)]]
assert result['core_sha256'] == expected_files['lock_core.py'] and result['factory_sha256'] == expected_files['entry_factory.py']
assert result['trainable_core_prefix'] == 'dec.cluster_att.fine_covariance.' and result['trainable_core_parameter_count'] == 41856
assert result['trainable_core_parameter_names'] == ['input_norm.weight','input_norm.bias','project.weight','readout.0.weight','readout.0.bias','readout.2.weight','readout.2.bias','readout.3.weight','readout.3.bias']
assert result['required_asset_sha256'] == {RUNTIME+'/tools/train.py':digest(train),RUNTIME+'/framework/dataset/scannetv2.py':'2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d',RUNTIME+'/framework/lib/pointgroup_ops/pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so':'c86f516858d480e2583a437deb598279bc626e74975a060b17d75bf03f630033','/home/songcl/data/data/scanrefer/ScanRefer_train_new.json':'018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d','/home/songcl/data/data/sp_unet_backbone.pth':'a6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f'}
reconcile_path = HERE / 'cso_collect_failure_reconcile.actual.json'
reconcile = read(reconcile_path)
assert sha(reconcile_path) == '5e16c277747ddb1456d9055f1e4aec9ff08175069b4569157caf45e7734ccbb5'
for path, expected in reconcile['frozen_local_readset_sha256'].items(): assert sha(path) == expected
for name, expected in read(TICK / 'cso_production_prepare/FROZEN.json')['files'].items(): assert sha(TICK/'cso_production_prepare'/name) == expected
review = {'owner':owner,'recorded_at':datetime.now(timezone.utc).isoformat(),'passed':True,'material_concerns':[],
    'reviewer_thread_id':'/root/cso_sync_peer','kind':'INDEPENDENT_ACTUAL_CSO_V2_CPU_COLLECT_REVIEW_NOT_TRAINING_PASS',
    'source_commit':SOURCE,'FROZEN_sha256':FROZEN,'admission_sha256':ADMISSION,
    'actual_observation_sha256':observed['remote_result_sha256'],'collect_actual_sha256':COLLECT,
    'stage_actual_sha256':STAGE,'source_review_sha256':SOURCE_REVIEW,
    'controller_sha256':frozen['files']['production_controller.py'],'producer':PRODUCER,'production_stage':PRODUCTION,
    'runtime_config_original_sha256':digest(config),'runtime_config_canonical_preview_sha256':preview['sha256'],
    'verified':{'terminal_ssh0_controller0_genuine_raw_remote_serialization_and_local_wrapper_agree':True,
        'new_v2_owner6_producer_source_review_admission_sync_request_intent_bound':True,
        'runtime_source8_train_and_raw_CRLF_YAML_exact_committed_bytes':True,
        'canonical_path_preview_semantics_and_serialized_bytes_reproduced_locally':True,
        'normal_user_site_CPU_interpreter_extension_hashes_no_Torch_or_compute':True,
        'GPU0_identity_only_not_occupancy_or_resource_PASS':True,
        'three_original_lock_device_inode_metadata':True,'required_assets_and_core9_41856_bindings':True,
        'old_failed_collect_frozen_packet_and_intents_preserved':True,'protected_main_and_existing_clean_checkout_rechecked':True},
    'review_scope':'Genuine new-v2 CPU collect only; render and production launch remain separate unobserved stages. GPU0 identity query is not availability or resource PASS. Old terminal failure and its independent read-only reconciliation remain preserved.',
    'training_launch_or_GPU_compute_verified':False,'production_render_reviewed':False,
    'SSH_performed_by_this_review':False,'Torch_imported_by_this_review':False,'GPU_query_or_compute_by_this_review':False,
    'shared_ledger_queue_SERVERS_or_source_modified_by_this_review':False}
assert sha(collect_path) == COLLECT and sha(PACKET/'FROZEN.json') == FROZEN
target = HERE / 'cso_collect_v2_actual_independent_review.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(review,stream,indent=2);stream.write('\n')
print(json.dumps({'path':str(target),'sha256':sha(target),'actual_observation_sha256':observed['remote_result_sha256'],'collect_actual_sha256':COLLECT,'passed':True}))
