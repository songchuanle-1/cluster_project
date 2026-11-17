"""Preserve old static declarations as history and label the actual completed operations."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json,os,sys
from anchor_bfc_packet import ROOT,guard,sha
HERE=Path(__file__).resolve().parent;CID='hierarchy-parent-antisymmetric-edge-flux'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();result=read(HERE/'aef_dispatch_result.json');assert result['verified_native_progress'] is True and sha(HERE/'aef_dispatch_result.json')=='267f9e6db11e90b8d6cc9dd67bd46112d5901b4320b955c2a5935c6a93c342a8'
  work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID);assert c['stage']=='training' and c['training_status']=='running'
  keys=['preparation_scope','version_packaging_status','operational_compatibility','resource_check','current_resource_check','admission_status','deployment_status','training_launch']
  before={k:copy.deepcopy(c.get(k)) for k in keys};now=datetime.now(timezone.utc).isoformat();commit=c['code_commit'];assert commit=='56b2a96dc48cc8a88f0f7105527ef448113b1060'
  updates={'preparation_scope':'Exact original frozen AEF9 and source56 tested in current fresh four native/resource arms against shared runtime026c, then exact9 ff-promoted and synced runtime56 with canonical increasing native training progress. Original150c null/reference4e8 declarations and original05f6 tool bindings remain immutable historical evidence.',
   'version_packaging_status':'EXACT9_TESTED_SOURCE56_PROMOTED_AND_SYNCED_NATIVE_TRAINING_VERIFIED',
   'operational_compatibility':{'actual_source_commit':commit,'actual_parent_commit':'026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563','actual_current_primary_commit':commit,'actual_current_training_runtime_commit':commit,'native_test_shared_runtime_commit':'026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563','frozen9_source_unchanged':True,'actual_native_or_resource_results':ref(HERE/'aef_actual_four_result_review.json'),'actual_launch':ref(HERE/'aef_dispatch_result.json'),'recorded_at':now},
   'resource_check':ref(HERE/'aef_resource_comparison.json'),
   'current_resource_check':{'kind':'resource_check','result':'passed','server':'server-4','physical_gpu':0,'recorded_at':read(HERE/'aef_resource_comparison.json')['recorded_at'],'evidence':ref(HERE/'aef_resource_comparison.json'),'scope':'Actual original paired prediction-resource processes under original protocol. This is historical measured admission evidence, not future GPU availability permission or pureTRAIN memory.'},
   'admission_status':'ADMITTED_AND_CANONICAL_NATIVE_PROGRESS_VERIFIED','deployment_status':'EXACT_TESTED_SOURCE56_SYNCED_AND_VERIFIED','training_launch':ref(HERE/'aef_dispatch_result.json')}
  record={'recorded_at':now,'reason':'Replace stale current NOT_RUN/NOT_PROMOTED/WAITING labels after their actual successful operations; preserve former declarations separately, never alter frozen packets or raw results.','prior_current_fields':before,'actual_current_fields':updates,'prior_transport_executed':c['execution_adapter'].get('transport_executed'),'transport_executed':True}
  p=HERE/'aef_current_metadata_reconciliation.json'
  with p.open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
  c.setdefault('current_state_history',[]).append(ref(p));c.update(updates);c['execution_adapter']['transport_executed']=True;c['evidence'].append(ref(p));work['updated_at']=now
  tmp=ROOT/'pipeline/research_work.json.458bf62f.metadata.tmp'
  with tmp.open('x',encoding='utf8') as f:json.dump(work,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  guard();os.replace(tmp,ROOT/'pipeline/research_work.json')
  print('Current AEF labels aligned to actual native/resource/admission/sync/verified training; old static fields preserved as history.')
 finally:lock.close()
if __name__=='__main__':main()
