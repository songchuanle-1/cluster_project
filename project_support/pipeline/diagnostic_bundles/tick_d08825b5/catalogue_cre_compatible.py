"""Anchor the actual compatible CRE source/static tools; never launch or mark native PASS."""
from pathlib import Path
from datetime import datetime,timezone
import copy,importlib.util,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent;PK=HERE/'cre_compatible_tooling';CID='hierarchy-cross-root-directed-edge-broadcast'
NEW='d58576b396cfb54577652be972f3ffaffda508c9';BASE='56b2a96dc48cc8a88f0f7105527ef448113b1060'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def atomic(p,v):
 guard();tmp=Path(str(p)+'.d088.cre_catalogue.tmp')
 with tmp.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 guard();os.replace(tmp,p)
def main():
 guard();checks={PK/'preparation.json':'dd7f12b3b3aa884caf90b4c5b1b8c02fce3791621677d9e0eb1541d227ac601b',HERE/'cre_compatible_actual_source_version_independent_review.json':'96651ba36e21499472d41853d95cc022bcbbf50182591cd8b266901486e29b5f',HERE/'cre_compatible_tooling_independent_review.json':'bb92b63691d7a687c06b2fa98055b27a0321212d298a11876004102fe66b5028',HERE/'cre_version_prepare/isolated_source_version.json':'1b9aac2e07fb729dc1cc658c1db9ffa99b7c01ab915c6f425742eefa1af9e47c'}
 for p,h in checks.items():assert sha(p)==h,p
 for p in [HERE/'cre_compatible_actual_source_version_independent_review.json',HERE/'cre_compatible_tooling_independent_review.json']:assert read(p)['material_concerns']==[]
 prep=read(PK/'preparation.json')
 for rel,h in prep['prepared_file_hashes'].items():assert sha(PK/rel)==h,rel
 assert prep['code_commit']==NEW and prep['source_parent_commit']==BASE and prep['all_actual_execution']=='NOT_RUN'
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();baseline=read(HERE/'protected_assets_before.json');assert all(sha(ROOT/'pipeline'/n)==h for n,h in baseline['protected_ledgers'].items())
  work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
  assert c['code_commit']=='7ed9373db335d44c884133da3eced3fca03ad29a' and c['stage']=='validation' and not c.get('revision_history')
  assert not (PK/'adapter_release.json').exists() and not (HERE/'cre_catalogue_result.json').exists() and not (HERE/'cre_execution').exists()
  now=datetime.now(timezone.utc).isoformat();prior=copy.deepcopy(c)
  save(HERE/'cre_catalogue_intent.json',{'owner':EXPECTED,'recorded_at':now,'prior_candidate':prior,'actual_compatible_source':ref(HERE/'cre_version_prepare/isolated_source_version.json'),'native_op_preparation':ref(PK/'preparation.json'),'operation':'compatible source/static catalogue only; no source deployment/admission/native/queue/launch'})
  guard()
  with (PK/'adapter_release.json').open('xb') as f:f.write((PK/'release_template.json').read_bytes());f.flush();os.fsync(f.fileno())
  assert sha(PK/'adapter_release.json')==sha(PK/'release_template.json')
  c.setdefault('source_version_history',[]).append({'recorded_at':now,'reason':'Actual unchanged CRE9 repackaged on current56; old7ed/026c source/native/op and c760 original null stay immutable, no model revision.','prior_fields':{k:copy.deepcopy(prior.get(k)) for k in ['code_commit','source_commit','source_parent_commit','future_version_parent','source_version','isolated_worktree','worker_preparation','execution_adapter','operational_compatibility','preparation_scope','source_status']},'actual_source_version':ref(HERE/'cre_version_prepare/isolated_source_version.json'),'actual_source_peer':ref(HERE/'cre_compatible_actual_source_version_independent_review.json')})
  c.update(code_commit=NEW,source_commit=NEW,source_parent_commit=BASE,future_version_parent=BASE,
   source_version=ref(HERE/'cre_version_prepare/isolated_source_version.json'),isolated_worktree=str(ROOT/'pipeline/isolated_versions/cre_d08825b5'),
   source_status='ACTUAL_COMPATIBLE_ISOLATED_SOURCE_D585_NATIVE_NOT_RUN',version_packaging_status='EXACT9A_SINGLE_CHILD56_PRIMARY_RUNTIME_NOT_PROMOTED',native_execution_code_commit=None,native_status='NOT_RUN',resource_status='NOT_RUN',queued=False,
   preparation_scope='Unchanged original CRE9 now has actual compatible isolated d585 child56 and independently reviewed static native/op tools. Original c760/null/source7ed-parent026c/old packets remain historical evidence; no Tensor/native/common pairing/resources or efficacy PASS.',
   operational_compatibility={'actual_source_commit':NEW,'actual_parent_commit':BASE,'actual_primary_runtime_unchanged':BASE,'frozen9_source_unchanged':True,'actual_native_or_resource_results':'NOT_RUN','source_version':ref(HERE/'cre_version_prepare/isolated_source_version.json'),'independent_review':ref(HERE/'cre_compatible_actual_source_version_independent_review.json')},
   next_action='Use this existing reviewed compatible CRE d585/parent-runtime56 tool packet only after genuinely idle authorized GPU0, fresh owner/context/original deadline/assets/UUID/three locks. AEF original GPU0 training continues. No GPU1, eviction, old-binding replay, old7ed sibling ff or scientific gate relaxation. Execute original paired nativeTRAIN2/resources then admit/dispatch when passed.')
  c['worker_preparation']={'status':'STATIC_COMPATIBLE_REVIEWED_NATIVE_NOT_RUN','preparation':ref(PK/'native/preparation.json'),'worker':ref(PK/'native/worker.py'),'runtime':ref(PK/'native/native_runtime.py'),'manifest_template':ref(PK/'native/manifest_template.json'),'source_commit':NEW,'source_parent_commit':BASE,'runtime_expected_commit':BASE,'independent_review':ref(HERE/'cre_compatible_tooling_independent_review.json'),'native_backward_executed':False,'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False,'draft_execution_disabled':False}
  c['execution_adapter']={'status':'STATIC_COMPATIBLE_REVIEWED_CATALOGUE_ONLY_NATIVE_NOT_RUN','preparation':ref(PK/'preparation.json'),'release':ref(PK/'adapter_release.json'),'independent_review':ref(HERE/'cre_compatible_tooling_independent_review.json'),'active_binding_manifest_lease_created':False,'transport_executed':False}
  evidence=[ref(p) for p in checks]+[ref(PK/'adapter_release.json'),ref(PK/'release_template.json'),ref(PK/'software_validation.json'),ref(PK/'exact_literal_port_validation.json'),ref(HERE/'cre_version_prepare/preparation.json')]
  for e in evidence:
   if e not in c['evidence']:c['evidence'].append(e)
  work['updated_at']=now;atomic(ROOT/'pipeline/research_work.json',work)
  save(HERE/'cre_catalogue_result.json',{'recorded_at':now,'owner':EXPECTED,'candidate_id':CID,'code_commit':NEW,'parent_runtime':BASE,'native_op_preparation':ref(PK/'preparation.json'),'source_version':ref(HERE/'cre_version_prepare/isolated_source_version.json'),'release':ref(PK/'adapter_release.json'),'release_is_exact_static_template_copy':True,'native_resources_admission_queue_launch':'NOT_RUN','source_deployment':False,'prior_frozen_artifacts_preserved':True})
  print(json.dumps({'code_commit':NEW,'static_release':ref(PK/'adapter_release.json'),'source_currently_compatible':True,'native_or_resources':'NOT_RUN'}))
 finally:lock.close()
if __name__=='__main__':main()
