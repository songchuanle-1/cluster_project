"""Source audit and CPU-only controls for the unchanged M95 feature path."""

import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick

TOKEN = '73d9f276d8ba41fe96f1176fb84e9ef4'
ROOT = Path('D:/project/cluster_project')
BUNDLE = Path(__file__).resolve().parent
MODEL = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
BASE = ROOT / 'Cluster/framework/model/Quard_model' / MODEL
GOAL_SHA = '6a11a897c8378c48934590d7603b5cbd18cac2d43da40690e0a7c72080f5478c'


def guard():
    owner = tick.load(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN
    assert owner['thread_id'] == os.environ['CODEX_THREAD_ID']
    assert tick.digest(ROOT / 'pipeline/goal.json') == GOAL_SHA
    assert (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds() > 180


def method(tree, cls, name):
    owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    return next(n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name == name)


def loaded(node, name):
    return any(isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id == name for n in ast.walk(node))


def source_audit():
    hierarchy = ast.parse((BASE / 'hier_postprocess.py').read_text(encoding='utf-8'))
    decoder = ast.parse((BASE / 'dec.py').read_text(encoding='utf-8'))
    ctf = method(hierarchy, 'C2F_ClusterAttn_CTF', 'forward')
    hcg = method(hierarchy, 'C2F_ClusterAttn_CTF_HCG', '_cluster_to_points')
    csort = method(hierarchy, 'C2F_ClusterAttn_CTF_HCG_CSORT', 'forward')
    enc = method(decoder, 'Encoder_layer', 'forward')
    head = method(decoder, 'Decoder_layer', 'prediction_head')
    dec = method(decoder, 'Decoder_layer', 'forward')
    statements = {n.targets[0].id: n for n in head.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
    formula = ast.unparse(statements['pred_masks'].value)
    def feature_edge(expression):
        return loaded(expression, 'mask_feats') and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'einsum' for n in ast.walk(expression))
    actual = feature_edge(statements['pred_masks'].value)
    disconnected = ast.parse("torch.zeros(1)", mode='eval').body
    identity = ast.parse(formula, mode='eval').body
    tests = {
        'ctf_query_argument_not_loaded': not loaded(ctf, 'query'),
        'ctf_child_maps_argument_not_loaded': not loaded(ctf, 'child_cluster_maps'),
        'ctf_no_scale_attention_call': not any(isinstance(n, ast.Attribute) and n.attr == '_scale_attn' for n in ast.walk(ctf)),
        'ctf_per_scale_ffn_used': any(isinstance(n, ast.Attribute) and n.attr == 'cluster_ffn' for n in ast.walk(ctf)),
        'hcg_composed_parent_gather_used': 'parent_ids.gather(0, level_ids[-1])' in ast.unparse(hcg),
        'hcg_unmasked_point_mean_present': 'point_feats.mean(dim=1, keepdim=True).expand_as(point_feats)' in ast.unparse(hcg),
        'encoder_cluster_point_writeback_used': "cluster_outputs['point']" in ast.unparse(enc) and 'inst_feats + gate * cluster_message' in ast.unparse(enc),
        'decoder_mask_head_receives_inst_feats': 'self.prediction_head(query, inst_feats, batch_mask)' in ast.unparse(dec),
        'actual_mask_feature_dependency': actual,
        'identity_source_control': feature_edge(identity) == actual,
        'disconnected_source_control_detected': not feature_edge(disconnected),
        'csort_returns_super_feature_result': any(isinstance(n, ast.Return) and isinstance(n.value, ast.Name) and n.value.id == 'result' for n in ast.walk(csort)),
    }
    assert all(tests.values()), tests
    return {'token': TOKEN, 'observed_at': datetime.now(timezone.utc).isoformat(),
            'source_sha256': {name: tick.digest(BASE / name) for name in ('dec.py', 'hier_postprocess.py')},
            'tests': tests, 'mask_formula': formula,
            'lines': {'ctf_forward': ctf.lineno, 'hcg_gather': hcg.lineno, 'csort_forward': csort.lineno, 'encoder_forward': enc.lineno, 'mask_head': head.lineno},
            'scope': 'AST dependencies of the named unchanged methods, not whole-program proof or trained effect.'}


REMOTE = r'''
import ast,copy,datetime,fcntl,hashlib,importlib.util,json,os,pathlib,subprocess,sys,types
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='1'
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
path=root/'framework/model/Quard_model'/MODEL/'hier_postprocess.py'
assert hashlib.sha256(path.read_bytes()).hexdigest()==EXPECTED_SHA
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert 'GPU-7f82edb9-f620-8045-caea-a75232265cd1' in gpu
compute=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
locks={}
for name in ('/tmp/cluster_project_gpu0_m201_migration.lock','/tmp/cluster_project_gpu0_exclusive.lock','/tmp/cluster_project_gpu0_parameter_transport.lock'):
    p=pathlib.Path(name)
    if not p.exists():
        locks[name]='missing_not_acquired'
        continue
    with p.open('rb') as handle:
        try:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            locks[name]='available'
            fcntl.flock(handle,fcntl.LOCK_UN)
        except BlockingIOError:
            locks[name]='held'
resource={'observed_at':datetime.datetime.now().astimezone().isoformat(),'gpu':gpu,'compute':compute,'locks':locks}
sys.path.insert(0,str(root))
import torch
torch.set_num_threads(1)
assert not torch.cuda.is_initialized()
spec=importlib.util.spec_from_file_location('m95_hierarchy_unchanged',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
torch.manual_seed(1999)
model=module.C2F_ClusterAttn_CTF_HCG_CSORT(d_model=256,nhead=8,cluster_layer_nums=[256,64,8],per_layer_topk_list=[32,16,8],dropout=0.0).eval()
points=torch.randn(1,6,256)
query=torch.randn(1,8,256)
tokens=[torch.randn(1,k,256) for k in (4,2,1)]
ids=[[torch.tensor([0,0,1,2,3,3])],[torch.tensor([0,0,1,1])],[torch.tensor([0,0])]]
children=[[{0:[0],1:[0],2:[1],3:[1]}],[{0:[0],1:[0]}]]
mask=torch.zeros(1,6,dtype=torch.bool)
def call(obj,p,q,t,m):
    module.reset_orth_accum()
    value=obj(p,q,m,t,children,ids)['point']
    module.get_orth_loss()
    return value
with torch.no_grad():
    a=call(model,points,query,tokens,mask)
    repeat=call(model,points,query,tokens,mask)
    query_swap=call(model,points,torch.randn_like(query),tokens,mask)
    padded=torch.cat([points,torch.zeros_like(points)],dim=1)
    padded_mask=torch.cat([mask,torch.ones_like(mask)],dim=1)
    padded_result=call(model,padded,query,tokens,padded_mask)[:,:6]
    changed=[t.clone() for t in tokens]
    changed[0]=changed[0].roll(1,dims=1)
    permuted=call(model,points,query,changed,mask)
    zero_points=torch.zeros_like(points)
    zero_a=call(model,zero_points,query,tokens,mask)
    zero_b=call(model,torch.cat([zero_points,zero_points],dim=1),query,tokens,padded_mask)[:,:6]
# One diagnostic-only counterfactual; production source and config are untouched.
tree=ast.parse(path.read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='C2F_ClusterAttn_CTF_HCG')
node=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_cluster_to_points'))
assignments=[n for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='global_mean' for t in n.targets)]
assert len(assignments)==1
assignments[0].value=ast.parse('torch.stack([point_feats[b, ~point_mask[b]].mean(dim=0) if (~point_mask[b]).any() else torch.zeros_like(point_feats[b, 0]) for b in range(point_feats.shape[0])], dim=0).unsqueeze(1).expand_as(point_feats)',mode='eval').body
code=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
scope={'torch':torch}
exec(compile(code,'<masked-mean-diagnostic-only>','exec'),scope)
control=copy.deepcopy(model)
control._cluster_to_points=types.MethodType(scope['_cluster_to_points'],control)
with torch.no_grad():
    corrected_a=call(control,points,query,tokens,mask)
    corrected_b=call(control,padded,query,tokens,padded_mask)[:,:6]
    fixed_query=torch.randn(1,8,256)
    fixed_query=torch.nn.functional.normalize(fixed_query,dim=-1)
    logit_gap=(torch.einsum('bnd,bmd->bnm',fixed_query,a)-torch.einsum('bnd,bmd->bnm',fixed_query,padded_result)).abs().max().item()
q=query.clone().requires_grad_()
t=[value.clone().requires_grad_() for value in tokens]
pred=call(model,points,q,t,mask)
grads=torch.autograd.grad((pred*torch.randn_like(pred)).sum(),[q,*t],allow_unused=True)
metrics={'repeat_delta':(a-repeat).abs().max().item(),'query_swap_delta':(a-query_swap).abs().max().item(),
         'fine_token_permutation_delta':(a-permuted).abs().max().item(),
         'padding_valid_feature_delta':(a-padded_result).abs().max().item(),
         'padding_fixed_query_logit_delta':logit_gap,
         'zero_point_mean_padding_control_delta':(zero_a-zero_b).abs().max().item(),
         'masked_mean_padding_control_delta':(corrected_a-corrected_b).abs().max().item(),
         'unpadded_counterfactual_delta':(a-corrected_a).abs().max().item(),
         'query_gradient_unused':grads[0] is None,
         'cluster_token_gradient_norms':[value.norm().item() if value is not None else None for value in grads[1:]]}
checks={'repeat_exact':metrics['repeat_delta']==0,'query_blind_given_bank':metrics['query_swap_delta']==0 and metrics['query_gradient_unused'],
        'token_path_active':metrics['fine_token_permutation_delta']>1e-6 and all(value and value>0 for value in metrics['cluster_token_gradient_norms']),
        'zero_mean_negative_control':metrics['zero_point_mean_padding_control_delta']<=1e-6,
        'masked_mean_control_padding_invariant':metrics['masked_mean_padding_control_delta']<=1e-6,
        'counterfactual_agrees_unpadded':metrics['unpadded_counterfactual_delta']<=1e-6}
assert all(checks.values()),(checks,metrics)
assert not torch.cuda.is_initialized()
print(json.dumps({'resource':resource,'metrics':metrics,'checks':checks,'cuda_initialized':False,
 'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'sample_scope':'One constructed CPU module fixture, random fixed seed1999 weights; 6valid superpoints/4-2-1 fixture tokens; NOT native TRAIN data or checkpoint.',
 'counterfactual_scope':'Exactly one global_mean expression changed in an in-memory method clone, diagnostic only. Not a new model or tuning proposal.',
 'optimizer_steps':0,'gpu_tests':0,'efficacy':'unknown','native_backward_gate':'not passed'}))
'''


def main():
    guard()
    static = source_audit()
    tick.save(BUNDLE / 'source_audit_v2.json', static)
    remote = 'MODEL='+repr(MODEL)+'\nEXPECTED_SHA='+repr(static['source_sha256']['hier_postprocess.py'])+'\n'+REMOTE
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12','server-4','/home/songcl/.conda/envs/project_cluster/bin/python','-B','-'],input=remote,text=True,encoding='utf-8',capture_output=True,timeout=150)
    guard()
    tick.save(BUNDLE / 'cpu_attempt_v2.json', {'token':TOKEN,'observed_at':datetime.now(timezone.utc).isoformat(),'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    if result.returncode:
        print(result.stderr[-5000:])
        raise SystemExit(result.returncode)
    data=json.loads(result.stdout)
    tick.save(BUNDLE / 'cpu_controls_v2.json', {'token':TOKEN,**data})
    print(json.dumps({'static_tests':len(static['tests']),**data},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
