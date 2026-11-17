"""Operational resume guard; leave the model, configuration and native loop unchanged."""
import argparse,fcntl,hashlib,json,os,socket,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--manifest',required=True)
parser.add_argument('native',nargs=argparse.REMAINDER)
args=parser.parse_args()
manifest=json.loads(Path(args.manifest).read_text())
root=Path(manifest['root'])
stage=Path(args.manifest).parent
uuid='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
handles=[]
status={'started_at':datetime.now(timezone.utc).isoformat(),'experiment_id':'M204-CPA','scientific_admission':False,'return_status':'starting','resume_observed':False}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()

def observe():
 assert socket.gethostname()=='dl04-MS-7E06'
 row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
 cells=[v.strip() for v in row.split(',')]
 assert cells[:2]==['0',uuid]
 contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
 assert not contexts and int(cells[2])<1024 and int(cells[3])<10,'GPU0 busy;do not share,evict or reset'
 return row

def layout(state):
 values=[(key,list(value.shape),str(value.dtype)) for key,value in state.items()]
 return hashlib.sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest()

def optimizer_summary(state):
 states=state['state'];first=next(iter(states.values()))
 steps=[float(value['step']) for value in states.values() if 'step' in value]
 return {'state_entries':len(states),'step_min':min(steps),'step_max':max(steps),
  'group_lrs':[value['lr'] for value in state['param_groups']],
  'group_parameter_counts':[len(value['params']) for value in state['param_groups']],
  'first_moment_prefix':{key:value.detach().reshape(-1)[:8].cpu().tolist() for key,value in first.items() if key in ('exp_avg','exp_avg_sq')}}

try:
 assert args.native==['tools/train.py',manifest['config'],'--resume',manifest['checkpoint'],'--gpu_ids','0','--num_gpus','1']
 assert sha(__file__)==manifest['guard_sha256']
 assert sha(manifest['authorization_path'])==manifest['authorization_sha256']
 auth=json.loads(Path(manifest['authorization_path']).read_text())
 assert auth['authorized'] and auth['kind']=='single_checkpoint_resume' and auth['maximum_resume_launches']==1
 assert auth['automatic_retry_or_restart'] is False and auth['experiment_id']=='M204-CPA' and not auth['scientific_admission']
 assert auth['checkpoint']==manifest['checkpoint'] and auth['checkpoint_sha256']==manifest['checkpoint_sha256']
 assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==manifest['code_commit']
 for path,digest in manifest['runtime_files'].items():assert sha(root/path)==digest,path
 for path,key in ((manifest['pretrain'],'pretrain_sha256'),(manifest['annotation'],'annotation_sha256'),(manifest['checkpoint'],'checkpoint_sha256'),(manifest['resume_implementation_path'],'resume_implementation_sha256')):
  assert sha(path)==manifest[key],path
 for file in Path('/proc').glob('[0-9]*/cmdline'):
  if file.parent.name==str(os.getpid()):continue
  try:parts=file.read_bytes().split(b'\0')
  except OSError:continue
  assert not (b'tools/train.py' in parts and manifest['config'].encode() in parts),'Exact candidate already running'
 before=observe()
 for kind in ('training','diagnostic','exclusive'):
  handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BaseException:handle.close();raise
  handles.append(handle)
 observe()
 os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES=uuid,PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
 sys.path[:0]=[str(root),str(root/'framework/lib')]
 os.chdir(root);sys.argv=args.native
 from tools import train
 assert not train.torch.cuda.is_initialized()
 native=train.get_args()
 assert native.resume==manifest['checkpoint'] and native.gpu_ids==[0] and native.num_gpus==1
 cfg=train.gorilla.Config.fromfile(native.config)
 assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
 assert cfg.dataloader.train.batch_size==2 and cfg.dataloader.train.num_workers==4
 assert cfg.model.dec.cluster_mode=='ctf_hcg_cpa_csort' and cfg.train.pretrain==manifest['pretrain']
 checkpoint=train.torch.load(manifest['checkpoint'],map_location='cpu',weights_only=False,mmap=True)
 expected_meta={'epoch':int(checkpoint['meta']['epoch']),'best_miou':float(checkpoint['meta']['best_miou']),'epochs_no_improve':int(checkpoint['meta']['epochs_no_improve'])}
 assert expected_meta=={'epoch':5,'best_miou':0.43399661779403687,'epochs_no_improve':0}
 expected_optimizer=optimizer_summary(checkpoint['optimizer'])
 expected_scheduler=checkpoint['scheduler']
 expected_layout=layout(checkpoint['model'])
 anchor_key=next(iter(checkpoint['model']))
 expected_anchor=checkpoint['model'][anchor_key].detach().reshape(-1)[:16].cpu().tolist()
 del checkpoint
 original_resume=train.gorilla.resume

 def observed_resume(*positional,**kwargs):
  assert not status['resume_observed'] and not positional
  assert kwargs['filename']==manifest['checkpoint'] and kwargs['map_location']=='cpu'
  meta=original_resume(*positional,**kwargs)
  actual_meta={'epoch':int(meta['epoch']),'best_miou':float(meta['best_miou']),'epochs_no_improve':int(meta['epochs_no_improve'])}
  actual_optimizer=optimizer_summary(kwargs['optimizer'].state_dict())
  actual_scheduler=kwargs['scheduler'].state_dict()
  model_state=kwargs['model'].state_dict()
  actual_layout=layout(model_state)
  actual_anchor=model_state[anchor_key].detach().reshape(-1)[:16].cpu().tolist()
  assert actual_meta==expected_meta
  assert actual_optimizer==expected_optimizer,'Optimizer state did not restore exactly'
  assert all(actual_scheduler[key]==value for key,value in expected_scheduler.items()),'Scheduler state did not restore exactly'
  assert actual_layout==expected_layout and actual_anchor==expected_anchor,'Model state restore mismatch'
  record={'observed_at':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'experiment_id':'M204-CPA','checkpoint':manifest['checkpoint'],'checkpoint_sha256':manifest['checkpoint_sha256'],'metadata':actual_meta,'planned_start_epoch':actual_meta['epoch']+1,'optimizer':actual_optimizer,'scheduler':actual_scheduler,'model_layout_sha256':actual_layout,'model_layout_and_anchor_match':True,'optimizer_matches_saved_state':True,'scheduler_matches_saved_state':True,'rng_state_saved':False,'scientific_admission':False}
  with (stage/'resume_restoration.json').open('x') as stream:json.dump(record,stream,indent=2)
  status['resume_observed']=True
  print('CPA_RESUME_STATE_VERIFIED='+json.dumps(record),flush=True)
  return meta

 train.gorilla.resume=observed_resume
 train.gorilla.set_cuda_visible_devices(gpu_ids=native.gpu_ids,num_gpu=1)
 os.environ['CUDA_VISIBLE_DEVICES']=uuid
 status.update(return_status='training',pid=os.getpid(),physical_gpu=0,gpu_uuid=uuid,before=before,locks=['training','diagnostic','exclusive'])
 print('CPA_CHECKPOINT_RESUME_GUARD='+json.dumps(status),flush=True)
 train.gorilla.launch(train.main,1,num_machines=native.num_machines,machine_rank=native.machine_rank,dist_url=native.dist_url,args=(native,))
 assert status['resume_observed']
 status['return_status']='native_training_returned'
except BaseException as error:
 status.update(return_status='failed',error_type=type(error).__name__,error=str(error))
 raise
finally:
 status['finished_at']=datetime.now(timezone.utc).isoformat()
 try:
  with (stage/'native_exit.json').open('x') as stream:json.dump(status,stream,indent=2)
 finally:
  for handle in reversed(handles):handle.close()
