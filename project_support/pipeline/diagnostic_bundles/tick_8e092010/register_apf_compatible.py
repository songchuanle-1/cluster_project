"""Register unchanged APF compatible source/static capability; no native or deployment."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent;OP=HERE/'apf_compatible_prepare'
CID='hierarchy-ancestry-path-factor-composition';COMMIT='d0e2f95712ed16446907706fbf6a65d34996a9ad'
BASE='6282263d805c1741234f97afc981a05aca2ad6e3'

def verify(p):
 v=u.read(p)
 for n,h in v['prepared_file_hashes'].items():
  q=(p.parent/n).resolve();assert q.is_relative_to(p.parent.resolve()) and sha(q)==h,n
 return v

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--preparation-sha256');ap.add_argument('--review');ap.add_argument('--review-sha256');args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_REGISTRATION');return
 guard();assert sha(OP/'preparation.json')==args.preparation_sha256
 peer=(ROOT/args.review).resolve();assert peer.is_relative_to(HERE) and sha(peer)==args.review_sha256
 review=u.read(peer);assert review['candidate_id']==CID and review['code_commit']==COMMIT and review['material_concerns']==[]
 op=verify(OP/'preparation.json');native=verify(OP/'native/preparation.json');version=u.read(OP/'version_prepare/isolated_source_version.json')
 assert op['code_commit']==native['source_commit']==version['code_commit']==COMMIT
 assert op['candidate_id']==native['candidate_id']==CID and native['source_parent_commit']==version['parent_commit']==BASE
 assert version['diff_exact9A'] and native['source_files']==version['frozen_source_files'] and len(native['source_files'])==9
 assert sha(OP/'native/worker.py')=='86e958aa847abf0f3f165c9cc8e10cd759846ec4f0f419a9a09157c43a48ac1b'
 assert u.ref(OP/'preparation.json') in review['anchors'].values() and u.ref(OP/'native/preparation.json') in review['anchors'].values()
 template=u.read(OP/'native/manifest_template.json')
 assert all(template[k] is None for k in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit'))
 release=u.read(OP/'release_template.json');assert release['code_commit']==COMMIT and release['candidate_id']==CID and release['native_preparation_sha256']==sha(OP/'native/preparation.json')
 assert release['source_hashes']=={n:sha(OP/n) for n in ('adapter.py','remote_ops.py')}
 assert not (OP/'adapter_release.json').exists() and not (HERE/'apf_execution').exists()
 assert not any((HERE/n).exists() for n in ('apf_registration_intent.json','apf_registration_result.json'))
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b)
  ledgers={n:sha(ROOT/'pipeline'/n) for n in b['protected_ledgers']}
  w=u.read(ROOT/'pipeline/research_work.json');before=sha(ROOT/'pipeline/research_work.json');digests={c['id']:u.digest(c) for c in w['candidates']}
  c=next(c for c in w['candidates'] if c['id']==CID);assert len(digests)==145 and c['code_commit']=='bf6c3fafe0f690e16e838e7c0192f09e789389f9' and c['stage']=='validation'
  now=datetime.now(timezone.utc).isoformat()
  c.setdefault('source_version_history',[]).append({k:copy.deepcopy(c.get(k)) for k in ('code_commit','source_commit','source_parent_commit','source_version','actual_source_version_independent_review')})
  for k in ('worker_preparation','execution_adapter','current_version_compatibility','resource_check','current_resource_check'):
   if c.get(k):c.setdefault(k+'_history',[]).append(copy.deepcopy(c[k]))
  release_ref={'path':(OP/'adapter_release.json').relative_to(ROOT).as_posix(),'sha256':sha(OP/'release_template.json')}
  c.update(code_commit=COMMIT,source_commit=COMMIT,source_parent_commit=BASE,source_version=u.ref(OP/'version_prepare/isolated_source_version.json'),actual_source_version_independent_review=u.ref(peer),source_status='ISOLATED_COMPATIBLE_SOURCE_STATIC_TOOLS_NATIVE_NOT_RUN',native_status='NOT_RUN_FOR_CURRENT_SOURCE_PACKET',resource_status='NOT_RUN_FOR_CURRENT_SOURCE_PACKET',native_execution_code_commit=None,queued=False,requires_current_runtime_compatible_copy=False)
  c['worker_preparation']={'status':'STATIC_REVIEWED_NATIVE_NOT_RUN','preparation':u.ref(OP/'native/preparation.json'),'worker':u.ref(OP/'native/worker.py'),'runtime':u.ref(OP/'native/native_runtime.py'),'manifest_template':u.ref(OP/'native/manifest_template.json'),'source_commit':COMMIT,'source_parent_commit':BASE,'runtime_expected_commit':BASE,'independent_review':u.ref(peer),'native_backward_executed':False,'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False}
  c['execution_adapter']={'status':'STATIC_REVIEWED_CATALOGUE_ONLY_NATIVE_NOT_RUN','preparation':u.ref(OP/'preparation.json'),'release':release_ref,'independent_review':u.ref(peer),'active_binding_manifest_lease_created':False,'transport_executed':False}
  c['current_version_compatibility']={'current_source_commit':COMMIT,'current_parent_commit':BASE,'current_primary_and_runtime':BASE,'source_version':c['source_version'],'status':'CURRENT_PARENT_COMPATIBLE_ISOLATED_SOURCE_AND_REVIEWED_STATIC_TOOLS','scope':'Same frozen nine APF files, no model revision. Original bf6/parentd585/NULL metadata retained. Native/resources unrun, no borrowed PASS.'}
  c.pop('resource_check',None)
  c['current_resource_check']={'status':'COMPATIBLE_STATIC_PACKET_READY_FRESH_GPU0_OCCUPATION_STILL_REQUIRED','recorded_at':now,'code_commit':COMMIT,'current_primary_and_runtime':BASE,'native_and_resources':'NOT_RUN','scope':'Static source compatibility only; does not prove GPU0 idle or authorize execution.'}
  c['next_action']='Execute original paired natural TRAIN2 and original resources with current owner and fresh idle authorized GPU0; then admit and canonical dispatch only if actual checks pass. GPU1 prohibited; HPC stopped_unknown is not restarted.'
  refs=[u.ref(OP/'preparation.json'),u.ref(OP/'native/preparation.json'),u.ref(OP/'native/manifest_template.json'),u.ref(OP/'version_prepare/isolated_source_version.json'),u.ref(peer),release_ref]
  for r in refs:
   if r not in c['evidence']:c['evidence'].append(r)
  w['updated_at']=now;w['last_event_tick']=EXPECTED['generated_at'];w['next_action']=c['next_action']
  assert all(u.digest(x)==digests[x['id']] for x in w['candidates'] if x['id']!=CID)
  json.dumps(w,ensure_ascii=False,allow_nan=False)
  u.save(HERE/'apf_registration_intent.json',{'owner':EXPECTED,'recorded_at':now,'before_work_sha256':before,'source_version':c['source_version'],'packet':u.ref(OP/'preparation.json'),'peer':u.ref(peer),'release':release_ref,'scope':'Existing APF compatible metadata/static release only; no source primary/runtime, native, admission, queue, launch, or model revision.'})
  guard();assert sha(ROOT/'pipeline/research_work.json')==before
  with (OP/'adapter_release.json').open('xb') as f:f.write((OP/'release_template.json').read_bytes());f.flush();os.fsync(f.fileno())
  assert sha(OP/'adapter_release.json')==release_ref['sha256']
  u.atomic(ROOT/'pipeline/research_work.json',w);u.primary_protection(b)
  assert all(sha(ROOT/'pipeline'/n)==h for n,h in ledgers.items())
  after=u.read(ROOT/'pipeline/research_work.json');assert all(u.digest(x)==digests[x['id']] for x in after['candidates'] if x['id']!=CID)
  u.save(HERE/'apf_registration_result.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'EXISTING_APF_COMPATIBLE_SOURCE_STATIC_CAPABILITY_REGISTERED_NATIVE_NOT_RUN','code_commit':COMMIT,'parent_commit':BASE,'candidate_count':145,'new_candidates':0,'model_revisions':0,'primary_index28_and_all_current_lifecycle_unchanged':True,'other_144_candidates_unchanged':True,'packet':u.ref(OP/'preparation.json'),'review':u.ref(peer),'release':release_ref})
  print('Existing APF compatible static capability registered; native tests not run.')
 finally:lock.close()
if __name__=='__main__':main()
