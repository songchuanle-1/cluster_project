"""Root anchor of reviewed static BFC modules, never native evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,sys,copy
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent;PACKET=ROOT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare';ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_ab7e46d4/bfc_native_prepare'
TOKEN='3824d9c96f6343e09d60362b4a00495b';CID='hierarchy-parent-butterfly-token-composition';COMMIT='48fc302c3c02ffef0b241be3593c386b6b65a72e';SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
def read(p):return json.loads(Path(p).read_text('utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def guard():
 o=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json');e={'token':TOKEN,'thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-25T08:06:47.370222+00:00','deadline_at':'2026-10-25T09:06:47.370222+00:00','context_sha256':'eeb5e674ac8ae4fb2c3d5142b0d3cfaa39a96e426127b39702ad55b02b839fe3','pending_sha256':'fe7d536849cc9c0d1dc633d37f1ec8bfb47c977d30ded4d77d2fc35a0835571c'}
 assert {k:o.get(k) for k in e}==e and read(ROOT/'pipeline/execution_mode.json')['target_thread_id']==os.environ['CODEX_THREAD_ID']==e['thread_id']
 assert read(ROOT/'pipeline/execution_mode.json')['mode']=='foreground' and datetime.now(timezone.utc)<datetime.fromisoformat(e['deadline_at'])
 assert sha(ROOT/'pipeline/headless/.tick_context.json')==e['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==e['pending_sha256']
 assert sha(ROOT/'pipeline/goal.json')=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85' and sha(ROOT/'SERVERS.yaml')=='d5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2'
 assert sha(ROOT/'pipeline/authorizations/server4_gpu1_20261025.json')=='90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8'
 return o
def save(p,x):
 t=p.with_name(p.name+'.'+TOKEN+'.tmp')
 with t.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def unused_historical_anchor_main():
 a=argparse.ArgumentParser();a.add_argument('--review',required=True);a.add_argument('--review-sha',required=True);args=a.parse_args();guard()
 rp=Path(args.review).resolve();assert rp.is_relative_to(HERE) and sha(rp)==args.review_sha;review=read(rp)
 assert review['status']=='STATIC_OPERATIONAL_BFC_PACKET_REVIEWED_NOT_NATIVE_PASS' and review['material_concerns']==[] and review['candidate_id']==CID and review['code_commit']==COMMIT
 for k,p in [('outer_preparation',PACKET/'preparation.json'),('native_preparation',PACKET/'native/preparation.json'),('release_template',PACKET/'release_template.json')]:assert review['anchors'][k]==ref(p)
 prep=read(PACKET/'preparation.json');np=read(PACKET/'native/preparation.json');template=read(PACKET/'release_template.json')
 for base,meta in [(PACKET,prep),(PACKET/'native',np)]:
  for n,h in meta['prepared_file_hashes'].items():
   p=(base/n).resolve();assert p.is_relative_to(base) and sha(p)==h
 assert prep['code_commit']==np['code_commit']==template['code_commit']==COMMIT and prep['all_actual_execution']==prep['native_TRAIN2']==np['native']=='NOT_RUN' and prep['resources']==np['resources']=='NOT_RUN'
 assert prep['active_binding_manifest_lease']=='NOT_CREATED' and not any((PACKET/'native'/n).exists() for n in ['native_manifest.json','execution_lease.json'])
 assert (ORIGIN/'worker.py').read_bytes()==(PACKET/'native/worker.py').read_bytes()
 old=(ORIGIN/'native_runtime.py').read_bytes();assert old.count(b'DRAFT_EXECUTION_DISABLED = True')==1 and old.replace(b'DRAFT_EXECUTION_DISABLED = True',b'DRAFT_EXECUTION_DISABLED = False')==(PACKET/'native/native_runtime.py').read_bytes()
 testref=prep['current_passing_offline_suite'];testpath=(PACKET/testref['path']).resolve();assert testpath.is_relative_to(PACKET) and sha(testpath)==testref['sha256'];test=read(testpath)
 assert test['successful'] and test['failures']==test['errors']==0 and test['torch_imported'] is False and test['real_process_or_network_audit_events']==[]
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();protected=['queue.json','running.json','experiments/M211-BTC.json','experiments/M212-BCR.json','experiments/M206-CGCA.json','admissions/M211-BTC.json','admissions/M212-BCR.json'];before={n:sha(ROOT/'pipeline'/n) for n in protected}
  work=read(ROOT/'pipeline/research_work.json');c=next(x for x in work['candidates'] if x['id']==CID);assert c['stage']=='validation' and c['code_commit']==COMMIT and c['native_execution_code_commit'] is None
  tasks=monitor.load_queue(str(ROOT))['gpu_queues']['server-4']
  for eid,pid,gpu in [('M211-BTC',2784474,'0'),('M212-BCR',1215422,'1')]:
   t=next(t for t in tasks if t['id']==eid);assert t['status']=='running' and t['pid']==pid and str(t['gpu'])==gpu and t['launch_verified']
  pause=next(t for t in tasks if t['id']=='M206-CGCA');assert pause['dispatch_hold'] and pause['resume_authorized'] is False
  assert not any(t['id']=='M213-BFC' for t in tasks) and monitor.load_experiment(str(ROOT),'M213-BFC') is None and not (ROOT/'pipeline/admissions/M213-BFC.json').exists()
  c.setdefault('execution_preparation_history',[]).append({'recorded_at':datetime.now(timezone.utc).isoformat(),'reason':'Preserve original disabled native727b and no-adapter state before reviewed static module promotion; no native execution or binding is inferred.','worker_preparation':copy.deepcopy(c['worker_preparation']),'execution_adapter':copy.deepcopy(c['execution_adapter'])})
  release=PACKET/'adapter_release.json'
  with release.open('xb') as f:f.write((PACKET/'release_template.json').read_bytes())
  assert sha(release)==sha(PACKET/'release_template.json');n=PACKET/'native'
  c['worker_preparation']={'status':'PREPARED_REVIEWED_UNEXECUTED','preparation':ref(n/'preparation.json'),'worker':ref(n/'worker.py'),'runtime':ref(n/'native_runtime.py'),'manifest_template':ref(n/'manifest_template.json'),'source_commit':COMMIT,'native_backward_executed':False,'resource_profile_executed':False,'native_backward_passed':False,'resources_passed':False,'active_native_manifest_or_execution_lease_created':False}
  c['execution_adapter']={'status':'PREPARED_REVIEWED_STATIC_CATALOG_ONLY_UNEXECUTED','preparation':ref(PACKET/'preparation.json'),'release':ref(release),'adapter':ref(PACKET/'adapter.py'),'remote_ops':ref(PACKET/'remote_ops.py'),'README':ref(PACKET/'README.md'),'independent_review':ref(rp),'independent_tests':ref(testpath),'external_anchor_required':True,'source_commit':COMMIT,'native_execution_code_commit':None,'native_execution_tested':False,'remote_adapter_execution_tested':False,'active_binding_manifest_lease_created':False,'static_module_release_only':True,'standard_result_formatter_implemented':False,'static_release_scope':'Reviewed selected-one-GPU0-or1 modules only. Not an idle/resource grant, active binding or native PASS; fresh exact owner/assets/UUID/idle/three locks and same original deadline still required.'}
  c['operational_preparation_status']='COMPLETE_REVIEWED_STATIC_GUARDED_BFC_PACKET_NATIVE_NOT_RUN';c['native_status']='NOT_RUN_BOTH_AUTHORIZED_GPUS_RUNNING_PROTECTED_TASKS';c['native_smoke_status']='NOT_RUN';c['resource_profile_status']='NOT_RUN';c['admission_status']='NOT_EVALUATED';c['efficacy']='UNKNOWN'
  c['next_action']='Use reviewed BFC48fc static catalog under a fresh actual owner/context/deadline. Both GPU0 BTC andGPU1 BCR currently run protected jobs. Once one naturally ends and current whitelist/UUID/idle/contexts/three locks/assets/runtime pass, bind that one selected card, stage BFC and run original paired M95/BFC TRAIN2 plus original resource pair. Verify actualnonpower2/n3/multistage and fourWquadrant original-loss finite/nonzero gradients+updates, allowing individual call/half zero. Only actual passing raw results and independent semantics may generate standard receipt/queue/safe ff-only promotion and verified canonical launch. No M206 resume, eviction, protocol/source/YAML/seed/data/schedule or oldhold changes.'
  for p in [PACKET/'preparation.json',n/'preparation.json',release,rp,testpath,PACKET/'native_promotion.json']:
   e=ref(p)
   if e not in c['evidence']:c['evidence'].append(e)
  work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']=c['next_action'];guard();save(ROOT/'pipeline/research_work.json',work)
  assert {n:sha(ROOT/'pipeline'/n) for n in protected}==before
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'candidate_id':CID,'source_commit':COMMIT,'static_catalog_anchored':True,'native_or_resources_executed':False,'source_or_existing_queue_runs_changed':False,'outer':ref(PACKET/'preparation.json'),'native':ref(n/'preparation.json'),'release':ref(release),'independent_review':ref(rp),'test_proof':ref(testpath),'active_binding_manifest_lease_created':False}
  with (HERE/'bfc_static_anchor_result.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
  print(json.dumps({'status':'REVIEWED_BFC_STATIC_CATALOG_ANCHORED_NATIVE_NOT_RUN','test_count':test['tests_run'],'active_binding':False}))
 finally:lock.close()
if __name__=='__main__':raise SystemExit('READONLY_GUARD_REBINDING_ONLY_NO_CATALOG_MUTATION')
