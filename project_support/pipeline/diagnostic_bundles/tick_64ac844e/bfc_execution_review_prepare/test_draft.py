"""Author-local offline refusal fixtures, never an actual native result review."""
from pathlib import Path
from datetime import datetime,timezone
import ast
import builtins
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import sys

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
ORIGIN=PROJECT/'pipeline/diagnostic_bundles/tick_ab7e46d4/bfc_native_prepare'
checks={};refusals=[];actions=[]


def audit(event,args):
    if event=='subprocess.Popen' or event.startswith('socket.'):
        actions.append(event);raise AssertionError('No subprocess/network permitted in author-local fixtures')


sys.addaudithook(audit)
original_import=builtins.__import__
def guarded_import(name,*args,**kwargs):
    assert not name.startswith(('torch','framework','gorilla')),'Native import forbidden in offline checker fixtures'
    return original_import(name,*args,**kwargs)
builtins.__import__=guarded_import


def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


r=load('review_bfc');a=load('admit_bfc_draft');h=load('bfc_operation_history')
r.FROZEN=ORIGIN.relative_to(PROJECT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ORIGIN/'worker.py')==r.WORKER_SHA
build,describe=r.topology_functions()


def refuse(label,fn):
    try:fn()
    except (ValueError,KeyError,TypeError,OSError,StopIteration) as error:
        refusals.append({'case':label,'reason':str(error)[:220]})
    else:raise AssertionError('Bad fixture accepted: '+label)


def tensor(shape,magnitude=1.0):
    return {'shape':list(shape),'dtype':'torch.float32','finite':True,'nonfinite_count':0,'abs_max':magnitude}


def fixture_record():
    counts=[1,0,2,1,0,3,1,1];parents=[0,0,0,0,0,0,0,1]
    centers=[[float(i//2),0.,0.] for i in range(8)];support=[n>0 for n in counts]
    plan=build(centers,parents,support,64);groups,seq=describe(plan)
    for g in groups:g['batch']=0
    for s in seq:s['batch']=0
    groups=json.loads(json.dumps(groups));seq=json.loads(json.dumps(seq));calls=[]
    for index,step in enumerate(seq):
        rows=len(step['left_ids']) if step['kind']=='round' else len(step['original_ids'])
        call={**step,'forward':1,'call_index':index,'actual_both_inputs_from_same_old_state':True,
            'no_fake_padded_pair_participant':True,'activation_original_calls':1,
            'input':tensor([rows,512]),'linear_output':tensor([rows,512]),'output':tensor([rows,512]),
            'left_input':tensor([rows,256]),'right_input':tensor([rows,256],0. if step['kind']=='singleton' else 1.),
            'left_output':tensor([rows,256]),'right_output':tensor([rows,256]),
            'native_input_gradients':[tensor([rows,512],0.)],
            'native_linear_output_gradients':[tensor([rows,512],0.)],
            'native_output_gradients':[tensor([rows,512],0.)],
            'native_output_half_gradients':[{'left':tensor([rows,256],0.),'right':tensor([rows,256],0.)}]}
        call.update({key:'a'*64 for key in ('input_sha256','linear_output_sha256','output_sha256','old_state_sha256','writeback_reference_sha256')})
        if step['kind']=='round':call['unpaired_carry_reference_exact']=True
        else:call['singleton_private_zero_right_input']=True
        calls.append(call)
    return {'forward':1,'input':tensor([1,10,256]),'output':tensor([1,10,256]),
        'original_middle_norm_calls':1,'original_butterfly_forward_calls':1,'returned_original_bank_shape':True,
        'original_ID_inverse_scatter_observed':True,'unsupported_and_batch_padding_update_zero':True,
        'final_writeback_from_actual_outputs_reference_exact':True,'actual_output_requires_grad':True,
        'self_exclusive_claim':False,'native_input_gradients':[tensor([1,10,256])],'native_output_gradients':[tensor([1,10,256])],
        'batches':[{'batch':0,'real_point_counts':counts,'middle_prefix':8,'padded_width':10,'centers':centers,'parent_ids':parents,
            'true_supported_original_ids':[i for i,n in enumerate(counts) if n>0],
            'unsupported_internal_ids':[i for i,n in enumerate(counts) if n==0],
            'batch_padding_rows':2,'support_formula':'bincount(ids1[ids0],minlength=ids2.numel())>0'}],
        'groups':groups,'actual_builder_calls':1,'mix_calls':calls,
        'actual_n_ge3_supported_parent_groups':1,'actual_nonpower2_supported_parent_groups':1,'actual_multistage_supported_parent_groups':1,
        'actual_round_mix_calls':sum(c['kind']=='round' for c in calls),'actual_singleton_mix_calls':1,
        'actual_supported_singleton_groups':1,'actual_unsupported_internal_rows':2,'actual_padding_rows':2,
        'offdiagonal_dependency_probe':'NOT_IMPLEMENTED_NOT_MEASURED'}


record=fixture_record();r.butterfly_record(record)
checks['synthetic_component_fixture_all_individual_call_and_half_zero_gradients_accepted']=True
mutations={
    'same_old_stage_false':lambda x:x['mix_calls'][0].update(actual_both_inputs_from_same_old_state=False),
    'fake_pair_participant':lambda x:x['mix_calls'][0].update(no_fake_padded_pair_participant=False),
    'carry_not_exact':lambda x:x['mix_calls'][0].update(unpaired_carry_reference_exact=False),
    'extra_activation':lambda x:x['mix_calls'][0].update(activation_original_calls=2),
    'stage_order_changed':lambda x:x['mix_calls'][0].update(round_index=99),
    'half_gradient_missing':lambda x:x['mix_calls'][0].update(native_output_half_gradients=[]),
    'half_nonfinite':lambda x:x['mix_calls'][0]['native_output_half_gradients'][0]['left'].update(finite=False,nonfinite_count=1),
    'pair_wrong_shape':lambda x:x['mix_calls'][0]['input'].update(shape=[1,256]),
    'private_boundary_nonzero':lambda x:x['mix_calls'][-1]['right_input'].update(abs_max=1.),
    'inverse_not_observed':lambda x:x.update(original_ID_inverse_scatter_observed=False),
    'full_writeback_not_observed':lambda x:x.update(final_writeback_from_actual_outputs_reference_exact=False),
    'autograd_path_absent':lambda x:x.update(actual_output_requires_grad=False),
    'false_self_exclusive':lambda x:x.update(self_exclusive_claim=True),
    'n3_coverage_missing':lambda x:x.update(actual_n_ge3_supported_parent_groups=0),
    'nonpower_coverage_missing':lambda x:x.update(actual_nonpower2_supported_parent_groups=0),
    'multistage_coverage_missing':lambda x:x.update(actual_multistage_supported_parent_groups=0),
    'true_support_mismatch':lambda x:x['batches'][0].update(true_supported_original_ids=[0]),
    'wrong_group_order':lambda x:x['groups'][0]['order'].reverse(),
    'builder_missing':lambda x:x.update(actual_builder_calls=0),
    'middle_norm_repeated':lambda x:x.update(original_middle_norm_calls=2),
    'padding_claim_mismatch':lambda x:x.update(actual_padding_rows=0),
}
for label,mutation in mutations.items():
    changed=copy.deepcopy(record);mutation(changed);refuse(label,lambda:r.butterfly_record(changed))
blocks=['left_output_from_left_input','left_output_from_right_input','right_output_from_left_input','right_output_from_right_input']
step={'native_parameter_block_gradients':{key:tensor([256,256]) for key in blocks},
    'parameter_block_before_step_hash':{key:'a'*64 for key in blocks},'parameter_block_after_step_hash':{key:'b'*64 for key in blocks}}
r.required_weight_blocks({'steps':[step]},True)
checks['synthetic_four_aggregate_quadrants_nonzero_and_actual_slice_updates_required']=True
for key in blocks:
    changed=copy.deepcopy(step);changed['native_parameter_block_gradients'][key]['abs_max']=0.
    refuse('zero_aggregate_'+key,lambda:r.required_weight_blocks({'steps':[changed]},True))
for label,mutation in {
    'missing_quadrant':lambda x:x['native_parameter_block_gradients'].pop(blocks[0]),
    'quadrant_nonfinite':lambda x:x['native_parameter_block_gradients'][blocks[0]].update(finite=False,nonfinite_count=1),
    'weight_decay_only_no_slice_change':lambda x:x['parameter_block_after_step_hash'].update({blocks[0]:'a'*64}),
}.items():
    changed=copy.deepcopy(step);mutation(changed);refuse(label,lambda:r.required_weight_blocks({'steps':[changed]},True))

resource={'batch_size':1,'lang_num_max':1,'warmup':20,'repeat':100,'optimizer_steps':0,'native_loss_forwards':0,
    'native_criterion_backwards':0,'native_predict_calls':121,'measurements_ms':[1.]*100,'median_ms':1.,'p90_ms':1.,
    'input_sha256':'a'*64,'scan_ids':['synthetic-fixture-only'],'ann_ids':[1],'parameters':123,
    'peak_allocated_bytes':1024,'peak_reserved_bytes':2048,'parameter_flags_preserved':True,
    'source_body_executed_without_replacement':True,'validation_accuracy_evaluated_for_selection':False,
    'full_optimizer_training_peak':'UNKNOWN fixture only','profile':{'profiler_file_sha256':r.HANDLERS,'flops':9e9,'flops_g':9.,
        'within10G':True,'unsupported_ops':{'aten::fixture':3},'by_operator':{'linear':9e9},'fvcore_version':'synthetic-fixture-only'}}
r.resources(resource);checks['nonzero_unsupported_is_disclosed_and_not_new_rejection_gate']=True
for label,mutation in {
    'warmup_changed':lambda x:x.update(warmup=1),
    'timings_missing':lambda x:x['measurements_ms'].pop(),
    'timing_nonfinite':lambda x:x['measurements_ms'].__setitem__(0,float('nan')),
    'median_false':lambda x:x.update(median_ms=2.),
    'handler_changed':lambda x:x['profile'].update(profiler_file_sha256={}),
    'budget_flag_false':lambda x:x['profile'].update(within10G=False),
    'unsupported_negative':lambda x:x['profile'].update(unsupported_ops={'aten::fixture':-1}),
    'formal_train_in_resource':lambda x:x.update(optimizer_steps=1),
    'fake_pure_train_memory':lambda x:x.update(full_optimizer_training_peak='MEASURED'),
}.items():
    changed=copy.deepcopy(resource);mutation(changed);refuse(label,lambda:r.resources(changed))

binding={'stage':'synthetic-only','native_manifest_sha256':'a'*64,'owner':{'token':'b'*32},'physical_gpu':0,'gpu_uuid':r.UUIDS[0]}
remote={'stage':binding['stage'],'exists':True,'read_only':True,'native_manifest_sha256':'a'*64,'binding_token':'b'*32,
    'workers':[],'compute_contexts':'','gpu_inventory':'0, '+r.UUIDS[0]+', 41, 0','gpu_identity_matches':True}
h.remote_state(remote,binding)
checks['operation_history_binds_selected_physical0_without_other_GPU_query']=True
for label,mutation in {
    'wrong_gpu_inventory':lambda x:x.update(gpu_inventory='1, '+r.UUIDS[1]+', 41, 0'),
    'workers_remain':lambda x:x.update(workers=[{'pid':1}]),
    'selected_context_busy':lambda x:x.update(compute_contexts='1, 1000'),
    'not_read_only':lambda x:x.update(read_only=False),
}.items():
    changed=copy.deepcopy(remote);mutation(changed);refuse(label,lambda:h.remote_state(changed,binding))

oldresource=ast.parse((HERE.parents[1]/'manual_gpu1_20261025/bcr_execution_review_prepare/review_bcr_v2.py').read_text(encoding='utf-8'))
newresource=ast.parse((HERE/'review_bfc.py').read_text(encoding='utf-8'))
fn=lambda t,n:ast.dump(next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n),include_attributes=False)
checks['resource_validator_whole_AST_equal_original_BCR_V2']=fn(oldresource,'resources')==fn(newresource,'resources')
for file in ('review_bfc.py','admit_bfc_draft.py','bfc_operation_history.py'):
    text=(HERE/file).read_text(encoding='utf-8');tree=ast.parse(text);compile(text,str(HERE/file),'exec')
    need_imports=[x for x in ast.walk(tree) if isinstance(x,(ast.Import,ast.ImportFrom)) and any(k in ast.unparse(x) for k in ('torch','framework','gorilla'))]
    assert not need_imports
checks['three_source_compile_no_native_import']=True
main=next(x for x in ast.parse((HERE/'admit_bfc_draft.py').read_text(encoding='utf-8')).body if isinstance(x,ast.FunctionDef) and x.name=='main')
guard=next(x for x in main.body if isinstance(x,ast.If) and ast.unparse(x.test)=='not args.execute_root')
checks['actual_foreground_mode_explicit_before_root_admission']="mode['mode'] == 'foreground'" in (HERE/'admit_bfc_draft.py').read_text(encoding='utf-8')
checks['default_returns_before_canonical_imports_and_standard_shared_writes']=any(isinstance(x,ast.Return) for x in guard.body) and guard.lineno<next(x.lineno for x in ast.walk(main) if isinstance(x,ast.Import) and any(n.name=='closure' for n in x.names))
a.current_owner=lambda:{'token':'synthetic-only'}
refuse('admission_no_actual_local_review_or_independent_hash',lambda:a.actual_checks(HERE/'does_not_exist.json','a'*64))
stdout=io.StringIO();saved=sys.argv
try:
    sys.argv=['review_bfc.py','--project',str(HERE/'no_actual_project'),'--execution-dir',str(HERE/'no_actual_project/bfc_execution')]
    with contextlib.redirect_stdout(stdout):returncode=r.main()
finally:sys.argv=saved
missing=json.loads(stdout.getvalue());assert returncode==2 and missing['review_status']=='REFUSED_MISSING_OR_INVALID_ACTUAL_EVIDENCE' and missing['standard_PASS_receipt_queue_written'] is False
checks['actual_reader_missing_all_actual_inputs_refuses_no_report_file_written']=True
checks['no_subprocess_socket_or_native_import_attempts']=not actions
assert all(checks.values()),checks
for name in ('actual_four_result_review.json','bfc_native_smoke.json','bfc_resource_comparison.json','bfc_constraints_independence.json'):
    assert not (HERE/name).exists()
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'AUTHOR_LOCAL_OFFLINE_NEGATIVE_AND_STATIC_CHECKS_ONLY',
    'checks':checks,'logical_checks':len(checks),'negative_fixture_count':len(refusals),'negative_fixtures':refusals,
    'source_hashes':{n:sha(HERE/n) for n in ('review_bfc.py','admit_bfc_draft.py','bfc_operation_history.py')},
    'scope':'In-memory deliberately synthetic component observations plus actual pure stdlib production-plan/observer functions. No fake actual four-result reports or native PASS/receipt/queue artifacts were generated. These checks are authored here, not an independent review.',
    'native':'NOT_RUN','resources':'NOT_RUN','actual_four_result_review':'PENDING_REAL_FOUR_RESULTS','SSH_GPU_transport':'NOT_RUN',
    'standard_PASS_receipt_queue_written':False,'subprocess_or_network_attempts':actions}
with (HERE/'draft_validation_final.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'status':result['status'],'logical_checks':len(checks),'negative_fixture_count':len(refusals),'validation_sha256':sha(HERE/'draft_validation_final.json'),'source_hashes':result['source_hashes']}))
