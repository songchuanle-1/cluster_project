"""Save frozen NEC exact-nine as one isolated child, without touching main/worktree/index."""
from pathlib import Path
from datetime import datetime,timezone
import sys,os,json,hashlib
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
PROTO=ROOT/'pipeline/diagnostic_bundles/tick_d94467a9/new_candidate_one'
BASE='4457a46f9075f61e83340aa0f0af87d5bf4e986c'
def main():
 if sys.argv[1:]!=['--execute-root']:print('DEFAULT_NOP');return
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  b=u.read(HERE/'protected_assets_before.json');u.protect(b)
  prep=PROTO/'preparation.json';assert sha(prep)=='7592b0e8225f907e4225ed63bcdf8b580fb42abb8d27ef3a0e9c5a08913deb7d'
  p=u.read(prep);peer=ROOT/'pipeline/diagnostic_bundles/tick_d94467a9/nec_source_independent_review.json'
  assert sha(peer)=='8cdca2c8c45a58ae03ef0344187439cc16518c4d641369456dbdc36aae73a1ec'
  paths=p['source_files'];assert len(paths)==9 and p['source_commit'] is None and p['source_parent_commit'] is None
  assert sha(PROTO/'native_protocol.md')=='17ba9fabee4b30da3ecbba33a8ca8d7096f017223013a0548b3a04551711c709'
  checks=[]
  for name,h in paths.items():
   content=(PROTO/'staged_repository'/name).read_bytes();assert hashlib.sha256(content).hexdigest()==h and not (ROOT/'Cluster'/name).exists()
   if name.endswith('.py'):compile(content,name,'exec')
   checks.append({'path':name,'sha256':h,'source_compile_if_python':True,'absent_from_primary':True})
  assert u.git('rev-parse','HEAD').decode().strip()==BASE and not u.git('ls-tree','-r','--name-only',BASE,'--',*list(paths))
  folder=HERE/'nec_version_prepare';folder.mkdir(exist_ok=False)
  u.save(folder/'version_intent.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'operation':'frozen_exact9_isolated_source_save_only','source_preparation':u.ref(prep),'source_protocol':u.ref(PROTO/'native_protocol.md'),'source_review':u.ref(peer),'parent_commit':BASE,'source_files':paths,'main_ff_remote_or_admission_authorized_by_this_helper':False})
  env=dict(os.environ,GIT_INDEX_FILE=str(folder/'isolated.index'),GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0')
  guard();u.git('read-tree',BASE,env=env)
  for name,h in paths.items():
   data=(PROTO/'staged_repository'/name).read_bytes();oid=u.git('hash-object','-w','--stdin',env=env,data=data).decode().strip();u.git('update-index','--add','--cacheinfo','100644,'+oid+','+name,env=env)
   dest=folder/'frozen_source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  tree=u.git('write-tree',env=env).decode().strip();guard();commit=u.git('commit-tree',tree,'-p',BASE,env=env,data=b'M228-NEC frozen independent native-YAML candidate source\n').decode().strip()
  reference='refs/codex/cluster_project/M228-NEC/94c2ad26';guard();u.git('update-ref',reference,commit,'0'*40)
  assert u.git('show','-s','--format=%P',commit).decode().strip()==BASE
  diff=u.git('diff-tree','--no-commit-id','--name-status','-r',commit).decode().splitlines();assert set(diff)=={'A\t'+name for name in paths}
  for name,h in paths.items():assert hashlib.sha256(u.git('show',commit+':'+name)).hexdigest()==h
  def entries(c):return {x.split(b'\t',1)[1]:x.split(b'\t',1)[0] for x in u.git('ls-tree','-r','-z',c).split(b'\0') if x}
  before=entries(BASE);after=entries(commit);assert all(after.get(n)==v for n,v in before.items())
  u.protect(b)
  proof={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'candidate_id':p['candidate_id'],'experiment_id':p['experiment_id'],'source_commit':commit,'code_commit':commit,'parent_commit':BASE,'source_parent_commit':BASE,'frozen_source_files':paths,'source_preparation':u.ref(prep),'native_protocol':u.ref(PROTO/'native_protocol.md'),'source_review':u.ref(peer),'pinned_ref':reference,'diff_exact9A':True,'all_prior_tree_entries_unchanged':True,'checks':checks,'new_model_revision':False,'main_HEAD_unchanged':True,'normal_index_and_user28_and_running18_source_files_and38_lifecycle_unchanged':True,'native_or_resource_checks':'NOT_RUN','scientific_admission':False}
  u.save(folder/'isolated_source_version.json',proof)
  print(json.dumps({'status':'NEC_FROZEN_SOURCE_SAVED_ISOLATED_NOT_NATIVE_TESTED','code_commit':commit,'parent_commit':BASE,'proof':u.ref(folder/'isolated_source_version.json')}))
 finally:lock.close()
if __name__=='__main__':main()
