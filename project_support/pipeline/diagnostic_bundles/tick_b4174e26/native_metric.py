"""Future native FPS/fine-kernel audit; no CUDA before a fresh lease and idle locks."""
import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys

os.environ.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
stage=Path(__file__).resolve().parent
manifest=json.loads((stage/'native_metric_manifest.json').read_text())
root=Path(manifest['root']);name=manifest['name'];handles=[]
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
def verify():
    assert sha(__file__)==manifest['runner_sha256']
    for file,value in manifest['source_hashes'].items():assert sha(root/'framework/model/Quard_model'/name/file)==value,file
    assert sha(manifest['config_path'])==manifest['config_sha256']
    assert sha(manifest['annotation_path'])==manifest['annotation_sha256']
    assert sha(root/'framework/dataset/scannetv2.py')==manifest['dataset_source_sha256']
    for row in manifest['geometry']:assert sha(stage/row['geometry_file'])==row['geometry_sha256']
def save(filename,value):
    value['observed_at']=datetime.now(timezone.utc).isoformat()
    with (stage/filename).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)
def observe(idle=False):
    assert socket.gethostname()=='dl04-MS-7E06'
    row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    parts=[p.strip() for p in row.split(',')]
    assert parts[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
    contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    assert all(int(v.split(',')[0])==os.getpid() for v in contexts.splitlines()),'Foreign GPU context,no sharing'
    if idle:assert not contexts and int(parts[2])<1024 and int(parts[3])<10
    return {'gpu':row,'contexts':contexts}
def release():
    for handle in reversed(handles):handle.close()
    handles.clear()
def acquire(path):
    lease=json.loads(Path(path).read_text())
    assert lease['project']=='cluster_project' and lease['thread_id']=='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
    assert lease['native_manifest_sha256']==sha(stage/'native_metric_manifest.json')
    remaining=(datetime.fromisoformat(lease['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
    assert 300<remaining<=3600 and len(lease['token'])==32
    before=observe(True)
    for kind in ('training','diagnostic','exclusive'):
        handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:handle.close();release();raise
        handles.append(handle)
    observe(True);verify()
    os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c')
    def timeout(signum,frame):raise TimeoutError('Current foreground deadline budget exhausted')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(min(1200,int(remaining)-150))
    return before

parser=argparse.ArgumentParser()
parser.add_argument('--prepare-check',action='store_true');parser.add_argument('--lease')
args=parser.parse_args()
if args.prepare_check:
    verify()
    save('native_metric_prepare_result.json',{'passed':True,'geometry_scenes':len(manifest['geometry']),
        'torch_imported':'torch' in sys.modules,'cuda_calls':0,'neural_model_forwards':0,'native_membership_tests':'NOT_RUN'})
    print('NATIVE_METRIC_PREPARE_CHECK_PASS_NO_TORCH_OR_CUDA');sys.exit(0)
if not args.lease:parser.error('a fresh owning foreground execution lease is required')
assert not (stage/'native_metric_result.json').exists(),'Preserve prior result;do not overwrite or silently retry'
result={'execution_passed':False,'scenes':[],'native_fps_layer_calls':0,'fine_kernel_calls':0,
    'neural_model_forwards':0,'native_backwards':0,'optimizer_steps':0,'features':'fixed synthetic probes,NOT trained inst_feats',
    'scientific_status':'native_geometry_and_fine_kernel_robustness_only;mask_effect_unknown'}
try:
    result['before']=acquire(args.lease)
    sys.path[:0]=[str(root),str(root/'framework/lib')]
    from tools import train
    import importlib
    import numpy as np
    import torch,gorilla
    from torch_scatter import scatter_mean
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized()
    torch.cuda.set_per_process_memory_fraction(.75,0)
    hierarchy=importlib.import_module('framework.model.Quard_model.'+name+'.hier_postprocess')
    operator=importlib.import_module('framework.model.Quard_model.'+name+'.fine_exchange')
    cfg=gorilla.Config.fromfile(manifest['config_path'])
    assert list(cfg.model.dec.cluster_layer_nums)==[256,64,8]
    c=math.cos(math.pi/4);s=math.sin(math.pi/4);rotation=np.array([[c,-s,0],[s,c,0],[0,0,1.]])
    transforms={'identity':lambda x:x.copy(),'reflection':lambda x:x*np.array([-1.,1.,1.]),'axis_permutation':lambda x:x[:,[2,0,1]],
        'scale2':lambda x:x*2.,'scale_half':lambda x:x*.5,'translation':lambda x:x+np.array([16.,-8.,4.]),'rotation_z_pi4':lambda x:x@rotation.T}
    with torch.no_grad():
        for row in manifest['geometry']:
            observe();data=np.load(stage/row['geometry_file'],allow_pickle=False)
            coords=torch.from_numpy(data['coords_float']).cuda();sp=torch.from_numpy(data['superpoints']).long().cuda()
            positions=scatter_mean(coords,sp,dim=0)
            offsets=torch.tensor([0,len(positions)],dtype=torch.long,device='cuda')
            bank=hierarchy.SharedClusterBank(cluster_layer_nums=[256,64,8]).cuda()
            bank.get_cluster(positions,offsets);result['native_fps_layer_calls']+=3
            fine_ids=bank.cluster_ids_list[0][0]
            geometry=positions.cpu().numpy().astype(np.float64)
            generator=torch.Generator(device='cpu').manual_seed(1999)
            features=torch.randn(len(positions),256,generator=generator,dtype=torch.float32).cuda()
            module=operator.FineLeafExchange(k=32,heads=8).cuda()
            padding=torch.zeros(1,len(positions),dtype=torch.bool,device='cuda')
            normal=module(features[None],padding,positions[None],[fine_ids])[0];result['fine_kernel_calls']+=1
            base=operator.build_graph(geometry,fine_ids.cpu().numpy())
            scene={'scene':row['scene'],'superpoints':len(positions),'fine_leaves':int(torch.unique(fine_ids).numel()),
                'cpu_gpu_position_max_error':float(np.max(np.abs(data['positions_cpu']-positions.cpu().numpy()))),'transforms':[]}
            for label,transform in transforms.items():
                transformed=transform(geometry);position_tensor=torch.as_tensor(transformed,dtype=torch.float64,device='cuda')
                actual=module(features[None],padding,position_tensor[None],[fine_ids])[0];result['fine_kernel_calls']+=1
                graph=operator.build_graph(transformed,fine_ids.cpu().numpy())
                error=float((actual-normal).abs().max().cpu())
                scene['transforms'].append({'transform':label,'output_max_error':error,'within_native_tolerance':error<=1e-6,
                    'fallback_flips':int((graph['fallback']!=base['fallback']).sum())})
            result['scenes'].append(scene)
            del bank,features,module,normal,actual,coords,sp,positions
            torch.cuda.empty_cache()
    verify();result['after']=observe();result['execution_passed']=True
    result['failures']=[{'scene':s['scene'],**v} for s in result['scenes'] for v in s['transforms'] if not v['within_native_tolerance']]
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:
    save('native_metric_result.json',result);release()
