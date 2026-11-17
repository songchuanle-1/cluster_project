"""Once-only root static catalogue; no native execution or source promotion."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='7e4925958fa041fab72b22b0d2a0b0ea'
CID='hierarchy-cross-root-directed-edge-broadcast';COMMIT='7ed9373db335d44c884133da3eced3fca03ad29a';BASE='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
NATIVE=HERE/'cre_native_prepare';OP=HERE/'cre_operational_prepare'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def exclusive(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def replace(p,b):
 t=p.with_name(p.name+'.'+TOKEN+'.catalogue.tmp');exclusive(t,b);os.replace(t,p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true')
 for name in ['native-preparation','operational-preparation','native-review','operational-review']:ap.add_argument('--'+name+'-sha256')
 args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_CATALOGUE_WRITE');return
 owner=guard();assert owner['token']==TOKEN and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
 bindings=[(NATIVE/'preparation.json',args.native_preparation_sha256),(OP/'preparation.json',args.operational_preparation_sha256),(HERE/'cre_native_preparation_independent_review.json',args.native_review_sha256),(HERE/'cre_operational_preparation_independent_review.json',args.operational_review_sha256)]
 assert all(h is not None and len(h)==64 and sha(p)==h for p,h in bindings)
 assert not (HERE/'cre_catalogue_intent.json').exists() and not (OP/'adapter_release.json').exists(),'Reconcile partial operation; never replay'
 n,o,nr,opr=[read(p) for p,h in bindings]
 for folder,packet in [(NATIVE,n),(OP,o)]:
  assert packet['candidate_id']==CID and packet['code_commit']==COMMIT and packet['source_parent_commit']==BASE
  for name,h in packet['prepared_file_hashes'].items():
   path=(folder/name).resolve();assert path.is_relative_to(folder.resolve()) and sha(path)==h
 for peer,packet_path in [(nr,NATIVE/'preparation.json'),(opr,OP/'preparation.json')]:
  assert peer['candidate_id']==CID and peer['code_commit']==COMMIT and peer['material_concerns']==[] and peer['anchors']['preparation']==ref(packet_path)
 assert n['native']==n['resources']=='NOT_RUN' and o['all_actual_execution']=='NOT_RUN'
 assert len(n['manifest_execution_fields'])==10 and all(v is None for v in n['manifest_execution_fields'].values())
 for key in ['source_preparation','native_protocol','isolated_source_version','isolated_source_version_independent_review']:
  e=n[key];p=(ROOT/e['path']).resolve();assert p.is_relative_to(ROOT.resolve()) and sha(p)==e['sha256']
 template=(OP/'release_template.json').read_bytes();release_ref={'path':(OP/'adapter_release.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(template).hexdigest()}
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();before=snapshot();baseline=read(HERE/'protected_assets_before.json')
  for k in ['head','index_empty','status_hex','files','protected_ledgers','candidate_digests']:assert before[k]==baseline[k],k
  wp=ROOT/'pipeline/research_work.json';work=read(wp);out=copy.deepcopy(work);c=next(x for x in out['candidates'] if x['id']==CID)
  assert len(out['candidates'])==143 and c['stage']=='implementation' and c['code_commit']==COMMIT and c['native_status']==c['resource_status']=='NOT_RUN' and c.get('native_execution_code_commit') is None
  assert not c.get('worker_preparation') and not c.get('execution_adapter') and not c.get('revision_history')
  c.update(stage='validation',implementation_status='STATIC_REVIEWED_CRE_NATIVE_TOOLING_NATIVE_NOT_RUN',source_status='ACTUAL_ISOLATED_SOURCE_WITH_REVIEWED_NATIVE_TOOLING_NATIVE_NOT_RUN')
  c['worker_preparation']={'status':'STATIC_REVIEWED_NATIVE_NOT_RUN','preparation':ref(NATIVE/'preparation.json'),'worker':ref(NATIVE/'worker.py'),'runtime':ref(NATIVE/'native_runtime.py'),'manifest_template':ref(NATIVE/'manifest_template.json'),'source_commit':COMMIT,'source_parent_commit':BASE,'runtime_expected_commit':BASE,'independent_review':ref(HERE/'cre_native_preparation_independent_review.json'),'native_backward_executed':False,'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False,'draft_execution_disabled':False}
  c['execution_adapter']={'status':'STATIC_REVIEWED_CATALOGUE_ONLY_NATIVE_NOT_RUN','preparation':ref(OP/'preparation.json'),'release':release_ref,'independent_review':ref(HERE/'cre_operational_preparation_independent_review.json'),'active_binding_manifest_lease_created':False,'transport_executed':False}
  c['next_action']='Reuse reviewed CRE native/op packet only with fresh root owner/context/original deadline and genuine idle permittedGPU0/assets/UUID/three locks. AEF remains earlier ready validation; BEC stays running. Packet binds7ed/expectedruntime026c; if main advances first, preserve historical packet and package/test exact compatible source before a new binding. No native/resource PASS, promotion, GPU1 or old-binding replay.'
  for e in [ref(NATIVE/'preparation.json'),ref(OP/'preparation.json'),ref(HERE/'cre_native_preparation_independent_review.json'),ref(HERE/'cre_operational_preparation_independent_review.json'),release_ref]:
   if e not in c['evidence']:c['evidence'].append(e)
  out['updated_at']=datetime.now(timezone.utc).isoformat()
  others=lambda w:{x['id']:x for x in w['candidates'] if x['id']!=CID}
  assert others(out)==others(work);wb=encode(out);before_sha=sha(wp)
  bb=encode({'owner_token':TOKEN,'work_sha256':before_sha,'candidate_before':next(x for x in work['candidates'] if x['id']==CID),'protected_snapshot':before})
  ib=encode({'owner_token':TOKEN,'recorded_at':out['updated_at'],'before_work_sha256':before_sha,'proposed_work_sha256':hashlib.sha256(wb).hexdigest(),'release':release_ref,'scope':'Only existing CRE static tooling anchors/stage validation; no source/lifecycle/native operation.'})
  guard();assert sha(wp)==before_sha
  exclusive(HERE/'cre_catalogue_before.json',bb);exclusive(HERE/'cre_catalogue_intent.json',ib)
  guard();assert sha(wp)==before_sha
  exclusive(OP/'adapter_release.json',template);replace(wp,wb)
  after=snapshot()
  for k in ['head','index_empty','status_hex','files','protected_ledgers']:assert after[k]==before[k]
  assert read(wp)==out and others(read(wp))==others(work) and not (HERE/'cre_execution').exists()
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'candidate_id':CID,'code_commit':COMMIT,'status':'REVIEWED_STATIC_CRE_CATALOGUE_ANCHORED_NATIVE_NOT_RUN','release':release_ref,'other142_candidates_unchanged':True,'all14_lifecycle_ledgers_unchanged':True,'primary28_status_bytes_index_and026c_unchanged':True,'active_execution_created':False,'work_sha256':sha(wp)}
  exclusive(HERE/'cre_catalogue_result.json',encode(result));print(json.dumps({'status':result['status'],'result':ref(HERE/'cre_catalogue_result.json')}))
 finally:lock.close()
if __name__=='__main__':main()
