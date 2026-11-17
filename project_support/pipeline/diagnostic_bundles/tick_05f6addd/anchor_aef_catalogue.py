"""Root-only once operation: static AE F catalogue, never execution authority."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot

ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='05f6addd722d487fbdc663753af44b83'
CID='hierarchy-parent-antisymmetric-edge-flux'
COMMIT='56b2a96dc48cc8a88f0f7105527ef448113b1060'
BASE='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
NATIVE=HERE/'aef_native_prepare'; OP=HERE/'aef_operational_prepare'
EXPECTED={
 'aef_native_prepare/preparation.json':'78f7c45ea05147009ce67689177486f4344191e8cf3d4eb19fec59e1a71a6e39',
 'aef_operational_prepare/preparation.json':'965ee3343199ab509bb6ce9d643204dc3b93f18322c11dd857047cd0e43d2b70',
 'aef_native_preparation_independent_review.json':'ddf934472d4ac713500d309a69a5817730a8d6c7483efc09078da05be92e9055',
}
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def save(p,v):
 with Path(p).open('xb') as f:f.write(encode(v));f.flush();os.fsync(f.fileno())
def replace(p,data):
 tmp=p.with_name(p.name+'.'+TOKEN+'.catalogue.tmp')
 with tmp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def check_ref(r):
 p=(ROOT/r['path']).resolve();assert p.is_relative_to(ROOT.resolve()) and sha(p)==r['sha256'];return p
def main():
 assert sys.argv[1:]==['--execute-root']
 owner=guard()
 assert not (HERE/'aef_catalogue_intent.json').exists(),'Partial operation must be reconciled, never replayed'
 assert not (OP/'adapter_release.json').exists()
 for name,digest in EXPECTED.items():assert sha(HERE/name)==digest,name
 n=read(NATIVE/'preparation.json');o=read(OP/'preparation.json');review=read(HERE/'aef_native_preparation_independent_review.json')
 assert review['material_concerns']==[] and review['status']=='STATIC_AEF_NATIVE_PREPARATION_REVIEWED_NOT_NATIVE_PASS'
 op_peer=read(HERE/'aef_operational_preparation_independent_review.json')
 assert op_peer['material_concerns']==[] and op_peer['candidate_id']==CID and op_peer['code_commit']==COMMIT
 assert check_ref(op_peer['anchors']['preparation'])==OP/'preparation.json'
 for folder,packet in [(NATIVE,n),(OP,o)]:
  assert packet['candidate_id']==CID and packet['code_commit']==COMMIT and packet['source_parent_commit']==BASE
  for name,digest in packet['prepared_file_hashes'].items():
   p=(folder/name).resolve();assert p.is_relative_to(folder.resolve()) and sha(p)==digest
 assert n['native']==n['resources']=='NOT_RUN' and o['all_actual_execution']=='NOT_RUN'
 assert len(n['manifest_execution_fields'])==10 and all(v is None for v in n['manifest_execution_fields'].values())
 for key in ['source_preparation','native_protocol','isolated_source_version','isolated_source_version_independent_review','source_version_binding']:check_ref(n[key])
 for key in ['native_preparation','native_manifest_template','native_source_version_binding','native_independent_review','source_preparation','actual_source_version','actual_source_version_independent_review','native_protocol','release_template']:check_ref(o[key])
 template_bytes=(OP/'release_template.json').read_bytes()
 release_ref={'path':(OP/'adapter_release.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(template_bytes).hexdigest()}
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();before=snapshot();baseline=read(HERE/'protected_assets_before.json')
  assert all(before[k]==baseline[k] for k in ['head','index_empty','status_hex','files','protected_ledgers','candidate_digests'])
  wp=ROOT/'pipeline/research_work.json';original=read(wp);out=copy.deepcopy(original)
  c=next(x for x in out['candidates'] if x['id']==CID)
  assert len(out['candidates'])==142 and c['stage']=='implementation' and c['code_commit']==COMMIT
  assert c['native_status']==c['resource_status']=='NOT_RUN' and c.get('native_execution_code_commit') is None
  assert not c.get('worker_preparation') and not c.get('execution_adapter') and not c.get('revision_history')
  c.update(stage='validation',source_status='ACTUAL_ISOLATED_SOURCE_WITH_REVIEWED_NATIVE_TOOLING_NATIVE_NOT_RUN')
  c['worker_preparation']={'status':'STATIC_REVIEWED_NATIVE_NOT_RUN','preparation':ref(NATIVE/'preparation.json'),'worker':ref(NATIVE/'worker.py'),'runtime':ref(NATIVE/'native_runtime.py'),'manifest_template':ref(NATIVE/'manifest_template.json'),'source_commit':COMMIT,'source_parent_commit':BASE,'runtime_expected_commit':BASE,'independent_review':ref(HERE/'aef_native_preparation_independent_review.json'),'native_backward_executed':False,'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False,'draft_execution_disabled':False}
  c['execution_adapter']={'status':'STATIC_REVIEWED_CATALOGUE_ONLY_NATIVE_NOT_RUN','preparation':ref(OP/'preparation.json'),'release':release_ref,'independent_review':ref(HERE/'aef_operational_preparation_independent_review.json'),'active_binding_manifest_lease_created':False,'transport_executed':False}
  c['next_action']='Run reviewed AEF adapter original matched M95/AEF TRAIN2/resource checks only after sole permitted GPU0 becomes genuinely idle; fresh actual owner/context/immutable deadline/source/assets/UUID/three-lock/lease checks required. Keep BEC1558071/source026c running; noGPU1, promotion, resampling, numeric tuning or old-hold recovery.'
  for r in [ref(NATIVE/'preparation.json'),ref(HERE/'aef_native_preparation_independent_review.json'),ref(OP/'preparation.json'),ref(HERE/'aef_operational_preparation_independent_review.json'),release_ref]:
   if r not in c['evidence']:c['evidence'].append(r)
  out['updated_at']=datetime.now(timezone.utc).isoformat()
  others=lambda w:{x['id']:x for x in w['candidates'] if x['id']!=CID}
  assert others(out)==others(original)
  data=encode(out);before_work=sha(wp)
  save(HERE/'aef_catalogue_before.json',{'owner_token':TOKEN,'work_sha256':before_work,'candidate_before':next(x for x in original['candidates'] if x['id']==CID),'protected_snapshot':before})
  save(HERE/'aef_catalogue_intent.json',{'owner_token':TOKEN,'recorded_at':out['updated_at'],'before_work_sha256':before_work,'proposed_work_sha256':hashlib.sha256(data).hexdigest(),'release':release_ref,'scope':'One candidate static preparation anchors and stage validation only; no active binding, lease, native, queue or source promotion.'})
  guard();assert sha(wp)==before_work
  with (OP/'adapter_release.json').open('xb') as f:f.write(template_bytes);f.flush();os.fsync(f.fileno())
  replace(wp,data)
  after=snapshot()
  assert all(after[k]==before[k] for k in ['head','index_empty','status_hex','files','protected_ledgers'])
  assert read(wp)==out and others(read(wp))==others(original) and (OP/'adapter_release.json').read_bytes()==template_bytes
  assert not (HERE/'aef_execution').exists()
  save(HERE/'aef_catalogue_result.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'candidate_id':CID,'code_commit':COMMIT,'status':'REVIEWED_STATIC_CATALOGUE_ANCHORED_NATIVE_NOT_RUN','release':release_ref,'all141_other_candidates_unchanged':True,'all14_lifecycle_ledgers_unchanged':True,'primary28_status_bytes_index_and026c_unchanged':True,'active_execution_created':False,'work_sha256':sha(wp)})
  print(json.dumps({'status':'REVIEWED_STATIC_CATALOGUE_ANCHORED_NATIVE_NOT_RUN','result':ref(HERE/'aef_catalogue_result.json')}))
 finally:lock.close()
if __name__=='__main__':main()
