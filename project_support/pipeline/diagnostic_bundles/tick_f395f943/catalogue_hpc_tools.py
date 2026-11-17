"""Anchor reviewed HPC static tools and enter validation, without native execution."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent;NATIVE=HERE/'hpc_native_prepare';OP=HERE/'hpc_operational_prepare';CID='hierarchy-tree-resolvent-nonlinear-composition'
COMMIT='2f7eff19ca59cc4586e13ca81a547a18ea7e313d';BASE='56b2a96dc48cc8a88f0f7105527ef448113b1060'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 guard();checks={NATIVE/'preparation.json':'f9a2ab3eb8ee8e26bb0facd437c7247ae075bb10183569c03a2fe124604c8f9f',OP/'preparation.json':'136255da0ba630c73469e7c20234d086776bf219f3e061aa997929ad65f41143',HERE/'hpc_native_preparation_independent_review.json':'b703cfdcff0f731394520180c0da1ba29458d66a9c793d8b5a5924efb5f8d14b',HERE/'hpc_operational_preparation_independent_review.json':'f95fa07070c49cb64ce64e7f1f0630b1513675fd697b75040a218f7aa07c4cfd'}
 for p,h in checks.items():assert sha(p)==h,p
 for p in [HERE/'hpc_native_preparation_independent_review.json',HERE/'hpc_operational_preparation_independent_review.json']:assert read(p)['material_concerns']==[] and read(p)['metadata_blockers']==[]
 for directory in [NATIVE,OP]:
  prep=read(directory/'preparation.json');assert prep['code_commit']==COMMIT
  for name,h in prep['prepared_file_hashes'].items():assert sha(directory/name)==h,name
 assert read(NATIVE/'preparation.json')['native_TRAIN2']=='NOT_RUN' and read(OP/'preparation.json')['all_actual_execution']=='NOT_RUN'
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();baseline=read(HERE/'protected_assets_before.json');assert all(sha(ROOT/'pipeline'/n)==h for n,h in baseline['protected_ledgers'].items())
  work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
  assert c['code_commit']==COMMIT and c['stage']=='implementation' and not c.get('revision_history')
  assert not (OP/'adapter_release.json').exists() and not (HERE/'hpc_execution').exists() and not (HERE/'hpc_tools_catalogue_result.json').exists()
  now=datetime.now(timezone.utc).isoformat();save(HERE/'hpc_tools_catalogue_intent.json',{'owner':EXPECTED,'recorded_at':now,'prior_fields':{k:copy.deepcopy(c.get(k)) for k in ['stage','implementation_status','source_status','worker_preparation','execution_adapter','preparation_scope','next_action']},'native':ref(NATIVE/'preparation.json'),'op':ref(OP/'preparation.json'),'operation':'Static external anchors and exact-template release copy only; no active/native/queue.'})
  guard()
  with (OP/'adapter_release.json').open('xb') as f:f.write((OP/'release_template.json').read_bytes());f.flush();os.fsync(f.fileno())
  assert sha(OP/'adapter_release.json')=='6bfe89a983464779b8faf3984906140d9e4c0575bf67610a4f96200b3038d255'
  c.setdefault('preparation_history',[]).append(ref(HERE/'hpc_tools_catalogue_intent.json'))
  c.update(stage='validation',implementation_status='ACTUAL_SOURCE_WITH_REVIEWED_NATIVE_OPERATIONAL_TOOLING_NATIVE_NOT_RUN',source_status='ACTUAL_ISOLATED_HPC_SOURCE_WITH_REVIEWED_STATIC_NATIVE_TOOLS',native_status='NOT_RUN',resource_status='NOT_RUN',native_execution_code_commit=None,queued=False,
   preparation_scope='Actual exact9 source2f7/parent56 with reviewed version-bound native/op preparation. Original c94/null/0311 and software proofs stay immutable; neither source save, static release nor harness software tests constitute Torch/native/common-pairing/resources/efficacy PASS.',
   next_action='Reuse this reviewed source2f7/parent-runtime56 HPC native/op packet only after genuinely idle authorized GPU0, fresh actual owner/context/original deadline/assets/UUID/three locks. Original AEF continues and CRE remains first prepared alternative. No GPU1, eviction, source sibling ff or old-binding replay. Run original pairedTRAIN2/resources before any receipt/queue/launch; source/main change requires compatible packaging.')
  c['worker_preparation']={'status':'STATIC_REVIEWED_NATIVE_NOT_RUN','preparation':ref(NATIVE/'preparation.json'),'worker':ref(NATIVE/'worker.py'),'runtime':ref(NATIVE/'native_runtime.py'),'manifest_template':ref(NATIVE/'manifest_template.json'),'source_commit':COMMIT,'source_parent_commit':BASE,'runtime_expected_commit':BASE,'independent_review':ref(HERE/'hpc_native_preparation_independent_review.json'),'native_backward_executed':False,'resource_profile_executed':False,'active_native_manifest_or_execution_lease_created':False,'draft_execution_disabled':False}
  c['execution_adapter']={'status':'STATIC_REVIEWED_CATALOGUE_ONLY_NATIVE_NOT_RUN','preparation':ref(OP/'preparation.json'),'release':ref(OP/'adapter_release.json'),'independent_review':ref(HERE/'hpc_operational_preparation_independent_review.json'),'active_binding_manifest_lease_created':False,'transport_executed':False}
  evidence=[ref(p) for p in checks]+[ref(OP/'adapter_release.json'),ref(OP/'release_template.json'),ref(NATIVE/'software_validation.json') if (NATIVE/'software_validation.json').exists() else ref(NATIVE/'static_validation.json'),ref(NATIVE/'packet_validation.json'),ref(HERE/'hpc_native_algorithm_scope_review.json')]
  for e in evidence:
   if e not in c['evidence']:c['evidence'].append(e)
  work['updated_at']=now;tmp=ROOT/'pipeline/research_work.json.f395.hpc_tools.tmp'
  with tmp.open('x',encoding='utf8') as f:json.dump(work,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  guard();os.replace(tmp,ROOT/'pipeline/research_work.json')
  assert all(sha(ROOT/'pipeline'/n)==h for n,h in baseline['protected_ledgers'].items()) and not (HERE/'hpc_execution').exists()
  save(HERE/'hpc_tools_catalogue_result.json',{'recorded_at':now,'candidate_id':CID,'code_commit':COMMIT,'stage':'validation','native':ref(NATIVE/'preparation.json'),'op':ref(OP/'preparation.json'),'release':ref(OP/'adapter_release.json'),'release_template_exact_bytecopy':True,'active_binding_manifest_lease_created':False,'native_resources_admission_queue_launch':'NOT_RUN','primary_runtime_unchanged':BASE})
  print(json.dumps({'HPC_stage':'validation','code_commit':COMMIT,'static_release':ref(OP/'adapter_release.json'),'native_or_resources':'NOT_RUN'}))
 finally:lock.close()
if __name__=='__main__':main()
