"""Private disabled promotion draft. No effect on import; no authority is created."""
from datetime import datetime, timezone
import hashlib
import copy
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/project/cluster_project')
PRIVATE = Path(__file__).resolve().parent
TICK = PRIVATE.parent
CODE = ROOT / 'Cluster'
BASE = '4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
TESTED = '026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
EXP = 'M215-BEC'
CID = 'hierarchy-cross-level-bipartite-edge-composition'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bec'
CONFIG = 'configs/Quard/ctf_hcg_csort_bec/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bec.yaml'
TOKEN = '94f8ddb8a6e049c48c8e6237f4c737e8'
CURRENT_OWNER = {'token': '94f8ddb8a6e049c48c8e6237f4c737e8', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-26T14:57:12.614254+00:00', 'deadline_at': '2026-10-26T15:57:12.614254+00:00', 'context_sha256': '0104947a1b56f553572b7cddc0fa2f5ab0edbee9ba33f161af61e6990c234793', 'pending_sha256': '95a698a880ff7b5655a002531c1e3b5704e0f9c34ed4e1093f2c6ad72dba2331'}
EXPECTED_OWNER = CURRENT_OWNER
TEST_OWNER = {'token': '94f8ddb8a6e049c48c8e6237f4c737e8', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-26T14:57:12.614254+00:00', 'deadline_at': '2026-10-26T15:57:12.614254+00:00', 'context_sha256': '0104947a1b56f553572b7cddc0fa2f5ab0edbee9ba33f161af61e6990c234793', 'pending_sha256': '95a698a880ff7b5655a002531c1e3b5704e0f9c34ed4e1093f2c6ad72dba2331'}
TEST_TOKEN = '94f8ddb8a6e049c48c8e6237f4c737e8'
TEST_TICK = TICK
EFFECTIVE_STOP_AT = '2026-10-26T15:57:12.614254+00:00'
CURRENT_RESOURCE_AUTHORIZATION = {'path':'pipeline/authorizations/server4_gpu0_only_20261026.json','sha256':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'}
# Root must review this draft and bind actual reviewed evidence; never invent hashes.
DRAFT_EXECUTION_ENABLED = True
SEMANTIC_REVIEW_PATH = 'pipeline/diagnostic_bundles/tick_94f8ddb8/bec_r1_actual_four_result_review.json'
SEMANTIC_REVIEW_SHA = '89099675a78da788f8186968102de364901859110f68ad8cd7bb45065ee798e0'
INDEPENDENT_REVIEW_PATH = 'pipeline/diagnostic_bundles/tick_94f8ddb8/bec_r1_actual_four_result_independent_review.json'
INDEPENDENT_REVIEW_SHA = '46c47d4983a31205d710be5889e7e9e812bd4d3649865edef60c5f046b4c0a36'
INDEPENDENT_STATUS = 'FOUR_ACTUAL_BEC_R1_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
PAIRS = [('smoke', 'champion'), ('smoke', 'candidate'),
         ('resources', 'champion'), ('resources', 'candidate')]
PROTECTED_BASELINE = ROOT / 'pipeline/diagnostic_bundles/tick_94f8ddb8/protected_assets_before.json'
PROTECTED_BASELINE_SHA = '53e9812a8e001ab9b7b450c411d5a8bbb24f57ee8d554ae0137702c3954b4a69'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text('utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'Evidence outside project')
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def execution_enabled(execute_root):
    require(execute_root and DRAFT_EXECUTION_ENABLED is True,
            'DRAFT_DISABLED: no ff/dispatch or shared/remote action is enabled')
    for path, expected in [(SEMANTIC_REVIEW_PATH, SEMANTIC_REVIEW_SHA),
                           (INDEPENDENT_REVIEW_PATH, INDEPENDENT_REVIEW_SHA)]:
        require(path is not None and isinstance(expected, str) and
                re.fullmatch(r'[0-9a-f]{64}', expected), 'Actual review path/SHA must be bound by root')
    require(isinstance(INDEPENDENT_STATUS,str) and INDEPENDENT_STATUS,'Actual independent status schema must be bound by root')


def owner_guard():
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    require({k: owner.get(k) for k in EXPECTED_OWNER} == EXPECTED_OWNER,
            'Original six-field owner binding changed; never extend this draft')
    mode = read(ROOT / 'pipeline/execution_mode.json')
    require(mode.get('mode') == 'foreground' and
            owner['thread_id'] == mode.get('target_thread_id') == os.environ.get('CODEX_THREAD_ID'),
            'Actual root/environment/mode mismatch; do not override identity')
    require(datetime.now(timezone.utc) < min(datetime.fromisoformat(owner['deadline_at']),datetime.fromisoformat(EFFECTIVE_STOP_AT)), 'Current owner or retained overall stop expired; no extension')
    require(sha(ROOT / 'pipeline/headless/.tick_context.json') == owner['context_sha256'] and
            sha(ROOT / 'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256'],
            'Original context/pending changed')
    require(sha(ROOT / 'pipeline/goal.json') == GOAL, 'Goal changed')
    require(sha(ROOT / 'SERVERS.yaml') == '2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1', 'Resource registry changed')
    require(sha(ROOT / CURRENT_RESOURCE_AUTHORIZATION['path']) == CURRENT_RESOURCE_AUTHORIZATION['sha256'], 'Current human GPU0-only resource authorization changed')
    import yaml
    resource_server=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
    require(resource_server['allowed_gpus']==[0] and resource_server['max_tasks_per_gpu']==1 and resource_server['dispatch_enabled'] is True,'Current GPU0-only scope changed')
    policy = read(ROOT / 'pipeline/closure_policy.json')
    auth = {'path':'pipeline/authorizations/experiment_first_20261021.json','sha256':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'}
    require(policy['enabled'] is True and policy['experiment_first']['enabled'] is True and policy['experiment_first']['authorization'] == auth and sha(ROOT / auth['path']) == auth['sha256'], 'Original experiment-first authorization changed')
    return owner


def git_bytes(*args):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(CODE), *args],
                                   env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))


def git(*args):
    return git_bytes(*args).decode('utf-8').strip()


def protected():
    require(sha(PROTECTED_BASELINE) == PROTECTED_BASELINE_SHA, 'Current protected baseline changed')
    baseline=read(PROTECTED_BASELINE)
    require(baseline['head']==BASE and baseline['index_empty'] is True and len(baseline['files'])==28,'Wrong original current primary/protected inventory')
    status=git_bytes('status','--porcelain=v1','-z','-uall')
    require(status.hex()==baseline['status_hex'],'Protected28 status bytes changed')
    require(all(sha(CODE/p)==h for p,h in baseline['files'].items()),'Protected28 bytes changed')
    require(not git_bytes('diff','--cached','--name-only','-z'),'Index is not empty')
    rows=[]
    for item in status.split(b'\0'):
        if item:rows.append({'status':item[:2].decode(),'path':item[3:].decode(),'sha256':baseline['files'][item[3:].decode()]})
    return rows


def reviewed_four_raw():
    execution_enabled(True)
    owner_guard()
    local_path = (ROOT / SEMANTIC_REVIEW_PATH).resolve()
    independent_path = (ROOT / INDEPENDENT_REVIEW_PATH).resolve()
    require(local_path.is_relative_to(ROOT) and independent_path.is_relative_to(ROOT), 'Review path escapes project')
    require(sha(local_path) == SEMANTIC_REVIEW_SHA and sha(independent_path) == INDEPENDENT_REVIEW_SHA,
            'Actual frozen review changed')
    local, independent = read(local_path), read(independent_path)
    observations = local.get('observations') or {}
    require(local.get('review_status') == 'RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' and
            observations.get('native_semantics_and_pairing_checked') is True and
            observations.get('resource_protocol_checked') is True and
            local.get('standard_PASS_receipt_queue_written') is False,
            'Actual local raw semantic review did not pass its recorded schema')
    require(independent.get('status') == INDEPENDENT_STATUS and
            independent.get('material_concerns') == [], 'Actual independent semantic review did not pass')
    for review in (local, independent):
        require((review.get('candidate_id'), review.get('code_commit'), review.get('goal_sha256')) ==
                (CID, TESTED, GOAL), 'Review candidate/version/goal mismatch')
    require(local.get('id') == EXP, 'Local review experiment mismatch')
    raw_refs = independent.get('raw_results', [])
    require(len(raw_refs) == 4, 'Independent review must bind all four original results')
    hashes = {}
    for mode, target in PAIRS:
        path = TEST_TICK / 'bec_r1_execution' / (mode + '_' + target + '_execution.json')
        matches = [r for r in raw_refs if r.get('mode') == mode and r.get('target') == target]
        require(len(matches) == 1, 'Missing/ambiguous independently reviewed pair')
        item = matches[0]
        require((ROOT / item['execution_path']).resolve() == path.resolve() and
                sha(path) == item['execution_sha256'], 'Original independently reviewed raw artifact drift')
        envelope = read(path)
        require(envelope.get('certainty') == 'terminal' and envelope.get('returncode') == 0,
                'A real original execution is not complete/rc0')
        result = envelope.get('result') or {}
        package = 'framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
        if target == 'candidate':
            package += '_bec'
        require(result.get('execution_completed') is True and
                (result.get('candidate_id'), result.get('code_commit'), result.get('goal_sha256'),
                 result.get('mode'), result.get('target'), result.get('model_package')) ==
                (CID, TESTED, GOAL, mode, target, package), 'Raw result identity/completion mismatch')
        require(item['result_sha256'] == envelope.get('result_sha256') and
                item['request_id'] == envelope['identity']['request_id'], 'Original request/result proof mismatch')
        hashes[mode + '_' + target] = sha(path)
    manifest = read(TEST_TICK / 'bec_r1_execution/native_manifest.json')
    require(manifest['candidate_id'] == CID and manifest['code_commit'] == TESTED and
            manifest['goal_sha256'] == GOAL and manifest['current_token'] == TEST_TOKEN,
            'Actual manifest candidate/version/original token mismatch')
    binding = read(TEST_TICK / 'bec_r1_execution/execution_binding.json')
    gpu = binding['physical_gpu']
    require(type(gpu) is int and gpu in UUIDS and binding['gpu_uuid'] == UUIDS[gpu], 'Wrong actual selected0or1 binding/UUID')
    require(binding['owner'] == TEST_OWNER and manifest['physical_gpu'] == gpu and manifest['gpu_uuid'] == UUIDS[gpu] and
            binding['native_manifest_sha256'] == sha(TEST_TICK / 'bec_r1_execution/native_manifest.json'),
            'Original fresh binding/GPU/manifest mismatch')
    require(manifest['allowed_gpus']==[0] and manifest['physical_gpu']==0, 'Actual BEC R1 GPU0-only native policy changed')
    require(binding['stage'] == '/data/songcl/Project/Cluster_project/pipeline/bec_r1_' + TEST_TOKEN[:8] + '_gpu' + str(gpu), 'Wrong selected-device stage')
    require(manifest['candidate_config_sha256'] == 'a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a' and
            manifest['source_preparation_sha256'] == '2ef488c483bf1fb5234dc9615069f7ec2a9232370d186ec4f92cb2bfb3212731' and
            manifest['diagnostic_files']['worker.py'] == '7e5d0f5b109e85d0d2f0bb7f2f806dd9db73fb7885add5abc372ce244ee753e3', 'Original BEC R1 source/YAML/observer lineage mismatch')
    require(manifest.get('revision')==1 and manifest.get('source_parent_commit')==BASE and manifest.get('runtime_code_commit')==BASE and manifest.get('implementation_revision_preregistration_sha256')=='3fa782b8970de909a219cc090e2188983e1afeab1ac99cac43df07b4f1e5b527','Actual R1 source/parent/runtime/prereg mismatch')
    checker = load_checker()
    fresh = checker.review_directory(ROOT, TEST_TICK/'bec_r1_execution')
    require(fresh['review_status']==local['review_status'] and fresh['observations']==local['observations'], 'Current raw semantics differ from frozen local report')
    require(not observations.get('existing_memory_condition_needs_separate_retention_decision'), 'Existing memory-retention condition needs a separate actual root decision')
    return manifest, hashes, [ref(local_path), ref(independent_path)]


def source_paths(manifest):
    require(manifest['candidate_name'] == NAME and manifest['config'] == CONFIG, 'Wrong tested package/config')
    names = {'__init__.py', 'backbone.py', 'dec.py', 'hier_postprocess.py', 'loss.py',
             'bipartite_edges.py', 'network.py', 'sample_model.py'}
    require(set(manifest['candidate_source_hashes']) == names, 'Expected exact eight independent sources')
    paths = {'framework/model/Quard_model/' + NAME + '/' + n: h
             for n, h in manifest['candidate_source_hashes'].items()}
    paths[CONFIG] = manifest['candidate_config_sha256']
    require(all(isinstance(h, str) and re.fullmatch(r'[0-9a-f]{64}', h) for h in paths.values()),
            'Unknown tested source hash')
    return paths


UUIDS={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}

def physical_gpu(value):
    """Accept only explicit physical0or1 integer/string, never bool/coercion."""
    if type(value) is int and value in (0,1):return value
    if type(value) is str and value in ('0','1'):return int(value)
    raise RuntimeError('Unknown or malformed physical GPU assignment; no bool/string coercion')


def running_assignments():
    running=read(ROOT/'pipeline/running.json')
    require(type(running) is dict,'Malformed running registry')
    assignments=[];seen=set();known={EXP}
    for server,gpus in running.items():
        require(type(server) is str and type(gpus) is dict,'Malformed server/GPU running map')
        for raw_gpu,eid in gpus.items():
            require(server=='server-4','Unknown nonempty running server; reconcile first')
            gpu=physical_gpu(raw_gpu)
            require((server,gpu) not in seen and type(eid) is str and eid in known,'Unknown/duplicate/malformed active running assignment')
            seen.add((server,gpu));assignments.append((server,gpu,eid))
    require(len({eid for _,_,eid in assignments})==len(assignments),'Same experiment reserved on multiple cards')
    return sorted(assignments)


def protected_lifecycle(queue=None):
    """Protect original archived experiments/receipts and pausedM206; no revival."""
    queue=read(ROOT/'pipeline/queue.json') if queue is None else queue
    assignments=running_assignments();result={}
    for eid,expected in PROTECTED_TERMINALS.items():
        rows=[x for ts in queue['gpu_queues'].values() for x in ts if x.get('id')==eid]
        require(not rows and not any(x[2]==eid for x in assignments),'Archived original task must not be reintroduced/reserved')
        p=ROOT/'pipeline/experiments'/(eid+'.json');e=read(p)
        require([e.get(k) for k in ('status','code_commit','pid','archive_id')]==expected['identity'],'Original canonical terminal identity changed')
        canonical=copy.deepcopy(e)
        if eid=='M214-CTS':
            local=canonical.pop('log_local',None)
            require(local in ('',str(TICK/'cts_exact_archive'/'train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cts_20261026_140443.log')),'CTS log_local may only be its exact independently SHA/size-verified single-log archive')
            if local:
                evidence=read(TICK/'cts_exact_archive/archive_evidence.json')
                require(evidence['sha256_size_match'] is True and evidence['local_path']==local and sha(Path(local))==evidence['local_sha256'] and Path(local).stat().st_size==evidence['local_size'],'CTS exact archived log bytes changed')
        digest=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        require(digest==expected['experiment_canonical_sha256'],'Original terminal experiment changed outside permitted exact log_local archival')
        rp=ROOT/'pipeline/admissions'/(eid+'.json');require(sha(rp)==expected['receipt_sha256'],'Original admitted receipt changed')
        result[eid]={'experiment_sha256':sha(p),'receipt_sha256':sha(rp),'archive_id':e['archive_id'],'state':e['status']}
    paused=[x for ts in queue['gpu_queues'].values() for x in ts if x.get('id')=='M206-CGCA']
    require(len(paused)==1 and paused[0].get('dispatch_hold') and paused[0].get('resume_authorized') is False,'M206 user pause cannot be resumed')
    require(not any(x[2]=='M206-CGCA' for x in assignments),'PausedM206 cannot reserve a GPU')
    require(sha(ROOT/'pipeline/experiments/M206-CGCA.json')=='9921211c288f9df842ecaf8a13d160825fd34809816a2c0550a41f9cacb9dc89','PausedM206 experiment changed')
    result['M206-CGCA']={'rows':copy.deepcopy(paused),'experiment_sha256':sha(ROOT/'pipeline/experiments/M206-CGCA.json')}
    result['all_other_queue_rows']={server:[copy.deepcopy(t) for t in rows if t.get('id')!=EXP] for server,rows in queue['gpu_queues'].items()}
    result['other_running_mappings']=[(server,str(gpu),eid) for server,gpu,eid in assignments if eid!=EXP]
    require(not result['other_running_mappings'],'Unknown registered work must be reconciled before this BEC-only promotion')
    return result

PROTECTED_TERMINALS = {'M211-BTC': {'identity': ['done_earlystop', '00e2b18c6b8d568a64edb496e6979d766440883c', 2784474, '73e3038e744b4f6a9bffb68a7b43e8f8'], 'experiment_canonical_sha256': '40b936bb5582d3974a4e9cdae42373629155a2a2a8a7c25ea6afeace0058e1ef', 'receipt_sha256': '93756329046cf30357c258848d6b3287c25b4b0c96ef69b0ffd5f3b8710f2a36'}, 'M212-BCR': {'identity': ['done_earlystop', '11a811618179ab1ddc0cee299194667413b7fdb9', 1215422, '5d060afca23d43deb4ae63525c00ff3d'], 'experiment_canonical_sha256': '34ad8be9fc7ca31730c4d28c929ad9838f581858af6e5cecde96b56cdc2f5b79', 'receipt_sha256': 'b8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac'}, 'M213-BFC': {'identity': ['crashed', '48fc302c3c02ffef0b241be3593c386b6b65a72e', 219369, 'b91b3ba11671451bb28f39dc3cc3f2c7'], 'experiment_canonical_sha256': 'dd6932f2ca8a12279e90bd59ad74f374b3987c7d81d4a3653655d0b853014d99', 'receipt_sha256': '812454a819702e8f4d53080c1b479617d605f2175bf44a3422905688253ca01c'}, 'M214-CTS': {'identity': ['stopped_unknown', '4e80006047d5cb3dcdfb9c1102e02c33f354a07d', 3505065, 'a966d7e40d26454598863ac4a87fc4a9'], 'experiment_canonical_sha256': '5b7fcabf4585703482cfd7d2794f2ad7cf1e2adcb699a5aa89ec17da6bae0c16', 'receipt_sha256': '5416d5e2e3b1170f0c741ca5f7c17af48ff33f9e0f559c5aac979b5714f4d9e0'}}

CHECKER_PATH=ROOT/'pipeline/diagnostic_bundles/tick_faccbed6/bec_r1_execution_review_prepare/review_bec_r1.py'
CHECKER_SHA='071202cf0b3ccfed125c00e68e9e3b847fb20388f8fbd83d0bd66eb68a6b13c5'
def load_checker():
    import importlib.util
    require(sha(CHECKER_PATH)==CHECKER_SHA,'Frozen BEC reviewer changed')
    spec=importlib.util.spec_from_file_location('current_actual_bec_reviewer',CHECKER_PATH)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def begin_phase(name,payload):
    owner_guard();path=TICK/('bec_phase_'+name+'_intent.json')
    require(not path.exists(),'Existing durable phase intent requires read-only reconciliation; never rerun')
    require(not (TICK/('bec_phase_'+name+'_result.json')).exists(),'Existing phase result cannot be replayed')
    record={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':CURRENT_OWNER,'native_test_owner':TEST_OWNER,'effective_stop_at':EFFECTIVE_STOP_AT,'current_resource_authorization':CURRENT_RESOURCE_AUTHORIZATION,'id':EXP,'code_commit':TESTED,'phase':name,'status':'INTENT_NO_RESULT_YET',**payload}
    with path.open('x',encoding='utf-8') as stream:json.dump(record,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    return ref(path)

def phase_result(name,result):
    owner_guard();path=TICK/('bec_phase_'+name+'_result.json')
    with path.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    return ref(path)

def require_bec_runtime_settled(explicit_root_declaration):
    """All target four requests are independently reviewed terminal; no foreign scientific gate."""
    require(explicit_root_declaration,'Explicit root confirmation of this target round settlement required')
    manifest, hashes, reviews=reviewed_four_raw()
    return {'target_four_original_requests_terminal_rc0':True,'raw_hashes':hashes,'reviews':reviews}
