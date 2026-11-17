"""Record the actual first HPC isolated source version; no native/admission claims."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent;CID='hierarchy-tree-resolvent-nonlinear-composition'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 guard();source=HERE/'hpc_version_prepare/isolated_source_version.json';peer=HERE/'hpc_actual_source_version_independent_review.json'
 assert sha(source)=='9cc3661e59d02204c718e0c217112a41a5087e654db06ad816009cf50a88b639' and sha(peer)=='e3e2b16cb9f3c65d6aa4d3ae7502355cd337626712f3f6e5394fc6801161dee4'
 proof=read(source);review=read(peer);assert review['material_concerns']==[] and proof['diff_exact9A'] is True and proof['isolated_worktree_and_index_clean'] is True
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
  assert c['code_commit'] is None and c['source_commit'] is None and c['stage']=='implementation' and not c.get('revision_history')
  now=datetime.now(timezone.utc).isoformat();old={k:copy.deepcopy(c.get(k)) for k in ['code_commit','source_commit','source_parent_commit','future_version_parent','source_status','source_version','isolated_worktree','next_action']}
  save(HERE/'hpc_source_catalogue_intent.json',{'recorded_at':now,'owner':EXPECTED,'prior_fields':old,'actual_source_version':ref(source),'actual_source_review':ref(peer)})
  c.setdefault('source_version_history',[]).append({'recorded_at':now,'reason':'First exact9 local source save on actual current56; original c94 private source/null declarations unchanged. No model revision/native execution or source deployment.','prior_fields':old,'actual_version':ref(source),'actual_version_review':ref(peer)})
  c.update(code_commit=proof['code_commit'],source_commit=proof['code_commit'],source_parent_commit=proof['parent_commit'],future_version_parent=proof['parent_commit'],source_version=ref(source),isolated_worktree=proof['worktree'],version_packaging_status='EXACT9A_SINGLE_CHILD56_PRIMARY_RUNTIME_NOT_PROMOTED',source_status='ACTUAL_ISOLATED_HPC_SOURCE_NATIVE_TOOLING_PENDING',native_execution_code_commit=None,native_status='NOT_RUN',resource_status='NOT_RUN',queued=False,next_action='Complete version-bound reviewed HPC native and operational preparation for actual2f7eff19/parent-runtime56 while original AEF runs. Then use fresh owner/unchanged deadline/assets/actual idle authorizedGPU0/UUID/three locks for original paired TRAIN2/resources before admission. No GPU1, eviction, sibling ff, resampling or untested receipt.')
  c['operational_compatibility']={'actual_source_commit':proof['code_commit'],'actual_parent_commit':proof['parent_commit'],'actual_primary_runtime_unchanged':proof['parent_commit'],'frozen9_source_unchanged':True,'source_version':ref(source),'independent_review':ref(peer),'actual_native_or_resource_results':'NOT_RUN'}
  for p in [source,peer,HERE/'hpc_version_prepare/preparation.json',HERE/'hpc_source_version_helper_review.json']:
   e=ref(p)
   if e not in c['evidence']:c['evidence'].append(e)
  work['updated_at']=now;tmp=ROOT/'pipeline/research_work.json.f395.hpc_source.tmp'
  with tmp.open('x',encoding='utf8') as f:json.dump(work,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  guard();os.replace(tmp,ROOT/'pipeline/research_work.json')
  save(HERE/'hpc_source_catalogue_result.json',{'recorded_at':now,'candidate_id':CID,'code_commit':c['code_commit'],'source_version':ref(source),'primary_runtime_unchanged':True,'native_resources_admission_queue_launch':'NOT_RUN','original_null_frozen_payload_unchanged':True})
  print('HPC actual source2f7eff19 recorded; primary/runtime56 unchanged; native/resources NOT_RUN.')
 finally:lock.close()
if __name__=='__main__':main()
