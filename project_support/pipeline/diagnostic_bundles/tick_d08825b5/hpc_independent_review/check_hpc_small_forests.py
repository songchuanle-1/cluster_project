"""Small independent production-AST forest/solve audit; stdlib only, never Torch."""
from pathlib import Path
from fractions import Fraction as F
import ast,copy,hashlib,json,datetime
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_d08825b5/new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hpc/hierarchy_resolvent.py'

def cv(x):
 if isinstance(x,list):return [cv(v) for v in x]
 return x if isinstance(x,F) else F(str(x))
def calc(a,b,op):
 if isinstance(a,list):
  if not isinstance(b,list):return [calc(x,b,op) for x in a]
  if len(b)==1 and len(a)!=1:return [calc(x,b[0],op) for x in a]
  if len(a)!=len(b):raise AssertionError('standin shape mismatch')
  return [calc(x,y,op) for x,y in zip(a,b)]
 if isinstance(b,list):raise AssertionError('standin scalar mismatch')
 return op(a,cv(b))
class Rows:
 device='stdlib_only'
 def __init__(self,x):self.data=cv(x)
 @property
 def shape(self):
  z=self.data;v=[]
  while isinstance(z,list):
   v.append(len(z));z=z[0] if z else None
  return tuple(v)
 def __getitem__(self,n):return Rows(self.data[n])
 def __add__(self,b):return Rows(calc(self.data,b.data if isinstance(b,Rows) else b,lambda x,y:x+y))
 def __mul__(self,b):return Rows(calc(self.data,b.data if isinstance(b,Rows) else b,lambda x,y:x*y))
 def __truediv__(self,b):return Rows(calc(self.data,b.data if isinstance(b,Rows) else b,lambda x,y:x/y))
 def new_tensor(self,x):return Rows(x)
 def unsqueeze(self,dim):
  assert dim==-1;return Rows([[x] for x in self.data])
 def index_select(self,dim,ids):
  assert dim==0;return Rows([self.data[i] for i in ids])
 def index_add(self,dim,ids,values):
  assert dim==0 and len(ids)==len(values.data);v=copy.deepcopy(self.data)
  for i,row in zip(ids,values.data):v[i]=calc(v[i],row,lambda x,y:x+y)
  return Rows(v)
 def index_copy(self,dim,ids,values):
  assert dim==0 and len(ids)==len(values.data);v=copy.deepcopy(self.data)
  for i,row in zip(ids,values.data):v[i]=copy.deepcopy(row)
  return Rows(v)
class Standin:
 long='stdlib_metadata'
 @staticmethod
 def tensor(x,**kwargs):return list(x)
 @staticmethod
 def stack(rows,dim):
  assert dim==0;return Rows([x.data for x in rows])

text=SOURCE.read_text('utf8');tree=ast.parse(text);selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['_checked_ids','build_resolvent_plan','solve_resolvent_levels']]
ns={'torch':Standin};exec(compile(ast.Module(body=selected,type_ignores=[]),str(SOURCE),'exec'),ns)
build=ns['build_resolvent_plan'];solve=ns['solve_resolvent_levels'];checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def dense_original_ids(point,f2m,m2c,sizes,full):
 ids=[sorted(set(point))];ids.append(sorted({f2m[i] for i in ids[0]}));ids.append(sorted({m2c[j] for j in ids[1]}))
 nodes=[(l,i) for l in range(3) for i in ids[l]];pos={node:k for k,node in enumerate(nodes)};n=len(nodes)
 a=[[F(i==j) for j in range(n)] for i in range(n)]
 for l,parents in [(0,f2m),(1,m2c)]:
  for i in ids[l]:
   j=parents[i];u,v=pos[(l,i)],pos[(l+1,j)]
   a[u][u]+=1;a[v][v]+=1;a[u][v]-=1;a[v][u]-=1
 out=copy.deepcopy(full)
 for c in range(2):
  aug=[a[k][:]+[full[l][i][c]] for k,(l,i) in enumerate(nodes)]
  for k in range(n):
   pivot=aug[k][k];assert pivot>0;aug[k]=[x/pivot for x in aug[k]]
   for j in range(n):
    if j!=k:
     factor=aug[j][k];aug[j]=[x-factor*y for x,y in zip(aug[j],aug[k])]
  for k,(l,i) in enumerate(nodes):out[l][i][c]=aug[k][-1]
 return out,ids
cases=[('empty',[[],[0,1],[0,1]],[2,2,2]),('one_chain',[[0],[0],[0]],[1,1,1]),('two_fine_siblings',[[0,1],[0,0],[0]],[2,1,1]),('four_fine_one_middle',[[0,1,2,3],[0,0,0,0],[0]],[4,1,1]),('two_roots',[[0,1],[0,1],[0,1]],[2,2,2]),('holes_duplicate_points',[[1,1,1,4,6],[0,3,1,2,3,0,1],[2,0,1,2]],[7,4,3])]
max_error=0.0
for label,(point,f2m,m2c),sizes in cases:
 plan=build(point,f2m,m2c,sizes);full=[[[F((l+1)*100+i*7+c,11) for c in range(2)] for i in range(sizes[l])] for l in range(3)]
 actual=[x.data[0] for x in solve([Rows([v]) for v in full],[plan])];expected,ids=dense_original_ids(point,f2m,m2c,sizes,full)
 ck(label+': exact support from original composed IDs',[plan[k] for k in ['fine_ids','middle_ids','coarse_ids']]==ids)
 error=max([float(abs(actual[l][i][c]-expected[l][i][c])) for l in range(3) for i in range(sizes[l]) for c in range(2)] or [0]);max_error=max(max_error,error)
 ck(label+': actual production solve equals independently assembled original-ID dense solve (software double metadata only)',error<1e-12)
 ck(label+': unsupported/pad identity retained',all(actual[l][i]==full[l][i] for l in range(3) for i in range(sizes[l]) if i not in ids[l]))
 ck(label+': original inputs unmodified',full==[[[F((l+1)*100+i*7+c,11) for c in range(2)] for i in range(sizes[l])] for l in range(3)])
# Same sized different forests in one original batch, compare each to its independently assembled block.
sizes=[7,4,3];metadata=[([1,4,6],[0,3,1,2,3,0,1],[2,0,1,2]),([0,2],[2,0,3,0,0,0,0],[1,0,2,1])]
fulls=[[[[F(1000*b+100*l+7*i+c,13) for c in range(2)] for i in range(sizes[l])] for l in range(3)] for b in range(2)]
plans=[build(*m,sizes) for m in metadata];levels=[Rows([fulls[b][l] for b in range(2)]) for l in range(3)];actual=solve(levels,plans)
for b,m in enumerate(metadata):
 expected,_=dense_original_ids(*m,sizes,fulls[b]);error=max(float(abs(actual[l].data[b][i][c]-expected[l][i][c])) for l in range(3) for i in range(sizes[l]) for c in range(2));max_error=max(max_error,error)
 ck('batch'+str(b)+': no cross-batch/parent offset leakage',error<1e-12)
invalid=[([True],[0],[0],[1,1,1]),([-1],[0],[0],[1,1,1]),([1],[0],[0],[1,1,1]),([0],[],[0],[1,1,1]),([0],[0],[],[1,1,1]),([],[0,0],[0],[1,1,1]),([],[0],[0],[1,1,-1]),([0],[1],[0],[1,1,1])]
for i,args in enumerate(invalid):
 refused=False
 try:build(*args)
 except ValueError:refused=True
 ck('invalid metadata '+str(i)+' rejected',refused)
result={'status':'INDEPENDENT_HPC_PRODUCTION_AST_SMALL_FOREST_SOFTWARE_CHECKS_PASSED_NOT_NATIVE','source_path':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'build_function_AST_sha256':hashlib.sha256(ast.dump(next(n for n in selected if n.name=='build_resolvent_plan'),include_attributes=False).encode()).hexdigest(),'solve_function_AST_sha256':hashlib.sha256(ast.dump(next(n for n in selected if n.name=='solve_resolvent_levels'),include_attributes=False).encode()).hexdigest(),'checks_count':len(checks),'checks':checks,'cases_count':len(cases),'mixed_batch_forests':2,'invalid_cases':len(invalid),'maximum_software_error':max_error,'numeric_scope':'Fraction dense Gaussian oracle assembled from original IDs; production plan contains Python float Schur metadata, represented by decimal Fractions in list standin. 1e-12 used solely as local software arithmetic comparison, not a Torch/FP32/native scientific gate.','Torch_autograd_native_resources':'NOT_RUN','limitations':['No Tensor execution or autograd is established by list standin.','No algorithm novelty, efficiency, point-mass conservation, Markov claim or accuracy evidence follows.']}
with (HERE/'software_validation.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({'checks_count':len(checks),'max_software_error':max_error,'proof_sha256':hashlib.sha256((HERE/'software_validation.json').read_bytes()).hexdigest()}))
