"""CPU-only independent aggregation and source-bound synthetic head controls."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
import ast,hashlib,json,math
import numpy as np
import torch
torch.set_num_threads(1)
ROOT=Path('/data/songcl/Project/Cluster_project/pipeline')
STAGE=ROOT/'fle_targetmix_0d3bdd38'
output={'observed_at':datetime.now(timezone.utc).isoformat(),'native_summaries':{}}
for label,sub in [('early','fle_norm_interval_0d3bdd38'),('terminal','fle_terminal_content_0d3bdd38')]:
    p=ROOT/sub;r=json.loads((p/'native_diagnostic_result.json').read_text());m=json.loads((p/'native_manifest.json').read_text())
    assert r['passed'] and len(r['scenes'])==len(m['cohort'])
    values=[];selection=[];keys=set();controlmax=0;normmax=0;truemax=0;maskchanged=0;queryflips=0
    for scene,frozen in zip(r['scenes'],m['cohort']):
        assert scene['scene']==frozen['scene_id'] and scene['group_index']==frozen['group_index']
        controlmax=max(controlmax,max(scene['controls'].values()))
        for entry in scene['interventions']:
            for row in entry['rows']:
                assert not row['self_term_modified']
                normmax=max(normmax,row['norm_max_error']);truemax=max(truemax,row['true_norm_max_error'])
        delta=[];own=[]
        for row,identity in zip(scene['expressions'],frozen['expression_ids']):
            assert row['ann_id']==int(identity['ann_id'])
            key=(scene['scene'],identity['object_id'],identity['ann_id']);assert key not in keys;keys.add(key)
            delta.append(row['normal_piou']-row['fixed_query_piou']);own.append(row['normal_piou']-row['own_query_piou'])
            queryflips+=row['normal_query']!=row['intervention_query'];maskchanged+=row['final_mask_max_change']>0
        values.append(math.fsum(delta)/len(delta));selection.append(math.fsum(own)/len(own))
    assert controlmax<=1e-6 and normmax<=1e-6 and truemax<=1e-6
    average=math.fsum(values)/len(values);assert abs(average-r['scene_mean_normal_minus_intervention_piou'])<1e-12
    bootstrap=np.random.default_rng(1999).choice(np.array(values),(10000,len(values)),replace=True).mean(1)
    ci=np.quantile(bootstrap,[.025,.975]);assert np.max(np.abs(ci-np.array(r['scene_bootstrap_95ci'])))<1e-12
    output['native_summaries'][label]={'scenes':len(values),'expressions':len(keys),'normal_minus_fixed_piou':average,'ci95':ci.tolist(),
        'normal_minus_reselected_piou':math.fsum(selection)/len(selection),'query_index_flips':queryflips,'nonzero_mask_changes':maskchanged,
        'control_max_error':controlmax,'native_norm_max_error':normmax,'true_norm_max_error':truemax,'native_forwards':r['native_forwards'],'suffix_replays':r['suffix_replays'],
        'scope':'TRAINmechanism diagnosis;fixed query INDEX,not final query feature;not VALbenefit or generalization'}
obs=json.loads((STAGE/'native_attention_result.json').read_text());assert obs['passed'] and obs['unknown_label_expressions']==0
scenevalues=[];weighted=[];uniform=[];valid=0;missing_support=0;source_max=0;complement_max=0;denom=0
for scene in obs['scenes']:
    values=[]
    for row in scene['expressions']:
        source_max=max(source_max,row['source_error']);complement_max=max(complement_max,row['controls']['complement_error'])
        assert row['controls']['all_equal_null_error']==0
        denom+=row['target_recipients']
        if row['target_weighted_minus_uniform'] is None:missing_support+=1;continue
        values.append(row['target_weighted_minus_uniform']);weighted.append(row['target_weighted_cross_fraction']);uniform.append(row['target_uniform_cross_fraction']);valid+=1
    if values:scenevalues.append(math.fsum(values)/len(values))
assert source_max<=1e-6 and complement_max<=1e-6 and len(scenevalues)==32 and valid==119
v=np.array(scenevalues);ci=np.quantile(np.random.default_rng(1999).choice(v,(5000,len(v)),replace=True).mean(1),[.025,.975])
assert abs(v.mean()-obs['primary_scene_mean'])<1e-12 and np.max(np.abs(ci-np.array(obs['primary_scene_ci95'])))<1e-12
output['target_mixing']={'scenes':32,'expressions':128,'known_primary_expressions':valid,'unknown_labels':0,'no_target_nonself_support_expressions':missing_support,
    'target_recipients':denom,'primary_scene_mean':float(v.mean()),'ci95':ci.tolist(),'expression_mean_weighted_fraction':math.fsum(weighted)/len(weighted),
    'expression_mean_uniform_fraction':math.fsum(uniform)/len(uniform),'source_max_error':source_max,'complement_max_error':complement_max,
    'interpretation':'Locally target-aligned weights versus identical uniform support;not causal task improvement'}
m=json.loads((STAGE/'native_manifest.json').read_text());source=Path(m['root'])/'framework/model/Quard_model'/m['name']/'dec.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()==m['assets']['source_hashes']['dec.py']
tree=ast.parse(source.read_text());functions=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='prediction_head'];assert len(functions)==1
function=functions[0];namespace={'torch':torch};exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),namespace)
torch.manual_seed(1999);d=16;head=SimpleNamespace(out_norm=torch.nn.LayerNorm(d).double(),out_score=lambda q:q.sum(-1,keepdim=True))
q0=torch.randn(2,3,d,dtype=torch.float64);q1=torch.randn(2,3,d,dtype=torch.float64);f0=torch.randn(2,7,d,dtype=torch.float64);f1=torch.randn(2,7,d,dtype=torch.float64)
def mask(q,f):return namespace['prediction_head'](head,q,f,None)[1]
checks=[]
for name,qa,qb,fa,fb in [('general',q0,q1,f0,f1),('Qidentity',q0,q0,f0,f1),('Fidentity',q0,q1,f0,f0),('bothidentity',q0,q0,f0,f0),('zeroF',q0,q1,f0*0,f0*0)]:
    l00=mask(qa,fa);l01=mask(qa,fb);l10=mask(qb,fa);l11=mask(qb,fb)
    point=((l01-l00)+(l11-l10))/2;query=((l10-l00)+(l11-l01))/2
    error=float(((point+query)-(l11-l00)).abs().max().detach());assert error<=1e-12
    assert float((l00-torch.einsum('bnd,bmd->bnm',head.out_norm(qa),fa)).abs().max().detach())<=1e-12
    if name in ('Qidentity','bothidentity'):assert float(query.abs().max().detach())==0
    if name in ('Fidentity','bothidentity','zeroF'):assert float(point.abs().max().detach())==0
    checks.append({'case':name,'logit_additivity_max_error':error})
output['QF_source_head_controls']={'passed':True,'cases':checks,'source_sha256':m['assets']['source_hashes']['dec.py'],'out_norm_retained':True,
    'scope':'Synthetic float64actual-source functional fixture;NOT native trained query/point attribution or additive IoU'}
output.update(passed=True,cuda_initialized=torch.cuda.is_initialized(),native_forwards=0,new_training=0,noise_floor='UNKNOWN_NOT_INDEPENDENT_NATIVE_REPEATS')
assert not output['cuda_initialized']
with (STAGE/'final_analysis.json').open('x') as f:json.dump(output,f,indent=2,allow_nan=False)
print(json.dumps({'passed':True,'native_summaries':output['native_summaries'],'target_mixing':output['target_mixing'],'QF_CPU_cases':len(checks)}))
