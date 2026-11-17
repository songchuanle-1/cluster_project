"""Stdlib draft/rejection checks, without actual raw results or shared writes."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=Path('D:/project/cluster_project')
review=HERE/'review_bcr.py';admit=HERE/'admit_bcr_draft.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rt=ast.parse(review.read_text(encoding='utf-8'));at=ast.parse(admit.read_text(encoding='utf-8'))
for path in (review,admit):compile(path.read_text(encoding='utf-8'),str(path),'exec')
spec=importlib.util.spec_from_file_location('bcr_draft_only',review);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def refused(label,call):
    try:call()
    except (m.Refused,KeyError,TypeError,ValueError):checks.append({'label':label,'outcome':'REFUSED_AS_EXPECTED'})
    else:raise AssertionError(label)
refused('no_native_optimizer_steps',lambda:m.smoke({'optimizer_steps':0},True))
refused('changed_original_resource_protocol',lambda:m.resources({'batch_size':2,'lang_num_max':1,'warmup':20,'repeat':100}))
refused('foreign_manifest_identity_before_any_payload',lambda:m.review_payloads({}, {'candidate_id':'foreign'}))
refused('nonfinite_gradient_tensor',lambda:m.tensor({'finite':False,'nonfinite_count':1,'shape':[256,256],'dtype':'torch.float32','abs_max':1.},True))
refused('boolean_loss_not_a_finite_numeric_observation',lambda:m.need(m.finite(True),'bool must be rejected'))
blocks=('scan_token','scan_state','readout_own','readout_left','readout_right')
tensor={'shape':[256,256],'dtype':'torch.float32','finite':True,'nonfinite_count':0,'abs_max':1.}
def block_fixture():
    return {'steps':[{'native_parameter_block_gradients':{n:copy.deepcopy(tensor) for n in blocks},'parameter_block_before_step_hash':{n:'a'*64 for n in blocks},'parameter_block_after_step_hash':{n:'b'*64 for n in blocks}}]}
v=block_fixture();v['steps'][0]['native_parameter_block_gradients'].pop('scan_state');refused('missing_state_weight_block',lambda:m.required_weight_blocks(v,True))
v=block_fixture();v['steps'][0]['native_parameter_block_gradients']['scan_state']['abs_max']=0.;refused('weight_decay_update_without_state_loss_gradient',lambda:m.required_weight_blocks(v,True))
v=block_fixture();v['steps'][0]['parameter_block_after_step_hash']['readout_left']='a'*64;refused('readout_left_weight_block_not_updated',lambda:m.required_weight_blocks(v,True))
v=block_fixture();v['steps'][0]['native_parameter_block_gradients']['readout_right']['shape']=[256,512];refused('wrong_actual_weight_block_slice_dimensions',lambda:m.required_weight_blocks(v,True))
record={'actual_depth_ge2_scan_calls':1,'maximum_consumed_scan_depth':2}
def state_fixture(state=0.,gradient=1.):return [{'depth':2,'state_input':{'finite':True,'abs_max':state},'native_output_gradients':[{'finite':True,'abs_max':gradient}]}]
refused('depth2_without_nonzero_actual_prior_state',lambda:m.required_prior_state(record,state_fixture()))
refused('prior_state_without_original_loss_gradient',lambda:m.required_prior_state(record,state_fixture(1.,0.)))
refused('invented_depth2_coverage',lambda:m.required_prior_state(record,[]))
old=ast.parse((ROOT/'pipeline/diagnostic_bundles/tick_ddb531fb/btc_execution_review_preparation/review_btc.py').read_text(encoding='utf-8'))
fn=lambda t,n:next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
assert ast.dump(fn(rt,'resources'),include_attributes=False)==ast.dump(fn(old,'resources'),include_attributes=False)
checks.append({'label':'resource_semantic_protocol_function_AST_unchanged','outcome':'STATIC_MATCH'})
s=review.read_text(encoding='utf-8');a=admit.read_text(encoding='utf-8')
assert 'physical_gpu=0' not in s and "'physical_gpu': 0" not in s and "'gpu': '0'" not in a
assert "binding['physical_gpu'] == manifest['physical_gpu'] == 1" in s
assert 'pipeline/bcr_gpu1_' in s and 'GPU-7f82edb9-f620-8045-caea-a75232265cd1' in s
checks.append({'label':'only_GPU1_binding_manifest_lease_stage_and_waiting_assignment','outcome':'STATIC_MATCH'})
assert all(x in a for x in ('EXPECTED_AUTHORIZATION','2e892959','90f8820a',"'profile': 'experiment_first'","'status': 'waiting', 'gpu': '1'",'btc_before','btc_experiment_sha','btc_receipt_sha','m206_before','REVIEW_SHA = None','REVIEWER_SHA = None','--local-review-sha','--reviewer-sha'))
checks.append({'label':'admission_unbound_until_actual_reviews_and_preserves_BTC0_M206','outcome':'STATIC_MATCH'})
main=fn(at,'main');statements=ast.get_source_segment(a,main)
assert statements.index('if not args.execute_root:')<statements.index('import closure')<statements.index('save(paths[kind]')
assert "return" in statements[statements.index('if not args.execute_root:'):statements.index('import closure')]
checks.append({'label':'default_readonly_branch_returns_before_all_standard_shared_writes','outcome':'STATIC_MATCH'})
for path in (review,admit):
    done=subprocess.run([sys.executable,'-B',str(path)],capture_output=True,text=True,encoding='utf-8',timeout=20)
    assert done.returncode==2 and 'required' in done.stderr
    checks.append({'label':path.name+'_actual_missing_required_arguments_refusal','outcome':'ACTUAL_CLI_REFUSED_BEFORE_ACTION'})
result={'schema_version':1,'status':'DRAFT_CHECKER_FORMATTER_BOUNDARIES_CHECKED_NO_ACTUAL_RAW_REVIEW',
        'checks':checks,'logical_check_count':len(checks),'source_hashes':{'review_bcr.py':sha(review),'admit_bcr_draft.py':sha(admit)},
        'actual_raw_results_read':False,'native_or_GPU_or_SSH_run':False,'standard_PASS_receipt_queue_or_shared_written':False,
        'scope':'Negative in-memory scalar/JSON observations, actual code AST and two actual local missing-argument CLI refusals only. No synthetic fixture is an actual native result or an admissible PASS. Full real four-arm semantic and independent review remain pending.'}
with (HERE/'draft_validation.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'path':str(HERE/'draft_validation.json'),'sha256':sha(HERE/'draft_validation.json'),'checks':len(checks),'source_hashes':result['source_hashes']}))
