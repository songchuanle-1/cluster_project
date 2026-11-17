"""Apply the user's explicit GPU1 withdrawal after old lease release."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert os.environ.get('CODEX_THREAD_ID')=='01a159c5-29ab-7a22-ba7f-e79174757253'
 old=json.loads((ROOT/'pipeline/tick_receipts/45eb3b045c6243518d56eade38d5cd17.json').read_text('utf8'))
 assert old['status']=='FINALIZED' and old['lease_release']=='released'
 assert not (ROOT/'pipeline/headless/.foreground.lockdir').exists() and not (ROOT/'pipeline/headless/.tick_context_state.next.json').exists()
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  assert not (HERE/'applied.json').exists() and not (HERE/'intent.json').exists()
  servers=ROOT/'SERVERS.yaml';before=servers.read_bytes();assert hashlib.sha256(before).hexdigest()=='d5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2'
  text=before.decode('utf8');old_line='    allowed_gpus: [0, 1]   # User 2026-10-25 reauthorizes GPU1; one task per card.'
  new_line='    allowed_gpus: [0]   # User 2026-10-26: do not use GPU1; GPU0 only.'
  assert text.count(old_line)==1;updated=text.replace(old_line,new_line).encode('utf8')
  auth=ROOT/'pipeline/authorizations/server4_gpu0_only_20261026.json';assert not auth.exists()
  now=datetime.now(timezone.utc).isoformat();record={'schema_version':1,'recorded_at':now,'source':'Direct human instruction in owning chat','thread_id':os.environ['CODEX_THREAD_ID'],'verbatim_user_instruction':'不用gpu1',
   'project':'cluster_project','server':'server-4','allowed_physical_gpus':[0],'gpu0_uuid':'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c','max_tasks_per_gpu':1,
   'supersedes_future_GPU1_allocation':'pipeline/authorizations/server4_gpu1_20261025.json','effective_scope':'Immediate future computation/dispatch ban on GPU1; historical lawful GPU1 evidence remains bound to original GPU/time. No scheduler or other project change.',
   'SERVERS_before_sha256':hashlib.sha256(before).hexdigest(),'SERVERS_after_sha256':hashlib.sha256(updated).hexdigest(),'old_foreground_tick':'45eb3b045c6243518d56eade38d5cd17','old_tick_finalized_and_released':True,'gpu1_new_training_started':False}
  with (HERE/'intent.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  with auth.open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  temp=servers.with_name('SERVERS.yaml.gpu0_only.tmp')
  with temp.open('xb') as f:f.write(updated);f.flush();os.fsync(f.fileno())
  os.replace(temp,servers)
  srv=monitor.load_servers(str(ROOT))['server-4'];assert srv['allowed_gpus']==[0] and srv['max_tasks_per_gpu']==1 and srv['dispatch_enabled'] is True
  q=monitor.load_queue(str(ROOT));assert not any(t.get('status') in ('running','claiming') and str(t.get('gpu'))=='1' for t in q['gpu_queues']['server-4'])
  args=['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','manual','User requests 不用gpu1','Disable future server4GPU1 computation and dispatch; only physicalGPU0 remains allowed. Preserve native history, M206 user pause and existing scheduler.',
   'Direct human instruction supersedes 20261025 GPU1 grant prospectively. Old foreground snapshot was finalized/released before resource mutation; no GPU1 new training was launched.',str(auth)+' SHA'+sha(auth)+'; SERVERS SHA'+sha(servers)]
  logged=subprocess.run(args,capture_output=True,text=True,encoding='utf8',timeout=30);assert logged.returncode==0,logged.stderr
  result={'recorded_at':now,'authorization':{'path':auth.relative_to(ROOT).as_posix(),'sha256':sha(auth)},'servers_sha256':sha(servers),'allowed_gpus':[0],'manual_decision_stdout':logged.stdout,'scheduler_changed':False,'old_tick_report_or_memory_rewritten':False}
  with (HERE/'applied.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
  print(json.dumps(result,ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
