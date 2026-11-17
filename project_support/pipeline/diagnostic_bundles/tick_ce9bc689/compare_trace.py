"""CPU comparison of the preregistered pairs, never selects a matching retry."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('--root',required=True)
p.add_argument('--model',choices=['m95','fle'],required=True)
a=p.parse_args()
root=Path(a.root)
left=root/('trace_'+a.model+'_1')
right=root/('trace_'+a.model+'_2')
def load(path):return json.loads(path.read_text())
l=load(left/'native_trace_result.json')
r=load(right/'native_trace_result.json')
assert l['passed'] and r['passed']
ev1=load(left/'trace_events.json')['events']
ev2=load(right/'trace_events.json')['events']
assert len(ev1)==len(ev2)
raw1=np.load(left/'trace_arrays.npz',allow_pickle=False)
raw2=np.load(right/'trace_arrays.npz',allow_pickle=False)
differences=[]
selected=[]
latest_pre={}
for e1,e2 in zip(ev1,ev2):
    assert (e1['sequence'],e1['label'],e1['phase'])==(e2['sequence'],e2['label'],e2['phase'])
    assert e1['tensors'].keys()==e2['tensors'].keys()
    unequal=[key for key in e1['tensors'] if e1['tensors'][key]!=e2['tensors'][key]]
    scalars_equal=e1['scalars']==e2['scalars']
    same=not unequal and scalars_equal
    if e1['phase']=='pre':latest_pre[e1['label']]={'sequence':e1['sequence'],'equal':same}
    item={'sequence':e1['sequence'],'label':e1['label'],'phase':e1['phase'],
        'equal':same,'different_tensor_keys':unequal,'scalars_equal':scalars_equal}
    if e1['phase']=='post':item['matching_pre']=latest_pre[e1['label']]
    if not same:differences.append(item)
    raw_stats={}
    for key,v in e1['tensors'].items():
        if 'raw_key' not in v:continue
        x,y=raw1[v['raw_key']],raw2[e2['tensors'][key]['raw_key']]
        assert x.shape==y.shape and x.dtype==y.dtype
        stat={'shape':list(x.shape),'different':int(np.count_nonzero(x!=y)),'elements':int(x.size)}
        if np.issubdtype(x.dtype,np.floating):
            d=np.abs(x.astype(np.float64)-y.astype(np.float64))
            stat.update(max_absolute=float(d.max(initial=0)),mean_absolute=float(d.mean()) if d.size else 0)
        raw_stats[key]=stat
    if raw_stats or e1['label'].startswith(('dec.encoder_layers.','dec.decoder_layers.')) or e1['label'] in ('text_encoder','dec','extract_feat','expand_and_fps'):
        selected.append({**item,'raw_statistics':raw_stats})
summary={'passed':True,'model':a.model,'observed_at':datetime.now(timezone.utc).isoformat(),
    'input_equal':l['input_sha256']==r['input_sha256'],
    'model_equal':l['model_loaded_sha256']==r['model_loaded_sha256'],
    'rng_before_equal':{k:l['rng_before'][k]==r['rng_before'][k] for k in l['rng_before']},
    'rng_after_forward_equal':{k:l['rng_after_forward'][k]==r['rng_after_forward'][k] for k in l['rng_after_forward']},
    'trace_event_count':len(ev1),'different_event_count':len(differences),
    'first_difference':differences[0] if differences else None,
    'first_divergent_equal_input_boundary':next((v for v in differences if v['phase']=='post' and v['matching_pre']['equal']),None),
    'loss_abs_difference':abs(l['loss']-r['loss']),
    'target_gradient_norm_abs_differences':{k:abs(l['target_gradient_norms'][k]-r['target_gradient_norms'][k]) for k in l['target_gradient_norms']},
    'selected_boundaries':selected,
    'scope':'one instrumented ORIGINAL pair/model;not seedvariance/CI,operatorcause or efficacy'}
assert summary['input_equal'] and summary['model_equal'] and all(summary['rng_before_equal'].values())
with (root/(a.model+'_trace_comparison.json')).open('x') as f:json.dump(summary,f,indent=2,allow_nan=False)
print(json.dumps({k:v for k,v in summary.items() if k!='selected_boundaries'}))
