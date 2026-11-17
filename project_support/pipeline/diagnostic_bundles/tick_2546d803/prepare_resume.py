"""Bind the new human consent and recheck unchanged resume assets without CUDA."""
from ops import *
import pipeline_monitor as monitor

guard(240)
old=tick.load(ORIGINAL/'runtime_manifest.json')
prior=tick.load(ROOT/'pipeline/authorizations/cpa_exploratory_20261019_72695a5d.json')
cp=tick.load(OLD/'checkpoint_cpu.json')['checkpoints']['last.pth']
assert cp['sha256']=='50ce84c115849e984966b95247e20bbea46c6df3983393802f451b44ff9f1537'
assert not AUTH.exists(),'Consent already recorded;read and reconcile instead of overwriting/replaying'
for path,digest in prior['files'].items():
 assert tick.digest(CODE/path)==digest,path
 blob=subprocess.check_output(['git','-C',str(CODE),'show',old['code_commit']+':'+path])
 assert hashlib.sha256(blob).hexdigest()==digest,path
authorization={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'project':'cluster_project','thread_id':THREAD,'candidate_id':CID,'experiment_id':ID,'kind':'single_checkpoint_resume','human_reply_verbatim':'授权','reply_to':'是否授权从已核验的 last.pth 恢复同一 M204-CPA：使用 server4 GPU0，从第6轮开始，保留优化器及学习率状态，总上限仍为50轮，不调参？第6轮未保存部分需要重跑。','provenance':'Direct unambiguous human reply in the owning chat after the scoped resume question;not a heartbeat or model-generated consent.','authorized':True,'maximum_training_launches':1,'maximum_resume_launches':1,'automatic_retry_or_restart':False,'operations':['read-only fresh identity/source/checkpoint/resource verification','stage a same-native-loop operational resume guard,without model/config changes or code synchronization','one guarded native --resume for the SAME M204-CPA with actual restoration/progress verification'],'server':'server-4','physical_gpu':0,'hostname':'dl04-MS-7E06','gpu_uuid':'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c','root':old['root'],'code_commit':old['code_commit'],'config':old['config'],'runtime_files':old['runtime_files'],'checkpoint':cp['path'],'checkpoint_sha256':cp['sha256'],'expected_saved_epoch':5,'planned_start_epoch':6,'seed':1999,'batch_size':2,'workers':4,'epochs':50,'max_iters':70,'scientific_admission':False,'diagnosis_passed':False,'semantic_controls_passed':False,'implementation_revision_result':'inconclusive','exception':'Continue only the already human-authorized exploratory realization from its full saved epoch5 state despite unresolved scientific gates. Not a scientific PASS,normal admission receipt or general restart policy.','goal_sha256':GOAL,'original_launch_authorization':evidence(ROOT/'pipeline/authorizations/cpa_exploratory_20261019_72695a5d.json'),'resume_request':evidence(OLD/'resume_request.json'),'checkpoint_evidence':evidence(OLD/'checkpoint_cpu.json'),'resume_contract_evidence':evidence(OLD/'resume_contract_cpu.json'),'preserved_boundaries':'No cold start,migration,new candidate,hyperparameter/data/validation change,automatic later restart,eviction,reset,lock deletion,scheduler change or other-project operation.','rng_state_saved':False,'exact_mid_epoch_replay':False}
guard()
with AUTH.open('x',encoding='utf-8') as stream:json.dump(authorization,stream,ensure_ascii=False,indent=2)
save('authorization_binding.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'authorization':evidence(AUTH),'human_reply':'授权','scoped_operation':'Same M204 native checkpoint resume,not new scientific admission','original_runtime':evidence(ORIGINAL/'runtime_manifest.json'),'local_model_files_equal_original_nine_tested_blobs':True})
advance([AUTH,OUT/'authorization_binding.json',OUT/'prepare_resume.py'],checkpoint_resume_authorization=evidence(AUTH),next_action='Use the newly granted SAME-experiment resume consent;verify live identity/resources/exclusive locks and immutable assets,then launch once and verify real restored native progress. Do not request the same consent again.')
program=r'''import json,hashlib,subprocess,fcntl,shutil
from pathlib import Path
from datetime import datetime,timezone
import yaml,importlib.metadata
root=Path(MANIFEST['root'])
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==MANIFEST['code_commit']
runtime={path:sha(root/path) for path in MANIFEST['runtime_files']}
assert runtime==MANIFEST['runtime_files']
assert sha(MANIFEST['pretrain'])==MANIFEST['pretrain_sha256']
assert sha(MANIFEST['annotation'])==MANIFEST['annotation_sha256']
checkpoint=Path(CHECKPOINT);digest=sha(checkpoint);assert digest==CHECKPOINT_SHA
cfg=yaml.safe_load((root/MANIFEST['config']).read_text())
assert cfg['train']['seed']==1999 and cfg['train']['epochs']==50 and cfg['lr_scheduler']['max_iters']==70
assert cfg['dataloader']['train']['batch_size']==2 and cfg['dataloader']['train']['num_workers']==4
assert cfg['train']['pretrain']==MANIFEST['pretrain']
assert all(Path(cfg['data'][split]['data_root']).is_dir() for split in ('train','val'))
matched=[]
for path in Path('/proc').glob('[0-9]*/cmdline'):
 try:args=path.read_bytes().split(b'\0')
 except OSError:continue
 if b'tools/train.py' in args and MANIFEST['config'].encode() in args:matched.append(int(path.parent.name))
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
values=[x.strip() for x in gpu.split(',')]
assert values[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
locks={};handles=[]
for kind in ('training','diagnostic','exclusive'):
 handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
 try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True;handles.append(handle)
 except BlockingIOError:locks[kind]=False;handle.close()
for handle in reversed(handles):handle.close()
disk=shutil.disk_usage(root.parent)
boot=next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
ready=not matched and not contexts and int(values[2])<1024 and int(values[3])<10 and all(locks.values()) and disk.free>3*1024**3
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':'dl04-MS-7E06','boot_at':datetime.fromtimestamp(boot,timezone.utc).isoformat(),'code_commit':MANIFEST['code_commit'],'runtime_files_unchanged':True,'runtime_files':runtime,'checkpoint':str(checkpoint),'checkpoint_sha256':digest,'checkpoint_bytes':checkpoint.stat().st_size,'pretrain_and_annotation_unchanged':True,'fixed_config_verified':True,'data_roots_exist':True,'torch_version':importlib.metadata.version('torch'),'gpu':gpu,'contexts':contexts,'exact_config_process_ids':matched,'exclusive_locks_available':locks,'probe_locks_released':True,'disk_free_bytes':disk.free,'ready_for_guarded_resume':ready,'cuda_computations':0,'training_launches':0}))
'''
program='MANIFEST='+repr(old)+'\nCHECKPOINT='+repr(cp['path'])+'\nCHECKPOINT_SHA='+repr(cp['sha256'])+'\n'+program
result=ssh(program,conda=True,timeout=180)
save('fresh_resume_environment.json',result)
advance([OUT/'fresh_resume_environment.json'])
print(json.dumps({k:v for k,v in result.items() if k!='runtime_files'},ensure_ascii=True,indent=2))
