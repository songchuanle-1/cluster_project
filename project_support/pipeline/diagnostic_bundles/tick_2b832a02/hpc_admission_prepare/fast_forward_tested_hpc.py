"""One reviewed exact-nine local ff; no remote action and no new commit."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from anchor import ROOT,guard,sha
import hpc_evidence as evidence
HERE=evidence.TICK;CODE=ROOT/'Cluster'
BASE=evidence.BASE;TESTED=evidence.COMMIT
def read(p):return json.loads(Path(p).read_text('utf8'))
def git(*a):return subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(CODE),*a])
def save(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');args=ap.parse_args()
 if not args.execute_root:print('DRAFT_READ_ONLY_NO_FF');return
 evidence.require_execution();evidence.reviewed()
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();assert not any((HERE/n).exists() for n in ['hpc_root_ff_intent.json','hpc_root_ff_result.json','hpc_root_ff_command.json'])
  assert sha(HERE/'hpc_actual_four_result_review.json')==evidence.review_ref()['sha256']
  for e in [evidence.independent_ref()]:assert sha(ROOT/e['path'])==e['sha256'] and read(ROOT/e['path'])['material_concerns']==[]
  b=read(HERE/'protected_assets_before.json');assert b['head']==BASE and b['index_empty'] is True and len(b['files'])==28
  def protected():
   assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex']
   assert not git('diff','--cached','--name-only','-z')
   for p,h in b['files'].items():assert sha(CODE/p)==h
  protected();assert git('rev-parse','HEAD').decode().strip()==BASE
  ledgers={p:sha(ROOT/'pipeline'/p) for p in b['protected_ledgers']};ledgers['research_work.json']=sha(ROOT/'pipeline/research_work.json')
  m=read(HERE/'hpc_execution/native_manifest.json');paths={'framework/model/Quard_model/'+m['candidate_name']+'/'+k:v for k,v in m['candidate_source_hashes'].items()};paths[m['config']]=m['candidate_config_sha256']
  assert len(paths)==9 and git('show','-s','--format=%P',TESTED).decode().strip()==BASE
  assert set(git('diff-tree','--no-commit-id','--name-status','-r',TESTED).decode().splitlines())=={'A\t'+p for p in paths}
  for p,h in paths.items():
   assert not (CODE/p).exists() and p not in b['files']
   assert hashlib.sha256(git('show',TESTED+':'+p)).hexdigest()==h
   assert git('ls-tree',TESTED,'--',p).decode().split()[0]=='100644'
  intent={'recorded_at':datetime.now(timezone.utc).isoformat(),'base':BASE,'tested':TESTED,'source_paths':paths,'protected_status_hex':b['status_hex'],'protected_files':b['files'],'protected_ledgers_after_CRE_archive':ledgers,'new_commit_hpcated':False}
  save(HERE/'hpc_root_ff_intent.json',intent)
  hooks=HERE/'hpc_empty_hooks';hooks.mkdir(exist_ok=False)
  cmd=['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(CODE),'-c','merge.autoStash=false','-c','core.autocrlf=false','-c','core.eol=lf','-c','core.hooksPath='+str(hooks),'merge','--ff-only',TESTED]
  guard();protected();run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=120,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_LFS_SKIP_SMUDGE='1'))
  save(HERE/'hpc_root_ff_command.json',{'command':cmd,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
  assert run.returncode==0,'Inspect exact HEAD/status; no reset/stash/clean/retry'
  assert git('rev-parse','HEAD').decode().strip()==TESTED;protected()
  for p,h in paths.items():assert sha(CODE/p)==h
  assert all(sha(ROOT/'pipeline'/p)==h for p,h in ledgers.items())
  save(HERE/'hpc_root_ff_result.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'HEAD':TESTED,'source_paths':paths,'only_nine_tested_additions':True,'protected_28_status_and_bytes_unchanged':True,'index_empty':True,'protected_lifecycle_unchanged':True,'new_commit_hpcated':False,'remote_sync_performed':False,'admission_or_launch_performed':False})
  print('Local primary fast-forwarded to exact tested HPC6282; 28 user files/index/all protected lifecycle ledgers retained. No remote sync or launch.')
 finally:lock.close()
if __name__=='__main__':main()
