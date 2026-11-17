"""Read exact stopped M204 checkpoint metadata on CPU; never resume or mutate."""
import json
from ops import guard,remote,save,evidence
guard(120)
program=r'''
import os,json,hashlib,re,subprocess
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
from datetime import datetime,timezone
import torch
torch.set_num_threads(1)
folder=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1/20261019_093003')
records={}
def clean(value):
 if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [clean(v) for v in value]
 if torch.is_tensor(value):return value.item() if value.numel()==1 else {'shape':list(value.shape),'dtype':str(value.dtype)}
 if value is None or isinstance(value,(str,int,float,bool)):return value
 return repr(value)
for name in ('best.pth','last.pth'):
 p=folder/name
 before=p.stat()
 try:
  checkpoint=torch.load(p,map_location='cpu',weights_only=False,mmap=True)
  meta=clean(checkpoint.get('meta',{}))
  keys=list(checkpoint)
  after=p.stat()
  assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
  records[name]={'meta':meta,'checkpoint_keys':keys,'file_size':after.st_size,'mtime':datetime.fromtimestamp(after.st_mtime,timezone.utc).isoformat(),'unchanged_stat':True}
  del checkpoint
 except Exception as error:
  records[name]={'error_type':type(error).__name__,'error':str(error),'file_size':before.st_size}
log=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1_resume_2546d803_native_serializer.log')
with log.open('rb') as stream:
 stream.seek(max(0,log.stat().st_size-65536));tail=stream.read()
text=tail.decode('utf-8',errors='replace')
markers=[line for line in text.splitlines() if 'Early stopping at epoch' in line or line.startswith('mIOU:') or line.startswith('spmIOU:')]
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'checkpoints':records,'terminal_markers':markers[-5:],'log_tail_sha256':hashlib.sha256(tail).hexdigest(),'cuda_initialized':torch.cuda.is_initialized(),'new_training':0,'scope':'Native28/50earlystop versuslastserializedepoch may differ because break precedes checkpointsave;no forced terminalqueue edit or restart.'}))
'''
value=remote('server-4',program,timeout=180,conda=True)
path=save('M204_exit_and_checkpoint_metadata.json',value)
print(json.dumps({'evidence':evidence(path),'returncode':value['returncode'],'data':value.get('data'),'stderr':value['stderr'][-1000:]},ensure_ascii=False,indent=2))
