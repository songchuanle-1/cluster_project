from pathlib import Path
import ast,copy,hashlib,json,math
import author_guard as ag
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/project/cluster_project');checks=[]
def ck(n,v):assert v,n;checks.append(n)
def tree(p):return ast.parse(p.read_text('utf8'))
def fn(t,n):return next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
def dump(n):return ast.dump(n,include_attributes=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ag.check();w=tree(HERE/'worker.py');old=tree(ROOT/'pipeline/diagnostic_bundles/tick_94c2ad26/nec_native_prepare/worker.py')
for p in [HERE/'worker.py',HERE/'native_runtime.py',*sorted((HERE/'candidate_model').glob('*.py'))]:compile(p.read_text('utf8'),str(p),'exec');ck('compile_'+p.name,True)
for n in ('resources','json_safe'):ck('whole_'+n+'_AST_identical',dump(fn(w,n))==dump(fn(old,n)))
proto=ROOT/'pipeline/diagnostic_bundles/tick_d94467a9/new_candidate_two';prep=json.loads((proto/'preparation.json').read_text('utf8'))
for rel,h in prep['source_files'].items():ck('source_'+Path(rel).name,sha(HERE/('candidate.yaml' if rel.endswith('.yaml') else 'candidate_model/'+Path(rel).name))==h)
text=(HERE/'worker.py').read_text('utf8');ck('actual_MIC_namespace','MIC_mobius_interaction_observations=' in text and 'node_edge_coupling' not in text)
ck('common_only_three_removed_FFN_and_new_subtree',"excluded = ('dec.cluster_att.cluster_ffn.0.','dec.cluster_att.cluster_ffn.1.','dec.cluster_att.cluster_ffn.2.','dec.cluster_att.mobius_interaction.')" in text)
ns={'copy':copy};exec(compile(ast.Module(body=[fn(w,n) for n in ('mic_coverage_preflight','mic_plan_observation')],type_ignores=[]),'new_observer_metadata','exec'),ns)
source=tree(HERE/'candidate_model/ancestry_mobius.py');env={};exec(compile(ast.Module(body=[fn(source,n) for n in ('_ids','build_mobius_path_plan')],type_ignores=[]),'original_metadata_only','exec'),env)
for i,members in enumerate((([2],[0,0,1],[0,0]),([0,1,2,3],[0,1,1,1],[0,0]))):
 p=env['build_mobius_path_plan'](*members,[4,2,1]);ck('actual_observer_plan_'+str(i),ns['mic_plan_observation'](p,members)==p)
ck('empty_preflight_no_forced_sample',not ns['mic_coverage_preflight']([([],[],[])])['true_supported_core_possible'])
smoke=fn(w,'smoke');block=next(x for x in smoke.body if isinstance(x,ast.If) and any(isinstance(y,ast.FunctionDef) and y.name=='observed_getitem' for y in x.body));names=('arithmetic','observed_plus','observed_minus','observed_getitem','observed_mean');callbacks=[next(y for y in block.body if isinstance(y,ast.FunctionDef) and y.name==n) for n in names]
class V:
 def __init__(self,value):self.value=value
calls=[]
def plus(a,b,*args,**kwargs):calls.append(('add',a,b));return V(a.value+b.value)
def minus(a,b,*args,**kwargs):calls.append(('sub',a,b));return V(a.value-b.value)
a,b,c=V(2),V(3),V(5);ctx={'phase':'subset0_ab','gathered':[a,b,c],'subset_refs':{},'record':{'subset_arithmetic_calls':[],'contrast_arithmetic_calls':[],'slice_calls':[],'mean_calls':[]},'slices':[],'contrast_ops':0,'n':1};state={'mic_context':ctx};subsets=[];getitem_calls=[]
def getitem(t,key):getitem_calls.append(key);return subsets[key.start or 0]
e={'state':state,'original_plus':plus,'original_minus':minus,'original_getitem':getitem,'summary':lambda x:{'finite':math.isfinite(x.value),'value':x.value},'fingerprint':lambda t,x:str(x.value),'torch':None,'lite_watch':lambda *x:None}
exec(compile(ast.Module(body=callbacks,type_ignores=[]),'actual_opaque_callbacks','exec'),e)
ab0=e['observed_plus'](a,b);abc=e['observed_plus'](ab0,c);ab=e['observed_plus'](a,b);ac=e['observed_plus'](a,c);bc=e['observed_plus'](b,c)
ck('actual_five_input_adds_not_one_reused_AB',ctx['phase']=='cat' and len(calls)==5 and ab0 is not ab and [abc.value,ab.value,ac.value,bc.value]==[10,5,7,8])
# Opaque captured activation values: integer polynomial+offset only tests routing/signs, not real GELU/FP32.
subsets=[V(x**3+7) for x in (10,5,7,8,2,3,5,0)];activation=object();ctx.update(phase='contrast',activation_ref=activation)
left=e['observed_getitem'](activation,slice(None,1));right=e['observed_getitem'](activation,slice(1,2));value=e['observed_minus'](left,right)
for i,kind in enumerate(('sub','sub','add','add','add','sub'),2):
 right=e['observed_getitem'](activation,slice(i,i+1));value=e['observed_plus' if kind=='add' else 'observed_minus'](value,right)
ck('actual_eight_slices_each_original_once',len(getitem_calls)==len(ctx['slices'])==8 and [v['subset_index'] for v in ctx['record']['slice_calls']]==list(range(8)))
ck('actual_signed_coefficients_and_phi0_kept',[v['coefficient'] for v in ctx['record']['slice_calls']]==[1,-1,-1,-1,1,1,1,-1] and [v['kind'] for v in ctx['record']['contrast_arithmetic_calls']]==['sub','sub','sub','add','add','add','sub'])
expected=sum(sgn*x.value for sgn,x in zip((1,-1,-1,-1,1,1,1,-1),subsets));ck('actual_q_original_arithmetic_once_and_independent_sign_oracle',ctx['q_ref'] is value and value.value==expected==180 and len(calls)==12 and ctx['phase']=='middle_mean')
mean_calls=[];mean_returns=[]
def mean(messages,positions,counts):
 out=V(messages.value);mean_calls.append((messages,positions,counts));mean_returns.append(out);return out
e['original_mean']=mean;ctx.update(mean_count=0,mean_outputs=[],mp=[0],cp=[0],mc=[1],cc=[1])
o0=e['observed_mean'](value,[0],[1]);o1=e['observed_mean'](value,[0],[1]);ck('two_original_direct_fine_means_once_same_q',len(mean_calls)==2 and all(x[0] is value for x in mean_calls) and o0 is mean_returns[0] and o1 is mean_returns[1] and ctx['phase']=='final_scatter' and not ctx['mean_active'])
ctx.update(phase='middle_mean',mean_count=0,mean_outputs=[])
def fail(*args):raise ValueError('intentional opaque original mean failure')
e['original_mean']=fail
try:e['observed_mean'](value,[0],[1]);raise AssertionError('missing opaque failure')
except ValueError:ck('mean_failure_finally_context_clear',ctx['mean_active'] is False and ctx['mean_count']==0)
state.clear();before=len(calls);out=e['observed_plus'](V(8),V(9));ck('global_wrapper_context_outside_original_once',len(calls)==before+1 and out.value==17)
# Runtime functions exact except label; isolated prefix rejects before file/NVML/Torch imports.
oldrt=tree(ROOT/'pipeline/diagnostic_bundles/tick_94c2ad26/nec_native_prepare/native_runtime.py');rt=tree(HERE/'native_runtime.py')
class Label(ast.NodeTransformer):
 def visit_Constant(self,n):
  if isinstance(n.value,str):n.value=n.value.replace('NEC','MIC')
  return n
for f in [x for x in rt.body if isinstance(x,ast.FunctionDef)]:ck('runtime_'+f.name,dump(f)==dump(Label().visit(copy.deepcopy(fn(oldrt,f.name)))))
s=(HERE/'native_runtime.py').read_text('utf8');prefix=s[:s.index('\nimport os')]
try:exec(compile(prefix,'disabled_predicate_only','exec'),{});raise AssertionError('expected disabled')
except RuntimeError as x:ck('DRAFT_rejection_before_manifest_NVML_Torch','execution-disabled' in str(x))
result={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','check_count':len(checks),'checks':checks,'worker_sha256':sha(HERE/'worker.py'),'Torch':False,'model_forward':False,'entry_imported':False,'native':False,'resources':False,'scope':'New observer metadata/opaque original-call routing and signs/phi0, compile/source/runtime/resource AST only; no original33/MICsource/NEC48 suites or learned-model/GELU/FP32/autograd run.','author_guard':ag.check()}
ag.save('static_validation.json',json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':len(checks),'result_sha256':sha(HERE/'static_validation.json')}))
