"""Static independence and CPU adapter smoke; never a native admission gate."""
import ast
from datetime import datetime, timezone
import json
import os
import subprocess
from run import BUNDLE, ROOT, TOKEN, guard, tick

guard()
parent = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
name = parent + '_hds_canon_r1'
models = ROOT / 'Cluster/framework/model/Quard_model'
source = models / name
original = models / parent
assert source.resolve() != original.resolve()
assert not source.is_symlink()
files = sorted(source.glob('*.py'))
assert len(files) == len(list(original.glob('*.py'))) + 1 == 8
for path in files:
    compile(path.read_text(encoding='utf-8'), str(path), 'exec')
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module and parent in node.module)
        if isinstance(node, ast.Import):
            assert not any(parent in item.name for item in node.names)
    if path.name not in ('hier_postprocess.py', 'hierarchical_readout.py'):
        assert path.read_bytes() == (original / path.name).read_bytes()
assert (source / 'hierarchical_readout.py').read_bytes() == (BUNDLE / 'canonical_readout.py').read_bytes()
config = ROOT / ('Cluster/configs/Quard/ctf_hcg_csort_hds_canon_r1/' + name + '.yaml')
original_config = ROOT / ('Cluster/configs/Quard/ctf_hcg_csort/' + parent + '.yaml')
assert config.read_bytes() == original_config.read_bytes()
old_ast = ast.parse((original / 'hier_postprocess.py').read_text(encoding='utf-8'))
new_text = (source / 'hier_postprocess.py').read_text(encoding='utf-8')
new_ast = ast.parse(new_text)
old_classes = {node.name: node for node in old_ast.body if isinstance(node, ast.ClassDef)}
new_classes = {node.name: node for node in new_ast.body if isinstance(node, ast.ClassDef)}
for key in old_classes:
    if key != 'C2F_ClusterAttn_CTF_HCG':
        assert ast.dump(old_classes[key]) == ast.dump(new_classes[key])
dirty = ROOT / 'Cluster/scripts/validate_pdc_20261009.py'
assert tick.digest(dirty) == '00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26'
classes = ('C2F_ClusterAttn_Lite', 'C2F_ClusterAttn_CTF', 'C2F_ClusterAttn_CTF_HCG', 'C2F_ClusterAttn_CTF_HCG_CSORT')
selected = ast.Module(body=[new_classes[key] for key in classes], type_ignores=[])
class_text = ast.unparse(selected)
payload = '''import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='sysu311-MS-7C59'
import json,torch
import torch.nn as nn
torch.set_num_threads(1)
torch.manual_seed(1999)
assert not torch.cuda.is_initialized()
'''
payload += (BUNDLE / 'canonical_readout.py').read_text(encoding='utf-8') + '\n' + class_text
payload += '''
_orth_loss_accum=None
model=C2F_ClusterAttn_CTF_HCG_CSORT(d_model=16,nhead=8,cluster_layer_nums=[4,2,2],dropout=0).double()
p=torch.randn(2,7,16,dtype=torch.float64,requires_grad=True)
mask=torch.tensor([[False]*5+[True]*2,[False]*7])
banks=[torch.randn(2,k,16,dtype=torch.float64,requires_grad=True) for k in (4,2,2)]
ids=[[torch.tensor([0,1,2,3,1]),torch.tensor([3,2,1,0,2,3,0])],
     [torch.tensor([0,0,1,1]),torch.tensor([0,0,1,1])],
     [torch.tensor([0,1]),torch.tensor([0,1])]]
weights=model.level_gate(torch.cat([p,p.mean(1,keepdim=True).expand_as(p)],-1)).softmax(-1)
expected=torch.stack([canonical(p[b],[bank[b] for bank in banks],ids[0][b],ids[1][b],ids[2][b],weights[b],heads=8) for b in range(2)])
expected=model.point_out_proj(model.dropout(expected)).masked_fill(mask.unsqueeze(-1),0)
actual=model._cluster_to_points(p,banks,ids,mask)
error=float((expected-actual).abs().max())
assert error==0
maps=[[{0:[0],2:[1]} for _ in range(2)],[{0:[0],1:[1]} for _ in range(2)]]
result=model(p,torch.randn(2,3,16,dtype=torch.float64),mask,banks,maps,ids)['point']
assert result.shape==p.shape and torch.isfinite(result).all()
assert torch.count_nonzero(result[mask]).item()==0
loss=(result*torch.randn_like(result)).sum()+_orth_loss_accum
loss.backward()
assert all(x.grad is not None and torch.isfinite(x.grad).all() and x.grad.norm()>0 for x in [p]+banks)
assert not torch.cuda.is_initialized()
print('ADAPTER_RESULT='+json.dumps({'cpu_smoke_passed':True,'readout_max_error':error,'padding_zero':True,'point_and_bank_gradients_finite_nonzero':True,'cuda_initialized':False,'native_full_model':False}))
'''
process = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
    'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=payload,
    text=True,encoding='utf-8',capture_output=True,timeout=65)
guard()
attempt = BUNDLE / 'independent_adapter_attempt.json'
assert not attempt.exists()
tick.save(attempt, {'token':TOKEN,'observed_at':datetime.now(timezone.utc).isoformat(),
    'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr,
    'source_sha256':tick.digest(source/'hier_postprocess.py')})
assert process.returncode == 0, process.stderr
rows=[json.loads(line.split('=',1)[1]) for line in process.stdout.splitlines() if line.startswith('ADAPTER_RESULT=')]
assert len(rows)==1
result={'token':TOKEN,'observed_at':datetime.now(timezone.utc).isoformat(),
    'static_checks_passed':True,'independent_package':name,'python_files':8,
    'unchanged_config_sha256':tick.digest(config),'canonical_sha256':tick.digest(source/'hierarchical_readout.py'),
    'files':[{'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)} for path in files+[config]],
    'adapter':rows[0],'scope':'Static physical copy and constructed CPU adapter smoke only; no native full-model gate, commit, deployment, training, or trained gain.'}
tick.save(BUNDLE/'independent_adapter_result.json',result)
print(json.dumps({key:value for key,value in result.items() if key!='files'}))
