"""Canonical archival of the exact naturally finished BTC run only."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, re, shutil, sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='336ca5d7348b4018b7fd8b9e41f6eee3'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
 t=p.with_name(p.name+'.'+TOKEN+'.tmp')
 with t.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def main():
 guard();proof=read(HERE/'btc_full_terminal_log_evidence.json');obs=read(HERE/'btc_terminal_or_phase_observation.json')['observation']
 assert obs['process']['present'] is False and not obs['contexts']
 assert proof['owner_token']==TOKEN and proof['terminal']=='done_earlystop' and proof['remote']['original_pid_absent']
 source=ROOT/proof['full_original_native_log']['path'];assert sha(source)==proof['remote']['sha256']=='2b4032d0b705ae7f5e8ebdba81f14d5ed7eb55da491b4b9fec2ba78342aba38c'
 text=source.read_text('utf8',errors='replace');assert 'Early stopping at epoch 31: no improvement for 10 epochs (best=0.4914)' in text and 'Traceback (most recent call last)' not in text
 assert tuple(map(int,re.findall(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text)[-1]))==(31,50,4686,4686)
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None;original=monitor.pull_log
 try:
  guard();q=monitor.load_queue(str(ROOT));task=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M211-BTC')
  assert task['pid']==2784474 and task['status']=='running' and str(task['gpu'])=='0' and task['launch_verified'] is True
  assert task['code_commit']=='00e2b18c6b8d568a64edb496e6979d766440883c' and task['log']==obs['log']==proof['remote']['path']
  before_task=copy.deepcopy(task);others=copy.deepcopy([t for t in q['gpu_queues']['server-4'] if t['id']!='M211-BTC'])
  protected=['experiments/M212-BCR.json','experiments/M206-CGCA.json','admissions/M211-BTC.json','admissions/M212-BCR.json'];before={n:sha(ROOT/'pipeline'/n) for n in protected}
  running_before=monitor.load_running(str(ROOT));bcr_running=copy.deepcopy(running_before.get('server-4',{}).get('1'))
  cfg=Path(task['config']).stem;local=ROOT/'Checkpoints/server_4'/cfg/'native_earlystop_336ca5d7'/Path(task['log']).name
  local.parent.mkdir(parents=True,exist_ok=True);assert not local.exists()
  with source.open('rb') as src,local.open('xb') as dst:shutil.copyfileobj(src,dst)
  assert sha(local)==proof['remote']['sha256']
  def exact_pull(project,host,user,remote_log,cfg_name,state,srv_name=''):
   assert Path(project)==ROOT and (host,user,state,srv_name)==('192.168.1.115','songcl','done_earlystop','server-4')
   assert remote_log==task['log'] and cfg_name==cfg and sha(local)==proof['remote']['sha256'];return str(local)
  monitor.pull_log=exact_pull;events=[]
  monitor.finalize_task(str(ROOT),q,'server-4','192.168.1.115','songcl',task,cfg,'done_earlystop',0.4914,'31/50',task['gpu'],task['log'],events)
  exp=monitor.load_experiment(str(ROOT),'M211-BTC');exp['training_status']='done_earlystop';monitor.save_experiment(str(ROOT),exp)
  assert exp['code_commit']==task['code_commit'] and exp['admission_receipt']==task['admission_receipt'] and exp['launch_verified'] is True
  after=monitor.load_queue(str(ROOT));assert after['gpu_queues']['server-4']==others
  assert monitor.load_running(str(ROOT)).get('server-4',{}).get('1')==bcr_running
  assert before=={n:sha(ROOT/'pipeline'/n) for n in protected}
  work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c.get('experiment_id')=='M211-BTC')
  c.update(stage='complete',training_status='done_earlystop',finished_at=exp['finished_at'],final_best_miou=0.4914,epochs_final='31/50',next_action='Preserve exact original BTC native earlystop31/best0.4914 and all admission/source/launch history. This run did not exceed M95 .5020; no restart/tuning or whole-hierarchy hypothesis rejection. Prepared BFC may use only actually idle authorized GPU0 under fresh original owner/assets/three-lock checks; BCR GPU1 and M206pause stay protected.')
  for p in [HERE/'btc_terminal_or_phase_observation.json',HERE/'btc_full_terminal_log_evidence.json']:
   item=ref(p)
   if item not in c['evidence']:c['evidence'].append(item)
  work['updated_at']=datetime.now(timezone.utc).isoformat();guard();save(ROOT/'pipeline/research_work.json',work)
  out={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'canonical_function':'pipeline_monitor.finalize_task','exact_log_adapter':True,'events':events,'original_queue_task':before_task,'archived_experiment':exp,'full_original_log':ref(local),'BCR_queue_running_experiment_and_M206_pause_unchanged':True,'admission_source_launch_proof_preserved':True,'signals_sent':False,'monitor_preflight_repeated':False,'source_changed':False}
  with (HERE/'btc_terminal_archive.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
  print(json.dumps({'status':exp['status'],'best':exp['final_best'],'epochs':exp['epochs_final'],'archive_id':exp['archive_id'],'evidence':ref(HERE/'btc_terminal_archive.json')}))
 finally:monitor.pull_log=original;lock.close()
if __name__=='__main__':main()
