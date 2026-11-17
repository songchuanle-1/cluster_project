"""Independent production PES AST controls; stdlib carriers are not Tensor/native evidence."""
from pathlib import Path
from types import SimpleNamespace
from itertools import product
from collections import Counter
import ast,math,json,hashlib
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SOURCE=HERE/'new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pes/euler_state.py'
# Reuse only transparent list-carrier definitions by AST; do not execute the prior DCE suite.
carrier=ast.parse((ROOT/'pipeline/diagnostic_bundles/tick_01d9102a/dce_independent_software.py').read_text(encoding='utf8'))
parts=[n for n in carrier.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ['prod','T','cat']]
ns={'product':product};exec(compile(ast.fix_missing_locations(ast.Module(parts,[])),'prior_carrier_definitions_only','exec'),ns)
T=ns['T'];cat=ns['cat'];prod=ns['prod']
def get(self,key):
 if isinstance(key,int):
  width=prod(self.shape[1:]);return T(self.v[key*width:(key+1)*width],self.shape[1:])
 assert isinstance(key,slice);return self.index_select(0,T(list(range(self.shape[0]))[key]))
T.__getitem__=get
stack=lambda vals,dim=0:T([a for v in vals for a in v.v],(len(vals),)+vals[0].shape)
torch=SimpleNamespace(tensor=lambda v,**kw:T(v),cat=cat,stack=stack,long='index')
module=ast.parse(SOURCE.read_text(encoding='utf8'));nodes=[n for n in module.body if isinstance(n,ast.FunctionDef)];cls=next(n for n in module.body if isinstance(n,ast.ClassDef));nodes.append(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward'));ns={'torch':torch};exec(compile(ast.fix_missing_locations(ast.Module(nodes,[])),str(SOURCE),'exec'),ns)
owner=SimpleNamespace(channels=1,activation=lambda x:x,cell=lambda x:T([.2*x.v[i]+.3*x.v[i+1]+.1 for i in range(0,len(x.v),2)],(x.shape[0],1)))
def reference(ids,values,widths,reset=False):
 fine=sorted(set(ids[0]));mid=sorted({ids[1][i] for i in fine});roots=sorted({ids[2][j] for j in mid});nodes=[(0,i) for i in fine]+[(1,j) for j in mid]+[(2,k) for k in roots];state={node:values[node[0]][node[1]] for node in nodes};initial=dict(state);walks=[]
 neighbors={n:[] for n in nodes}
 for i in fine:neighbors[(0,i)].append((1,ids[1][i]));neighbors[(1,ids[1][i])].append((0,i))
 for j in mid:neighbors[(1,j)].append((2,ids[2][j]));neighbors[(2,ids[2][j])].append((1,j))
 def dfs(n,parent=None):
  out=[n]
  for child in sorted(x for x in neighbors[n] if x!=parent):out.extend(dfs(child,n));out.append(n)
  return out
 for k in roots:
  walk=dfs((2,k));walks.append(walk)
  for pass_number,seq in enumerate([walk,list(reversed(walk))]):
   if reset and pass_number==1:
    for n in set(walk):state[n]=initial[n]
   for sender,receiver in zip(seq[:-1],seq[1:]):state[receiver]=.2*state[receiver]+.3*state[sender]+.1
 out=[[0.]*k for k in widths]
 for (l,i),v in state.items():out[l][i]=v
 return out,walks
cases=[('empty',([],[],[]),(4,3,2)),('one_true_path',([2,2],[0,0,1],[0,1]),(4,3,2)),('unequal_branching',([0,1,2,3],[0,0,0,2],[0,1,0]),(5,4,2)),('sparse_two_roots',([1,3,4,1],[0,2,1,2,3],[0,1,1,0]),(6,5,3)),('duplicate_point_order',([3,1,1,3],[0,2,1,2],[1,0,1]),(5,4,3))];checks=0;topology=[];reset_discriminated=False
for name,ids,widths in cases:
 vals=[[float(1+10*l+i) for i in range(k)] for l,k in enumerate(widths)];levels=[T([[[v] for v in bank]]) for bank in vals];members=[[T(ids[l])] for l in range(3)]
 actual=ns['forward'](owner,levels,members);expected,walks=reference(ids,vals,widths);broken,_=reference(ids,vals,widths,True)
 for l in range(3):assert actual[l].shape==(1,widths[l],1) and all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12) for a,b in zip(actual[l].v,expected[l]));checks+=1
 if expected!=broken:reset_discriminated=True
 plan=ns['build_euler_plan'](*ids,widths);assert plan['node_keys']==[(l,i) for l,key in enumerate(['fine_ids','middle_ids','coarse_ids']) for i in plan[key]];checks+=1
 assert sum(len(c['events']) for c in plan['components'])==4*plan['edge_count'];checks+=1
 for comp,walk in zip(plan['components'],walks):
  real=[plan['node_keys'][i] for i in comp['walk']];assert real==walk and real[0]==real[-1] and len(comp['forward_events'])==len(comp['backward_events'])==2*comp['edge_count'];checks+=1
  counter=Counter(comp['events']);assert all(n==2 for n in counter.values()) and all(counter[(v,u)]==n for (u,v),n in counter.items());checks+=1
  sources={i:{i} for i in set(comp['walk'])}
  for u,v in comp['events']:sources[v]=sources[v]|sources[u]
  assert all(sources[v]==set(comp['walk']) for v in sources);checks+=1
 topology.append({'case':name,'supported_nodes':len(plan['node_keys']),'edges':plan['edge_count'],'actual_events':sum(len(c['events']) for c in plan['components'])})
assert reset_discriminated;checks+=1
# Mixed empty/nonempty scenes, disjoint components with unequal event lengths, and original-ID batch offsets.
widths=(6,5,3);batch_ids=[([],[],[]),cases[3][1],([0,2],[1,0,1],[0,2])];values=[[[float(1+b*100+l*10+i) for i in range(k)] for l,k in enumerate(widths)] for b in range(3)];levels=[T([[[v] for v in values[b][l]] for b in range(3)]) for l in range(3)];members=[[T(batch_ids[b][l]) for b in range(3)] for l in range(3)]
actual=ns['forward'](owner,levels,members);plans=[ns['build_euler_plan'](*ids,widths) for ids in batch_ids];rounds=ns['build_event_rounds'](plans)
for l in range(3):
 expected=[v for b in range(3) for v in reference(batch_ids[b],values[b],widths)[0][l]];assert all(math.isclose(a,z,rel_tol=1e-12,abs_tol=1e-12) for a,z in zip(actual[l].v,expected));checks+=1
assert sum(map(len,rounds))==4*sum(p['edge_count'] for p in plans);checks+=1
for events in rounds:assert len({v for u,v in events})==len(events) and not(set(u for u,v in events)&set(v for u,v in events));checks+=1
invalid=[([-1],[],[],(2,2,2)),([True],[0],[0],(2,2,2)),([1],[0],[0],(2,2,2)),([0],[1],[0],(2,2,2)),([0],[0],[2],(2,2,2)),([],[],[],(2,True,2))]
for args in invalid:
 try:ns['build_euler_plan'](*args)
 except ValueError:checks+=1
 else:raise AssertionError(('invalid accepted',args))
proof={'status':'ACTUAL_PES_PRODUCTION_AST_TOPOLOGY_AND_LIST_FORWARD_VALIDATED_NOT_TORCH','helper_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'actual_checks':checks,'single_batch_forward_cases':5,'mixed_batch_forward_cases':1,'invalid_cases':6,'topology':topology,'reverse_reset_error_discriminated':True,'scope':'Only production AST with transparent stdlib carriers/asymmetric scalar affine cell and identity activation; independent direct keyed-tree recursive Euler oracle, not producer round builder. Checks4E/eachdirection2/closedwalk/full structural source reachability, original ID support and sparse/mixed batches/current receiver update. No real Tensor/Linear/GELU/autograd/FP32/native/Jacobian/resources/efficacy.'}
if __name__=='__main__':print(json.dumps(proof,indent=2))
