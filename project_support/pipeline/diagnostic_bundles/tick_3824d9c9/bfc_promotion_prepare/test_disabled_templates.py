"""Author-local defaults/refusals and command-construction stubs, never actions."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import shlex
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
actions=[]
def audit(event,args):
    if event=='subprocess.Popen' or event.startswith('socket.'):
        actions.append(event);raise AssertionError('Author-local checks forbid all subprocess and network actions')
sys.addaudithook(audit)
import promotion_common as common
def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
ff=load('fast_forward_tested_bfc');dispatch=load('dispatch_bfc')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={};refusals=[]
def refuse(label,fn):
    try:fn()
    except RuntimeError as error:refusals.append({'case':label,'reason':str(error)[:220]})
    else:raise AssertionError('Unsafe fixture accepted: '+label)
for module in (ff,dispatch):
    argv=sys.argv;sys.argv=['draft']
    try:
        output=io.StringIO()
        with contextlib.redirect_stdout(output):module.main()
        assert 'DRAFT_DISABLED' in output.getvalue()
    finally:sys.argv=argv
    argv=sys.argv;sys.argv=['draft','--execute-root']
    try:refuse(module.__name__+'_execute_root_still_disabled',module.main)
    finally:sys.argv=argv
checks['both_default_entries_return_without_owner_source_or_canonical_actions']=True
checks['explicit_flag_alone_cannot_enable_draft']=common.DRAFT_EXECUTION_ENABLED is False
refuse('reviewed_four_raw_disabled_before_any_input_access',common.reviewed_four_raw)
common.DRAFT_EXECUTION_ENABLED=True
try:refuse('enabled_flag_but_missing_actual_review_refs',lambda:common.execution_enabled(True))
finally:common.DRAFT_EXECUTION_ENABLED=False
checks['all_four_actual_review_path_hash_slots_unbound']=all(getattr(common,key) is None for key in ('SEMANTIC_REVIEW_PATH','SEMANTIC_REVIEW_SHA','INDEPENDENT_REVIEW_PATH','INDEPENDENT_REVIEW_SHA'))

# Exercise actual lifecycle helper on in-memory states. These are fixtures,
# not project/queue evidence and not claims about existing processes.
read_original,sha_original=common.read,common.sha
receipt_shas={'M211-BTC.json':'93756329046cf30357c258848d6b3287c25b4b0c96ef69b0ffd5f3b8710f2a36','M212-BCR.json':'b8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac'}
specs={'M211-BTC':('00e2b18c6b8d568a64edb496e6979d766440883c',2784474,'0'),'M212-BCR':('11a811618179ab1ddc0cee299194667413b7fdb9',1215422,'1')}
for active_names in ((),('M211-BTC',),('M212-BCR',),('M211-BTC','M212-BCR')):
    rows=[{'id':'M206-CGCA','status':'waiting','dispatch_hold':'synthetic user pause','resume_authorized':False}]
    for eid in active_names:
        commit,pid,gpu=specs[eid];rows.append({'id':eid,'status':'running','code_commit':commit,'pid':pid,'gpu':gpu,'launch_verified':True,'note':'before'})
    queue={'gpu_queues':{'server-4':rows}}
    experiments={eid:{'id':eid,'code_commit':values[0],'status':'running' if eid in active_names else 'done_earlystop'} for eid,values in specs.items()}
    def fixture_read(path):
        path=Path(path)
        if path.name=='running.json':return {'server-4':{specs[eid][2]:eid for eid in active_names}}
        if path.parent.name=='experiments':return experiments[path.stem]
        raise AssertionError('Unexpected fixture read '+str(path))
    common.read=fixture_read
    common.sha=lambda path:receipt_shas[Path(path).name] if Path(path).parent.name=='admissions' else 'synthetic-file-fingerprint-only'
    before=common.protected_lifecycle(queue)
    if active_names:
        target=next(t for t in rows if t['id']==active_names[0]);target['note']='after'
        assert before[active_names[0]]['queue_rows'][0]['note']=='before'
        assert common.protected_lifecycle(queue)!=before
    if not active_names:
        assert before['M211-BTC']['queue_rows']==before['M212-BCR']['queue_rows']==[]
    paused=rows[0];paused['resume_authorized']=True
    refuse('resource_grant_cannot_resume_M206_'+str(len(active_names)),lambda:common.protected_lifecycle(queue))
common.read,common.sha=read_original,sha_original
checks['actual_lifecycle_function_all0_1_2_active_cases_and_terminal_absent_rows']=True
checks['protected_rows_deepcopied_not_aliased_to_mutable_queue']=True

# Actual strict_ssh body is invoked only with action functions replaced by
# in-memory capture stubs. No SSH/Popen/socket command is ever executed.
enabled_original,owner_original=common.execution_enabled,common.owner_guard
run_original,save_original=dispatch.subprocess.run,dispatch.save
common.execution_enabled=lambda value:None
common.owner_guard=lambda:dict(common.EXPECTED_OWNER)
captured=[];saved=[];rendered=[]
def capture(args,**kwargs):
    captured.append({'args':args,'kwargs':kwargs});return SimpleNamespace(returncode=0,stdout='synthetic-construction-only',stderr='')
dispatch.subprocess.run=capture
dispatch.save=lambda path,value:saved.append(str(path))
try:
    inventory='nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null'
    for gpu in (0,1):
        dispatch.SELECTED_GPU=gpu;dispatch.CALLS.clear()
        dispatch.strict_ssh('192.168.1.115','songcl',inventory)
        query=captured[-1]['args'];assert 'BatchMode=yes' in query and 'StrictHostKeyChecking=yes' in query and 'ConnectTimeout=8' in query
        assert 'nvidia-smi -i '+str(gpu)+' ' in query[-1]
        toy_launch="proc=subprocess.Popen(['python','tools/train.py','synthetic_cfg','--gpu_ids',"+repr(str(gpu))+",'--num_gpus','1'])"
        dispatch.strict_ssh('192.168.1.115','songcl',toy_launch)
        args=captured[-1]['args'];words=shlex.split(args[-1]);guard=words[words.index('-c')+1];tree=ast.parse(guard);compile(guard,'captured_remote_guard_not_executed','exec')
        assignments={target.id:node.value.value for node in tree.body if isinstance(node,ast.Assign) for target in node.targets if isinstance(target,ast.Name) and isinstance(node.value,ast.Constant)}
        assert assignments['gpu']==str(gpu) and assignments['uuid']==common.UUIDS[gpu]
        assert "('training', 'diagnostic', 'exclusive')" in ast.unparse(tree)
        assert "socket.gethostname() == 'dl04-MS-7E06'" in ast.unparse(tree)
        outer=next(node for node in tree.body if isinstance(node,ast.Try));assert outer.finalbody
        assert any(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='close' for node in ast.walk(outer.finalbody[0]))
        # The same try holds all locks through the wrapped original command's return.
        assert "subprocess.run(['/bin/bash', '-lc'," in ast.unparse(outer)
        rendered.append({'selected_physical_gpu':gpu,'uuid':assignments['uuid'],'rendered_guard_sha256':hashlib.sha256(guard.encode()).hexdigest(),'scope':'Construction/AST only; guard was not executed'})
        refuse('second_native_launch_same_invocation_gpu'+str(gpu),lambda:dispatch.strict_ssh('192.168.1.115','songcl',toy_launch))
        refuse('unknown_nvidia_query_gpu'+str(gpu),lambda:dispatch.strict_ssh('192.168.1.115','songcl','nvidia-smi --query-compute-apps=pid'))
        refuse('unrecognized_Popen_whitespace_gpu'+str(gpu),lambda:dispatch.strict_ssh('192.168.1.115','songcl',"proc = subprocess.Popen(['tools/train.py'])"))
        refuse('wrong_host_gpu'+str(gpu),lambda:dispatch.strict_ssh('untrusted.invalid','songcl',inventory))
finally:
    common.execution_enabled,common.owner_guard=enabled_original,owner_original
    dispatch.subprocess.run,dispatch.save=run_original,save_original
checks['selected0or1_query_UUID_locks_hostname_keySSH_rendered_with_stubs_only']=len(rendered)==2
checks['three_flocks_cover_idle_checks_through_wrapped_Popen_return']=True
checks['same_invocation_second_launch_and_unrecognized_queries_refused']=True
tree=ast.parse((HERE/'dispatch_bfc.py').read_text(encoding='utf-8'))
calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='_process_queue']
assert len(calls)==1;call=calls[0]
assert ast.unparse(call.args[6])=='{str(SELECTED_GPU)}'
keywords={node.arg:ast.unparse(node.value) for node in call.keywords}
assert keywords['current_tasks']=='len(active)' and keywords['max_tasks_total']=='2' and keywords['max_tasks_per_gpu']=='1'
checks['single_original_canonical_call_selected_card_only_dynamic_active_count']=True
text=(HERE/'fast_forward_tested_bfc.py').read_text(encoding='utf-8')
assert "'merge', '--ff-only', common.TESTED" in text and 'merge.autoStash=false' in text and 'core.hooksPath=' in text
assert "len(diff) == 9" in text and "{'A\\t' + p for p in paths}" in text
checks['ff_only_exact9A_with_index_protected_bytes_no_force_stash_reset']=True
for name in ('promotion_common.py','fast_forward_tested_bfc.py','dispatch_bfc.py'):
    text=(HERE/name).read_text(encoding='utf-8');ast.parse(text);compile(text,str(HERE/name),'exec')
checks['three_templates_compile_without_native_or_canonical_import_execution']=True
checks['no_torch_process_network_Git_or_shared_mutation']='torch' not in sys.modules and not actions
assert all(checks.values()),checks
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'AUTHOR_LOCAL_DISABLED_TEMPLATE_REFUSALS_AND_COMMAND_CONSTRUCTION_ONLY',
    'checks':checks,'logical_checks':len(checks),'negative_fixture_count':len(refusals),'negative_fixtures':refusals,
    'rendered_selected_device_guard_stubs':rendered,'captured_stub_transport_calls':len(captured),'actual_transport_calls':0,
    'source_hashes':{name:sha(HERE/name) for name in ('promotion_common.py','fast_forward_tested_bfc.py','dispatch_bfc.py')},
    'actual_four_BFC_results':'PENDING_REAL_RESULTS','native_resources_source_ff_admission_dispatch':'NOT_RUN',
    'SSH_GPU_Git_shared_actions':'NOT_RUN','subprocess_network_attempts':actions,
    'scope':'Author-local in-memory lifecycle fixtures and actual strict_ssh command construction with replaced action callbacks. No remote guard, canonical queue dispatcher, Git, training/model, real sources or scientific results executed. Not independent review or hardware availability.'}
with (HERE/'disabled_validation.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'status':result['status'],'logical_checks':len(checks),'negative_fixture_count':len(refusals),'source_hashes':result['source_hashes'],'validation_sha256':sha(HERE/'disabled_validation.json')}))
