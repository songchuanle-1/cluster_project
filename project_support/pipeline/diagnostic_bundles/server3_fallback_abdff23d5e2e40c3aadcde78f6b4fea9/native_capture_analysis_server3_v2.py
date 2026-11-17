"""CPU-only matched controls on the frozen, genuinely native TRAIN capture."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import types

os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
ROOT=Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
CAPTURE=ROOT.parent/'pipeline/server3_fallback_abdff23d/native_capture.pt'
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
SOURCE=ROOT/'framework/model/Quard_model'/MODEL/'hier_postprocess.py'
def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()
assert subprocess.check_output(['hostname'],universal_newlines=True,timeout=5).strip()=='sysu311-MS-7C59'
assert sha(CAPTURE)=='e4a7e63605bb60d9e9a543cd22ac2635a37627ee3db22d870122e1a254342e08'
assert sha(SOURCE)=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
import torch
torch.set_num_threads(1)
capture=torch.load(CAPTURE,map_location='cpu')
assert not torch.cuda.is_initialized()
assert capture['optimizer_steps']==0 and not capture['training_started']
assert capture['preparation']['frozen_groups']==[0,60,101,124]
records=capture['records']
assert len(records)==4 and sorted((r['trial'],r['pair']) for r in records)==[(0,0),(0,1),(1,0),(1,1)]
spec=importlib.util.spec_from_file_location('frozen_native_hierarchy',str(SOURCE))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
tree=ast.parse(SOURCE.read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='C2F_ClusterAttn_CTF_HCG')
node=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_cluster_to_points'))
assigns=[n for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='global_mean' for t in n.targets)]
assert len(assigns)==1
assigns[0].value=ast.parse('torch.stack([point_feats[b, ~point_mask[b]].mean(dim=0) if (~point_mask[b]).any() else torch.zeros_like(point_feats[b, 0]) for b in range(point_feats.shape[0])], dim=0).unsqueeze(1).expand_as(point_feats)',mode='eval').body
scope={'torch':torch}
exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<same-shape-native-mean-diagnostic>','exec'),scope)
def forward(model,inputs):
    mod.reset_orth_accum()
    value=model(*inputs)['point']
    mod.get_orth_loss()
    return value
def delta(a,b):return (a-b).abs().max().item()
rows=[]
scenes=set()
expressions=set()
appearances=0
with torch.no_grad():
    for record in records:
        p,q,mask,tokens,children,ids=record['cluster']['inputs']
        scene_counts=[int(n) for n in record['scenes_len']]
        assert len(record['scan_ids'])==len(scene_counts)
        expanded_scans=[scan for scan,n in zip(record['scan_ids'],scene_counts) for _ in range(n)]
        assert len(expanded_scans)==len(record['ann_ids'])==p.shape[0]
        appearances+=p.shape[0]
        assert torch.isfinite(record['cluster']['point_message']).all()
        assert torch.isfinite(record['head']['pred_masks']).all()
        if record['trial']!=0:continue
        assert p.dtype==torch.float32 and mask.dtype==torch.bool
        net=mod.C2F_ClusterAttn_CTF_HCG_CSORT(d_model=p.shape[-1],nhead=8,
            cluster_layer_nums=[256,64,8],per_layer_topk_list=[32,16,8],dropout=0.0).eval()
        net.load_state_dict(record['cluster']['state'],strict=True)
        original=forward(net,(p,q,mask,tokens,children,ids))
        repeated=forward(net,(p,q,mask,tokens,children,ids))
        swapped=forward(net,(p,q.flip(1),mask,tokens,children,ids))
        clone=copy.deepcopy(net)
        clone._cluster_to_points=types.MethodType(scope['_cluster_to_points'],clone)
        counterfactual=forward(clone,(p,q,mask,tokens,children,ids))
        refined=[cf+net.cluster_ffn[i](net.cluster_ffn_norm[i](cf)) for i,cf in enumerate(tokens)]
        row={'pair':record['pair'],'batch_shape':list(p.shape),'expressions':[],
            'cpu_repeat_delta':delta(original,repeated),'query_swap_given_bank_delta':delta(original,swapped),
            'native_gpu_vs_cpu_message_delta':delta(original,record['cluster']['point_message']),
            'masked_mean_valid_message_delta':delta(original[~mask],counterfactual[~mask])}
        assert row['cpu_repeat_delta']==0 and row['query_swap_given_bank_delta']==0
        head=record['head']
        predicted=torch.einsum('bnd,bmd->bnm',head['normalized_query'],head['inst_feats'])
        row['captured_mask_formula_cpu_gpu_delta']=delta(predicted,head['pred_masks'])
        for b in range(p.shape[0]):
            valid=~mask[b]
            n=int(valid.sum())
            composed=[ids[0][b].long().clamp(0,refined[0].shape[1]-1)]
            assert len(composed[0])==n
            for level in (1,2):
                parents=ids[level][b].long().clamp(0,refined[level].shape[1]-1)
                composed.append(parents.gather(0,composed[-1]))
            messages=[refined[level][b,composed[level]] for level in range(3)]
            cosines={str(a)+'_'+str(c):torch.nn.functional.cosine_similarity(messages[a],messages[c],dim=-1).mean().item()
                for a,c in ((0,1),(0,2),(1,2))}
            masked_mean=p[b,valid].mean(dim=0)
            raw_mean=p[b].mean(dim=0)
            ann=str(record['ann_ids'][b])
            scan=str(expanded_scans[b])
            scenes.add(scan)
            expressions.add((scan,ann))
            row['expressions'].append({'scan_id':scan,'ann_id':ann,'valid_points':n,
                'padded_points':int(mask[b].sum()),'mean_path_delta':delta(masked_mean,raw_mean),
                'same_shape_message_delta':delta(original[b,valid],counterfactual[b,valid]),
                'scale_cosine':cosines})
        other=next(r for r in records if r['trial']==1 and r['pair']==record['pair'])
        row['native_repeat_message_delta']=delta(record['cluster']['point_message'],other['cluster']['point_message'])
        rows.append(row)
expressions_rows=[entry for row in rows for entry in row['expressions']]
result={'observed_at':datetime.now(timezone.utc).isoformat(),'capture_sha256':sha(CAPTURE),
    'source_sha256':sha(SOURCE),'cuda_initialized':torch.cuda.is_initialized(),
    'frozen_train_groups':4,'network_forwards_in_capture':4,'unique_scenes':len(scenes),
    'unique_expression_ids':len(expressions),'expression_appearances':appearances,
    'first_repeat_expression_rows':len(expressions_rows),
    'first_repeat_valid_point_rows':sum(r['valid_points'] for r in expressions_rows),
    'same_shape_cpu_identity_and_query_controls_passed':len(rows)*2,
    'expressions_with_padding':sum(r['padded_points']>0 for r in expressions_rows),
    'expressions_with_message_change_above_original_1e_minus_6':sum(r['same_shape_message_delta']>1e-6 for r in expressions_rows),
    'scale_cosine_expression_mean':{key:sum(r['scale_cosine'][key] for r in expressions_rows)/len(expressions_rows)
        for key in ('0_1','0_2','1_2')},'rows':rows,'optimizer_steps':0,
    'prior_failures_reclassified':False,'task_harm_proven':False,'new_model_backward':False,
    'scope':'Native learned-input same-shape module sensitivity and descriptive scale similarity, not trained efficacy, causal task harm, new-core controls or admission.'}
assert not result['cuda_initialized']
print('SERVER3_CAPTURE_ANALYSIS_JSON='+json.dumps(result))
