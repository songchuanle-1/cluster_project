"""BFC author-local AST/stdlib/list-stub/refusal checks; no torch/native."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,json,math,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/project/cluster_project')
OLD=ROOT/'pipeline/diagnostic_bundles/tick_41eb62fa/bcr_native_prepare'
MODEL=HERE.parent/'new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
wt=(HERE/'worker.py').read_text(encoding='utf-8');rt=(HERE/'native_runtime.py').read_text(encoding='utf-8');w=ast.parse(wt);r=ast.parse(rt)
function=lambda t,n:next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
checks={}
for name,text in [('worker.py',wt),('native_runtime.py',rt)]:compile(text,str(HERE/name),'exec')
checks['actual_sources_compile_without_import']=True
oldw=ast.parse((OLD/'worker.py').read_text(encoding='utf-8'));oldr=ast.parse((OLD/'native_runtime.py').read_text(encoding='utf-8'))
same=lambda a,b,n:ast.dump(function(a,n),include_attributes=False)==ast.dump(function(b,n),include_attributes=False)
checks['complete_resources_AST_exact_original']=same(w,oldw,'resources')
checks['seven_runtime_guard_utility_AST_exact_original']=all(same(r,oldr,n) for n in ('sha','verify','observe','acquire','release','fingerprint','save'))
checks['disabled_entry_before_manifest_fcntl_torch']='DRAFT_EXECUTION_DISABLED = True' in rt and rt.index('require_promoted_version()\n')<rt.index('import fcntl')<rt.index('MANIFEST =')
checks['future_selected_GPU0_or1_single_uuid_stage_binding']='PHYSICAL_GPU in GPU_UUIDS' in rt and "'_gpu' + str(MANIFEST['physical_gpu'])" in rt and 'CUDA_VISIBLE_DEVICES=GPU_UUIDS[PHYSICAL_GPU]' in rt
checks['original_TRAIN2_no_aux_backward_or_replay']='train.train(1,model,TwoNativeBatches(loader),optimizer,scheduler,cfg,logger,writer)' in wt and 'torch.autograd.grad(' not in wt and 'loss.backward(' not in wt
checks['exact_common_prefixes_and_middle_LN_retained']="excluded = ('dec.cluster_att.cluster_ffn.1.', 'dec.cluster_att.middle_butterfly.')" in wt and 'retain middle LayerNorm' in wt
env={'math':math};model_ast=ast.parse((MODEL/'middle_butterfly.py').read_text(encoding='utf-8'))
for tree,name in [(model_ast,'build_butterfly_plan'),(w,'butterfly_plan_observation')]:exec(compile(ast.Module(body=[function(tree,name)],type_ignores=[]),name,'exec'),env)
cases=[]
for n in (0,1,2,3,5,8):
    plan=env['build_butterfly_plan']([[float(n-i),0.,0.] for i in range(n)],[0]*n,[True]*n,max(8,n));groups,seq=env['butterfly_plan_observation'](plan)
    for stage in seq:
        if stage['kind']=='round':
            assert len(stage['participant_ids'])==2*len(stage['pairs'])
            assert set(stage['participant_ids'])|set(stage['unpaired_active_ids'])==set(range(n))
    cases.append({'n':n,'groups':len(groups),'mix_calls':len(seq)})
checks['six_actual_production_plans_described_without_fake_states']=True

class Tensor:
    def __init__(self,data):self.data=copy.deepcopy(data);self.device='stub';self.requires_grad=True;self.callbacks=[]
    @property
    def shape(self):return (len(self.data),len(self.data[0])) if self.data and isinstance(self.data[0],list) else (len(self.data),)
    def detach(self):return self
    def clone(self):return Tensor(self.data)
    def __getitem__(self,key):
        if isinstance(key,tuple):
            row,col=key
            return Tensor([x[col] for x in self.data[row]]) if isinstance(row,slice) else Tensor(self.data[row][col])
        return Tensor(self.data[key])
    def index_select(self,dim,ids):assert dim==0;return Tensor([self.data[i] for i in ids])
    def index_copy(self,dim,ids,values):
        assert dim==0;data=copy.deepcopy(self.data)
        for i,value in zip(ids,values.data):data[i]=copy.deepcopy(value)
        return Tensor(data)
    def register_hook(self,callback):self.callbacks.append(callback);return SimpleNamespace(remove=lambda:None)
    def emit(self,gradient):
        for callback in self.callbacks:assert callback(gradient) is None
class Features:
    def __init__(self,rows):self.rows=rows
    def __getitem__(self,index):return Tensor(self.rows[index])
class Torch:
    long='long'
    @staticmethod
    def tensor(value,**kw):return list(value)
    @staticmethod
    def zeros_like(value):return Tensor([[0.]*len(row) for row in value.data])
def summary(tensor):
    flat=[v for row in tensor.data for v in row] if tensor.data and isinstance(tensor.data[0],list) else tensor.data
    return {'shape':list(tensor.shape),'finite':all(math.isfinite(v) for v in flat),'abs_max':max([abs(v) for v in flat]+[0.])}
def fingerprint(unused,tensor):return json.dumps(tensor.data,separators=(',',':'))
def watch(value,record,key):assert value.requires_grad
callbacks={n.name:n for n in ast.walk(function(w,'smoke')) if isinstance(n,ast.FunctionDef)}
environment={'torch':Torch,'fingerprint':fingerprint,'summary':summary,'watch':watch,'hooks':[],
             'att':SimpleNamespace(middle_butterfly=SimpleNamespace(channels=2)),'state':{}}
for name in ('mix_pre','mix_post','activation_post'):exec(compile(ast.Module(body=[callbacks[name]],type_ignores=[]),name,'exec'),environment)
features=Features([[[1.,2.],[3.,4.],[5.,6.],[7.,8.]]])
plan=env['build_butterfly_plan']([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.],[3.,0.,0.]],[0,0,0,1],[True]*4,4);groups,sequence=env['butterfly_plan_observation'](plan)
for stage in sequence:stage['batch']=0
context={'features':features,'sequence':sequence,'index':0,'working':{0:features[0].clone()},'pending':None,'pending_activation':None,'record':{'mix_calls':[]}}
environment['state'].update(butterfly_context=context,forward_index=1)
counter=0
for stage in sequence:
    old=context['working'][0].clone()
    if stage['kind']=='round':left=old.index_select(0,stage['left_ids']);right=old.index_select(0,stage['right_ids'])
    else:left=features[0].index_select(0,stage['original_ids']);right=Torch.zeros_like(left)
    pair=Tensor([a+b for a,b in zip(left.data,right.data)])
    assert environment['mix_pre'](None,(pair,)) is None
    counter+=1;preactivation=Tensor([[-counter,-2*counter,-3*counter,-4*counter] for _ in pair.data])
    assert environment['mix_post'](None,(pair,),preactivation) is None
    actual_activation=Tensor([[10.*counter,20.*counter,30.*counter,40.*counter] for _ in pair.data])
    assert environment['activation_post'](None,(preactivation,),actual_activation) is None
    actual_activation.emit(Tensor([[1.,2.,3.,4.] for _ in pair.data]))
    expected=copy.deepcopy(old.data)
    if stage['kind']=='round':
        for row,lid,rid in zip(actual_activation.data,stage['left_ids'],stage['right_ids']):expected[lid]=row[:2];expected[rid]=row[2:]
    else:
        for row,token in zip(actual_activation.data,stage['original_ids']):expected[token]=row[:2]
    assert context['working'][0].data==expected
assert context['index']==len(sequence) and context['pending'] is None and context['pending_activation'] is None
assert all(record['activation_original_calls']==1 for record in context['record']['mix_calls'])
checks['actual_mix_activation_hooks_list_stub_both_old_inputs_two_outputs_carry_and_singleton']=True
before=ast.unparse(callbacks['before_step']);after=ast.unparse(callbacks['after_step'])
checks['four_original_loss_gradient_and_actual_update_quadrant_checks']=all(k in wt for k in ('left_output_from_left_input','left_output_from_right_input','right_output_from_left_input','right_output_from_right_input')) and 'weight.grad[r0:r1, c0:c1]' in before and 'weight.detach()[r0:r1, c0:c1]' in after
post=ast.unparse(callbacks['butterfly_post'])
checks['absent_or_empty_coverage_INCONCLUSIVE_before_output_gradient_watch']=post.index('if not coverage:')<post.index("watch(output, record, 'native_output_gradients')") and 'INCONCLUSIVE_COVERAGE' in post
checks['per_call_output_half_zero_allowed_four_quadrants_remain_required']="all(g['left']['finite'] and g['right']['finite']" in wt and "g['left']['abs_max']>0" not in wt and "g['right']['abs_max']>0" not in wt
checks['coverage_INCONCLUSIVE_and_no_self_exclusive_claim']=all(k in wt for k in ('INCONCLUSIVE_COVERAGE','actual_nonpower2_supported_parent_groups','actual_multistage_supported_parent_groups',"'self_exclusive_claim':False",'native_output_half_gradients'))
probe="""import json,runpy,sys
sys.path.insert(0,str(__import__('pathlib').Path(sys.argv[1]).parent))
try:runpy.run_path(sys.argv[1],run_name='__main__')
except RuntimeError as e:
 assert 'BFC native preparation is execution-disabled' in str(e)
 assert 'torch' not in sys.modules and 'fcntl' not in sys.modules
 print(json.dumps({'own_disabled_error':str(e),'torch_imported':False,'fcntl_imported':False}))
else:raise AssertionError('Disabled entry accepted')
"""
entries=[]
for name in ('native_runtime.py','worker.py'):
    done=subprocess.run([sys.executable,'-B','-c',probe,str(HERE/name)],capture_output=True,text=True,encoding='utf-8',timeout=20)
    assert done.returncode==0,(name,done.stdout,done.stderr);entries.append({'entry':name,'result':json.loads(done.stdout)})
checks['two_actual_local_stdlib_disabled_entry_refusals_before_manifest_torch']=True
assert all(checks.values()),checks
result={'status':'BFC_AUTHOR_LOCAL_AST_STDLIB_HOOK_STUB_REFUSAL_CHECKED_NATIVE_NOT_RUN','checks':checks,'logical_check_count':len(checks),
        'production_plan_examples':cases,'entry_refusals':entries,'source_hashes':{n:sha(HERE/n) for n in ('worker.py','native_runtime.py')},
        'scope':'Actual isolated pure production plan and actual callback AST executed on Python lists only; no torch/tensors/autograd/FP32/native or resource behavior tested. Author selfchecks are not independent packet review.',
        'native':'NOT_RUN','resources':'NOT_RUN','SSH_GPU_transport':'NOT_RUN','actual_loss_gradients_and_coverage':'UNKNOWN'}
out=HERE/'static_validation_final.json'
with out.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'path':str(out),'sha256':sha(out),'checks':len(checks),'source_hashes':result['source_hashes']}))
