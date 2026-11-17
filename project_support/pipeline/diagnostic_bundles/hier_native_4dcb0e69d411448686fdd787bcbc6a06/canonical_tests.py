"""Frozen strict controls for revision1, not a replacement for old failures."""
import ast
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
assert subprocess.check_output(['hostname'],text=True,timeout=5).strip()=='sysu311-MS-7C59'
import torch
torch.set_num_threads(1)
core={}
exec(compile(CANONICAL_SOURCE,'<canonical-axis-revision1>','exec'),core)
reference={}
exec(compile(REFERENCE_SOURCE,'<unchanged-frozen-dense-reference>','exec'),reference)
fixture_node=next(node for node in ast.parse(FIXTURE_SOURCE).body if isinstance(node,ast.FunctionDef) and node.name=='fixture')
fixture_namespace={'torch':torch}
exec(compile(ast.fix_missing_locations(ast.Module(body=[fixture_node],type_ignores=[])),'<unchanged-frozen-fixture>','exec'),fixture_namespace)
canonical=core['canonical']
dense=reference['dense_reference']
fixture=fixture_namespace['fixture']
checks={}
metrics={}
def evaluate(function,data,project=None):
    p,banks,leaf,parent1,parent2,logits,query=data
    variables=[v.detach().clone().requires_grad_() for v in (p,*banks,logits)]
    output=function(variables[0],variables[1:4],leaf,parent1,parent2,variables[-1].softmax(-1))
    if project is not None:output=project(output)
    readout=query@output.T
    loss=output.square().mean()+readout.square().mean()
    gradients=torch.autograd.grad(loss,variables)
    assert torch.isfinite(output).all() and all(torch.isfinite(g).all() for g in gradients)
    return output.detach(),[g.detach() for g in gradients],readout.detach()
def compare(label,data,tolerance,project=None):
    actual,grads,readout=evaluate(canonical,data,project)
    expected,ref_grads,ref_readout=evaluate(dense,data,project)
    errors={'output':float((actual-expected).abs().max()),
        'fixed_query_logits':float((readout-ref_readout).abs().max()),
        'input_gradients':[float((a-b).abs().max()) for a,b in zip(grads,ref_grads)]}
    metrics[label]=errors
    checks[label]=max(errors['output'],errors['fixed_query_logits'],*errors['input_gradients'])<=tolerance
    masks=core['support_masks'](data[2],data[3],data[4],[len(b) for b in data[1]])
    tree=reference['supports'](data[2],data[3],data[4])
    for level,mask in enumerate(masks):
        frozen=torch.zeros_like(mask)
        for leaf,selected in tree.items():
            row=torch.nonzero(data[2]==leaf,as_tuple=False).flatten()
            frozen[row[:,None],selected[level][None,:]]=True
        checks[label+'_support'+str(level)]=bool(torch.equal(mask,frozen))
    return actual

for dtype,label,tolerance in ((torch.float32,'float32',1e-6),(torch.float64,'float64',1e-10)):
    for large in (False,True):compare(label+('_64_16_4' if large else '_16_4_2'),fixture(dtype,large),tolerance)

p,banks,leaf,p1,p2,logits,query=fixture(torch.float32,True)
weights=logits.softmax(-1)
with torch.no_grad():
    baseline=canonical(p,banks,leaf,p1,p2,weights)
    padded=[bank.clone() for bank in banks]
    for bank in padded:bank[-2:]=10000
    ppad=p.clone()
    ppad[len(leaf):]=10000
    out=canonical(ppad,padded,leaf,p1,p2,weights)
    checks['padding_exact_zero']=bool(torch.equal(out,baseline)) and bool((out[len(leaf):]==0).all())
    for level in range(3):
        selected=reference['supports'](leaf,p1,p2)[int(leaf[0])][level]
        changed=[bank.clone() for bank in banks]
        changed[level][selected[0]]+=.25
        out=canonical(p,changed,leaf,p1,p2,weights)
        value=float(((query@out.T)[:,0]-(query@baseline.T)[:,0]).abs().max())
        metrics['included_level'+str(level)]=value
        checks['included_level'+str(level)]=value>1e-6
    changed=[bank.clone() for bank in banks]
    changed[2][p2[p1[leaf[0]]]]+=100
    out=canonical(p,changed,leaf,p1,p2,weights)
    checks['excluded_point0_exact']=bool(torch.equal(out[0],baseline[0]))
    def readout(message,frozen_message=None):
        feature=p+(message if frozen_message is None else frozen_message)
        return query@feature.T
    checks['blocked_readout_exact']=bool(torch.equal(readout(out,baseline),readout(baseline,baseline)))
    checks['unblocked_readout_active']=float((readout(out)-readout(baseline)).abs().max())>1e-6
    permutation=torch.arange(len(p1)-1,-1,-1)
    permuted=[torch.cat([banks[0][permutation],banks[0][-2:]]),banks[1],banks[2]]
    relabeled=canonical(p,permuted,torch.argsort(permutation)[leaf],p1[permutation],p2,weights)
    metrics['leaf_relabel_delta']=float((relabeled-baseline).abs().max())
    checks['leaf_relabel_original1e6']=metrics['leaf_relabel_delta']<=1e-6
    one=canonical(p[:2],[bank[:1] for bank in banks],torch.zeros(1,dtype=torch.long),torch.zeros(1,dtype=torch.long),torch.zeros(1,dtype=torch.long),weights[:2])
    checks['single_and_empty_roles_finite']=bool(torch.isfinite(one).all()) and bool((one[1]==0).all())
    empty=canonical(p[:2],[bank[:1] for bank in banks],torch.zeros(0,dtype=torch.long),torch.zeros(1,dtype=torch.long),torch.zeros(1,dtype=torch.long),weights[:2])
    checks['empty_scene_zero']=bool((empty==0).all())

ROOT=Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
capture_path=ROOT.parent/'pipeline/server3_fallback_abdff23d/native_capture.pt'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
assert sha(capture_path)=='e4a7e63605bb60d9e9a543cd22ac2635a37627ee3db22d870122e1a254342e08'
sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
source=ROOT/'framework/model/Quard_model'/MODEL/'hier_postprocess.py'
assert sha(source)=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
spec=importlib.util.spec_from_file_location('canonical_native_frozen_hierarchy',str(source))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
capture=torch.load(capture_path,map_location='cpu')
native_rows=[]
for record in capture['records']:
    if record['trial']!=0:continue
    points,query,mask,tokens,children,ids=record['cluster']['inputs']
    net=module.C2F_ClusterAttn_CTF_HCG_CSORT(d_model=256,nhead=8,cluster_layer_nums=[256,64,8],per_layer_topk_list=[32,16,8],dropout=0).eval()
    net.load_state_dict(record['cluster']['state'],strict=True)
    with torch.no_grad():
        refined=[cf+net.cluster_ffn[i](net.cluster_ffn_norm[i](cf)) for i,cf in enumerate(tokens)]
        gate_logits=net.level_gate(torch.cat([points,points.mean(1,keepdim=True).expand_as(points)],-1))
    for b in range(points.shape[0]):
        leaf,parent1,parent2=[ids[level][b].long() for level in range(3)]
        n=len(leaf)
        data=(points[b],[bank[b] for bank in refined],leaf,parent1,parent2,gate_logits[b],record['head']['normalized_query'][b])
        def project(value):
            value=net.point_out_proj(value)
            value=value.clone()
            value[n:]=0
            value=net.message_norm(value)
            return torch.cat([value[:n],value[n:]*0])
        label='native_pair'+str(record['pair'])+'_expression'+str(b)
        compare(label,data,1e-6,project)
        masks=core['support_masks'](leaf,parent1,parent2,[len(bank) for bank in data[1]])
        native_rows.append({'pair':record['pair'],'expression':b,'valid_points':n,
            'strict_passed':checks[label],'errors':metrics[label],
            'active_edges':sum(int(mask.sum()) for mask in masks),'computed_edges':n*sum(len(bank) for bank in data[1])})
assert len(native_rows)==16
checks['cuda_not_initialized']=not torch.cuda.is_initialized()
failures=[key for key,value in checks.items() if not value]
print('HIER_NATIVE_RESULT='+json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),
    'revision':1,'check_count':len(checks),'passed':len(checks)-len(failures),'failures':failures,
    'core_sha256':hashlib.sha256(CANONICAL_SOURCE.encode()).hexdigest(),
    'reference_sha256':hashlib.sha256(REFERENCE_SOURCE.encode()).hexdigest(),
    'checks':checks,'metrics':metrics,'native_rows':native_rows,'native_expression_count':16,
    'original12failures_reclassified':False,'compacted_native4failures_reclassified':False,
    'chunk_checkpoint_paths_tested':False,'new_model_backward':False,'optimizer_steps':0,'cuda_initialized':False,
    'scope':'Revision1 canonical-axis correctness only, original fixtures and all16native learned inputs; not full model, training efficacy or efficiency admission.'}))
raise SystemExit(0 if not failures else 1)
