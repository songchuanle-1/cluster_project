"""Locate resumed output from actual native save markers, not original input."""
import json
from ops import guard,remote,save,evidence
guard(150)
program=r'''
import os,json,re,hashlib
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
from datetime import datetime,timezone
import torch
torch.set_num_threads(1)
root=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
log=root/'logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1_resume_2546d803_native_serializer.log'
with log.open('rb') as stream:
 stream.seek(max(0,log.stat().st_size-8*1024*1024));tail=stream.read()
markers=re.findall(rb'save (?:best|last) pth to ([^\r\n]+)',tail)
assert markers,'No save marker in bounded last8MiB;do not guess checkpoint path'
marker=markers[-1].decode().strip()
path=Path(marker)
if not path.is_absolute():path=(root/path).resolve()
assert path.is_relative_to(Path('/data/songcl/Project/Cluster_project'))
folder=path.parent
def clean(value):
 if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [clean(v) for v in value]
 if torch.is_tensor(value):return value.item() if value.numel()==1 else {'shape':list(value.shape),'dtype':str(value.dtype)}
 if value is None or isinstance(value,(str,int,float,bool)):return value
 return repr(value)
records={}
for name in ('best.pth','last.pth'):
 p=folder/name
 before=p.stat()
 checkpoint=torch.load(p,map_location='cpu',weights_only=False,mmap=True)
 records[name]={'path':str(p),'meta':clean(checkpoint.get('meta',{})),'checkpoint_keys':list(checkpoint),'file_size':before.st_size,'mtime':datetime.fromtimestamp(before.st_mtime,timezone.utc).isoformat()}
 after=p.stat()
 assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
 records[name]['unchanged_stat']=True
 del checkpoint
text=tail.decode('utf-8',errors='replace')
metrics=re.findall(r'mIOU:\s*([0-9.]+)\. Acc_50:\s*([0-9.]+)\. Acc_25:\s*([0-9.]+)',text)
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'latest_actual_save_marker':marker,'actual_output_folder':str(folder),'checkpoints':records,'bounded_log_bytes':len(tail),'bounded_log_sha256':hashlib.sha256(tail).hexdigest(),'last_printed_metric':metrics[-1] if metrics else None,'original_epoch5_resume_input_preserved':True,'cuda_initialized':torch.cuda.is_initialized(),'new_training':0,'scope':'Exact resumed output located from native save marker;original input checkpoint metadata is historical,not current. No rewrite/restart or forced queue terminal.'}))
'''
value=remote('server-4',program,timeout=180,conda=True)
path=save('M204_actual_output_checkpoint_metadata.json',value)
print(json.dumps({'evidence':evidence(path),'returncode':value['returncode'],'data':value.get('data'),'stderr':value['stderr'][-1500:]},ensure_ascii=False,indent=2))
