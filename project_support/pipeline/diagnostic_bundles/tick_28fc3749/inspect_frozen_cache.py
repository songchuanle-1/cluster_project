"""Read-only bounded cache and active-train observation; no CUDA initialized."""
from ops import *
guard(120)
program=r'''import json,hashlib,os,re,subprocess
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
prefix=Path('/data/songcl/Project/Cluster_project/pipeline/native_stride_ed0d2b32/rank_m95/rank_prefix.npz')
known=[prefix,
 Path('/data/songcl/Project/Cluster_project/pipeline/native_coarse_2d7cbb68/raw_key_revision1'),
 Path('/data/songcl/Project/Cluster_project/pipeline/native_coarse_2d7cbb68/attribution_0'),
 Path('/data/songcl/Project/Cluster_project/pipeline/hds_server4_3c22e34d')]
records=[]
for path in known:
 record={'path':str(path),'exists':path.exists()}
 if path.is_file():
  record.update(size=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
  if path.suffix=='.npz':
   with np.load(path,allow_pickle=False) as data:
    record['arrays']=[{'key':key,'shape':list(data[key].shape),'dtype':str(data[key].dtype)} for key in data.files]
 elif path.is_dir():
  record['tensor_cache_files']=[{'name':x.name,'size':x.stat().st_size} for x in path.iterdir() if x.is_file() and x.suffix in ('.pt','.pth','.npz','.npy')][:25]
 records.append(record)
log=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1_resume_2546d803_native_serializer.log')
with log.open('rb') as stream:
 stream.seek(max(0,log.stat().st_size-32000));tail=stream.read().decode('utf-8',errors='replace')
lines=tail.splitlines()
progress=[line for line in lines if 'Train' in line or 'Epoch' in line or 'mIoU' in line or 'Val' in line]
status={'pid':1085297,'alive':Path('/proc/1085297').exists(),'log_size':log.stat().st_size,'native_tail':progress[-8:],'recent_traceback':'Traceback' in tail}
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'cache':records,'M204':status,'cuda_initialized':False,'training_changed':False}))
'''
result=remote('server-4',program,conda=True,timeout=120)
save('cache_and_training_observation.json',result)
advance([OUT/'cache_and_training_observation.json',OUT/'inspect_frozen_cache.py'])
print(json.dumps(result,ensure_ascii=True,indent=2))
