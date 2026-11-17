"""Single fresh resource observation; preserve existing training and foreign jobs."""
import json
from ops import guard,remote,save,evidence,now
guard(120)
program = r'''
import json,subprocess,fcntl,re
from pathlib import Path
from datetime import datetime,timezone
cards={}
for index,expected in ((0,'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),(1,'GPU-7f82edb9-f620-8045-caea-a75232265cd1')):
 row=subprocess.check_output(['nvidia-smi','-i',str(index),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 assert [part.strip() for part in row.split(',')][:2]==[str(index),expected]
 contexts=subprocess.check_output(['nvidia-smi','-i',str(index),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 locks={}
 for kind in ('training','diagnostic','exclusive'):
  with open('/tmp/cluster_project_gpu'+str(index)+'_'+kind+'.lock','a+b') as handle:
   try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True
   except BlockingIOError:locks[kind]=False
 processes=[]
 for line in contexts.splitlines():
  pid=int(line.split(',')[0]);p=subprocess.run(['ps','-p',str(pid),'-o','pid=,user=,etime=,args='],capture_output=True,text=True,timeout=10)
  processes.append({'pid':pid,'ps':p.stdout.strip(),'ps_returncode':p.returncode})
 cards[str(index)]={'gpu':row,'contexts':contexts,'locks_available':locks,'processes':processes}
log=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1_resume_2546d803_native_serializer.log')
with log.open('rb') as stream:
 stream.seek(max(0,log.stat().st_size-131072));tail=stream.read().decode('utf-8',errors='replace')
steps=re.findall(r'Train\[(\d+)/50\][^\r\n]*?(\d+)/4686',tail)
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'cards':cards,'M204_native_steps':steps[-8:],'M204_log_modified_at':datetime.fromtimestamp(log.stat().st_mtime,timezone.utc).isoformat(),'M204_recent_traceback':'Traceback (most recent call last)' in tail[-20000:]}))
'''
server4 = remote('server-4', program)
server3 = {'recorded_at':now(),'actual_probe':'ssh key/strict-known-host/ConnectTimeout10 to server3 hostname','observed_stderr':'ssh: connect to host 192.168.1.120 port 22: Connection timed out','tool_exit_code':1,'ssh_exit_code':None,'hostname_verified_this_probe':False,'gpu1_occupation':None,'scope':'Actual earlier bounded probe timed out; unknown GPU occupation, not idle or occupied.'}
path = save('current_resources_and_training.json',{'server4':server4,'server3':server3,'scope':'Authorized cards only; no eviction/reset/restart/migration or scheduler changes.','local_probe_fault':'One malformed PowerShell SSH invocation exited1 without observations; corrected through structured subprocess/shlex. Not a server failure or GPU experiment.'})
print(json.dumps({'evidence':evidence(path),'server4':server4,'server3':server3},ensure_ascii=False,indent=2))
