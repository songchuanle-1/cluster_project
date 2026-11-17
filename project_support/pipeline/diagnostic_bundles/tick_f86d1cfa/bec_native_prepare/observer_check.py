"""Execute actual BEC observer callbacks around actual production forward AST.

Only stdlib list/set interface carriers: no Torch, tensors, gradients, optimizer,
GELU numeric equivalence, native data or resource execution is represented.
"""
from pathlib import Path
import ast,copy,hashlib,itertools,json,types,sys
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
checks=[];runs=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def extract(nodes,names,scope):
 body=[n for n in nodes if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
 exec(compile(ast.Module(body=body,type_ignores=[]),'<actual-production-or-observer-AST>','exec'),scope)
 return scope

def run():
 original=ROOT/'pipeline/diagnostic_bundles/tick_6bdbcf77/new_candidate_prepare/static_check.py'
 source_tree=ast.parse(original.read_text());carrier={ 'itertools':itertools,'copy':copy,'types':types }
 extract(source_tree.body,{'coords','add','Tensor','TorchStub','Module','Linear','GELU'},carrier)
 Tensor,Torch,Module,Linear,GELU=(carrier[n] for n in ('Tensor','TorchStub','Module','Linear','GELU'))
 class Handle:
  def remove(self):pass
 Tensor.clone=lambda self:Tensor(self.shape,copy.deepcopy(self.data),self.dtype,self.device)
 Tensor.register_hook=lambda self,fn:Handle()
 def pre_register(self,fn):
  if not hasattr(self,'fixture_pre'):self.fixture_pre=[]
  self.fixture_pre.append(fn);return Handle()
 def post_register(self,fn):
  if not hasattr(self,'fixture_post'):self.fixture_post=[]
  self.fixture_post.append(fn);return Handle()
 def wrap(original_call):
  def call(self,*values):
   for fn in getattr(self,'fixture_pre',[]):assert fn(self,values) is None
   output=original_call(self,*values)
   for fn in getattr(self,'fixture_post',[]):assert fn(self,values,output) is None
   return output
  return call
 for Cls in (Module,Linear,GELU):
  Cls.register_forward_pre_hook=pre_register;Cls.register_forward_hook=post_register;Cls.__call__=wrap(Cls.__call__)
 Torch.Tensor=Tensor
 prod=ast.parse((HERE/'candidate_model/bipartite_edges.py').read_text());ps={'torch':Torch,'nn':types.SimpleNamespace(Module=Module,Linear=Linear,GELU=GELU)}
 extract(prod.body,{'build_bipartite_plan','CrossLevelBipartiteEdgeComposition'},ps)
 wt=ast.parse((HERE/'worker.py').read_text());smoke=next(n for n in wt.body if isinstance(n,ast.FunctionDef) and n.name=='smoke')
 nested=[n for n in ast.walk(smoke) if isinstance(n,ast.FunctionDef)]
 helper_names={'bec_membership_observation','bec_core_preflight'}
 def normalized(value):
  if isinstance(value,Tensor):return {'shape':value.shape,'dtype':value.dtype,'cells':[(str(k),normalized(v)) for k,v in sorted(value.data.items())]}
  if isinstance(value,frozenset):return sorted(map(repr,value))
  if isinstance(value,(list,tuple)):return [normalized(x) for x in value]
  if isinstance(value,dict):return {str(k):normalized(v) for k,v in value.items()}
  return value
 def fingerprint(torch,value):return hashlib.sha256(json.dumps(normalized(value),sort_keys=True).encode()).hexdigest()
 def summary(value):return {'shape':list(value.shape),'dtype':value.dtype,'finite':True,'nonfinite_count':0,'abs_max':int(any(bool(x) for x in value.data.values())),'fixture_scope':'SYMBOLIC_NOT_NATIVE_NUMERIC_FINITE'}
 cases=[([([0,1,2],[0,0,1],[0,0])],(3,2,1)),([([2,2,7],[4,0,4,1,2,2,3,0],[1,0,2,1,2])],(10,7,4)),([([],[0],[0]),([0],[0],[0])],(3,3,2)),([([0],[0],[0])],(2,2,2))]
 observer_names={'norm_pre','norm_post','bec_pre','observed_plan','observed_mean','operator_pre','operator_post','activation_post','original_coarse_post','bec_post','parameter_blocks'}
 for index,(members,widths) in enumerate(cases):
  C=2;B=len(members);edge=ps['CrossLevelBipartiteEdgeComposition'](C)
  banks=[Tensor((B,w,C),{(b,i,j):frozenset({('raw',level,b,i,j)}) for b in range(B) for i in range(w) for j in range(C)}) for level,w in enumerate(widths)]
  ids=[[Torch.tensor(members[b][level],dtype='long') for b in range(B)] for level in range(3)]
  bank=types.SimpleNamespace(cluster_ids_list=ids);att=types.SimpleNamespace(bipartite_edges=edge)
  state={'forward_index':1,'raw_refs':banks,'bec_norm_counts':{0:0,1:0,2:0},'bec_norm_output_refs':{}}
  watches=[];hooks=[];records=[];result={};original_mean=edge._mean_messages;original_plan=ps['build_bipartite_plan']
  def watch(value,record,key):watches.append({'shape':value.shape,'key':key})
  env={'torch':Torch,'summary':summary,'fingerprint':fingerprint,'watch':watch,'state':state,'edge_module':edge,'bank':bank,'att':att,
      'original_plan':original_plan,'original_mean':original_mean,'hooks':hooks,'bec_calls':records,'result':result,'candidate':True}
  extract(wt.body,helper_names,env);extract(nested,observer_names,env)
  for level in (0,1):env['norm_pre'](level)(None,(banks[level],));env['norm_post'](level)(None,(banks[level],),banks[level])
  ps['build_bipartite_plan']=env['observed_plan'];edge._mean_messages=env['observed_mean']
  for name in ('up_fine','up_middle','down_middle','down_fine'):
   module=getattr(edge,name);module.weight=object();module.register_forward_pre_hook(env['operator_pre'](name));module.register_forward_hook(env['operator_post'](name))
  edge.activation.register_forward_hook(env['activation_post']);edge.register_forward_pre_hook(env['bec_pre']);edge.register_forward_hook(env['bec_post'])
  callbacks=[]
  def original_coarse_transform(values):
   callbacks.append(values);env['norm_pre'](2)(None,(values,));env['norm_post'](2)(None,(values,),values)
   output=Tensor(values.shape,{i:(v if isinstance(v,frozenset) else frozenset())|frozenset({('coarse_FFN',i[0],i[1],i[2])}) for i,v in values.data.items()})
   env['original_coarse_post'](None,(values,),output);return output
  before=fingerprint(Torch,banks);output=edge(*banks,ids,original_coarse_transform)
  check('production_forward_observer_case'+str(index),len(records)==1 and records[0]['core_path_observed'] and len(callbacks)==1 and before==fingerprint(Torch,banks))
  check('actual_mean_observed_once_per_level_case'+str(index),len(records[0]['private_mean_calls'])==2*B and all(x['original_mean_calls']==1 and not x['means_recomputed_by_observer'] for x in records[0]['private_mean_calls']))
  check('actual_up_down_references_and_mask_case'+str(index),records[0]['actual_two_up_split_private_mean_two_down_path'] and records[0]['actual_original_coarse_skip_masked_and_consumed'] and records[0]['original_ID_restoration_and_unsupported_padding_delta0_exact'])
  blocks=env['parameter_blocks']();check('exact12_actual_parameter_blocks_case'+str(index),len(blocks)==12)
  for name in ('up_fine','up_middle','down_middle','down_fine'):
   entries=[v for k,v in blocks.items() if k.startswith(name+'_')];covered=[(r,c) for _,r0,r1,c0,c1 in entries for r in range(r0,r1) for c in range(c0,c1)]
   expected={(r,c) for r in range(2*C if name.startswith('up_') else C) for c in range(2*C)}
   check(name+'_block_partition_case'+str(index),set(covered)==expected and len(covered)==len(set(covered)))
  runs.append({'case':index,'batches':B,'actual_operator_calls':len(records[0]['operator_calls']),'actual_private_mean_calls':len(records[0]['private_mean_calls']),
     'actual_builder_calls':records[0]['actual_builder_calls'],'watch_registrations':len(watches),'native_gradients_executed':False})
  ps['build_bipartite_plan']=original_plan
 # Actual metadata/core preflight, without inventing a nontrivial-degree hard gate.
 env={};extract(wt.body,helper_names,env)
 singleton=env['bec_core_preflight']([([0],[0],[0])]);empty=env['bec_core_preflight']([([],[0],[0])])
 check('single_child_both_levels_core_legal_no_degree2_gate',singleton['core_path_possible'])
 check('all_empty_core_is_inconclusive',not empty['core_path_possible'] and empty['fine_edges']==empty['middle_edges']==0)
 # Actual bec_pre on an all-empty batch rejects before invoking the first watch.
 edge=ps['CrossLevelBipartiteEdgeComposition'](2);banks=[Tensor((1,2,2)) for _ in range(3)];ids=[[Torch.tensor([],dtype='long')],[Torch.tensor([0],dtype='long')],[Torch.tensor([0],dtype='long')]];watches=[]
 state={'raw_refs':banks,'bec_norm_counts':{0:1,1:1,2:0},'bec_norm_output_refs':{0:banks[0],1:banks[1]}};result={}
 env.update(state=state,edge_module=edge,bank=types.SimpleNamespace(cluster_ids_list=ids),result=result,summary=summary,watch=lambda *x:watches.append(x))
 extract(nested,{'bec_pre'},env)
 try:env['bec_pre'](edge,(*banks,ids,lambda x:x))
 except RuntimeError as exc:message=str(exc)
 else:raise AssertionError('Empty core accepted')
 check('actual_bec_pre_empty_refusal_before_all_watches',message.startswith('INCONCLUSIVE_COVERAGE:') and watches==[] and 'bec_context' not in state)
 check('no_Torch_or_native_data','torch' not in sys.modules)
 return {'runs':runs,'empty_refusal':message,'gradient_callbacks_and_optimizer_steps':'NOT_EXECUTED','fixture_carrier_source':str(original),'fixture_carrier_source_sha256':sha(original)}

def main():
 result={'schema_version':1,'checked_at':datetime.now(timezone.utc).isoformat(),'status':'PENDING','scope':'STDLIB_ACTUAL_OBSERVER_AND_PRODUCTION_FORWARD_INTERFACE_ONLY',
   'candidate_id':'hierarchy-cross-level-bipartite-edge-composition','code_commit':None,'worker_sha256':sha(HERE/'worker.py'),'checks':checks,'native':'NOT_RUN','resources':'NOT_RUN','Torch':'NOT_IMPORTED'}
 try:result['observations']=run();result['status']='SOFTWARE_OBSERVER_FIXTURES_PASSED_NATIVE_NOT_RUN'
 except Exception as exc:
  import traceback
  result.update(status='SOFTWARE_OBSERVER_FIXTURE_FAILED_NOT_NATIVE',error=str(exc),traceback=traceback.format_exc())
 result['check_count']=len(checks);result['failed_checks']=[x for x in checks if not x['passed']]
 with (HERE/'observer_fixture_run1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'status':result['status'],'checks':len(checks),'sha256':sha(HERE/'observer_fixture_run1.json')}));return int(result['status']=='SOFTWARE_OBSERVER_FIXTURE_FAILED_NOT_NATIVE')
if __name__=='__main__':raise SystemExit(main())
