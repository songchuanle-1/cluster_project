from pathlib import Path
import ast,copy,hashlib,json,re
import author_guard as ag
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/project/cluster_project');checks=[]
def ck(n,v):
 assert v,n;checks.append(n)
def tree(p):return ast.parse(p.read_text('utf8'))
def fn(t,n):return next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
def dump(n):return ast.dump(n,include_attributes=False)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ag.check();worker=tree(HERE/'worker.py');old=tree(ROOT/'pipeline/diagnostic_bundles/tick_85772373/lft_native_prepare/worker.py')
for p in [HERE/'worker.py',HERE/'native_runtime.py',*sorted((HERE/'candidate_model').glob('*.py'))]:compile(p.read_text('utf8'),str(p),'exec');ck('compile_'+p.name,True)
ck('resources_complete_AST_identical',dump(fn(worker,'resources'))==dump(fn(old,'resources')))
ck('json_safe_AST_identical',dump(fn(worker,'json_safe'))==dump(fn(old,'json_safe')))
proto=ROOT/'pipeline/diagnostic_bundles/tick_d94467a9/new_candidate_one';source=json.loads((proto/'preparation.json').read_text('utf8'))
for rel,h in source['source_files'].items():p=HERE/('candidate.yaml' if rel.endswith('.yaml') else 'candidate_model/'+Path(rel).name);ck('exact_source_'+Path(rel).name,digest(p)==h)
m=json.loads((HERE/'manifest_template.json').read_text('utf8'));ck('ten_active_NULL',all(m[k] is None for k in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')))
ck('draft_true_real_version',m['draft_execution_disabled'] is True and m['code_commit']=='6bc36adfe42764aac2209e6600fb3a783e2fa374' and m['runtime_expected_commit']=='4457a46f9075f61e83340aa0f0af87d5bf4e986c')
runtime=(HERE/'native_runtime.py').read_text('utf8');prefix=runtime[:runtime.index('\nimport os')]
try:exec(compile(prefix,'isolated_version_predicate','exec'),{});raise AssertionError('Expected disabled refusal')
except RuntimeError as e:ck('version_predicate_rejects_before_manifest_NVML_Torch','execution-disabled' in str(e))
text=(HERE/'worker.py').read_text('utf8');ck('NEC_key_and_no_old_lifting_subtree','NEC_node_edge_observations=' in text and 'nonlinear_lifting' not in text)
ck('common_excludes_three_FFN_and_new_only',"excluded = ('dec.cluster_att.cluster_ffn.0.','dec.cluster_att.cluster_ffn.1.','dec.cluster_att.cluster_ffn.2.','dec.cluster_att.node_edge_coupling.')" in text)
# Execute only new metadata functions, not the model or its original software suite.
ns={'copy':copy};exec(compile(ast.Module(body=[fn(worker,n) for n in ('nec_coverage_preflight','nec_plan_observation','nec_rounds_observation')],type_ignores=[]),'new_metadata','exec'),ns)
source_tree=tree(HERE/'candidate_model/node_edge_coupling.py');meta={};exec(compile(ast.Module(body=[fn(source_tree,n) for n in ('build_node_edge_plan','build_node_edge_rounds')],type_ignores=[]),'frozen_metadata_producer','exec'),meta)
for i,members in enumerate((([2],[0,0,1],[0,0]),([0,2,3],[0,0,1,1],[0,0]))):
 p=meta['build_node_edge_plan'](*members,[4,2,1]);ck('new_observer_plan_'+str(i),ns['nec_plan_observation'](p,members)==p)
 r=meta['build_node_edge_rounds']([p]);ck('new_observer_rounds_'+str(i),ns['nec_rounds_observation'](r,[p])==r)
ck('empty_preflight_false',not ns['nec_coverage_preflight']([([],[],[])])['true_supported_core_possible'])
# Extract only actual transparent mean callback functions with opaque return carriers.
smoke=fn(worker,'smoke');candidate=next(x for x in smoke.body if isinstance(x,ast.If) and any(isinstance(y,ast.FunctionDef) and y.name=='observed_endpoint' for y in x.body))
callbacks={n:next(x for x in candidate.body if isinstance(x,ast.FunctionDef) and x.name==n) for n in ('observed_endpoint','observed_incident')}
for role in ('endpoint','incident'):
 for failing in (False,True):
  original_input=object();original_output=object();rp={};record={'mean_calls':[]};c={'phase':role+'_mean','node_state':original_input,'edge_state':original_input,'rounds_ref':[rp],'round_index':0,'endpoint_calls':0,'incident_calls':0,'record':record};calls=[]
  if role=='incident':rp['node_counts']=[1]
  def original(*args):
   calls.append(args)
   if failing:raise ValueError('intentional opaque original failure')
   return original_output
  env={'state':{'nec_context':c},'original_'+role:original,'summary':lambda x:{'opaque':True},'fingerprint':lambda t,x:'opaque','torch':None,'lite_watch':lambda *x:None};exec(compile(ast.Module(body=[callbacks['observed_'+role]],type_ignores=[]),'actual_mean_callback','exec'),env)
  try:
   out=env['observed_'+role](original_input,rp);ck(role+'_return_exact_'+str(failing),out is original_output and len(calls)==1 and not failing)
  except ValueError:ck(role+'_failure_original_once',failing and len(calls)==1)
  ck(role+'_finally_active_clear_'+str(failing),c['mean_active'] is False)
# Nine runtime functions remain exact except candidate diagnostic label in version predicate.
oldrt=tree(ROOT/'pipeline/diagnostic_bundles/tick_d94467a9/lft_native_compatible_prepare/native_runtime.py');newrt=tree(HERE/'native_runtime.py')
class Labels(ast.NodeTransformer):
 def visit_Constant(self,n):
  if isinstance(n.value,str):n.value=n.value.replace('LFT','NEC')
  return n
for f in [x for x in newrt.body if isinstance(x,ast.FunctionDef)]:ck('runtime_function_'+f.name,dump(f)==dump(Labels().visit(copy.deepcopy(fn(oldrt,f.name)))))
result={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','check_count':len(checks),'checks':checks,'worker_sha256':digest(HERE/'worker.py'),'Torch':False,'model_forward':False,'native':False,'resources':False,'entry_imported':False,'scope':'Compile/hash/resource AST, new observer metadata and opaque once-return/failure-finally mean controls only. No old source suite or full model control.','author_guard':ag.check()}
ag.save('static_validation.json',json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'result_sha256':digest(HERE/'static_validation.json')}))
