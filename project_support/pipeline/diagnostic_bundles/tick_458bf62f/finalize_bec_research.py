"""Align BEC research and auxiliary status to already-completed canonical archive."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json,os,sys
from anchor_bfc_packet import ROOT,guard,sha
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save_new(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();assert sha(HERE/'bec_terminal_independent_review.json')=='4730ed3bba817677e209c36cceb36e615a84a7e4741b8ce21f7804c58dbae427'
  review=read(HERE/'bec_terminal_independent_review.json');assert review['material_concerns']==[]
  exp=mon.load_experiment(str(ROOT),'M215-BEC');assert exp['status']=='done_earlystop' and str(exp['final_best'])=='0.5001' and exp['epochs_final']=='24/50'
  assert sha(ROOT/'pipeline/admissions/M215-BEC.json')=='113a72afb83c57401d00072b1a723a5cc3094a76a1e2d9acfe75b465f10238dc'
  before=copy.deepcopy(exp);work=read(ROOT/'pipeline/research_work.json');cand=next(c for c in work['candidates'] if c.get('experiment_id')=='M215-BEC');old=copy.deepcopy(cand)
  assert cand['stage']=='training' and exp.get('training_status')=='running'
  save_new(HERE/'bec_research_terminal_intent.json',{'experiment_before':before,'candidate_before':old,'review':ref(HERE/'bec_terminal_independent_review.json')})
  exp['training_status']='done_earlystop';mon.save_experiment(str(ROOT),exp)
  cand.update(review['recommended_research_work_update']);cand['terminal_archive_id']='4bd2119b138d4676972019b7462720fa'
  for p in [HERE/'bec_finalize_result.json',HERE/'bec_terminal_independent_review.json',HERE/'bec_exact_terminal_archive/exact_log_evidence.json']:
   entry=ref(p)
   if entry not in cand.setdefault('evidence',[]):cand['evidence'].append(entry)
  now=datetime.now(timezone.utc).isoformat();cand['terminal_assessment']={'recorded_at':now,'native_printed_best_miou':0.5001,'stored_M95_miou':0.5020,'delta':-0.0019,'checkpoint_exact_best_read':False,'scope':'This realization completed below stored M95; one run does not falsify entire mechanism. No automatic restart or tuning.'}
  work['updated_at']=now
  tmp=ROOT/'pipeline/research_work.json.458bf62f.bec_terminal.tmp'
  with tmp.open('x',encoding='utf8') as f:json.dump(work,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  guard();os.replace(tmp,ROOT/'pipeline/research_work.json')
  assert {k:v for k,v in exp.items() if k!='training_status'}=={k:v for k,v in before.items() if k!='training_status'}
  save_new(HERE/'bec_research_terminal_result.json',{'recorded_at':now,'canonical_status':exp['status'],'auxiliary_training_status':exp['training_status'],'stage':cand['stage'],'only_experiment_auxiliary_field_changed':True,'original_receipt_preserved':True,'restart_or_signal':False})
  print('BEC complete/done_earlystop aligned; original archive/source/receipt retained.')
 finally:lock.close()
if __name__=='__main__':main()
