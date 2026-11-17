"""Root-only minimal alignment to ALREADY canonical archived AEF; default no writes."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent;TICK=HERE.parent
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard,sha
REPO=ROOT/'Cluster';GIT=Path('C:/Program Files (x86)/Git/cmd/git.exe')
EXP='M216-AEF';CID='hierarchy-parent-antisymmetric-edge-flux'
SOURCE='56b2a96dc48cc8a88f0f7105527ef448113b1060'
RECEIPT={'path':'pipeline/admissions/M216-AEF.json','sha256':'041074985258a51cf2a5629dcbf19f55fceb42c5255c78251c1fb9cc680ae9a9'}
ARCHIVE_SHA='38278aa809d0cb43f90dd937f624b5c508efe822fe8fdb581d1455d55e4d6530'
# Canonical printed metric remains four decimals; precise native validation log maximum is distinct.
EXACT_NATIVE_BEST=0.495597243309021;PRINTED_BEST=0.4956;EPOCHS='23/50'

def read(p):return json.loads(Path(p).read_text('utf8'))
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def owner():
 guard();assert os.environ.get('GIT_OPTIONAL_LOCKS')=='0' and sys.dont_write_bytecode
 assert EXPECTED['token']=='0f02aaa25b1a4f6e9d27cf8da33b8ca1'
def exclusive(p,b):
 owner()
 with Path(p).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def git(*args):
 assert args in [('rev-parse','HEAD'),('status','--porcelain=v1','-z','--untracked-files=all'),('diff','--cached','--name-only','-z'),('rev-parse','--git-path','index')]
 p=subprocess.run([str(GIT),'--no-optional-locks','-c','core.fsmonitor=false','-C',str(REPO),*args],capture_output=True,timeout=20,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'))
 assert p.returncode==0,p.stderr.decode('utf8',errors='replace');return p.stdout
def protected(baseline):
 assert git('rev-parse','HEAD').decode().strip()==baseline['head']==SOURCE
 assert git('status','--porcelain=v1','-z','--untracked-files=all').hex()==baseline['status_hex']
 assert not git('diff','--cached','--name-only','-z') and baseline['index_empty'] is True
 assert len(baseline['files'])==28 and {n:sha(REPO/n) for n in baseline['files']}==baseline['files']
 index=Path(git('rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else REPO/index
 return {'head':SOURCE,'status_hex':baseline['status_hex'],'index_sha256':sha(index),'protected28':baseline['files'],'ledgers':{n:sha(ROOT/'pipeline'/n) for n in baseline['protected_ledgers']}}
def contains_id(v):
 if isinstance(v,dict):return any(contains_id(x) for x in v.values())
 if isinstance(v,list):return any(contains_id(x) for x in v)
 return v==EXP

def execute():
 owner()
 for n in ['aef_lifecycle_intent.json','aef_lifecycle_result.json']:
  assert not (HERE/n).exists(),'Existing/partial lifecycle alignment: read-only reconcile; never replay'
 tmp=ROOT/'pipeline/research_work.json.0f02aaa2.aef_lifecycle.tmp';assert not tmp.exists()
 assert sha(ROOT/RECEIPT['path'])==RECEIPT['sha256'] and sha(TICK/'aef_finalize_result.json')==ARCHIVE_SHA
 final=read(TICK/'aef_finalize_result.json');obs=read(TICK/'aef_end_and_slot_observation.json');logmeta=read(TICK/'aef_exact_terminal_archive/exact_log_evidence.json')
 assert final['status']=='CANONICAL_DONE_EARLYSTOP_RECORDED' and final['experiment_id']==EXP and final['archive_id']=='ad76de1eebbd43f7be720a8b17fca1cb'
 assert final['best']=='0.4956' and final['epochs']==EPOCHS and final['source_commit']==SOURCE and final['new_training_launches']==0 and final['canonical_pending_absent'] is True
 assert obs['owner']==EXPECTED and obs['observation']['process']=={'pid':759301,'exists':False}
 assert obs['observation']['explicit_early_stop_lines']==['Early stopping at epoch 23: no improvement for 10 epochs (best=0.4956)'] and obs['observation']['explicit_exception_lines']==[]
 assert obs['precise_native_validation']['best']==EXACT_NATIVE_BEST and obs['precise_native_validation']['no_improve']==10
 assert final['exact_full_log']==logmeta['local']
 baseline=read(TICK/'protected_assets_before.json');assert len(baseline['protected_ledgers'])==16
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  owner();before=protected(baseline)
  # Canonical archive already changed these four legitimately. All other12 stay begin-exact.
  archive_changes={'queue.json','running.json','experiments.csv','experiments/'+EXP+'.json'}
  assert all(before['ledgers'][n]==h for n,h in baseline['protected_ledgers'].items() if n not in archive_changes)
  q=read(ROOT/'pipeline/queue.json');running=read(ROOT/'pipeline/running.json')
  assert not any(t.get('id')==EXP for rows in q['gpu_queues'].values() for t in rows) and not contains_id(running)
  exp=mon.load_experiment(str(ROOT),EXP);assert exp['status']=='done_earlystop' and exp['final_best']=='0.4956' and exp['epochs_final']==EPOCHS
  assert exp['archive_id']==final['archive_id'] and exp['code_commit']==SOURCE and exp['admission_receipt']==RECEIPT['path'] and exp['launch_verified'] is True and exp['training_status']=='running'
  exp_before=copy.deepcopy(exp);exp['training_status']='done_earlystop'
  work=read(ROOT/'pipeline/research_work.json');work_before=copy.deepcopy(work);matches=[c for c in work['candidates'] if c.get('id')==CID];assert len(matches)==1;c=matches[0]
  assert c['experiment_id']==EXP and c['stage']=='training' and c.get('training_status')=='running' and c['code_commit']==SOURCE and c['source_commit']==SOURCE and c['admission_receipt']==RECEIPT
  before_digests={x['id']:digest(x) for x in work['candidates']};assert before_digests==baseline['candidate_digests']
  now=datetime.now(timezone.utc).isoformat()
  c.update(stage='complete',training_status='done_earlystop',finished_at=exp_before['finished_at'],final_best_miou=EXACT_NATIVE_BEST,epochs_final=EPOCHS,terminal_archive_id=final['archive_id'],terminal_log_metric_scope='Native validation logger maximum0.495597243309021; four-decimal earlystop/canonical best0.4956 retained separately. Checkpoint body not read.',completion_outcome='native_earlystop_no_champion_gain_this_realization',next_action='Preserve AEF exact source56/receipt/native-resource gates/original logs and all negative evidence. Native normal earlystop23/50 precise logger best0.495597243309021 did not exceed stored M95 .5020. No automatic restart, tuning, new model revision or whole-family falsification. Continue other independently admitted candidates under fresh resource guards.')
  c['terminal_assessment']={'recorded_at':now,'native_validation_logger_best_miou':EXACT_NATIVE_BEST,'native_printed_earlystop_best_miou':PRINTED_BEST,'stored_M95_miou':0.5020,'delta_vs_stored_M95':EXACT_NATIVE_BEST-0.5020,'checkpoint_exact_best_read':False,'scope':'This one realization completed below stored M95; no whole-mechanism falsification or automatic restart/tuning.'}
  for p in [TICK/'aef_finalize_result.json',TICK/'aef_end_and_slot_observation.json',TICK/'aef_exact_terminal_archive/exact_log_evidence.json']:
   e=ref(p)
   if e not in c.setdefault('evidence',[]):c['evidence'].append(e)
  work['updated_at']=now
  assert len(work['candidates'])==len(work_before['candidates']) and all(digest(x)==before_digests[x['id']] for x in work['candidates'] if x['id']!=CID)
  # Serialize every future shared payload BEFORE the exclusive operation intent.
  work_bytes=encoded(work);exp_bytes=encoded(exp)
  intent=encoded({'owner':EXPECTED,'recorded_at':now,'canonical_result':ref(TICK/'aef_finalize_result.json'),'before':before,'research_before_sha256':sha(ROOT/'pipeline/research_work.json'),'experiment_before':exp_before,'candidate_before':next(x for x in work_before['candidates'] if x['id']==CID),'planned_research_sha256':hashlib.sha256(work_bytes).hexdigest(),'planned_experiment_json_sha256':hashlib.sha256(exp_bytes).hexdigest(),'allowed_mutations':'Only AEF research terminal fields/evidence and its experiment auxiliary training_status. No finalize_task replay/source/receipt/queue/running/CSV/native/GPU action.'})
  owner();assert protected(baseline)==before and read(ROOT/'pipeline/research_work.json')==work_before
  exclusive(HERE/'aef_lifecycle_intent.json',intent)
  owner();mon.save_experiment(str(ROOT),exp)
  exclusive(tmp,work_bytes);owner();os.replace(tmp,ROOT/'pipeline/research_work.json')
  after=protected(baseline);assert all(after[k]==before[k] for k in ['head','status_hex','index_sha256','protected28'])
  assert all(after['ledgers'][n]==h for n,h in before['ledgers'].items() if n!='experiments/'+EXP+'.json')
  current=mon.load_experiment(str(ROOT),EXP);assert {k:v for k,v in current.items() if k!='training_status'}=={k:v for k,v in exp_before.items() if k!='training_status'} and current['training_status']=='done_earlystop'
  saved=read(ROOT/'pipeline/research_work.json');assert saved==work and sha(ROOT/RECEIPT['path'])==RECEIPT['sha256']
  exclusive(HERE/'aef_lifecycle_result.json',encoded({'recorded_at':now,'status':'AEF_RESEARCH_COMPLETE_AND_AUXILIARY_STATUS_ALIGNED_TO_EXISTING_CANONICAL_ARCHIVE','canonical_result':ref(TICK/'aef_finalize_result.json'),'canonical_status':'done_earlystop','archive_id':final['archive_id'],'stage':'complete','auxiliary_training_status':'done_earlystop','precise_native_logger_best':EXACT_NATIVE_BEST,'printed_canonical_best':'0.4956','epochs':EPOCHS,'experiment_only_auxiliary_field_changed':True,'other15_postarchive_ledgers_and_other_candidates_preserved':True,'original_source_receipt_raw_negative_evidence_preserved':True,'new_native_restart_signal_or_launch':False,'before':before,'after':after}))
  print('AEF research complete/auxiliary done_earlystop aligned; no canonical archive replay/source/receipt/queue/native change.')
 finally:lock.close()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_SHARED_WRITE');return
 execute()
if __name__=='__main__':main()
