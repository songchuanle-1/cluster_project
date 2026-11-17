"""Small executable APF production-plan/forward list-interface checks, no Torch."""
from pathlib import Path
from fractions import Fraction as F
import ast,copy,hashlib,json,math
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_apf'
D=HERE/'staged_repository/framework/model/Quard_model'/MODEL
BASE=ROOT/'Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
checks=[]
def ck(n,x):
 if not x:raise AssertionError(n)
 checks.append(n)
def flatten(x):
 if isinstance(x,list):return [z for y in x for z in flatten(y)]
 return [x]
def shape_of(x):return (len(x),)+shape_of(x[0]) if isinstance(x,list) and x else ((0,) if isinstance(x,list) else ())
def rebuild(values,shape):
 it=iter(values)
 def go(q):return [go(q[1:]) for _ in range(q[0])] if q else next(it)
 return go(tuple(shape))
class Rows:
 device='stdlib';dtype='Fraction_software'
 def __init__(self,data,shape=None):self.data=copy.deepcopy(data);self.shape=tuple(shape) if shape is not None else shape_of(data);self.ndim=len(self.shape)
 def reshape(self,*shape):
  if len(shape)==1 and isinstance(shape[0],(tuple,list)):shape=tuple(shape[0])
  assert math.prod(shape)==math.prod(self.shape);return Rows(rebuild(flatten(self.data),shape),shape)
 def new_zeros(self,shape):return Rows(rebuild([F(0)]*math.prod(shape),shape),shape)
 def new_tensor(self,values):return Rows([F(x) for x in values])
 def unsqueeze(self,dim):assert dim==-1;return Rows([[x] for x in self.data],self.shape+(1,))
 def index_select(self,dim,idx):assert dim==0;return Rows([self.data[i] for i in idx],(len(idx),)+self.shape[1:])
 def index_add(self,dim,idx,other):
  assert dim==0;z=copy.deepcopy(self.data)
  for i,row in zip(idx,other.data):z[i]=[x+y for x,y in zip(z[i],row)]
  return Rows(z,self.shape)
 def index_copy(self,dim,idx,other):
  assert dim==0 and len(idx)==len(other.data);z=copy.deepcopy(self.data)
  for i,row in zip(idx,other.data):z[i]=copy.deepcopy(row)
  return Rows(z,self.shape)
 def __truediv__(self,other):return Rows([[x/other.data[i][0] for x in row] for i,row in enumerate(self.data)],self.shape)
 def __getitem__(self,item):
  a,b=item;assert a==slice(None);v=[row[b] for row in self.data];return Rows(v,(self.shape[0],len(v[0]) if v else 0))
class IDs:
 def __init__(self,v):self.v=v
 def detach(self):return self
 def cpu(self):return self
 def tolist(self):return list(self.v)
class Ops:
 long='ids_only'
 @staticmethod
 def tensor(x,**kw):return list(x)
 @staticmethod
 def cat(xs,dim):
  assert dim==-1;assert len({x.shape[0] for x in xs})==1
  return Rows([sum((x.data[i] for x in xs),[]) for i in range(xs[0].shape[0])],(xs[0].shape[0],sum(x.shape[1] for x in xs)))
text=(D/'ancestry_path_factor.py').read_text('utf8');tree=ast.parse(text)
fns=[n for n in tree.body if isinstance(n,ast.FunctionDef)];cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));forward_node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward');ns={'torch':Ops}
exec(compile(ast.Module(body=fns+[forward_node],type_ignores=[]),'actual_APF_production_functions','exec'),ns)
plan=ns['build_ancestry_path_plan'];forward=ns['forward'];original_mean=ns['mean_path_messages']
metadata=[([0],[0],[0],[1,1,1]),([0,2,4,4],[0,2,1,0,1],[0,0,1],[5,3,2]),([],[0,1],[0,1],[2,2,2]),([1,3],[0,1,0,1],[0,1],[4,2,2])]
for point,f2m,m2c,widths in metadata:
 v=plan(point,f2m,m2c,widths);fine=sorted(set(point))
 ck('Plan original ancestry IDs and one factor per unique true fine',v['fine_ids']==fine and v['middle_for_paths']==[f2m[i] for i in fine] and v['coarse_for_paths']==[m2c[f2m[i]] for i in fine])
 ck('Plan private grouping preserves exact path incidence/counts',sum(v['middle_path_counts'])==sum(v['coarse_path_counts'])==len(fine) and all(v['middle_ids'][j]==f2m[i] and v['coarse_ids'][k]==m2c[f2m[i]] for i,j,k in zip(fine,v['middle_parent_positions'],v['coarse_parent_positions'])))
invalid=[([True],[0],[0],[1,1,1]),([-1],[0],[0],[1,1,1]),([1],[0],[0],[1,1,1]),([0],[],[0],[1,1,1]),([0],[0],[],[1,1,1]),([],[0,0],[0],[1,1,1]),([],[0],[0],[1,1,-1]),([0],[1],[0],[1,1,1])]
for i,args in enumerate(invalid):
 refused=False
 try:plan(*args)
 except ValueError:refused=True
 ck('Invalid metadata '+str(i)+' fails closed',refused)
class Operator:
 channels=1
 def __init__(self):self.map_calls=[];self.activation_calls=0;self.mean_calls=0
 def path_map(self,x):
  self.map_calls.append(copy.deepcopy(x.data))
  return Rows([[a+2*b+3*c,5*a+7*b+11*c,13*a+17*b+19*c] for a,b,c in x.data],x.shape)
 def activation(self,x):self.activation_calls+=1;return x
cases=[('unequal_degree_holes',[([0,2,4,4],[0,2,1,0,1],[0,0,1])],[5,3,2]),('two_batch_offsets',[([0,2,4],[0,2,1,0,1],[0,0,1]),([1,3],[0,2,1,0,1],[0,0,1])],[5,3,2]),('singleton_true_triplet',[([0],[0],[0])],[1,1,1]),('all_empty',[([],[0,1,0],[0,0])],[3,2,1]),('zero_batch',[],[3,2,1])]
for label,members,widths in cases:
 B=len(members);data=[[[[F(100*b+20*l+3*i+1)] for i in range(widths[l])] for b in range(B)] for l in range(3)]
 levels=[Rows(data[l],(B,widths[l],1)) for l in range(3)];before=copy.deepcopy(data);ids=[[IDs(m[l]) for m in members] for l in range(3)];op=Operator()
 def observed_mean(messages,positions,counts):op.mean_calls+=1;return original_mean(messages,positions,counts)
 ns['mean_path_messages']=observed_mean;out=forward(op,levels,ids)
 expected=[rebuild([F(0)]*(B*widths[l]),(B,widths[l],1)) for l in range(3)];expected_inputs=[]
 for b,(point,f2m,m2c) in enumerate(members):
  mids={};coarses={}
  for i in sorted(set(point)):
   j=f2m[i];k=m2c[j];a,bv,c=(data[0][b][i][0],data[1][b][j][0],data[2][b][k][0]);expected_inputs.append([a,bv,c]);expected[0][b][i]=[a+2*bv+3*c]
   mids.setdefault(j,[]).append(5*a+7*bv+11*c);coarses.setdefault(k,[]).append(13*a+17*bv+19*c)
  for j,vals in mids.items():expected[1][b][j]=[sum(vals)/len(vals)]
  for k,vals in coarses.items():expected[2][b][k]=[sum(vals)/len(vals)]
 ck(label+': actual production forward restores original IDs and fixed means',all(x.data==expected[l] and x.shape==(B,widths[l],1) for l,x in enumerate(out)))
 ck(label+': one actual joint map/GELU and two means or no-path zero',op.map_calls==([expected_inputs] if expected_inputs else []) and op.activation_calls==int(bool(expected_inputs)) and op.mean_calls==2*int(bool(expected_inputs)))
 ck(label+': original input banks unmodified',all(x.data==before[l] for l,x in enumerate(levels)))
# Static integration/initialization checks, without importing modules.
for n in D.glob('*.py'):compile(n.read_bytes(),str(n),'exec')
ck('Eight source files compile without Torch import',len(list(D.glob('*.py')))==8)
basefiles=['__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py']
ck('Six original files including decoder byte-identical',all((D/n).read_bytes()==(BASE/n).read_bytes() for n in basefiles))
h=(D/'hier_postprocess.py').read_text('utf8');ck('Original LN and sole raw skip with new joint factor only',all(s in h for s in ['self.cluster_ffn_norm[lvl](cf)','deltas = self.path_factor(normalized, cluster_ids_list)','refined_cluster_feats = [cf + deltas[lvl]','with torch.random.fork_rng(devices=[]):','self.cluster_ffn = nn.ModuleList([nn.Identity()']))
C=256;ck('Exact source-only parameter arithmetic',3*C*(3*C)+3*C==590592 and 3*(8*C*C+5*C)==1576704 and 590592-1576704==-986112)
result={'status':'APF_PRODUCTION_PLAN_FORWARD_STDLIB_SOFTWARE_CHECKS_PASSED_NOT_NATIVE','checks_count':len(checks),'checks':checks,'valid_metadata_cases':len(metadata),'invalid_metadata_cases':len(invalid),'actual_forward_cases':len(cases),'actual_source_function_AST_hashes':{n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in fns+[forward_node]},'scope':'Actual production plan/prepare/mean/forward bodies executed with plain Fraction/list Tensor-interface and diagnostic map/identity activation stubs. This verifies incidence/gather/scatter/mean/output/call controls; does not test real nn.Linear/GELU/Torch/autograd/FP32/native/optimizer/resources. No trained or synthetic model result is produced.','parameters_source_inference':{'original_three_FFN':1576704,'new_joint_factor':590592,'delta':-986112},'Torch_native_resources':'NOT_RUN'}
with (HERE/'static_validation.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({'checks_count':len(checks),'result_sha256':hashlib.sha256((HERE/'static_validation.json').read_bytes()).hexdigest()}))
