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
BASE = '11a811618179ab1ddc0cee299194667413b7fdb9'
TESTED = '48fc302c3c02ffef0b241be3593c386b6b65a72e'
EXP = 'M213-BFC'
CID = 'hierarchy-parent-butterfly-token-composition'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc'
CONFIG = 'configs/Quard/ctf_hcg_csort_bfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc.yaml'
TOKEN = '3824d9c96f6343e09d60362b4a00495b'
EXPECTED_OWNER = {'token': '3824d9c96f6343e09d60362b4a00495b', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-25T08:06:47.370222+00:00', 'deadline_at': '2026-10-25T09:06:47.370222+00:00', 'context_sha256': 'eeb5e674ac8ae4fb2c3d5142b0d3cfaa39a96e426127b39702ad55b02b839fe3', 'pending_sha256': 'fe7d536849cc9c0d1dc633d37f1ec8bfb47c977d30ded4d77d2fc35a0835571c'}
# Root must review this draft and bind actual reviewed evidence; never invent hashes.
DRAFT_EXECUTION_ENABLED = False
SEMANTIC_REVIEW_PATH = None
SEMANTIC_REVIEW_SHA = None
INDEPENDENT_REVIEW_PATH = None
INDEPENDENT_REVIEW_SHA = None
INDEPENDENT_STATUS = 'FOUR_ACTUAL_BFC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
PAIRS = [('smoke', 'champion'), ('smoke', 'candidate'),
         ('resources', 'champion'), ('resources', 'candidate')]
PROTECTED_BASELINE = ROOT / 'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json'
PROTECTED_BASELINE_SHA = 'deb2f6e1093be710fbbae886b4008c187b2e6b63d63276bfb47706b36b4be142'


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


def owner_guard():
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    require({k: owner.get(k) for k in EXPECTED_OWNER} == EXPECTED_OWNER,
            'Original six-field owner binding changed; never extend this draft')
    mode = read(ROOT / 'pipeline/execution_mode.json')
    require(mode.get('mode') == 'foreground' and
            owner['thread_id'] == mode.get('target_thread_id') == os.environ.get('CODEX_THREAD_ID'),
            'Actual root/environment/mode mismatch; do not override identity')
    require(datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at']), 'Original deadline expired')
    require(sha(ROOT / 'pipeline/headless/.tick_context.json') == owner['context_sha256'] and
            sha(ROOT / 'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256'],
            'Original context/pending changed')
    require(sha(ROOT / 'pipeline/goal.json') == GOAL, 'Goal changed')
    require(sha(ROOT / 'SERVERS.yaml') == 'd5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2', 'Resource registry changed')
    require(sha(ROOT / 'pipeline/authorizations/server4_gpu1_20261025.json') == '90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8', 'Human GPU1 resource grant changed')
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
    require(sha(PROTECTED_BASELINE) == PROTECTED_BASELINE_SHA, 'Protected baseline changed')
    rows = read(PROTECTED_BASELINE)['protected_existing_worktree']
    require(len(rows) == 28, 'Wrong protected inventory')
    status = [x for x in git_bytes('status', '--porcelain=v1', '-z', '-uall').split(b'\0') if x]
    actual = {(x[:2].decode(), x[3:].decode()) for x in status}
    require(actual == {(r['status'], r['path']) for r in rows}, 'Protected28 status set changed')
    require(all(sha(CODE / r['path']) == r['sha256'] for r in rows), 'Protected28 bytes changed')
    require(not git_bytes('diff', '--cached', '--name-only', '-z'), 'Index is not empty')
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
        path = TICK / 'bfc_execution' / (mode + '_' + target + '_execution.json')
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
            package += '_bfc'
        require(result.get('execution_completed') is True and
                (result.get('candidate_id'), result.get('code_commit'), result.get('goal_sha256'),
                 result.get('mode'), result.get('target'), result.get('model_package')) ==
                (CID, TESTED, GOAL, mode, target, package), 'Raw result identity/completion mismatch')
        require(item['result_sha256'] == envelope.get('result_sha256') and
                item['request_id'] == envelope['identity']['request_id'], 'Original request/result proof mismatch')
        hashes[mode + '_' + target] = sha(path)
    manifest = read(TICK / 'bfc_execution/native_manifest.json')
    require(manifest['candidate_id'] == CID and manifest['code_commit'] == TESTED and
            manifest['goal_sha256'] == GOAL and manifest['current_token'] == TOKEN,
            'Actual manifest candidate/version/original token mismatch')
    binding = read(TICK / 'bfc_execution/execution_binding.json')
    gpu = binding['physical_gpu']
    require(type(gpu) is int and gpu in UUIDS and binding['gpu_uuid'] == UUIDS[gpu], 'Wrong actual selected0or1 binding/UUID')
    require(binding['owner'] == EXPECTED_OWNER and manifest['physical_gpu'] == gpu and manifest['gpu_uuid'] == UUIDS[gpu] and
            binding['native_manifest_sha256'] == sha(TICK / 'bfc_execution/native_manifest.json'),
            'Original fresh binding/GPU/manifest mismatch')
    require(binding['stage'] == '/data/songcl/Project/Cluster_project/pipeline/bfc_' + TOKEN[:8] + '_gpu' + str(gpu), 'Wrong selected-device stage')
    require(manifest['candidate_config_sha256'] == 'a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a' and
            manifest['source_preparation_sha256'] == '8512a69de3d5fcdd32523bbf966833485f3e17329235881de7aa0bd5adbe4501' and
            manifest['diagnostic_files']['worker.py'] == '8839251920577921493b0b663df123c330b850b08779c9841d1d98bbe26e813e', 'Original BFC source/YAML/observer lineage mismatch')
    return manifest, hashes, [ref(local_path), ref(independent_path)]


def source_paths(manifest):
    require(manifest['candidate_name'] == NAME and manifest['config'] == CONFIG, 'Wrong tested package/config')
    names = {'__init__.py', 'backbone.py', 'dec.py', 'hier_postprocess.py', 'loss.py',
             'middle_butterfly.py', 'network.py', 'sample_model.py'}
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
    assignments=[];seen=set();known={'M211-BTC','M212-BCR',EXP}
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
    """Exact original active identities or explicit canonical terminal states."""
    queue = read(ROOT/'pipeline/queue.json') if queue is None else queue
    assignments=running_assignments()
    expected = {
        'M211-BTC':('00e2b18c6b8d568a64edb496e6979d766440883c','93756329046cf30357c258848d6b3287c25b4b0c96ef69b0ffd5f3b8710f2a36',2784474,0),
        'M212-BCR':('11a811618179ab1ddc0cee299194667413b7fdb9','b8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac',1215422,1),
    }
    terminal={'done_complete','done_earlystop'}
    result={}
    for eid,(commit,receipt_sha,pid,gpu) in expected.items():
        rows=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')==eid]
        require(len(rows)<=1,'Duplicate protected experiment row')
        exp_path=ROOT/'pipeline/experiments'/str(eid+'.json');experiment=read(exp_path)
        require(experiment['id']==eid and experiment['code_commit']==commit,'Protected experiment identity changed')
        receipt_relative='pipeline/admissions/'+eid+'.json';receipt_path=ROOT/receipt_relative
        require(sha(receipt_path)==receipt_sha,'Protected original receipt changed')
        reserved=[item for item in assignments if item[2]==eid]
        if rows:
            row=rows[0]
            require(row['code_commit']==commit and row['admission_receipt']==receipt_relative and physical_gpu(row['gpu'])==gpu,'Protected row source/receipt/physical GPU differs from original admitted experiment')
            if row['status']=='running':
                require(type(row.get('pid')) is int and row['pid']==pid and row.get('launch_verified') is True and experiment['status']=='running','Uncertain or replaced protected active process; reconcile first')
                require(reserved==[('server-4',gpu,eid)],'Protected original active row/running mapping disagree')
            else:
                require(row['status'] in terminal and experiment['status']==row['status'] and not reserved,'Unexpected old-row state or terminal experiment still reserved')
        else:
            require(experiment['status'] in terminal and not reserved,'Missing old row requires explicit canonical terminal status and no remaining reservation')
        result[eid]={'queue_rows':copy.deepcopy(rows),'experiment_sha256':sha(exp_path),'receipt_sha256':receipt_sha}
    paused=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')=='M206-CGCA']
    require(len(paused)==1 and paused[0].get('dispatch_hold') and paused[0].get('resume_authorized') is False,'M206 user pause cannot be resumed by resource authorization')
    require(not any(item[2]=='M206-CGCA' for item in assignments),'Paused M206 must not be registered active')
    result['M206-CGCA']={'queue_rows':copy.deepcopy(paused),'experiment_sha256':sha(ROOT/'pipeline/experiments/M206-CGCA.json')}
    result['other_running_mappings']=[(server,str(gpu),eid) for server,gpu,eid in assignments if eid!=EXP]
    return result
