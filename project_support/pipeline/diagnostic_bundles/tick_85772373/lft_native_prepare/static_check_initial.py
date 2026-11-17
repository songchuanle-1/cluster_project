"""Bounded new LFT callback/schema checks. No model/worker/Torch execution."""
from pathlib import Path
import ast, copy, hashlib, itertools, json, re
import author_guard as ag

ag.check();HERE=ag.HERE;ROOT=ag.ROOT
BASE=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/wfc_native_prepare'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)});assert value,name
def functions(path):return {n.name:n for n in ast.walk(ast.parse(path.read_text(encoding='utf-8'))) if isinstance(n,ast.FunctionDef)}
dump=lambda n:ast.dump(n,include_attributes=False)
worker=functions(HERE/'worker.py');base=functions(BASE/'worker.py')
runtime=functions(HERE/'native_runtime.py');oldruntime=functions(BASE/'native_runtime.py')
check('resources_complete_original_AST',dump(worker['resources'])==dump(base['resources']))
check('json_safe_original_failure_flags',dump(worker['json_safe'])==dump(base['json_safe']))
check('runtime_same_function_names',runtime.keys()==oldruntime.keys())
check('runtime_eight_other_bodies_exact',all(dump(n)==dump(oldruntime[name]) for name,n in runtime.items() if name!='require_promoted_version'))
for name in ('worker.py','native_runtime.py','assemble_packet.py','author_guard.py'):
    compile((HERE/name).read_text(encoding='utf-8'),str(HERE/name),'exec')
check('four_packet_Python_compile',True)
manifest=json.loads((HERE/'manifest_template.json').read_text(encoding='utf-8'))
check('actual5931_parent18e_DRAFTTrue',manifest['code_commit']=='5931d403a8bfc9f4d3fe6115a194bbeb55a9e8b1' and manifest['source_parent_commit']==manifest['runtime_expected_commit']=='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324' and manifest['draft_execution_disabled'] is True)
active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
check('ten_active_NULL_no_execution_assets',all(manifest[n] is None for n in active) and not any((HERE/n).exists() for n in ('native_manifest.json','lease.json','adapter_release.json')))
check('all_diagnostic_hashes',all(sha(HERE/n)==h for n,h in manifest['diagnostic_files'].items()))
setup=ast.unparse(worker['setup']);smoke=ast.unparse(worker['smoke'])
assignment=next(n for n in ast.walk(worker['setup']) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='excluded' for t in n.targets))
check('common_excludes_ONLY_new_lifting_FFNs_LNs_retained',ast.literal_eval(assignment.value)==('dec.cluster_att.nonlinear_lifting.',))
check('dynamic_common_names_shapes_count_fingerprint',all(s in setup for s in ("'names'","'shapes'","'tensor_count'","'parameter_count'","'sha256'")))
check('three_original_FFN_both_targets', 'ffn_levels = (0, 1, 2)' in smoke and 'assert len(calls) == 6' in smoke)
check('candidate_readback_uses_actual_synthesis_not_oldFFN', 'for level in () if candidate else ffn_levels:' in smoke and 'LFT_original_three_skips_and_exact_HCG_inputs' in smoke)
check('new_wholecore_gate_independent_oldFFN',"if candidate and name == 'nonlinear_lifting':" in smoke and 'whole_nonlinear_lifting_weight_gradient' in smoke and 'whole_nonlinear_lifting_weight_updated' in smoke)
check('no_per_map_block_positive_gate',"assert info is None or info['finite']" in smoke and 'Four new P/U whole weight blocks descriptive' in smoke)
check('finally_global_instance_hook_restore',all(s in smoke for s in ('reversed(global_replacements)','setattr(owner, name, original)','hook.remove()','state.clear()')))
check('no_WFC_or_removedFFN_inheritance',not any(s in smoke for s in ('wedge_factor','actual_wedges','actual_factor_map_calls','actual_private_incidence_mean_calls','nn.Identity')))
metadata={'copy':copy,'itertools':itertools}
exec(compile(ast.Module(body=[worker['lft_plan_observation'],worker['lft_coverage_preflight']],type_ignores=[]),'<actual-LFT-metadata>','exec'),metadata)
plan={'fine_ids':[2,5],'middle_ids':[1],'coarse_ids':[0],'fine_parent_positions':[0,0],'middle_parent_positions':[0],'middle_fine_counts':[2],'coarse_middle_counts':[1],'point_count':3}
members=([2,5,2],[0,0,1,0,0,1],[0,0])
check('actual_plan_holes_duplicates_original_parents',metadata['lft_plan_observation'](plan,members)==plan)
check('empty_before_watch_inconclusive',not metadata['lft_coverage_preflight']([([],[],[])])['true_supported_core_possible'])
check('mixed_empty_supported_legal',metadata['lft_coverage_preflight']([([],[],[]),members])['true_supported_core_possible'])
bad=copy.deepcopy(plan);bad['middle_fine_counts']=[3]
try:metadata['lft_plan_observation'](bad,members)
except AssertionError:check('wrong_child_counts_refused',True)
else:raise AssertionError('bad plan accepted')

class Opaque:
    counter=0
    def __init__(self,shape,label='opaque'):
        self.shape=tuple(shape);self.requires_grad=True;self.label=(label,Opaque.counter);Opaque.counter+=1
    def detach(self):return self
    def reshape(self,*args):return self
    def __eq__(self,other):return self
    def all(self):return True
class IDs:
    def __init__(self,values):self.values=list(values)
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return list(self.values)
class Box:pass
core=Box();core.channels=256;core.activation=object()
for name in ('predict_fine','update_middle','predict_middle','update_coarse'):setattr(core,name,object())
att=Box();att.nonlinear_lifting=core;att.cluster_ffn=[object(),object(),object()]
bank=Box();bank.cluster_ids_list=[[IDs(members[0])],[IDs(members[1])],[IDs(members[2])]]
normalized=[Opaque((1,k,256),'normalized') for k in (6,2,1)]
state={'forward_index':1,'norm_counts':[1,1,1],'norm_outputs':dict(enumerate(normalized))}
result={};exchange_calls=[];original_calls=[]
def summary(x):return {'shape':list(x.shape),'finite':True,'abs_max':0.0}
def fingerprint(torch,x):return repr(x.label) if isinstance(x,Opaque) else repr(x)
def original_select(tensor,dim,index,*args,**kwargs):original_calls.append('select');return Opaque((len(index.values),256),'selected')
def original_plus(tensor,other,*args,**kwargs):original_calls.append('plus');return Opaque(tensor.shape,'plus')
def original_minus(tensor,other,*args,**kwargs):original_calls.append('minus');return Opaque(tensor.shape,'minus')
def original_add(tensor,dim,index,source,*args,**kwargs):original_calls.append('index_add');return Opaque(tensor.shape,'sum')
def original_copy(tensor,dim,index,source,*args,**kwargs):original_calls.append('index_copy');return Opaque(tensor.shape,'copy')
scope={'state':state,'result':result,'att':att,'bank':bank,'summary':summary,'fingerprint':fingerprint,'torch':None,
    'watch':lambda *args:None,'lite_watch':lambda *args:None,'exchange_calls':exchange_calls,
    'original_select':original_select,'original_plus':original_plus,'original_minus':original_minus,
    'original_add':original_add,'original_copy':original_copy,'copy':copy,'itertools':itertools,
    'lft_coverage_preflight':metadata['lft_coverage_preflight'],'lft_plan_observation':metadata['lft_plan_observation']}
for name in ('exchange_pre','observed_plan','observed_prepare','observed_select','arithmetic','observed_plus','observed_minus','expected_map_input','map_pre','map_post','activation_post','observed_mean','observed_add','packed_ffn_pre','packed_ffn_post','observed_copy','exchange_post'):
    exec(compile(ast.Module(body=[worker[name]],type_ignores=[]),'<actual-LFT-callback>','exec'),scope)
scope['map_roles']=('pf_a','um_a','pm_a','uc_a','uc_s','pm_s','um_s','pf_s')
scope['map_names']=('predict_fine','update_middle','predict_middle','update_coarse','update_coarse','predict_middle','update_middle','predict_fine')
scope['mean_specs']=(('mean_fine_analysis','detail_fine','fine_parents','fine_counts','map_um_a'),('mean_middle_analysis','detail_middle','middle_parents','middle_counts','map_uc_a'),('mean_middle_synthesis','middle_core','middle_parents','middle_counts','map_uc_s'),('mean_fine_synthesis','fine_core','fine_parents','fine_counts','map_um_s'))
scope['original_plan']=lambda p,f,m,w:copy.deepcopy(plan)
def original_prepare(levels,ids):
    return [scope['observed_plan'](*(values[0].tolist() for values in ids),[6,2,1])]
scope['original_prepare']=original_prepare
def original_mean(messages,parents,counts):
    original_calls.append('mean')
    scope['observed_add'](Opaque((len(counts),256),'zero'),0,IDs(parents),messages)
    return Opaque((len(counts),256),'mean_return')
scope['original_mean']=original_mean
scope['exchange_pre'](core,(normalized,bank.cluster_ids_list,att.cluster_ffn))
returned_plans=scope['observed_prepare'](normalized,bank.cluster_ids_list)
check('actual_prepare_once_original_return',returned_plans is state['lft_context']['plans_ref'])
c=state['lft_context']
for level in range(3):scope['observed_select'](normalized[level],0,IDs(c['destinations'][level]))
def emit_map(name,input_ref):
    module=getattr(core,name);scope['map_pre'](name)(module,(input_ref,))
    linear=Opaque(input_ref.shape,'actual_linear_return');scope['map_post'](name)(module,(input_ref,),linear)
    output=Opaque(input_ref.shape,'actual_GELU_return');scope['activation_post'](core.activation,(linear,),output)
    return output
def mean(key,parentkey,countkey):return scope['observed_mean'](c[key],c[parentkey],c[countkey])
a0=emit_map('predict_fine',c['middle']);g0=scope['observed_select'](a0,0,IDs(c['fine_parents']))
scope['observed_minus'](c['fine'],g0)
m0=mean('detail_fine','fine_parents','fine_counts');a1=emit_map('update_middle',m0)
scope['observed_plus'](c['middle'],a1)
a2=emit_map('predict_middle',c['coarse']);g2=scope['observed_select'](a2,0,IDs(c['middle_parents']))
scope['observed_minus'](c['lifted_middle'],g2)
m1=mean('detail_middle','middle_parents','middle_counts');a3=emit_map('update_coarse',m1)
scope['observed_plus'](c['coarse'],a3)
for level,key in enumerate(('detail_fine','detail_middle','lifted_coarse')):
    module=att.cluster_ffn[level];inputs=(c[key],);scope['packed_ffn_pre'](level)(module,inputs)
    scope['packed_ffn_post'](level)(module,inputs,Opaque(c[key].shape,'actual_FFN_return'))
m2=mean('middle_core','middle_parents','middle_counts');a4=emit_map('update_coarse',m2)
scope['observed_minus'](c['coarse_core'],a4)
a5=emit_map('predict_middle',c['coarse_out']);g5=scope['observed_select'](a5,0,IDs(c['middle_parents']))
scope['observed_plus'](c['middle_core'],g5)
m3=mean('fine_core','fine_parents','fine_counts');a6=emit_map('update_middle',m3)
scope['observed_minus'](c['lifted_middle_out'],a6)
a7=emit_map('predict_fine',c['middle_out']);g7=scope['observed_select'](a7,0,IDs(c['fine_parents']))
scope['observed_plus'](c['fine_core'],g7)
for level,key in enumerate(('fine_out','middle_out','coarse_out')):scope['observed_copy'](Opaque((c['widths'][level],256),'zero'),0,IDs(c['destinations'][level]),c[key])
outputs=list(c['final_outputs']);scope['exchange_post'](core,(normalized,bank.cluster_ids_list,att.cluster_ffn),outputs)
record=exchange_calls[0]
check('actual_callbacks_full_analysis_FFN_inverse_phase_once',record['actual_map_calls']==record['actual_GELU_calls']==8 and record['actual_private_mean_calls']==4 and record['actual_arithmetic_calls']==8 and record['actual_original_FFN_calls']==[1,1,1] and record['actual_final_index_copy_calls']==3)
check('actual_mean_and_primitive_once_counts',original_calls.count('mean')==original_calls.count('index_add')==4 and original_calls.count('select')==7 and original_calls.count('plus')==original_calls.count('minus')==4 and original_calls.count('index_copy')==3)
check('actual_context_removed_and_actual_deltas_captured','lft_context' not in state and state['lft_delta_snapshots'] is not None if 'lft_delta_snapshots' in state else False)
for name,args in [('observed_select',(Opaque((1,256)),0,IDs([0]))),('observed_add',(Opaque((1,256)),0,IDs([0]),Opaque((1,256)))),('observed_copy',(Opaque((1,256)),0,IDs([0]),Opaque((1,256)))),('observed_plus',(Opaque((1,256)),Opaque((1,256)))),('observed_minus',(Opaque((1,256)),Opaque((1,256))))]:
    before=len(original_calls);returned=scope[name](*args)
    check('actual_inactive_once_transparent:'+name,isinstance(returned,Opaque) and len(original_calls)==before+1)
guard={'re':re,'DRAFT_EXECUTION_DISABLED':True,'CANDIDATE_COMMIT':manifest['code_commit'],'SOURCE_PARENT_COMMIT':manifest['source_parent_commit'],'SOURCE_PREPARATION_SHA256':manifest['source_preparation_sha256']}
exec(compile(ast.Module(body=[runtime['require_promoted_version']],type_ignores=[]),'<actual-version-guard>','exec'),guard)
try:guard['require_promoted_version']()
except RuntimeError:check('DRAFT_before_manifest_Torch',True)
else:raise AssertionError('draft passed')
ag.save(HERE/'static_validation.json',{'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','check_count':len(checks),'checks':checks,'Torch':False,'native':'NOT_RUN','resources':'NOT_RUN',
    'command':'python -B pipeline/diagnostic_bundles/tick_85772373/lft_native_prepare/static_check.py',
    'scope':'New callback phase/opaque once-return control plus metadata/compile/AST only. No production forward, Tensor descriptors, GELU, autograd, original72/97 source suites, worker entry, Git/SSH/GPU.'})
print(json.dumps({'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','check_count':len(checks),'sha256':sha(HERE/'static_validation.json')}))
