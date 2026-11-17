"""CPU-only checkpoint metadata and annotation-only cohort freeze."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import torch

stage=Path(__file__).resolve().parent
assets=json.loads((stage/'frozen_assets.json').read_text())
annotation=json.loads(Path(assets['annotation_path']).read_text())
annotation.sort(key=lambda x:x['scene_id'])
groups=[];current=[];scene=None
for row in annotation:
    if row['scene_id']!=scene or len(current)>=4:
        if current:groups.append(current)
        current=[];scene=row['scene_id']
    current.append(row)
if current:groups.append(current)
first={}
for index,group in enumerate(groups):first.setdefault(group[0]['scene_id'],index)
selected=sorted(first,key=lambda s:hashlib.sha256(('fle-self-neighbor-1999:'+s).encode()).hexdigest())[:8]
cohort=[{'scene_id':s,'group_index':first[s],'expression_ids':[{'object_id':str(r['object_id']),'ann_id':str(r['ann_id'])} for r in groups[first[s]]]} for s in selected]
assert len(cohort)==8 and sum(len(g['expression_ids']) for g in cohort)==32
checkpoint=torch.load(assets['checkpoint'],map_location='cpu',weights_only=False,mmap=True)
scalar_metadata={}
for key,value in checkpoint.items():
    if value is None or isinstance(value,(str,int,float,bool)):scalar_metadata[key]=value
    elif isinstance(value,dict):scalar_metadata[key]={'kind':'dict','keys':list(value.keys())[:20],'length':len(value)}
    else:scalar_metadata[key]={'kind':type(value).__name__}
result={'observed_at':datetime.now(timezone.utc).isoformat(),'cohort':cohort,'groups':len(groups),'checkpoint_metadata':scalar_metadata,
    'checkpoint_sha256':assets['checkpoint_sha256'],'cohort_selection':'first native group in eight TRAIN scenes;scene SHA256 rank before outcomes',
    'cuda_initialized':torch.cuda.is_initialized(),'native_forwards':0,'optimizer_steps':0,'checkpoint_loading':'map_location=cpu,weights_only=False,mmap=True','limitations':'early-training,time-selected checkpoint;not a terminal efficacy estimate'}
assert not torch.cuda.is_initialized()
with (stage/'asset_metadata_result.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps({'cohort_scenes':len(cohort),'expressions':32,'cuda_initialized':False,'checkpoint_metadata':scalar_metadata}))
