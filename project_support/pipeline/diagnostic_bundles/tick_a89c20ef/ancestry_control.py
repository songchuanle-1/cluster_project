"""Test actual parent-child incidence against the aggregation tree."""
import ast
from datetime import datetime,timezone
from ops import *

guard(600)
cid='hierarchical-ancestry-cover-audit'
protocol={'candidate_id':cid,'preregistered_at':datetime.now(timezone.utc).isoformat(),
 'hypothesis':'The current partitioner child maps may describe centroid-nearest representatives instead of all fine tokens that generated a coarse token. If so, current CSORT is not the documented coarse-versus-child-average orthogonality control. This is a source/gradient binding audit, not proof of training harm or authorization to reopen HDS/FLE.',
 'matched_control':'Same actual aggregate_cluster and actual partitioner.forward with deterministic frozen memberships; compare original child-map consumer against the complete descendant incidence implied by the same memberships. No new partition, loss weight, labels or validation selection.',
 'first_test':'Execute actual source CPU float64 on8fine/2coarse cells, compare link coverage and original versus canonical child-average orthogonality.',
 'next_action':'If a source discrepancy exists, quantify its coverage and task/regularizer gradient distinction on the fixed native TRAIN capture before calling it a bug or training intervention.',
 'scientific_admission':False,'tolerance':1e-6}
save('ancestry_protocol.json',protocol)
w=tick.load(ROOT/'pipeline/research_work.json')
assert not any(c['id']==cid for c in w['candidates'])
w['candidates'].append({'id':cid,'stage':'diagnosis','hypothesis':protocol['hypothesis'],'matched_control':protocol['matched_control'],'next_action':protocol['first_test'],'evidence':[evidence(OUT/'ancestry_protocol.json')],'created_at':protocol['preregistered_at']})
tick.save(ROOT/'pipeline/research_work.json',w)
path=ROOT/'Cluster/framework/model/Quard_model'/NAME/'hier_postprocess.py'
tree=ast.parse(path.read_text(encoding='utf-8-sig'))
body=[]
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name=='aggregate_cluster':body.append(node)
    if isinstance(node,ast.ClassDef) and node.name=='PointCloudPartitioner':
        node.body=[m for m in node.body if isinstance(m,ast.FunctionDef) and m.name in ('__init__','forward')]
        body.append(node)
    if isinstance(node,ast.ClassDef) and node.name=='C2F_ClusterAttn_CTF_HCG_CSORT':
        node.bases=[ast.Attribute(value=ast.Name(id='nn',ctx=ast.Load()),attr='Module',ctx=ast.Load())]
        node.body=[m for m in node.body if isinstance(m,ast.FunctionDef) and m.name in ('_safe_norm','_cross_scale_orth_loss')]
        body.append(node)
source=ast.unparse(ast.Module(body=body,type_ignores=[]))
program='''import os,socket,json
assert socket.gethostname()=='dl04-MS-7E06'
os.environ['CUDA_VISIBLE_DEVICES']=''
import torch
from torch import nn
from torch_scatter import scatter_mean,scatter_max
exec(SOURCE)
partitioner=PointCloudPartitioner([8,2,1])
def deterministic_layer(pos,num,device):
    ids=torch.arange(len(pos),device=device) if num==8 else torch.arange(len(pos),device=device)//4 if num==2 else torch.zeros(len(pos),device=device,dtype=torch.long)
    return aggregate_cluster(pos,ids),ids
partitioner.cluster_layer=deterministic_layer
positions=torch.tensor([[v,0.,0.] for v in (0.,1.,2.,3.,10.,11.,12.,13.)],dtype=torch.float64)
ids,maps=partitioner(positions,torch.tensor([0,8]))
mapping=maps[0][0]
actual=[[] for _ in range(2)]
for fine,coarse_list in mapping.items():
    for coarse in coarse_list:actual[coarse].append(fine)
expected=[(ids[1][0]==coarse).nonzero().flatten().tolist() for coarse in range(2)]
fine=torch.tensor([[[2.,0.],[0.,2.],[2.,0.],[2.,0.],[2.,0.],[0.,2.],[2.,0.],[2.,0.]]],dtype=torch.float64)
coarse=aggregate_cluster(fine[0],ids[1][0]).unsqueeze(0)
original=C2F_ClusterAttn_CTF_HCG_CSORT._cross_scale_orth_loss(coarse,fine,maps[0])
canonical={}
for c,children in enumerate(expected):
    for f in children:canonical.setdefault(f,[]).append(c)
reference=C2F_ClusterAttn_CTF_HCG_CSORT._cross_scale_orth_loss(coarse,fine,[canonical])
print(json.dumps({'source_cpu_calls':{'partitioner':1,'orthogonality':2},'cuda_calls':0,'original_children':actual,'generating_children':expected,'covered_edges':sum(len(x) for x in actual),'actual_tree_edges':8,'original_orthogonality_loss':float(original),'canonical_child_average_loss':float(reference),'original_map_is_complete_tree':actual==expected,'training_harm_established':False}))
'''.replace('SOURCE',repr(source))
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B -c '+shlex.quote(program)
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],120)
save('ancestry_source_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
assert result.returncode==0,result.stderr
value=json.loads(result.stdout)
value['source']=evidence(path)
save('ancestry_source_control.json',value)
advance([OUT/'ancestry_source_control.json',OUT/'ancestry_source_execution.json'],candidate_id=cid,next_action=protocol['next_action'],failure_scope='inconclusive',gate_result='Original child map differs from generating tree on synthetic source control;native relevance and intended design remain unverified')
print(json.dumps(value,ensure_ascii=False))
