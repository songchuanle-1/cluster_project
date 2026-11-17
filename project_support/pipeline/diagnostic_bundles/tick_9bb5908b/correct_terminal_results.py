from pathlib import Path
from datetime import datetime,timezone
import sys,json,csv,io,base64,copy
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
IDS=['M224-SFC','M225-ELC']
def main():
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock
 try:
  guard();u.primary_protection(u.read(HERE/'protected_assets_before.json'))
  archive=u.read(HERE/'native_terminal_full_log_archive.json');peer=u.read(HERE/'terminal_full_archive_independent_review.json')
  assert archive['owner']==EXPECTED and archive['all_actual_full_log_bytes_verified'] is True
  assert sha(HERE/'terminal_full_archive_independent_review.json')=='ec08039d88106dbd3980832599c2605db61b68c0267a2514c1bf2f485348b444'
  refs=[u.ref(HERE/'native_terminal_full_log_archive.json'),u.ref(HERE/'terminal_independent_review.json'),u.ref(HERE/'terminal_full_archive_independent_review.json')]
  u.check_refs(refs);logs={x['id']:x for x in archive['native_logs']}
  paths={eid:ROOT/'pipeline/experiments'/f'{eid}.json' for eid in IDS};old={eid:u.read(p) for eid,p in paths.items()};csvpath=ROOT/'pipeline/experiments.csv';rawcsv=csvpath.read_bytes();lines=rawcsv.decode('utf8').splitlines(keepends=True);header=next(csv.reader([lines[0]]));new=copy.deepcopy(old);native={}
  expected={'M224-SFC':('2816b8f70b8d408f926eff84343e3a6f','0.4970','30/50',0.49663493037223816,'c9be548699cd66bf68badff9ae6198a03eafa142'),'M225-ELC':('c437036a689c43ff862361292dc1dea8','0.5020','31/50',0.5015384554862976,'18e64b8d95ed0ba5c1053ead114c0f91a4b0c324')}
  now=datetime.now(timezone.utc).isoformat()
  for eid in IDS:
   e=old[eid];aid,approx,epochs,best,commit=expected[eid];assert (e['archive_id'],e['status'],e['final_best'],e['epochs_final'],e['code_commit'],e['log_local'])==(aid,'done_earlystop',approx,epochs,commit,'')
   log=ROOT/logs[eid]['local']['path'];assert log.is_file() and sha(log)==logs[eid]['remote']['sha256']==logs[eid]['local']['sha256']
   vals,actual,noimp=mon.parse_native_lineage(log.read_text('utf8'),resumed=False);assert actual==best and noimp==10 and len(vals)==int(epochs.split('/')[0])
   n=new[eid];n.update(final_best=format(best,'.4f'),native_final_best=best,training_status='done_earlystop',log_local=str(log),log_local_sha256=sha(log),native_result_evidence=refs)
   n['history'].append({'ts':now,'action':'native_full_log_result_correction','status':'done_earlystop','previous_final_best':approx,'previous_log_local':'','best_miou_exact':best,'best_miou':n['final_best'],'log_local':str(log),'evidence':refs,'scope':'Correct derived rounded-stdout metric and failed generic pull using actual full native log; preserve original archive_id/history/source/receipt/epochs/finished_at. No rerun or lifecycle replay.'})
   assert all(n[k]==e[k] for k in e if k not in ('final_best','training_status','log_local','history'))
   native[eid]={'best':best,'display':n['final_best'],'epochs':epochs,'log_local':str(log),'log_sha256':sha(log)}
  counts={eid:0 for eid in IDS};out=[lines[0]]
  for line in lines[1:]:
   row=next(csv.reader([line]));d=dict(zip(header,row));eid=d.get('id')
   if eid not in IDS:out.append(line);continue
   counts[eid]+=1;assert d['state']=='done_earlystop' and d['best_miou']==expected[eid][1] and d['epochs']==expected[eid][2] and d['log_local']==''
   d['best_miou']=new[eid]['final_best'];d['log_local']=new[eid]['log_local'];f=io.StringIO(newline='');writer=csv.writer(f,lineterminator='\r\n' if line.endswith('\r\n') else '\n');writer.writerow([d[k] for k in header]);out.append(f.getvalue())
  assert all(n==1 for n in counts.values());newcsv=''.join(out).encode('utf8');fixed={n:sha(ROOT/'pipeline'/n) for n in ['queue.json','running.json','research_work.json','admissions/M224-SFC.json','admissions/M225-ELC.json']}
  u.save(HERE/'terminal_result_correction_intent.json',{'owner':EXPECTED,'recorded_at':now,'before_experiments':old,'before_experiment_bytes_base64':{eid:base64.b64encode(p.read_bytes()).decode() for eid,p in paths.items()},'before_csv_base64':base64.b64encode(rawcsv).decode(),'before_csv_sha256':sha(csvpath),'planned_native_results':native,'refs':refs,'protected_fixed':fixed})
  assert csvpath.read_bytes()==rawcsv
  for eid,p in paths.items():assert u.read(p)==old[eid]
  for eid,p in paths.items():u.atomic(p,new[eid])
  u.atomic(csvpath,newcsv.decode('utf8'),text=True)
  assert {n:sha(ROOT/'pipeline'/n) for n in fixed}==fixed
  for eid,p in paths.items():assert u.read(p)==new[eid]
  assert csvpath.read_bytes()==newcsv
  u.primary_protection(u.read(HERE/'protected_assets_before.json'))
  u.save(HERE/'terminal_result_correction_result.json',{'owner':EXPECTED,'native_results':native,'after_experiments':{eid:u.ref(p) for eid,p in paths.items()},'after_csv':u.ref(csvpath),'queue_running_work_receipts_unchanged':True,'other_csv_rows_byte_identical':True,'no_new_archive_or_replay':True,'no_source_or_process_or_policy_change':True})
  print(json.dumps({'result':u.ref(HERE/'terminal_result_correction_result.json'),'native_results':native}))
 finally:lock.close()
if __name__=='__main__':main()
