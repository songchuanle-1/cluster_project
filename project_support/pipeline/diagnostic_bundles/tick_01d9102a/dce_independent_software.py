"""Pure-stdlib execution of actual DCE production AST with transparent list tensors.
Not Torch, real GELU/Linear, autograd, native, or resource evidence.
"""
from pathlib import Path
from types import SimpleNamespace
from itertools import product
import ast,math,json,hashlib
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SOURCE=HERE/'new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_dce/directed_cavity.py'
def prod(x):
 v=1
 for a in x:v*=a
 return v
class T:
 def __init__(self,values,shape=None):
  if shape is None:
   def form(x):return (len(x),)+form(x[0]) if isinstance(x,list) and x else ((0,) if isinstance(x,list) else ())
   shape=form(values)
   def flat(x):return sum((flat(v) for v in x),[]) if isinstance(x,list) else [x]
   values=flat(values)
  self.v=list(values);self.shape=tuple(shape);self.ndim=len(self.shape);self.device='cpu';self.dtype='stdlib-real';assert len(self.v)==prod(self.shape)
 def reshape(self,*shape):
  shape=list(shape[0] if len(shape)==1 and isinstance(shape[0],(tuple,list)) else shape)
  if -1 in shape:shape[shape.index(-1)]=len(self.v)//prod([x for x in shape if x!=-1])
  return T(self.v,shape)
 def new_zeros(self,shape):return T([0.0]*prod(shape),shape)
 def new_tensor(self,x):return T(x)
 def detach(self):return self
 def cpu(self):return self
 def tolist(self):
  def f(vals,shape):
   if not shape:return vals[0]
   n=prod(shape[1:]);return [f(vals[i*n:(i+1)*n],shape[1:]) for i in range(shape[0])]
  return f(self.v,self.shape)
 def index_select(self,dim,index):
  assert dim==0;n=prod(self.shape[1:]);return T([a for i in index.v for a in self.v[int(i)*n:(int(i)+1)*n]],(len(index.v),)+self.shape[1:])
 def index_add(self,dim,index,source):
  assert dim==0;n=prod(self.shape[1:]);out=list(self.v)
  for a,i in enumerate(index.v):
   for j in range(n):out[int(i)*n+j]+=source.v[a*n+j]
  return T(out,self.shape)
 def index_copy(self,dim,index,source):
  assert dim==0;n=prod(self.shape[1:]);assert source.shape==(len(index.v),)+self.shape[1:];out=list(self.v)
  for a,i in enumerate(index.v):out[int(i)*n:(int(i)+1)*n]=source.v[a*n:(a+1)*n]
  return T(out,self.shape)
 def unsqueeze(self,dim):assert dim==-1;return T(self.v,self.shape+(1,))
 def __getitem__(self,key):
  assert isinstance(key,slice);ids=list(range(self.shape[0]))[key];return self.index_select(0,T(ids))
 def flip(self,axes):assert axes==[0];return self.index_select(0,T(list(reversed(range(self.shape[0])))))
 def op(self,other,fn):
  if not isinstance(other,T):return T([fn(v,other) for v in self.v],self.shape)
  n=max(self.ndim,other.ndim);sa=(1,)*(n-self.ndim)+self.shape;sb=(1,)*(n-other.ndim)+other.shape;outshape=tuple(max(a,b) for a,b in zip(sa,sb));assert all(a==b or a==1 or b==1 for a,b in zip(sa,sb))
  def get(t,shape,coords):
   ix=0
   for size,c in zip(shape,coords):ix=ix*size+(0 if size==1 else c)
   return t.v[ix]
  return T([fn(get(self,sa,c),get(other,sb,c)) for c in product(*(range(k) for k in outshape))],outshape)
 def __add__(self,x):return self.op(x,lambda a,b:a+b)
 def __mul__(self,x):return self.op(x,lambda a,b:a*b)
 def __truediv__(self,x):return self.op(x,lambda a,b:a/b)
def cat(values,dim):
 if dim==0:return T([a for v in values for a in v.v],(sum(v.shape[0] for v in values),)+values[0].shape[1:])
 assert dim==-1 and all(v.ndim==2 for v in values)
 return T([a for i in range(values[0].shape[0]) for v in values for a in v.v[i*v.shape[1]:(i+1)*v.shape[1]]],(values[0].shape[0],sum(v.shape[1] for v in values)))
def cumsum(value,dim):
 assert dim==0 and value.ndim==2;acc=[0.0]*value.shape[1];out=[]
 for i in range(value.shape[0]):
  acc=[a+b for a,b in zip(acc,value.v[i*value.shape[1]:(i+1)*value.shape[1]])];out.extend(acc)
 return T(out,value.shape)
torch=SimpleNamespace(tensor=lambda x,**kwargs:T(x),cat=cat,cumsum=cumsum,long='index')
module=ast.parse(SOURCE.read_text(encoding='utf8'));fns=[x for x in module.body if isinstance(x,ast.FunctionDef)]
cls=next(x for x in module.body if isinstance(x,ast.ClassDef));fns.append(next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='forward'))
ns={'torch':torch};exec(compile(ast.fix_missing_locations(ast.Module(body=fns,type_ignores=[])),str(SOURCE),'exec'),ns)
coefs={'up':(2,3),'down_root':(5,7),'down_middle':(11,13),'read_fine':(17,19),'read_middle':(23,29),'read_coarse':(31,37)}
def scalar(role,a,b):return coefs[role][0]*a+coefs[role][1]*b
def mapping(role):return lambda x:T([scalar(role,*x.v[i:i+2]) for i in range(0,len(x.v),2)],(x.shape[0],1))
owner=SimpleNamespace(channels=1,activation=lambda x:x,**{k:mapping(k) for k in coefs})
def avg(v):return sum(v)/len(v) if v else 0.0
def oracle(vals,ids,widths):
 fids=sorted(set(ids[0]));mids=sorted({ids[1][i] for i in fids});cids=sorted({ids[2][j] for j in mids});f=lambda j:[i for i in fids if ids[1][i]==j];m=lambda k:[j for j in mids if ids[2][j]==k]
 up={j:scalar('up',vals[1][j],avg([vals[0][i] for i in f(j)])) for j in mids}
 root={j:scalar('down_root',vals[2][ids[2][j]],avg([up[h] for h in m(ids[2][j]) if h!=j])) for j in mids}
 down={i:scalar('down_middle',vals[1][ids[1][i]],avg([root[ids[1][i]]]+[vals[0][h] for h in f(ids[1][i]) if h!=i])) for i in fids}
 out=[[0.0]*k for k in widths]
 for i in fids:out[0][i]=scalar('read_fine',vals[0][i],down[i])
 for j in mids:out[1][j]=scalar('read_middle',vals[1][j],avg([root[j]]+[vals[0][i] for i in f(j)]))
 for k in cids:out[2][k]=scalar('read_coarse',vals[2][k],avg([up[j] for j in m(k)]))
 return out
cases=[('empty',([],[],[]),(4,3,2)),('single',([2,2],[0,0,1],[0,1]),(4,3,2)),('unequal_siblings',([0,1,2,3],[0,0,0,2],[0,1,0]),(5,4,2)),('holes_multiroot',([1,3,4,1],[0,2,1,2,3],[0,1,1,0]),(6,5,3)),('samefine_duplicatepoints',([3,1,1,3],[0,2,1,2],[1,0,1]),(5,4,3))]
count=0
for name,ids,widths in cases:
 vals=[[float(1+l*10+i) for i in range(k)] for l,k in enumerate(widths)]
 levels=[T([[[v] for v in bank]]) for bank in vals];members=[[T(ids[l])] for l in range(3)]
 out=ns['forward'](owner,levels,members);want=oracle(vals,ids,widths)
 for l in range(3):
  assert out[l].shape==(1,widths[l],1)
  assert all(math.isclose(a,z,rel_tol=1e-12,abs_tol=1e-12) for a,z in zip(out[l].v,want[l])),(name,l,out[l].v,want[l]);count+=1
 plan=ns['build_cavity_plan'](*ids,widths);assert len(plan['fine_ids'])==len(set(ids[0]));count+=1
# Actual mixed-batch offsets, including an empty first row, independently checked against per-row direct edges.
widths=(6,5,3);batch_ids=[([],[],[]),cases[3][1]];values=[[[float(1+b*100+l*10+i) for i in range(k)] for l,k in enumerate(widths)] for b in range(2)]
levels=[T([[[v] for v in values[b][l]] for b in range(2)]) for l in range(3)];members=[[T(batch_ids[b][l]) for b in range(2)] for l in range(3)];actual=ns['forward'](owner,levels,members)
for l in range(3):
 wanted=[v for b in range(2) for v in oracle(values[b],batch_ids[b],widths)[l]];assert all(math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12) for x,y in zip(actual[l].v,wanted));count+=1
# Direct primitive check makes reverse-edge exclusion visible for unequal groups/singletons.
actual=ns['exclusive_group_sums'](T([[2.],[3.],[7.],[11.]]),[[0,2,3],[1]]);assert actual.v==[18.,0.,13.,9.];count+=1
bad=[([-1],[],[],(2,2,2)),([True],[0],[0],(2,2,2)),([1],[0],[0],(2,2,2)),([0],[1],[0],(2,2,2)),([0],[0],[2],(2,2,2)),([],[],[],(2,True,2))]
for args in bad:
 try:ns['build_cavity_plan'](*args)
 except ValueError:count+=1
 else:raise AssertionError(('invalid accepted',args))
proof={'status':'ACTUAL_PRODUCTION_DCE_AST_WITH_STDLIB_LIST_CARRIERS_AND_DIRECT_EDGE_ORACLE_VALIDATED_NOT_TORCH','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'checks':count,'actual_forward_cases':[x[0] for x in cases]+['two_batch_empty_then_nonempty'],'invalid_cases':len(bad),'scope':'Exec actual production plan/mean/exclusive/forward AST. Direct receiver-edge oracle uses explicit neighbor lists, no prefix/suffix/cached grouped algorithm. Role-specific scalar affine stand-ins and identity activation expose originalID, offset, degree and reverse-edge errors. No Torch/realLinear/GELU/autograd/native/FP32/resource or scientific PASS.'}
if __name__=='__main__':print(json.dumps(proof,indent=2))
