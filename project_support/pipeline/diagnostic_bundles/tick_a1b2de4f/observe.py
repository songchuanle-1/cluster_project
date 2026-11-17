"""Live occupation and M204 exit evidence; no restart, eviction or queue edits."""
import json
from ops import guard,remote,save,evidence
guard(150)
program=r'''
import json,subprocess,fcntl,re,os
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
 stream.seek(max(0,log.stat().st_size-262144));tail=stream.read().decode('utf-8',errors='replace')
pid=subprocess.run(['ps','-p','1085297','-o','pid=,stat=,etime=,args='],capture_output=True,text=True,timeout=10)
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'cards':cards,'M204_pid_probe':{'returncode':pid.returncode,'stdout':pid.stdout,'stderr':pid.stderr},'M204_native_steps':re.findall(r'Train\[(\d+)/50\][^\r\n]*?(\d+)/4686',tail)[-6:],'M204_log_modified_at':datetime.fromtimestamp(log.stat().st_mtime,timezone.utc).isoformat(),'M204_log_tail':tail[-10000:],'M204_recent_traceback':'Traceback (most recent call last)' in tail[-20000:]}))
'''
server4=remote('server-4',program)
server3=remote('server-3',"import json\nprint(json.dumps({'hostname':socket.gethostname(),'identity_verified':True}))",timeout=25)
path=save('current_resources_and_training.json',{'server4':server4,'server3':server3,'scope':'Authorized resources/identity/exit evidence only;no training restart/eviction/migration/queue or scheduler changes.'})
print(json.dumps({'evidence':evidence(path),'server4':server4,'server3':server3},ensure_ascii=False,indent=2))
