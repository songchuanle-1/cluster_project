"""Register one independently reviewed DCE static capability, not native results."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent;OP=HERE/'dce_operational_prepare';NATIVE=HERE/'dce_native_prepare';PREP=HERE/'new_candidate_prepare'
CID='hierarchy-directed-cavity-edge-composition';EXP='M220-DCE';COMMIT='5c0c211c8ecc9479ecb34dbb8118a95f4b20e391';BASE=u.SOURCE

def verify(p):
 v=u.read(p)
 for n,h in v['prepared_file_hashes'].items():
  f=(p.parent/n).resolve();assert f.is_relative_to(p.parent.resolve()) and sha(f)==h,n
 return v

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--native-sha256');ap.add_argument('--operational-sha256');ap.add_argument('--review');ap.add_argument('--review-sha256');args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_REGISTRATION');return
 guard();assert sha(PREP/'preparation.json')=='44e75f7c33e15d049716b8b477a601e8fbbc74a226c13a5552ace927a3e3ed5e'
 proto=verify(PREP/'preparation.json');assert sha(NATIVE/'preparation.json')==args.native_sha256 and sha(OP/'preparation.json')==args.operational_sha256
 n=verify(NATIVE/'preparation.json');op=verify(OP/'preparation.json')
 version=HERE/'dce_version_prepare/isolated_source_version.json';assert sha(version)=='0b837c82eb92593d0b5878c92ad5aaeb5f2e561140ee75a0db8ef20537d3489f'
 v=u.read(version);assert v['code_commit']==COMMIT and v['parent_commit']==BASE and v['diff_exact9A'] and v['frozen_source_files']==proto['source_files']==n['source_files']
 assert n['source_commit']==op['code_commit']==COMMIT and n['source_parent_commit']==BASE and n['candidate_id']==op['candidate_id']==CID
 peer=(ROOT/args.review).resolve();assert peer.is_relative_to(HERE.resolve()) and sha(peer)==args.review_sha256
 review=u.read(peer);assert review['candidate_id']==CID and review['code_commit']==COMMIT and review['material_concerns']==[]
 assert u.ref(NATIVE/'preparation.json') in review['anchors'].values() and u.ref(OP/'preparation.json') in review['anchors'].values()
 manifest=u.read(NATIVE/'manifest_template.json');assert all(manifest[k] is None for k in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit'))
 release=u.read(OP/'release_template.json');assert release['code_commit']==COMMIT and release['candidate_id']==CID and release['native_preparation_sha256']==sha(NATIVE/'preparation.json') and release['source_hashes']=={k:sha(OP/k) for k in ('adapter.py','remote_ops.py')}
 assert not any(p.exists() for p in [OP/'adapter_release.json',HERE/'dce_execution',HERE/'dce_registration_intent.json',HERE/'dce_registration_result.json'])
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b)
  ledgers={k:sha(ROOT/'pipeline'/k) for k in b['protected_ledgers']};w=u.read(ROOT/'pipeline/research_work.json');before=sha(ROOT/'pipeline/research_work.json');digests={c['id']:u.digest(c) for c in w['candidates']}
  assert len(digests)==145 and CID not in digests and not any(c.get('experiment_id')==EXP for c in w['candidates'])
  c=copy.deepcopy(u.read(PREP/'candidate_record.json'));assert c['id']==CID and c['experiment_id']==EXP and c['code_commit'] is None
  now=datetime.now(timezone.utc).isoformat();release_ref={'path':(OP/'adapter_release.json').relative_to(ROOT).as_posix(),'sha256':sha(OP/'release_template.json')}
  c.update(stage='validation',created_at=now,created_tick=EXPECTED['generated_at'],source_preparation=u.ref(PREP/'preparation.json'),source_version=u.ref(version),code_commit=COMMIT,source_commit=COMMIT,source_parent_commit=BASE,actual_source_version_independent_review=u.ref(HERE/'dce_actual_source_version_independent_review.json'),native_status='NOT_RUN',resource_status='NOT_RUN',native_execution_code_commit=None,queued=False,required_server='server-4',source_status='ISOLATED_SOURCE_AND_REVIEWED_STATIC_CAPABILITY_NATIVE_NOT_RUN')
  c['worker_preparation']={'status':'STATIC_REVIEWED_NATIVE_NOT_RUN','preparation':u.ref(NATIVE/'preparation.json'),'worker':u.ref(NATIVE/'worker.py'),'runtime':u.ref(NATIVE/'native_runtime.py'),'manifest_template':u.ref(NATIVE/'manifest_template.json'),'source_commit':COMMIT,'source_parent_commit':BASE,'runtime_expected_commit':BASE,'independent_review':u.ref(peer),'native_backward_executed':False,'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False}
  c['execution_adapter']={'status':'STATIC_REVIEWED_CATALOGUE_ONLY_NATIVE_NOT_RUN','preparation':u.ref(OP/'preparation.json'),'release':release_ref,'independent_review':u.ref(peer),'active_binding_manifest_lease_created':False,'transport_executed':False}
  c['current_version_compatibility']={'current_source_commit':COMMIT,'current_parent_commit':BASE,'current_primary_and_runtime':BASE,'status':'CURRENT_PARENT_COMPATIBLE_ISOLATED_SOURCE_AND_REVIEWED_STATIC_TOOLS','scope':'Actual isolated source only; original unversioned prototype metadata retained, no primary/runtime promotion or native PASS.'}
  c['next_action']='Execute original paired natural TRAIN2 and original resources on freshly idle authorized GPU0 with original owner/deadline, preserve full failures. If actually passing, test-bound exact9A ff/admit/canonical dispatch and confirm native progress. No GPU1 or automatic APF/HPC recovery.'
  for r in [u.ref(PREP/'preparation.json'),u.ref(version),u.ref(HERE/'dce_source_independent_review.json'),u.ref(HERE/'dce_actual_source_version_independent_review.json'),u.ref(NATIVE/'preparation.json'),u.ref(OP/'preparation.json'),u.ref(peer),release_ref]:
   if r not in c['evidence']:c['evidence'].append(r)
  w['candidates'].append(c);w['updated_at']=now;w['last_event_tick']=EXPECTED['generated_at'];w['next_action']=c['next_action']
  assert len(w['candidates'])==146 and all(u.digest(x)==digests[x['id']] for x in w['candidates'] if x['id']!=CID)
  json.dumps(w,ensure_ascii=False,allow_nan=False)
  u.save(HERE/'dce_registration_intent.json',{'owner':EXPECTED,'recorded_at':now,'before_work_sha256':before,'new_candidate_id':CID,'source_version':u.ref(version),'native_preparation':u.ref(NATIVE/'preparation.json'),'operational_preparation':u.ref(OP/'preparation.json'),'independent_review':u.ref(peer),'release':release_ref,'scope':'One new candidate/static capability only within snapshotcreation2. No source primary/runtime, GPU, native/PASS, admission, queue, recovery or launch.'})
  guard();assert sha(ROOT/'pipeline/research_work.json')==before
  with (OP/'adapter_release.json').open('xb') as f:f.write((OP/'release_template.json').read_bytes());f.flush();os.fsync(f.fileno())
  assert sha(OP/'adapter_release.json')==release_ref['sha256'];u.atomic(ROOT/'pipeline/research_work.json',w)
  u.primary_protection(b);assert all(sha(ROOT/'pipeline'/k)==h for k,h in ledgers.items())
  after=u.read(ROOT/'pipeline/research_work.json');assert len(after['candidates'])==146 and all(u.digest(x)==digests[x['id']] for x in after['candidates'] if x['id']!=CID)
  u.save(HERE/'dce_registration_result.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ONE_NEW_DCE_STATIC_CAPABILITY_REGISTERED_NATIVE_NOT_RUN','candidate_id':CID,'experiment_id':EXP,'code_commit':COMMIT,'source_parent_commit':BASE,'candidate_count':146,'new_candidates':1,'model_revisions':0,'other145_candidates_unchanged':True,'primary_index28_and22_current_lifecycle_unchanged':True,'release':release_ref,'native_preparation':u.ref(NATIVE/'preparation.json'),'operational_preparation':u.ref(OP/'preparation.json'),'independent_review':u.ref(peer)})
  print('One new DCE candidate registered with real isolated source/static capability. Native not run.')
 finally:lock.close()
if __name__=='__main__':main()
