"""Inspect native annotation/scene batching without model execution."""
import hashlib
import json
import os
from pathlib import Path
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
import torch
p=Path('/sdc1/songcl/Project/Cluster_project/pipeline/server3_fallback_abdff23d/native_capture.pt')
h=hashlib.sha256()
with p.open('rb') as stream:
    for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
assert h.hexdigest()=='e4a7e63605bb60d9e9a543cd22ac2635a37627ee3db22d870122e1a254342e08'
data=torch.load(p,map_location='cpu')
rows=[]
for r in data['records']:
    if r['trial']!=0:continue
    rows.append({'pair':r['pair'],'ann_ids':r['ann_ids'],'scan_ids':r['scan_ids'],
        'scenes_len':r['scenes_len'],'batch_offsets':r['batch_offsets'],
        'cluster_points_shape':list(r['cluster']['inputs'][0].shape),
        'cluster_query_shape':list(r['cluster']['inputs'][1].shape),
        'head_points_shape':list(r['head']['inst_feats'].shape)})
def convert(x):
    if torch.is_tensor(x):return x.tolist()
    return str(x)
assert not torch.cuda.is_initialized()
print('SERVER3_CAPTURE_METADATA_JSON='+json.dumps({'rows':rows,'cuda_initialized':False},default=convert))
