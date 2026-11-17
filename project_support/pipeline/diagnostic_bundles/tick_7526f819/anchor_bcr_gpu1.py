"""Root anchor of reviewed GPU1 static modules; creates no native result."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,sys
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PACKET=ROOT/'pipeline/diagnostic_bundles/manual_gpu1_20261025/bcr_gpu1_operational_prepare'
TOKEN='7526f819f16e4f688566119d347cd198';CID='hierarchy-parent-bidirectional-complement-recurrence';COMMIT='11a811618179ab1ddc0cee299194667413b7fdb9'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
def read(p):return json.loads(Path(p).read_text('utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
 t=p.with_name(p.name+'.'+TOKEN+'.tmp')
 with t.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def main():
 a=argparse.ArgumentParser();a.add_argument('--review',required=True);a.add_argument('--review-sha',required=True);args=a.parse_args()
 owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
 assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
 assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
 assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
 assert sha(ROOT/'SERVERS.yaml')=='d5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2'
 grant=ROOT/'pipeline/authorizations/server4_gpu1_20261025.json';assert sha(grant)=='90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8'
 reviewpath=Path(args.review).resolve();assert reviewpath.is_relative_to(ROOT) and sha(reviewpath)==args.review_sha
 review=read(reviewpath);assert review['status']=='STATIC_OPERATIONAL_BCR_PACKET_REVIEWED_NOT_NATIVE_PASS' and review['material_concerns']==[]
 assert review['candidate_id']==CID and review['code_commit']==COMMIT
 for k,p in [('outer_preparation',PACKET/'preparation.json'),('native_preparation',PACKET/'native/preparation.json'),('release_template',PACKET/'release_template.json')]:assert review['anchors'][k]==ref(p)
 prep=read(PACKET/'preparation.json');native=read(PACKET/'native/preparation.json');template=read(PACKET/'release_template.json')
 for base,meta in [(PACKET,prep),(PACKET/'native',native)]:
  for name,h in meta['prepared_file_hashes'].items():
   p=(base/name).resolve();assert p.is_relative_to(base) and sha(p)==h
 assert prep['code_commit']==native['code_commit']==template['code_commit']==COMMIT
 assert prep['native_execution']==native['native']=='NOT_RUN' and prep['resource_measurement']==native['resources']=='NOT_RUN'
 assert not prep['active_binding_manifest_lease_created']
 assert not any((PACKET/'native'/n).exists() for n in ['native_manifest.json','execution_lease.json'])
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  protected=['queue.json','running.json','experiments/M211-BTC.json','experiments/M206-CGCA.json','admissions/M211-BTC.json'];before={n:sha(ROOT/'pipeline'/n) for n in protected}
  work=read(ROOT/'pipeline/research_work.json');c=next(x for x in work['candidates'] if x['id']==CID)
  assert c['stage']=='validation' and c['code_commit']==COMMIT and c['native_execution_code_commit'] is None and c['requested_physical_gpu']==1
  assert c['resource_authorization']==ref(grant)
  q=monitor.load_queue(str(ROOT));btc=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M211-BTC');m206=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M206-CGCA')
  assert btc['status']=='running' and btc['pid']==2784474 and str(btc['gpu'])=='0' and btc['launch_verified']
  assert m206['dispatch_hold'] and m206['resume_authorized'] is False
  assert not any(t['id']=='M212-BCR' for ts in q['gpu_queues'].values() for t in ts) and monitor.load_experiment(str(ROOT),'M212-BCR') is None
  release=PACKET/'adapter_release.json'
  with release.open('xb') as f:f.write((PACKET/'release_template.json').read_bytes())
  assert sha(release)==sha(PACKET/'release_template.json')
  n=PACKET/'native'
  c['worker_preparation']={'status':'PREPARED_REVIEWED_UNEXECUTED','preparation':ref(n/'preparation.json'),'worker':ref(n/'worker.py'),'runtime':ref(n/'native_runtime.py'),'manifest_template':ref(n/'manifest_template.json'),'source_commit':COMMIT,'native_backward_passed':False,'resources_passed':False,'native_backward_executed':False,'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False}
  c['execution_adapter']={'status':'PREPARED_REVIEWED_STATIC_CATALOG_ONLY_UNEXECUTED','preparation':ref(PACKET/'preparation.json'),'release':ref(release),'adapter':ref(PACKET/'adapter.py'),'remote_ops':ref(PACKET/'remote_ops.py'),'README':ref(PACKET/'README.md'),'independent_review':ref(reviewpath),'independent_tests':ref(PACKET/'offline_tests/full_offline_run2.json'),'external_anchor_required':True,'source_commit':COMMIT,'native_execution_code_commit':None,'native_execution_tested':False,'remote_adapter_execution_tested':False,'active_binding_manifest_lease_created':False,'static_module_release_only':True,'standard_result_formatter_implemented':False,'static_release_scope':'Reviewed GPU1 static module/version hashes only, no native PASS or idle proof. Fresh original owner/UUID1/assets/three locks required.'}
  c['operational_preparation_status']='COMPLETE_GPU1_STATIC_GUARDED_PACKET_NATIVE_NOT_RUN';c['native_smoke_status']='NOT_RUN';c['resource_profile_status']='NOT_RUN';c['admission_status']='NOT_EVALUATED';c['efficacy']='UNKNOWN'
  c['next_action']='Use reviewed GPU1 packet with this original owner/context/deadline and fresh assets/UUID1/idle/three locks; run original paired M95/BCR TRAIN2 and resource protocol. Five Ws token/state and Wf own/left/right original-loss gradients and weight updates plus n>=3/depth2/nonzero priorstate required. On actual pass admit and dispatch GPU1, preserving BTC0 and M206 pause.'
  for x in [ref(grant),ref(PACKET/'preparation.json'),ref(n/'preparation.json'),ref(release),ref(reviewpath)]:
   if x not in c['evidence']:c['evidence'].append(x)
  work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']=c['next_action'];save(ROOT/'pipeline/research_work.json',work)
  assert {n:sha(ROOT/'pipeline'/n) for n in protected}==before
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'candidate_id':CID,'source_commit':COMMIT,'physical_gpu':1,'static_catalog_anchored':True,'native_or_resources_executed':False,'protected_existing_run_unchanged':True,'review':ref(reviewpath),'outer':ref(PACKET/'preparation.json'),'release':ref(release)}
  out=HERE/'bcr_gpu1_static_anchor_result.json'
  with out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
  print(json.dumps({'status':'GPU1_STATIC_CATALOG_ANCHORED_NATIVE_NOT_RUN','evidence':ref(out)}))
 finally:lock.close()
if __name__=='__main__':main()
