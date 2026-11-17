"""Root-only minimal alignment to ALREADY canonical archived CRE; default no writes."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent;TICK=HERE.parent
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard,sha
REPO=ROOT/'Cluster';GIT=Path('C:/Program Files (x86)/Git/cmd/git.exe')
EXP='M217-CRE';CID='hierarchy-cross-root-directed-edge-broadcast'
SOURCE='d58576b396cfb54577652be972f3ffaffda508c9'
RECEIPT={'path':'pipeline/admissions/M217-CRE.json','sha256':'0ab8d1bd7e518322c25ae36bb80344fb62f90c150e5ca09bd856cb53d0a6320b'}
ARCHIVE_SHA='1441262e2c046f93585b816d0cfb77f81f9607a494ae33578ccd4522cf7fb7fc'
# Canonical printed metric remains four decimals; precise native validation log maximum is distinct.
EXACT_NATIVE_BEST=0.4961479902267456;PRINTED_BEST=0.4961;EPOCHS='30/50'

def read(p):return json.loads(Path(p).read_text('utf8'))
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def owner():
 guard();assert os.environ.get('GIT_OPTIONAL_LOCKS')=='0' and sys.dont_write_bytecode
 assert EXPECTED['token']=='2b832a02d63c4182aeb90c38014ee5da'
def exclusive(p,b):
 owner()
 with Path(p).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def git(*args):
 assert args in [('rev-parse','HEAD'),('status','--porcelain=v1','-z','--untracked-files=all'),('diff','--cached','--name-only','-z'),('rev-parse','--git-path','index')]
 p=subprocess.run([str(GIT),'--no-optional-locks','-c','core.fsmonitor=false','-C',str(REPO),*args],capture_output=True,timeout=20,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'))
 assert p.returncode==0,p.stderr.decode('utf8',errors='replace');return p.stdout
def protected(baseline):
 head=git('rev-parse','HEAD').decode().strip();assert len(head)==40
 assert git('status','--porcelain=v1','-z','--untracked-files=all').hex()==baseline['status_hex']
 assert not git('diff','--cached','--name-only','-z') and baseline['index_empty'] is True
 assert len(baseline['files'])==28 and {n:sha(REPO/n) for n in baseline['files']}==baseline['files']
 index=Path(git('rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else REPO/index
 return {'head':head,'status_hex':baseline['status_hex'],'index_sha256':sha(index),'protected28':baseline['files'],'ledgers':{n:sha(ROOT/'pipeline'/n) for n in sorted(set(baseline['protected_ledgers'])|{'experiments/M218-HPC.json','admissions/M218-HPC.json','experiments/M219-APF.json','admissions/M219-APF.json'}) if (ROOT/'pipeline'/n).is_file()}}
def contains_id(v):
 if isinstance(v,dict):return any(contains_id(x) for x in v.values())
 if isinstance(v,list):return any(contains_id(x) for x in v)
 return v==EXP

def execute():
 owner()
 for n in ['cre_lifecycle_intent.json','cre_lifecycle_result.json']:
  assert not (HERE/n).exists(),'Existing/partial lifecycle alignment: read-only reconcile; never replay'
 tmp=ROOT/'pipeline/research_work.json.2b832a02.cre_lifecycle.tmp';assert not tmp.exists()
 assert sha(ROOT/RECEIPT['path'])==RECEIPT['sha256'] and sha(TICK/'cre_finalize_result.json')==ARCHIVE_SHA
 final=read(TICK/'cre_finalize_result.json');obs=read(TICK/'cre_end_and_slot_observation.json');logmeta=read(TICK/'cre_exact_terminal_archive/exact_log_evidence.json')
 assert final['status']=='CANONICAL_DONE_EARLYSTOP_RECORDED' and final['experiment_id']==EXP and final['archive_id']=='0177c22e3480465bac304836253de8aa'
 assert final['best']=='0.4961' and final['epochs']==EPOCHS and final['source_commit']==SOURCE and final['new_training_launches']==0 and final['canonical_pending_absent'] is True
 assert obs['owner']==EXPECTED and obs['observation']['process']=={'pid':118189,'exists':False}
 assert obs['observation']['explicit_early_stop_lines']==['Early stopping at epoch 30: no improvement for 10 epochs (best=0.4961)'] and obs['observation']['explicit_exception_lines']==[]
 assert obs['precise_native_validation']['best']==EXACT_NATIVE_BEST and obs['precise_native_validation']['no_improve']==10
 assert final['exact_full_log']==logmeta['local']
 baseline=read(TICK/'protected_assets_before.json');assert len(baseline['protected_ledgers'])==18
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  owner();before=protected(baseline)
  # Canonical archive already changed these four legitimately. All other14 stay begin-exact; optional new HPC/APF ledgers are protected from this alignment start.
  archive_changes={'queue.json','running.json','experiments.csv','experiments/'+EXP+'.json'}
  assert all(before['ledgers'][n]==h for n,h in baseline['protected_ledgers'].items() if n not in archive_changes)
  q=read(ROOT/'pipeline/queue.json');running=read(ROOT/'pipeline/running.json')
  assert not any(t.get('id')==EXP for rows in q['gpu_queues'].values() for t in rows) and not contains_id(running)
  exp=mon.load_experiment(str(ROOT),EXP);assert exp['status']=='done_earlystop' and exp['final_best']=='0.4961' and exp['epochs_final']==EPOCHS
  assert exp['archive_id']==final['archive_id'] and exp['code_commit']==SOURCE and exp['admission_receipt']==RECEIPT['path'] and exp['launch_verified'] is True and exp['training_status']=='running'
  exp_before=copy.deepcopy(exp);exp['training_status']='done_earlystop'
  work=read(ROOT/'pipeline/research_work.json');work_before=copy.deepcopy(work);matches=[c for c in work['candidates'] if c.get('id')==CID];assert len(matches)==1;c=matches[0]
  assert c['experiment_id']==EXP and c['stage']=='training' and c.get('training_status')=='running' and c['code_commit']==SOURCE and c['source_commit']==SOURCE and c['admission_receipt']==RECEIPT
  before_digests={x['id']:digest(x) for x in work['candidates']};assert set(before_digests)==set(baseline['candidate_digests'])
  now=datetime.now(timezone.utc).isoformat()
  c.update(stage='complete',training_status='done_earlystop',finished_at=exp_before['finished_at'],final_best_miou=EXACT_NATIVE_BEST,epochs_final=EPOCHS,terminal_archive_id=final['archive_id'],terminal_log_metric_scope='Native validation logger maximum0.4961479902267456; four-decimal earlystop/canonical best0.4961 retained separately. Checkpoint body not read.',completion_outcome='native_earlystop_no_champion_gain_this_realization',next_action='Preserve CRE exact sourced585/receipt/native-resource gates/original logs and all negative evidence. Native normal earlystop30/50 precise logger best0.4961479902267456 did not exceed stored M95 .5020. No automatic restart, tuning, new model revision or whole-family falsification. Continue other independently admitted candidates under fresh resource guards.')
  c['terminal_assessment']={'recorded_at':now,'native_validation_logger_best_miou':EXACT_NATIVE_BEST,'native_printed_earlystop_best_miou':PRINTED_BEST,'stored_M95_miou':0.5020,'delta_vs_stored_M95':EXACT_NATIVE_BEST-0.5020,'checkpoint_exact_best_read':False,'scope':'This one realization completed below stored M95; no whole-mechanism falsification or automatic restart/tuning.'}
  c.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check')),'reason':'Canonical original CRE normal terminal reconciliation; historical observation retained.'})
  c['current_resource_check']={'recorded_at':now,'kind':'terminal_reconciliation','result':'original_CRE_done_earlystop_canonical_archive','evidence':ref(TICK/'cre_finalize_result.json'),'scope':'Original CRE118189 has ended and its registered slot was canonically cleared. This is not current GPU idleness or permission for a future job; root may already be running HPC diagnostics.'}
  for p in [TICK/'cre_finalize_result.json',TICK/'cre_end_and_slot_observation.json',TICK/'cre_exact_terminal_archive/exact_log_evidence.json']:
   e=ref(p)
   if e not in c.setdefault('evidence',[]):c['evidence'].append(e)
  work['updated_at']=now
  assert len(work['candidates'])==len(work_before['candidates']) and all(digest(x)==before_digests[x['id']] for x in work['candidates'] if x['id']!=CID)
  # Serialize every future shared payload BEFORE the exclusive operation intent.
  work_bytes=encoded(work);exp_bytes=encoded(exp)
  intent=encoded({'owner':EXPECTED,'recorded_at':now,'canonical_result':ref(TICK/'cre_finalize_result.json'),'before':before,'research_before_sha256':sha(ROOT/'pipeline/research_work.json'),'experiment_before':exp_before,'candidate_before':next(x for x in work_before['candidates'] if x['id']==CID),'planned_research_sha256':hashlib.sha256(work_bytes).hexdigest(),'planned_experiment_json_sha256':hashlib.sha256(exp_bytes).hexdigest(),'allowed_mutations':'Only CRE research terminal fields/evidence and its experiment auxiliary training_status. No finalize_task replay/source/receipt/queue/running/CSV/native/GPU action.'})
  owner();assert protected(baseline)==before and read(ROOT/'pipeline/research_work.json')==work_before
  exclusive(HERE/'cre_lifecycle_intent.json',intent)
  owner();mon.save_experiment(str(ROOT),exp)
  exclusive(tmp,work_bytes);owner();os.replace(tmp,ROOT/'pipeline/research_work.json')
  after=protected(baseline);assert all(after[k]==before[k] for k in ['head','status_hex','index_sha256','protected28'])
  assert all(after['ledgers'][n]==h for n,h in before['ledgers'].items() if n!='experiments/'+EXP+'.json')
  current=mon.load_experiment(str(ROOT),EXP);assert {k:v for k,v in current.items() if k!='training_status'}=={k:v for k,v in exp_before.items() if k!='training_status'} and current['training_status']=='done_earlystop'
  saved=read(ROOT/'pipeline/research_work.json');assert saved==work and sha(ROOT/RECEIPT['path'])==RECEIPT['sha256']
  exclusive(HERE/'cre_lifecycle_result.json',encoded({'recorded_at':now,'status':'CRE_RESEARCH_COMPLETE_AND_AUXILIARY_STATUS_ALIGNED_TO_EXISTING_CANONICAL_ARCHIVE','canonical_result':ref(TICK/'cre_finalize_result.json'),'canonical_status':'done_earlystop','archive_id':final['archive_id'],'stage':'complete','auxiliary_training_status':'done_earlystop','precise_native_logger_best':EXACT_NATIVE_BEST,'printed_canonical_best':'0.4961','epochs':EPOCHS,'experiment_only_auxiliary_field_changed':True,'protected_ledger_count_at_start':len(before['ledgers']),'all_nonCRE_postarchive_ledgers_and_other_candidates_preserved':True,'original_source_receipt_raw_negative_evidence_preserved':True,'new_native_restart_signal_or_launch':False,'before':before,'after':after}))
  print('CRE research complete/auxiliary done_earlystop aligned; no canonical archive replay/source/receipt/queue/native change.')
 finally:lock.close()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_SHARED_WRITE');return
 execute()
if __name__=='__main__':main()
