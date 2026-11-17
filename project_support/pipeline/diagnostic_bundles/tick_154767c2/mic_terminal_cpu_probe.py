import socket,os,pathlib,subprocess,json,re,hashlib,gc
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_mic_20261105')
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()=='07ef534a6e44f22bd7b2d083550ebd7823d1d3d3'
assert not pathlib.Path('/proc/2881795').exists()
name='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mic'
base=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints')/name
runs=sorted(p for p in base.iterdir() if p.is_dir() and (p/'best.pth').is_file() and (p/'last.pth').is_file())
assert len(runs)==1,[(str(p),[q.name for q in p.iterdir()]) for p in runs]
run=runs[0]; native_logs=sorted(p for p in run.iterdir() if p.is_file() and p.suffix=='.log')
assert len(native_logs)==1,[str(p) for p in native_logs]
native_log=native_logs[0]
def fileinfo(p):
 st=p.stat(); h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''): h.update(chunk)
 st2=p.stat(); assert (st.st_size,st.st_mtime_ns)==(st2.st_size,st2.st_mtime_ns)
 return {'path':str(p),'size':st.st_size,'sha256':h.hexdigest(),'mtime_ns':st.st_mtime_ns}
text=native_log.read_text(encoding='utf-8',errors='replace')
validation_lines=[line for line in text.splitlines() if re.search(r'\bmIoU\s*:',line)]
vals=[float(re.search(r'\bmIoU\s*:\s*([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)',line).group(1)) for line in validation_lines]
assert len(vals)==26,{'count':len(vals),'lines':validation_lines[-3:]}
best=max(vals);best_epoch=vals.index(best)+1;no_improve=len(vals)-best_epoch
stdout=root/'logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mic_20261106_030700.log'
with stdout.open('rb') as f:
 size=f.seek(0,2);f.seek(max(0,size-131072));tail=f.read().decode('utf-8',errors='replace')
terminal_lines=[l for l in tail.splitlines() if 'Early stopping at epoch' in l]
assert any(re.search(r'Early stopping at epoch 26: no improvement for 10 epochs',l) for l in terminal_lines)
assert no_improve==10
import torch
assert not torch.cuda.is_initialized()
rows=[]
for kind in ['best','last']:
 p=run/(kind+'.pth'); row=fileinfo(p); ckpt=torch.load(str(p),map_location='cpu',weights_only=False); meta=ckpt['meta']; row['checkpoint_top_keys']=list(ckpt); row['native_meta']={k:meta.get(k) for k in ['epoch','best_miou','epochs_no_improve']}; row['model_tensor_devices']=sorted({v.device.type for v in ckpt.get('model',{}).values() if isinstance(v,torch.Tensor)}); assert row['model_tensor_devices']==['cpu']; assert float(meta['best_miou'])==best; rows.append(row); del ckpt;gc.collect()
assert rows[0]['native_meta']['epoch']==best_epoch
assert rows[0]['native_meta']['epochs_no_improve']==0
assert rows[1]['native_meta']['epoch']==25 and rows[1]['native_meta']['epochs_no_improve']==9
assert not torch.cuda.is_initialized()
events=[fileinfo(p) for p in sorted(run.glob('events.out.tfevents.*'))]
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'runtime_root':str(root),'source_commit':'07ef534a6e44f22bd7b2d083550ebd7823d1d3d3','trainer_pid':2881795,'trainer_absent':True,'config_basename':name,'native_run_directory':str(run),'native_log':fileinfo(native_log),'validation_lines':validation_lines,'completed_validation_count':len(vals),'validation_values':vals,'best_miou':best,'best_epoch':best_epoch,'last_validation_miou':vals[-1],'terminal_epoch':26,'no_improve':no_improve,'terminal_matching_lines':terminal_lines,'stdout_log_observation':fileinfo(stdout),'checkpoints':rows,'event_files':events,'CUDA_VISIBLE_DEVICES':os.environ.get('CUDA_VISIBLE_DEVICES'),'torch_cuda_initialized':torch.cuda.is_initialized(),'GPU_computation':False,'signals_sent':False,'remote_mutations':False,'checkpoint_note':'Native early-stop break precedes save; actual CPU meta confirms last epoch25/no-improve9, not terminal epoch26.'}))
