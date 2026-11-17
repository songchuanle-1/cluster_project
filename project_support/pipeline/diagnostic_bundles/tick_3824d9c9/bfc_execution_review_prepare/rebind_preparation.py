"""Local current-tick copy and bounded refusal checks; no actual result review."""
from pathlib import Path
from datetime import datetime,timezone
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import sys

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
OLD=PROJECT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_execution_review_prepare'
OLD_PREP_SHA='c42f8c196585bfcfb12314dd91ab0dc24981076a00edb8609433bd6e64da93d4'
TOKEN='3824d9c96f6343e09d60362b4a00495b'
OWNER_KEYS=('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def ref(path):
    return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}


def save(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


assert sha(OLD/'preparation.json')==OLD_PREP_SHA
old_prep=json.loads((OLD/'preparation.json').read_text(encoding='utf-8'))
owner=json.loads((PROJECT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
owner={key:owner[key] for key in OWNER_KEYS}
assert owner['token']==TOKEN and datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
assert owner['context_sha256']=='eeb5e674ac8ae4fb2c3d5142b0d3cfaa39a96e426127b39702ad55b02b839fe3'
assert owner['pending_sha256']=='fe7d536849cc9c0d1dc633d37f1ec8bfb47c977d30ded4d77d2fc35a0835571c'
changed=[]
for name in ('review_bfc.py','admit_bfc_draft.py','bfc_operation_history.py','evidence_contract.json'):
    assert sha(OLD/name)==old_prep['prepared_file_hashes'][name]
    old=(OLD/name).read_bytes();new=old
    if name=='admit_bfc_draft.py':
        assert old.count(b"TICK = ROOT/'pipeline/diagnostic_bundles/tick_64ac844e'")==1
        new=old.replace(b"TICK = ROOT/'pipeline/diagnostic_bundles/tick_64ac844e'",b"TICK = ROOT/'pipeline/diagnostic_bundles/tick_3824d9c9'",1)
        changed.append({'file':name,'scope':'Module-level TICK path constant only','before':"pipeline/diagnostic_bundles/tick_64ac844e",'after':"pipeline/diagnostic_bundles/tick_3824d9c9"})
    with (HERE/name).open('xb') as stream:stream.write(new)

checks={}
checks['reviewer_history_contract_byte_equal_original']=all((HERE/n).read_bytes()==(OLD/n).read_bytes() for n in ('review_bfc.py','bfc_operation_history.py','evidence_contract.json'))
checks['admission_exact_single_TICK_literal_transform']=(HERE/'admit_bfc_draft.py').read_bytes()==(OLD/'admit_bfc_draft.py').read_bytes().replace(b"TICK = ROOT/'pipeline/diagnostic_bundles/tick_64ac844e'",b"TICK = ROOT/'pipeline/diagnostic_bundles/tick_3824d9c9'",1)
oldtree=ast.parse((OLD/'admit_bfc_draft.py').read_text(encoding='utf-8'));newtree=ast.parse((HERE/'admit_bfc_draft.py').read_text(encoding='utf-8'))
function_map=lambda t:{node.name:ast.dump(node,include_attributes=False) for node in t.body if isinstance(node,ast.FunctionDef)}
checks['every_admission_function_whole_AST_unchanged']=function_map(oldtree)==function_map(newtree)
for file in ('review_bfc.py','admit_bfc_draft.py','bfc_operation_history.py'):
    text=(HERE/file).read_text(encoding='utf-8');ast.parse(text);compile(text,str(HERE/file),'exec')
checks['three_source_AST_and_inmemory_compile_without_native_import']=True

actions=[]
def audit(event,args):
    if event=='subprocess.Popen' or event.startswith('socket.'):
        actions.append(event);raise AssertionError('No local subprocess or network action allowed in bounded rebinding checks')
sys.addaudithook(audit)
def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
r=load('review_bfc');a=load('admit_bfc_draft');h=load('bfc_operation_history')
checks['current_default_execution_directory']=a.TICK==HERE.parent and a.EXECUTION==HERE.parent/'bfc_execution'
checks['no_prebound_outcome_report_or_token']=a.REVIEW is None and a.REVIEW_SHA is None and a.REVIEWER_SHA is None and a.TOKEN is None
checks['source48fc_identity_and_protocol_unchanged']=r.COMMIT==a.COMMIT==h.COMMIT=='48fc302c3c02ffef0b241be3593c386b6b65a72e' and r.CID==a.CID==h.CID=='hierarchy-parent-butterfly-token-composition' and r.GOAL==a.GOAL=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
checks['selectedGPU0or1_UUID_map_preserved']=r.UUIDS==a.UUIDS==h.UUIDS=={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
stdout=io.StringIO();argv=sys.argv
try:
    sys.argv=['review_bfc.py','--project',str(HERE/'absent_inputs_project'),'--execution-dir',str(HERE/'absent_inputs_project/bfc_execution')]
    with contextlib.redirect_stdout(stdout):code=r.main()
finally:sys.argv=argv
refused=json.loads(stdout.getvalue())
checks['actual_default_missing_input_review_refusal_without_writes']=code==2 and refused['review_status']=='REFUSED_MISSING_OR_INVALID_ACTUAL_EVIDENCE' and refused['standard_PASS_receipt_queue_written'] is False
old_owner=a.current_owner;a.current_owner=lambda:copy.deepcopy(owner)
try:
    try:a.actual_checks(HERE/'no_independent_actual_report.json','0'*64)
    except ValueError as error:missing_reason=str(error)
    else:raise AssertionError('Admission accepted absent actual review')
finally:a.current_owner=old_owner
checks['admission_missing_real_report_hash_refuses_before_source_or_shared_actions']='draft cannot assume results' in missing_reason
checks['no_torch_import_or_process_network_action']='torch' not in sys.modules and not actions
checks['protected_tasks_may_be_completed_or_archived_unchanged_function_reused']='len(rows)<=1' in ast.unparse(next(x for x in newtree.body if isinstance(x,ast.FunctionDef) and x.name=='protected_snapshot')).replace(' ','') and "== 'running'" not in ast.unparse(next(x for x in newtree.body if isinstance(x,ast.FunctionDef) and x.name=='protected_snapshot'))
assert all(checks.values()),checks
native=PROJECT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare/native/preparation.json'
assert sha(native)=='0c50b957129c44367d63ade6984d997fa1e0a22c59469a2355542095d0f25cf5'
native_json=json.loads(native.read_text(encoding='utf-8'));assert native_json['code_commit']==native_json['source_commit']==r.COMMIT
checks['known_actual_operational_native0c50_small_reference']=True
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'CURRENT_TICK_PATH_REBINDING_AND_DEFAULT_REFUSALS_ONLY',
    'source_preparation':ref(OLD/'preparation.json'),'changed_module_literals':changed,'checks':checks,'check_count':len(checks),
    'actual_default_missing_input_refusal':refused,'actual_admission_missing_evidence_reason':missing_reason,
    'fresh_preparation_owner_provenance':owner,'provenance_is_not_active_binding_or_lease':True,
    'functions_resource_science_protocol_body_changes':False,'new_actual_results':'NONE','native':'NOT_RUN','resources':'NOT_RUN',
    'prior42_negative_and61_operational_suites':'NOT_RERUN; original frozen evidence retained and referenced',
    'SSH_GPU_adapter_or_Git_actions':'NOT_RUN','standard_PASS_receipt_queue_written':False,
    'subprocess_or_network_attempts':actions,'core_hashes':{n:sha(HERE/n) for n in ('review_bfc.py','admit_bfc_draft.py','bfc_operation_history.py')}}
save('rebinding_validation.json',result)
readme='''# Current-tick BFC checker draft rebinding

Only the admission module-level default TICK constant changes from tick64ac844e to tick3824d9c9. The reviewer, operation-history helper and evidence contract are byte-identical to frozen c42f8c196585bfcfb12314dd91ab0dc24981076a00edb8609433bd6e64da93d4; all admission function ASTs and scientific/resource/protected-task behavior remain identical. TOKEN, local-review path and result/checker SHAs remain unbound until actual evidence. Current six-owner fields in this preparation are historical provenance, never an active binding or lease.

The complete protocol, command arguments, limitations, protected-task semantics and partial-write reconciliation boundary remain documented in the original frozen tick_64ac844e/bfc_execution_review_prepare/README.md. This copy does not include or relabel old test evidence as a new suite. The original42 negative fixtures and61 operational tests were not rerun. Only bounded local source/AST/default-refusal checks were performed, without Torch, subprocess, network, SSH, GPU, adapter or Git actions.

Source48fc, original YAML/seed/data/loss/backward/four aggregate W quadrant protocol and per-call zero legality are unchanged. The current operational native0c50 is a static actual reference; no fresh device availability or execution authority is inferred. Dynamic current-candidate external path/SHA anchors still gate actual review. Four raw arms are absent here, and no actual report, standard PASS, receipt or queue is prepared. BTC/BCR may already be canonically completed/archived when an idle card becomes available; their present rows, experiments, immutable receipts and running registry are preserved along with M206 pause. No forever-two-running condition exists.

Promotion/dispatcher preparation remains conditional on root first confirming a real idle card; no such operation is included in this bounded rebinding package. Future actual evidence must use the actual owning foreground token/context/pending/original deadline and exact selected0or1 binding. Defaults refuse missing inputs and perform no writes to shared state. Only an independently reviewed explicit root --execute-root may later create standard/receipt/waiting artifacts after actual checks; this helper never dispatches or launches.
'''
with (HERE/'README.md').open('x',encoding='utf-8',newline='\n') as stream:stream.write(readme)
files={p.name:sha(p) for p in HERE.iterdir() if p.is_file()}
prep={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'FROZEN_CURRENT_TICK_REBINDING_DRAFT_NO_ACTUAL_RESULTS',
    'candidate_id':r.CID,'experiment_id':r.EID,'code_commit':r.COMMIT,'goal_sha256':r.GOAL,'prepared_under_parent':owner,
    'original_frozen_checker_preparation':ref(OLD/'preparation.json'),'original_peer_review':ref(PROJECT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_checker_admission_draft_review.json'),
    'actual_known_operational_native_preparation':ref(native),'original_protocol_documentation':ref(OLD/'README.md'),
    'prepared_file_hashes':files,'rebinding_validation':ref(HERE/'rebinding_validation.json'),
    'changed_module_literals':changed,'all_function_bodies_and_scientific_resource_protocols_unchanged':True,
    'native':'NOT_RUN','resources':'NOT_RUN','actual_four_result_review':'PENDING_REAL_FOUR_RESULTS','active_binding_manifest_lease_created':False,
    'SSH_GPU_adapter_Git_or_shared_actions':'NOT_RUN','standard_PASS_receipt_queue_written':False}
save('preparation.json',prep)
print(json.dumps({'preparation':ref(HERE/'preparation.json'),'core_hashes':result['core_hashes'],'validation':ref(HERE/'rebinding_validation.json'),'checks':len(checks),'changed_module_literals':changed}))
