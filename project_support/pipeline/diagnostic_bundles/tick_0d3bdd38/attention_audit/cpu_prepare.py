"""Synthetic readout controls and prediction-blind native cohort selection."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
import copy,hashlib,importlib.util,json,logging,sys
from pathlib import Path
import numpy as np
import torch
from attention_readout import prepare,mixing

p=Path(__file__).resolve().parent;m=json.loads((p/'preparation_manifest.json').read_text());a=m['assets'];root=Path(m['root'])
for name,value in a['source_hashes'].items():assert hashlib.sha256((root/'framework/model/Quard_model'/m['name']/name).read_bytes()).hexdigest()==value
for field in ['config','annotation']:
    assert hashlib.sha256(Path(a[field+'_path']).read_bytes()).hexdigest()==a[field+'_sha256']
assert not torch.cuda.is_initialized();torch.set_num_threads(1)
spec=importlib.util.spec_from_file_location('original_operator',a['operator_path']);op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
checks=[]
for tied in (False,True):
    coords=np.zeros((40,3)) if tied else np.arange(120,dtype=float).reshape(40,3)
    ids=np.zeros(40,dtype=np.int64);graph=op.build_graph(coords,ids)
    for uniform in (False,True):
        x=torch.ones(40,16,dtype=torch.float64) if uniform else torch.arange(640,dtype=torch.float64).reshape(40,16).sin()
        labels=(torch.arange(40)%2).double()
        source,state=prepare(x,graph);expected=op.exchange(x,graph)
        assert torch.equal(source,expected)
        actual,raw=mixing(state,labels);zero,z=mixing(state,torch.zeros_like(labels));complement,c=mixing(state,1-labels)
        assert float(z['cross_mass'].abs().max())==0
        assert float((raw['fraction']-c['fraction']).abs().max())<=1e-12
        if uniform:assert abs(actual['target_weighted_minus_uniform'])<=1e-12
        checks.append({'tied':tied,'uniform_features':uniform,'source_exact':True,'null':True,'complement':True,'uniform_readout':actual['target_weighted_minus_uniform'] if uniform else None})
sys.path[:0]=[str(root),str(root/'framework/lib')]
from tools import train
import gorilla
from framework.dataset import build_dataset
cfg=gorilla.Config.fromfile(a['config_path'])
assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('targetmixprepare'))
first={}
for index,group in enumerate(dataset.scene_inputs):
    if len(group)==4 and len({r['scene_id'] for r in group})==1:first.setdefault(group[0]['scene_id'],index)
scenes=sorted(first,key=lambda s:hashlib.sha256(s.encode()).hexdigest())[:32]
assert len(scenes)==32
cohort=[{'scene_id':s,'group_index':first[s],'expression_ids':[{'object_id':str(r['object_id']),'ann_id':str(r['ann_id'])} for r in dataset.scene_inputs[first[s]]]} for s in scenes]
assert not torch.cuda.is_initialized()
result={'passed':True,'observed_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'cohort':cohort,'scenes':32,'expressions':128,'cuda_initialized':False,'native_forwards':0,'optimizer_steps':0,'selection':'SHA256scene,firstnative4expressiongroup,beforepredictions'}
with (p/'cpu_prepare_result.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps({'passed':True,'synthetic_cases':len(checks),'cohort_scenes':len(cohort),'cuda':False}))
