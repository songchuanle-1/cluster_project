"""Original TRAIN CPU preprocessing and explicitly artificial single-leaf stress."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
import copy
import hashlib
import importlib.util
import json
import logging
import math
from pathlib import Path
import sys
import numpy as np
import torch

stage=Path(__file__).resolve().parent;manifest=json.loads((stage/'manifest.json').read_text())
root=Path(manifest['root']);sys.path[:0]=[str(root),str(root/'framework/lib')]
from tools import train
import gorilla
from framework.dataset import build_dataset
from torch.utils.data import DataLoader,Subset
from torch_scatter import scatter_mean
source=Path(manifest['operator_path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['operator_sha256']
spec=importlib.util.spec_from_file_location('admitted_real_metric',source)
operator=importlib.util.module_from_spec(spec);spec.loader.exec_module(operator)
torch.set_num_threads(1)
result={'execution_passed':False,'scenes':[],'native_forwards':0,'native_backwards':0,'optimizer_steps':0,
    'membership':'one artificial leaf per scene,NOT native GPU FPSfine memberships','native_fine_membership':'not_run_CUDA_FPS_required'}
try:
    cfg=gorilla.Config.fromfile(manifest['config_path'])
    assert Path(cfg.data.train.data_root,'scanrefer/scene_graphs_new_train.json').is_file()
    gorilla.set_random_seed(1999)
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('metric-train-cpu'))
    for row in manifest['cohort']:
        group=dataset.scene_inputs[row['group_index']]
        assert group[0]['scene_id']==row['scene_id']
        assert [{'object_id':str(r['object_id']),'ann_id':str(r['ann_id'])} for r in group]==row['expression_ids']
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,[r['group_index'] for r in manifest['cohort']]),batch_size=1,num_workers=0,shuffle=False,collate_fn=dataset.collate_fn)
    c=math.cos(math.pi/4);s=math.sin(math.pi/4);rotation=np.array([[c,-s,0],[s,c,0],[0,0,1.]])
    transforms={'identity':lambda x:x.copy(),'reflection':lambda x:x*np.array([-1.,1.,1.]),'axis_permutation':lambda x:x[:,[2,0,1]],
        'scale2':lambda x:x*2.,'scale_half':lambda x:x*.5,'translation':lambda x:x+np.array([16.,-8.,4.]),'rotation_z_pi4':lambda x:x@rotation.T}
    for index,(cohort,batch) in enumerate(zip(manifest['cohort'],loader)):
        assert batch['scan_ids']==[cohort['scene_id']]
        positions=scatter_mean(batch['coords_float'],batch['superpoints'],dim=0).numpy()
        assert len(positions)>32
        path=stage/('train_geometry_'+str(index)+'.npz')
        with path.open('xb') as stream:np.savez_compressed(stream,coords_float=batch['coords_float'].numpy(),superpoints=batch['superpoints'].numpy(),positions_cpu=positions,ann_ids=np.array(batch['ann_ids']))
        geometry=positions.astype(np.float64);leaves=np.zeros(len(positions),dtype=np.int64)
        torch.manual_seed(1999);features=torch.randn(len(positions),256,dtype=torch.float32)
        original=operator.build_graph(geometry,leaves);normal=operator.exchange(features,original)
        scene={'scene':cohort['scene_id'],'group_index':cohort['group_index'],'expressions':len(batch['ann_ids']),
            'raw_points':len(batch['coords_float']),'superpoints':len(positions),'geometry_file':path.name,
            'geometry_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'membership':'artificial_single_leaf','transforms':[]}
        for name,transform in transforms.items():
            changed=operator.build_graph(transform(geometry),leaves)
            same=torch.equal(original['indices'],changed['indices']) and torch.equal(original['fallback'],changed['fallback'])
            actual=normal if same else operator.exchange(features,changed)
            error=float((actual-normal).abs().max())
            scene['transforms'].append({'transform':name,'max_output_error':error,'within_native_tolerance':error<=1e-6,
                'identical_graph_reused_exact_operator_input':same,'fallback_flips':int((original['fallback']!=changed['fallback']).sum()),
                'recipient_neighbor_set_changes':int((original['indices'].sort(1).values!=changed['indices'].sort(1).values).any(1).sum())})
        result['scenes'].append(scene)
        del features,normal
    assert len(result['scenes'])==8
    assert not torch.cuda.is_initialized()
    result.update(execution_passed=True,cuda_initialized=False,expressions=sum(r['expressions'] for r in result['scenes']),
        failures=[{'scene':scene['scene'],'transform':row['transform'],'error':row['max_output_error']} for scene in result['scenes'] for row in scene['transforms'] if not row['within_native_tolerance']],
        limitations='Real-coordinate artificial-leaf CPU probes only;not native fine membership,trained inst_feats,mask harm,generalization or source repair')
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:
    result['observed_at']=datetime.now(timezone.utc).isoformat()
    with (stage/'train_geometry_cpu_result.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
print(json.dumps({'passed_execution':result['execution_passed'],'scenes':len(result['scenes']),'failures':result.get('failures'),'cuda_initialized':result.get('cuda_initialized')}))
