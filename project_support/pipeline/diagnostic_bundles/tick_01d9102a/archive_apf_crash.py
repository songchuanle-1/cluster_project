"""One canonical archive of exact original APF DataLoader crash, never restart."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent;EXP='M219-APF';CID=u.APF;SOURCE=u.SOURCE

def durable(p,v):
 guard()
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY');return
 guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b)
 path=HERE/'apf_end_and_slot_observation.json';assert sha(path)=='de5c2d412933e23bdcb954d7fdd39524b81a73ce04c4c7e38dfcb7e3bc6f7654'
 obs=u.read(path);o=obs['observation'];assert obs['owner']==EXPECTED and o['process']=={'pid':793277,'exists':False}
 assert o['last_TRAIN_progress']==[2,50,301,4686] and not o['explicit_early_stop_lines']
 assert any('Expected dtype int32/int64 for index' in x for x in o['explicit_exception_lines'])
 assert obs['precise_native_validation']['values']==[0.27984941005706787]
 meta=u.read(HERE/'apf_exact_terminal_archive/exact_log_evidence.json');log=ROOT/meta['local']['path']
 assert sha(log)==meta['remote']['sha256']==meta['local']['sha256']=='949ad215b5bbc53f07bbfa64613d3192d10694b6e786289405e623e2eda6d5ab'
 assert meta['remote']['original_pid_absent_before_after'] and meta['remote']['same_config_processes']==[]
 tail=log.read_bytes()[-13000:].decode('utf8',errors='replace')
 assert all(x in tail for x in ['framework/dataset/scannetv2.py','get_sp_label','gt_spmask = torch_scatter.scatter_mean(ref_lbl.float(), superpoint, dim=-1)','Expected dtype int32/int64 for index'])
 assert sha(ROOT/'pipeline/admissions/M219-APF.json')=='71d5ffd471dd4f88b7607375f8e0acca17118126560a6f2b7ac3466bb18d68fe'
 assert not any((HERE/n).exists() for n in ['apf_finalize_intent.json','apf_finalize_result.json'])
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();u.primary_protection(b);queue=mon.load_queue(str(ROOT));task=next(t for rows in queue['gpu_queues'].values() for t in rows if t.get('id')==EXP)
  assert task['status']=='running' and task['pid']==793277 and task['code_commit']==SOURCE and str(task['gpu'])=='0' and task['launch_verified']
  before_queue=copy.deepcopy(queue);ledgers={n:sha(ROOT/'pipeline'/n) for n in b['protected_ledgers']}
  work=u.read(ROOT/'pipeline/research_work.json');digests={c['id']:u.digest(c) for c in work['candidates']};assert len(digests)==145
  c=next(x for x in work['candidates'] if x['id']==CID);assert c['stage']=='training' and c['code_commit']==SOURCE
  journal=ROOT/'pipeline/archive_pending'/(hashlib.sha256(EXP.encode()).hexdigest()+'.json');assert not journal.exists()
  durable(HERE/'apf_finalize_intent.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'task':task,'exact_log':meta['local'],'observation':u.ref(path),'protected_ledgers_before':ledgers,'candidate_digests_before':digests,'scope':'One canonical crashed archive from exact DataLoader traceback. Triggering sample/dtype/RNG/root cause UNKNOWN; no model-hypothesis rejection, source patch, restart or resume.'})
  original=mon.pull_log
  def exact_pull(project_dir,host,user,remote_log,cfg_name,state,srv_name=''):
   assert Path(project_dir).resolve()==ROOT.resolve() and (host,user,remote_log,cfg_name,state,srv_name)==('192.168.1.115','songcl',task['log'],Path(task['config']).stem,'crashed','server-4')
   assert sha(log)==meta['local']['sha256'];return str(log)
  mon.pull_log=exact_pull;events=[]
  try:mon.finalize_task(str(ROOT),queue,'server-4','192.168.1.115','songcl',task,Path(task['config']).stem,'crashed',0.2798,'2/50','0',task['log'],events)
  finally:mon.pull_log=original
  exp=mon.load_experiment(str(ROOT),EXP);assert exp['status']=='crashed' and exp['code_commit']==SOURCE and exp['final_best']=='0.2798' and exp['epochs_final']=='2/50' and exp['log_local']==str(log)
  if exp.get('training_status')!='crashed':exp['training_status']='crashed';mon.save_experiment(str(ROOT),exp)
  now=datetime.now(timezone.utc).isoformat()
  c.setdefault('admission_status_history',[]).append({'recorded_at':now,'admission_status':c.get('admission_status')})
  c.update(stage='complete',training_status='crashed',admission_status='ADMITTED_TRAINING_CRASH_ARCHIVED',queued=False,finished_at=exp['finished_at'],final_best_miou=0.27984941005706787,epochs_final='2/50',terminal_archive_id=exp['archive_id'],completion_outcome='incomplete_training_DataLoader_index_dtype_crash',failure_scope='implementation',next_action='Preserve exact original APF source/d0e2, four technical gates/receipt and full crash log. Diagnose pinned common DataLoader index dtype contract and capture missing triggering input/state before any concrete authorized recovery; no automatic resume or cold start. Independent candidate preparation remains allowed.')
  c['terminal_assessment']={'recorded_at':now,'state':'crashed','last_native_epoch':2,'last_native_step':301,'steps_per_epoch':4686,'native_validation_values':[0.27984941005706787],'best_scope':'Only epoch1 validation, incomplete run; not final method efficacy','failure_domain':'DataLoader worker before this batch entered model forward','observed_exception':'scatter index dtype contract violation','triggering_sample_actual_dtype_RNG_and_upstream_root_cause':'UNKNOWN','hypothesis_falsified':False,'automatic_recovery_authorized':False}
  c.setdefault('resource_check_history',[]).append(copy.deepcopy(c.get('current_resource_check')))
  c['current_resource_check']={'recorded_at':now,'result':'original_APF_crashed_registered_slot_canonically_cleared','evidence':u.ref(path),'scope':'Dated physicalGPU0 idle proof only, fresh checks required before any new test.'}
  for r in [u.ref(path),u.ref(HERE/'apf_exact_terminal_archive/exact_log_evidence.json'),u.ref(log),u.ref(HERE/'apf_terminal_input_dtype_independent_review.json')]:
   if r not in c['evidence']:c['evidence'].append(r)
  work['updated_at']=now;work['last_terminal_event']={'recorded_at':now,'experiment_id':EXP,'status':'crashed','archive_id':exp['archive_id'],'domain':'DataLoader index dtype'}
  assert all(u.digest(x)==digests[x['id']] for x in work['candidates'] if x['id']!=CID)
  u.atomic(ROOT/'pipeline/research_work.json',work)
  q=mon.load_queue(str(ROOT));old=copy.deepcopy(before_queue)
  for rows in old['gpu_queues'].values():rows[:]=[t for t in rows if t.get('id')!=EXP]
  assert q==old and not journal.exists()
  assert all(sha(ROOT/'pipeline'/n)==h for n,h in ledgers.items() if n not in {'queue.json','running.json','experiments.csv','experiments/M219-APF.json'})
  u.primary_protection(b)
  durable(HERE/'apf_finalize_result.json',{'owner':EXPECTED,'recorded_at':now,'status':'CANONICAL_CRASHED_AND_RESEARCH_TERMINAL_RECORDED','experiment_id':EXP,'archive_id':exp['archive_id'],'state':'crashed','printed_best':'0.2798','exact_logger_best':0.27984941005706787,'epochs':'2/50','last_native_step':301,'observed_exception':'DataLoader scatter index dtype contract violation','root_cause_and_triggering_input':'UNKNOWN','exact_full_log':meta['local'],'events':events,'no_signals_restart_patch_or_new_training':True,'other_candidates_and_lifecycle_preserved':True})
  print(json.dumps({'state':'crashed','archive_id':exp['archive_id'],'result':u.ref(HERE/'apf_finalize_result.json')}))
 finally:lock.close()
if __name__=='__main__':main()
