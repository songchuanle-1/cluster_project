"""Local template authoring from the actual proven M212 root helpers."""
from pathlib import Path
import ast
import hashlib
import json

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
OLD=PROJECT/'pipeline/diagnostic_bundles/tick_7526f819/bcr_promotion_execute'
OWNER_KEYS=('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')
owner=json.loads((PROJECT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
owner={k:owner[k] for k in OWNER_KEYS}
assert owner['token']=='3824d9c96f6343e09d60362b4a00495b'


def replace_function(source,name,replacement):
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1])+replacement.strip()+'\n'+''.join(lines[node.end_lineno:])


def replace_assignment(source,name,value):
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    lines=source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1])+name+' = '+repr(value)+'\n'+''.join(lines[node.end_lineno:])


common=(OLD/'promotion_common.py').read_text(encoding='utf-8').replace('import hashlib\n','import hashlib\nimport copy\n',1)
for key,value in {
    'BASE':'11a811618179ab1ddc0cee299194667413b7fdb9',
    'TESTED':'48fc302c3c02ffef0b241be3593c386b6b65a72e',
    'EXP':'M213-BFC','CID':'hierarchy-parent-butterfly-token-composition',
    'NAME':'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc',
    'CONFIG':'configs/Quard/ctf_hcg_csort_bfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc.yaml',
    'TOKEN':owner['token'],'EXPECTED_OWNER':owner,'DRAFT_EXECUTION_ENABLED':False,
    'SEMANTIC_REVIEW_PATH':None,'SEMANTIC_REVIEW_SHA':None,'INDEPENDENT_REVIEW_PATH':None,'INDEPENDENT_REVIEW_SHA':None,
    'INDEPENDENT_STATUS':'FOUR_ACTUAL_BFC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDLY_VALIDATED'.replace('INDEPENDLY','INDEPENDENTLY'),
}.items():common=replace_assignment(common,key,value)
common=common.replace('bcr_gpu1_execution','bfc_execution').replace("package += '_bcr'", "package += '_bfc'").replace("'middle_complement.py'", "'middle_butterfly.py'")
old="""    require(read(ROOT / 'pipeline/experiments/M210-PSNC.json')['status'] == 'done_earlystop',
            'Original PSNC has not been canonically archived')
"""
assert old in common;common=common.replace(old,'')
old="""    require(binding['owner'] == EXPECTED_OWNER and binding['physical_gpu'] == 1 and
            binding['native_manifest_sha256'] == sha(TICK / 'bfc_execution/native_manifest.json'),
            'Original fresh binding/GPU/manifest mismatch')"""
new="""    gpu = binding['physical_gpu']
    require(type(gpu) is int and gpu in UUIDS and binding['gpu_uuid'] == UUIDS[gpu], 'Wrong actual selected0or1 binding/UUID')
    require(binding['owner'] == EXPECTED_OWNER and manifest['physical_gpu'] == gpu and manifest['gpu_uuid'] == UUIDS[gpu] and
            binding['native_manifest_sha256'] == sha(TICK / 'bfc_execution/native_manifest.json'),
            'Original fresh binding/GPU/manifest mismatch')
    require(binding['stage'] == '/data/songcl/Project/Cluster_project/pipeline/bfc_' + TOKEN[:8] + '_gpu' + str(gpu), 'Wrong selected-device stage')
    require(manifest['candidate_config_sha256'] == 'a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a' and
            manifest['source_preparation_sha256'] == '8512a69de3d5fcdd32523bbf966833485f3e17329235881de7aa0bd5adbe4501' and
            manifest['diagnostic_files']['worker.py'] == '8839251920577921493b0b663df123c330b850b08779c9841d1d98bbe26e813e', 'Original BFC source/YAML/observer lineage mismatch')"""
assert old in common;common=common.replace(old,new)
common=common.replace("    return owner\n", """    policy = read(ROOT / 'pipeline/closure_policy.json')
    auth = {'path':'pipeline/authorizations/experiment_first_20261021.json','sha256':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'}
    require(policy['enabled'] is True and policy['experiment_first']['enabled'] is True and policy['experiment_first']['authorization'] == auth and sha(ROOT / auth['path']) == auth['sha256'], 'Original experiment-first authorization changed')
    return owner
""",1)
common += '''

UUIDS={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}

def protected_lifecycle(queue=None):
    """Preserve present original rows or canonical terminal archives; never resume."""
    queue = read(ROOT/'pipeline/queue.json') if queue is None else queue
    expected = {
        'M211-BTC':('00e2b18c6b8d568a64edb496e6979d766440883c','93756329046cf30357c258848d6b3287c25b4b0c96ef69b0ffd5f3b8710f2a36',2784474),
        'M212-BCR':('11a811618179ab1ddc0cee299194667413b7fdb9','b8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac',1215422),
    }
    result={}
    for eid,(commit,receipt_sha,pid) in expected.items():
        rows=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')==eid]
        require(len(rows)<=1,'Duplicate protected experiment row')
        exp_path=ROOT/'pipeline/experiments'/str(eid+'.json');experiment=read(exp_path)
        require(experiment['id']==eid and experiment['code_commit']==commit,'Protected experiment identity changed')
        receipt_path=ROOT/'pipeline/admissions'/str(eid+'.json');require(sha(receipt_path)==receipt_sha,'Protected original receipt changed')
        if rows and rows[0]['status'] in ('running','claiming'):
            require(rows[0]['status']=='running' and rows[0].get('pid')==pid and rows[0].get('launch_verified') is True,'Uncertain or replaced protected active process; reconcile first')
        if not rows:
            require(str(experiment['status']).startswith('done') or experiment['status'] in ('completed','archived','crashed','failed','cancelled'),'Missing queue row without canonical terminal archive; reconcile first')
        result[eid]={'queue_rows':copy.deepcopy(rows),'experiment_sha256':sha(exp_path),'receipt_sha256':receipt_sha}
    paused=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')=='M206-CGCA']
    require(len(paused)==1 and paused[0].get('dispatch_hold') and paused[0].get('resume_authorized') is False,'M206 user pause cannot be resumed by resource authorization')
    result['M206-CGCA']={'queue_rows':copy.deepcopy(paused),'experiment_sha256':sha(ROOT/'pipeline/experiments/M206-CGCA.json')}
    running=read(ROOT/'pipeline/running.json')
    result['other_running_mappings']=sorted((server,str(gpu),eid) for server,gpus in running.items() for gpu,eid in gpus.items() if eid!=EXP)
    return result
'''

ff=(OLD/'fast_forward_tested_bcr.py').read_text(encoding='utf-8').replace('BCR','BFC').replace('bcr','bfc').replace('Primary is not original BTC00e','Primary is not original common11a').replace('exact single child of00e','exact single child of11a')
ff=ff.replace("    rows = common.protected()", "    rows = common.protected()\n    lifecycle_before = common.protected_lifecycle()\n    ledger_names=('queue.json','running.json','research_work.json','experiments/M211-BTC.json','experiments/M212-BCR.json','experiments/M206-CGCA.json','admissions/M211-BTC.json','admissions/M212-BCR.json')\n    ledger_hashes={name:common.sha(common.ROOT/'pipeline'/name) for name in ledger_names}")
ff=ff.replace("    result = {", "    require(common.protected_lifecycle()==lifecycle_before and all(common.sha(common.ROOT/'pipeline'/name)==digest for name,digest in ledger_hashes.items()),'Protected lifecycle or ledgers changed during local ff; no rollback or retry')\n    result = {")
ff=ff.replace("'reset_clean_stash_force_used': False", "'reset_clean_stash_force_used': False, 'protected_lifecycle_and_ledger_bytes_unchanged': True")
for name,text in (('promotion_common.py',common),('fast_forward_tested_bfc.py',ff)):
    ast.parse(text)
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
print('Disabled source/common templates authored locally; no reviews assumed, no Git/shared/remote actions')
