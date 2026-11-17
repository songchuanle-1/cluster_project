"""Targeted author-local V2 assignment/lifecycle guards; no action callbacks."""
from pathlib import Path
from datetime import datetime,timezone
import ast
import copy
import hashlib
import importlib.util
import json
import sys

HERE=Path(__file__).resolve().parent
V1=HERE.parent/'bfc_promotion_prepare'
sys.path.insert(0,str(HERE))
attempts=[]
def audit(event,args):
    if event=='subprocess.Popen' or event.startswith('socket.'):
        attempts.append(event);raise AssertionError('No subprocess/network/Git/SSH actions permitted')
sys.addaudithook(audit)
import promotion_common as common
checks={};refusals=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def refuse(name,fn):
    try:fn()
    except RuntimeError as error:refusals.append({'case':name,'reason':str(error)[:200]})
    else:raise AssertionError('Malformed assignment accepted: '+name)
for value in (False,True,None,0.,1.,'00','01','False','unknown',2,-1,{},[]):
    refuse('physical_assignment_'+repr(value),lambda value=value:common.physical_gpu(value))
assert [common.physical_gpu(x) for x in (0,1,'0','1')]==[0,1,0,1]
checks['only_exact_physical_integer_or_literal_string0or1_bool_rejected']=True
specs={'M211-BTC':('00e2b18c6b8d568a64edb496e6979d766440883c','93756329046cf30357c258848d6b3287c25b4b0c96ef69b0ffd5f3b8710f2a36',2784474,0),
       'M212-BCR':('11a811618179ab1ddc0cee299194667413b7fdb9','b8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac',1215422,1)}
read_original,sha_original=common.read,common.sha
def fixture(active=('M211-BTC','M212-BCR'),terminal='done_earlystop'):
    rows=[{'id':'M206-CGCA','status':'waiting','dispatch_hold':'fixture user pause','resume_authorized':False}]
    exps={}
    for eid,(commit,receipt,pid,gpu) in specs.items():
        exps[eid]={'id':eid,'code_commit':commit,'status':'running' if eid in active else terminal}
        if eid in active:rows.append({'id':eid,'status':'running','code_commit':commit,'admission_receipt':'pipeline/admissions/'+eid+'.json','pid':pid,'gpu':str(gpu),'launch_verified':True,'note':'before'})
    return {'queue':{'gpu_queues':{'server-4':rows}},'experiments':exps,'running':{'server-6':{},'server-4':{str(specs[eid][3]):eid for eid in active}}}
def bind(data):
    def read(path):
        path=Path(path)
        if path.name=='running.json':return data['running']
        if path.parent.name=='experiments':return data['experiments'][path.stem]
        raise AssertionError('Unexpected fixture access '+str(path))
    common.read=read
    common.sha=lambda path:specs[Path(path).stem][1] if Path(path).parent.name=='admissions' else 'synthetic-opaque-fingerprint-only'
    return lambda:common.protected_lifecycle(data['queue'])
for active in ((),('M211-BTC',),('M212-BCR',),('M211-BTC','M212-BCR')):
    for terminal in ('done_complete','done_earlystop'):
        data=fixture(active,terminal);run=bind(data);value=run()
        if active:
            row=next(t for t in data['queue']['gpu_queues']['server-4'] if t['id']==active[0]);row['note']='after'
            assert value[active[0]]['queue_rows'][0]['note']=='before'
        else:assert value['M211-BTC']['queue_rows']==value['M212-BCR']['queue_rows']==[]
checks['all0_1_2_original_active_and_explicit_terminal_absent_row_cases']=True
checks['deepcopy_protected_rows_remains_nonaliased']=True

def btc(data):return next(t for t in data['queue']['gpu_queues']['server-4'] if t['id']=='M211-BTC')
mutations={
    'wrong_old_gpu':lambda d:btc(d).update(gpu='1'),
    'bool_old_gpu':lambda d:btc(d).update(gpu=False),
    'unknown_old_gpu':lambda d:btc(d).update(gpu='unknown'),
    'wrong_old_source':lambda d:btc(d).update(code_commit=specs['M212-BCR'][0]),
    'wrong_old_receipt_path':lambda d:btc(d).update(admission_receipt='pipeline/admissions/M212-BCR.json'),
    'wrong_old_pid':lambda d:btc(d).update(pid=12),
    'bool_old_pid':lambda d:btc(d).update(pid=True),
    'launch_not_verified':lambda d:btc(d).update(launch_verified=False),
    'old_claim_uncertain':lambda d:btc(d).update(status='claiming'),
    'old_waiting_unexpected':lambda d:btc(d).update(status='waiting'),
    'active_row_terminal_experiment':lambda d:d['experiments']['M211-BTC'].update(status='done_earlystop'),
    'active_running_map_missing':lambda d:d['running']['server-4'].pop('0'),
    'running_map_wrong_cards':lambda d:d['running'].update({'server-4':{'0':'M212-BCR','1':'M211-BTC'}}),
    'unknown_running_experiment':lambda d:d['running']['server-4'].update({'0':'UNKNOWN'}),
    'malformed_running_value_bool':lambda d:d['running']['server-4'].update({'0':False}),
    'malformed_running_key_bool':lambda d:d['running'].update({'server-4':{False:'M211-BTC','1':'M212-BCR'}}),
    'malformed_running_key_unknown':lambda d:d['running'].update({'server-4':{'unknown':'M211-BTC','1':'M212-BCR'}}),
    'duplicate_experiment_reserved_twice':lambda d:d['running'].update({'server-4':{'0':'M211-BTC','1':'M211-BTC'}}),
    'nonapproved_nonempty_server':lambda d:d['running'].update({'server-6':{'0':'M211-BTC'}}),
    'paused_M206_registered':lambda d:d['running']['server-4'].update({'0':'M206-CGCA'}),
    'paused_M206_resume_true':lambda d:d['queue']['gpu_queues']['server-4'][0].update(resume_authorized=True),
}
for label,change in mutations.items():
    data=fixture();change(data);refuse(label,bind(data))
for status in ('done_x','done','completed','archived','crashed','running','waiting'):
    data=fixture((),status);refuse('missing_row_not_explicit_canonical_terminal_'+status,bind(data))
data=fixture((),'done_earlystop');data['running']['server-4']={'0':'M211-BTC'};refuse('terminal_old_id_still_reserved',bind(data))
data=fixture(('M212-BCR',),'done_complete')
data['queue']['gpu_queues']['server-4'].append({'id':'M211-BTC','status':'done_complete','code_commit':specs['M211-BTC'][0],'admission_receipt':'pipeline/admissions/M211-BTC.json','gpu':'0'})
bind(data)();checks['explicit_terminal_present_row_without_reservation_accepted']=True
common.read,common.sha=read_original,sha_original

tree1=ast.parse((V1/'promotion_common.py').read_text(encoding='utf-8'));tree2=ast.parse((HERE/'promotion_common.py').read_text(encoding='utf-8'))
functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
f1,f2=functions(tree1),functions(tree2)
assert set(f2)-set(f1)=={'physical_gpu','running_assignments'}
assert [name for name in f1 if f1[name]!=f2[name]]==['protected_lifecycle']
checks['common_only_two_assignment_helpers_and_lifecycle_body_changed']=True
assert (V1/'fast_forward_tested_bfc.py').read_bytes()==(HERE/'fast_forward_tested_bfc.py').read_bytes()
checks['source_ff_body_and_bytes_exact_V1']=True
dt1=ast.parse((V1/'dispatch_bfc.py').read_text(encoding='utf-8'));dt2=ast.parse((HERE/'dispatch_bfc.py').read_text(encoding='utf-8'))
d1,d2=functions(dt1),functions(dt2);assert set(d1)==set(d2) and [name for name in d1 if d1[name]!=d2[name]]==['main']
checks['dispatch_transport_and_lockholder_whole_AST_equal_V1_only_main_guards_changed']=True
main=next(n for n in dt2.body if isinstance(n,ast.FunctionDef) and n.name=='main')
busy_line=next(n.lineno for n in ast.walk(main) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='busy' for t in n.targets))
lifecycle_line=next(n.lineno for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='protected_lifecycle')
registry_line=next(n.lineno for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='running_assignments')
assert lifecycle_line<busy_line and registry_line<busy_line
body=ast.unparse(main);assert "str(t['gpu'])" not in body and "str(task['gpu'])" not in body
checks['strict_assignment_and_lifecycle_validation_precedes_busy_GPU_construction']=True
calls=[n for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_process_queue'];assert len(calls)==1 and ast.unparse(calls[0].args[6])=='{str(SELECTED_GPU)}'
checks['canonical_one_call_only_selected_allow_set_preserved']=True
assert common.DRAFT_EXECUTION_ENABLED is False and all(getattr(common,key) is None for key in ('SEMANTIC_REVIEW_PATH','SEMANTIC_REVIEW_SHA','INDEPENDENT_REVIEW_PATH','INDEPENDENT_REVIEW_SHA'))
refuse('V2_explicit_execute_still_disabled',lambda:common.execution_enabled(True))
checks['V2_stays_disabled_four_actual_review_refs_none']=True
for name in ('promotion_common.py','fast_forward_tested_bfc.py','dispatch_bfc.py'):compile((HERE/name).read_text(encoding='utf-8'),str(HERE/name),'exec')
checks['three_sources_compile_no_Torch_or_action_attempt']=not attempts and 'torch' not in sys.modules
assert all(checks.values()),checks
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'AUTHOR_LOCAL_V2_STRICT_ASSIGNMENT_AND_LIFECYCLE_FIXTURES_ONLY','checks':checks,'logical_checks':len(checks),'negative_fixture_count':len(refusals),'negative_fixtures':refusals,'source_hashes':{n:sha(HERE/n) for n in ('promotion_common.py','fast_forward_tested_bfc.py','dispatch_bfc.py')},'unchanged_V1_transport_proof':{'path':'pipeline/diagnostic_bundles/tick_3824d9c9/bfc_promotion_prepare/disabled_validation.json','sha256':sha(V1/'disabled_validation.json')},'scope':'Only actual guard functions on in-memory lifecycle/assignment fixtures and AST comparisons. No registered/current process claims, no actual-source or remote validation, no old16/12 or42/61 suites rerun. Not scientific/native/resource PASS or independent review.','native_resources_ff_admission_dispatch':'NOT_RUN','SSH_GPU_Git_shared_actions':'NOT_RUN','subprocess_network_attempts':attempts}
with (HERE/'guard_validation.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'logical_checks':len(checks),'negative_fixture_count':len(refusals),'source_hashes':result['source_hashes'],'validation_sha256':sha(HERE/'guard_validation.json'),'actual_operations':'NOT_RUN'}))
