"""Archive only two proven original terminal runs via canonical finalize_task."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');TOKEN='45eb3b045c6243518d56eade38d5cd17'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
 temporary=p.with_name(p.name+'.'+TOKEN+'.tmp')
 with temporary.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(temporary,p)
def main():
 guard();assert not any((HERE/n).exists() for n in ['exact_archive_intent.json','exact_terminal_archive_result.json'])
 proof_path=HERE/'full_terminal_log_evidence.json';proof=read(proof_path);phase_path=HERE/'original_phase_reconciliation.json';phase=read(phase_path)
 assert sha(proof_path)=='6304243523380f887494a7119d5c5c7b5b751469298f553d3db26e013ff8fbd9' and proof['owner_token']==TOKEN
 assert sha(phase_path)=='e6355b9b3e90bf377a869e73dd7b9e21f4e688f4dcea00d59a3ae52d1b965d44'
 assert all(t['process']['present'] is False and not t['gpu_contexts'] for t in phase['result']['tasks'])
 expected={'M213-BFC':(219369,'48fc302c3c02ffef0b241be3593c386b6b65a72e','crashed','20/50'),'M212-BCR':(1215422,'11a811618179ab1ddc0cee299194667413b7fdb9','done_earlystop','27/50')}
 for item in proof['results']:
  assert item['id'] in expected and item['state']==expected[item['id']][2] and item['epochs']==expected[item['id']][3]
  assert item['remote']['original_pid_absent'] and not item['remote']['gpu_contexts'] and item['remote']['log_age_seconds']>600
  p=ROOT/item['full_original_native_log']['path'];assert sha(p)==item['remote']['sha256'] and p.stat().st_size==item['remote']['bytes']
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None;original=monitor.pull_log
 try:
  guard();q=monitor.load_queue(str(ROOT));before=copy.deepcopy(q);protected={n:sha(ROOT/'pipeline'/n) for n in ['experiments/M206-CGCA.json','admissions/M212-BCR.json','admissions/M213-BFC.json','experiments/M211-BTC.json']}
  for eid,(pid,commit,state,epoch) in expected.items():
   t=next(t for t in q['gpu_queues']['server-4'] if t['id']==eid)
   assert t['status']=='running' and t['pid']==pid and t['code_commit']==commit and t['launch_verified'] is True
   d=next(x for x in proof['results'] if x['id']==eid);assert t['log']==d['remote']['path']
   pending=ROOT/'pipeline/archive_pending'/(hashlib.sha256(eid.encode()).hexdigest()+'.json');assert not pending.exists()
  with (HERE/'exact_archive_intent.json').open('x',encoding='utf8') as f:
   json.dump({'token':TOKEN,'helper_sha256':sha(Path(__file__)),'queue_before_sha256':sha(ROOT/'pipeline/queue.json'),'original_queue_tasks':[t for t in q['gpu_queues']['server-4'] if t['id'] in expected],
    'scope':'Exact original terminal archival only via canonical finalize_task; interrupted archive_pending must recover, never replay.'},f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  results=[]
  for d in proof['results']:
   guard();task=next(t for t in q['gpu_queues']['server-4'] if t['id']==d['id']);cfg=Path(task['config']).stem;local=ROOT/d['full_original_native_log']['path']
   def exact_pull(project,host,user,remote_log,cfg_name,state,srv_name=''):
    assert Path(project)==ROOT and (host,user,srv_name)==('192.168.1.115','songcl','server-4')
    assert remote_log==task['log']==d['remote']['path'] and cfg_name==cfg and state==d['state'] and sha(local)==d['remote']['sha256'];return str(local)
   monitor.pull_log=exact_pull;events=[]
   monitor.finalize_task(str(ROOT),q,'server-4','192.168.1.115','songcl',task,cfg,d['state'],d['best_miou'],d['epochs'],task['gpu'],task['log'],events)
   exp=monitor.load_experiment(str(ROOT),d['id']);exp['training_status']=d['state']
   exp['terminal_log_metric_scope']=d['best_scope'];monitor.save_experiment(str(ROOT),exp)
   assert exp['code_commit']==task['code_commit'] and exp['admission_receipt']==task['admission_receipt'] and exp['launch_verified'] is True
   results.append({'id':d['id'],'state':exp['status'],'archive_id':exp['archive_id'],'best':exp['final_best'],'metric_scope':d['best_scope'],'epochs':exp['epochs_final'],'log':ref(local),'events':events})
  after=monitor.load_queue(str(ROOT));target=copy.deepcopy(before);target['gpu_queues']['server-4']=[t for t in before['gpu_queues']['server-4'] if t['id'] not in expected]
  assert after==target and all(sha(ROOT/'pipeline'/n)==h for n,h in protected.items())
  assert not monitor.load_running(str(ROOT)).get('server-4',{})
  work=read(ROOT/'pipeline/research_work.json');old=copy.deepcopy(work)
  for c in work['candidates']:
   if c.get('experiment_id') not in expected:continue
   d=next(x for x in proof['results'] if x['id']==c['experiment_id']);exp=monitor.load_experiment(str(ROOT),d['id'])
   c.update(training_status=d['state'],finished_at=exp['finished_at'],final_best_miou=d['best_miou'],epochs_final=d['epochs'],terminal_log_metric_scope=d['best_scope'])
   if d['id']=='M212-BCR':
    c.update(stage='complete',next_action='Preserve original BCR native earlystop27/best0.4995 and exact source11a/receipt/launch proof. It did not exceed completed M95 .5020; no tuning/restart or whole-hierarchy rejection.')
   else:
    c.update(stage='blocked',blocker_kind='human_authorization',blocker='Original BFC interrupted at TRAIN20:3832 by shared dataset/scatter RuntimeError before model forward. Recovery needs concrete full-checkpoint/runtime verification and BFC-specific native resume authorization; no automatic restart or source patch.',
     retry_after=(datetime.now(timezone.utc)+timedelta(hours=4)).isoformat(),unblock_condition='Prepare and verify exact original full checkpoint/source recovery plan, then obtain experiment-specific human resume authorization required by native entry. Preserve original crash and partial-epoch limits.',
     next_action='Investigate dataset/scatter overlap with exact failing input and actual installed library before proposing a fix; do not infer clone solves it. Verify original complete checkpoint on CPU, optimizer/scheduler/best/patience/source, expose RNG/sampler limits, prepare concrete reviewed BFC recovery plan before asking for its specific resume authorization. Do not borrow HAP/M206 grants or cold restart. This runtime interruption does not falsify BFC. CTS/BEC proceed independently.')
   for p in [phase_path,proof_path]:
    item=ref(p)
    if item not in c['evidence']:c['evidence'].append(item)
  permitted={c['id'] for c in old['candidates'] if c.get('experiment_id') in expected}
  assert [c for c in old['candidates'] if c['id'] not in permitted]==[c for c in work['candidates'] if c['id'] not in permitted]
  work['updated_at']=datetime.now(timezone.utc).isoformat();guard();save(ROOT/'pipeline/research_work.json',work)
  out={'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),'canonical_function':'pipeline_monitor.finalize_task','full_original_proof':ref(proof_path),'results':results,
   'exact_native_log_adapter':True,'source_admission_launch_preserved':True,'M206_and_all_other_queue_tasks_unchanged':True,'deathwatch_threshold_or_counter_changed_by_wrapper':False,'source_or_remote_state_changed':False,'signals_sent':False}
  with (HERE/'exact_terminal_archive_result.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
  print(json.dumps({'results':results,'evidence':ref(HERE/'exact_terminal_archive_result.json')},ensure_ascii=False))
 finally:monitor.pull_log=original;lock.close()
if __name__=='__main__':main()
