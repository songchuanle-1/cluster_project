"""Root-only exact-nine APF isolated source save. Default no Git/source/shared write."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,re,subprocess,sys
HERE=Path(__file__).resolve().parent;TICK=HERE.parent;ROOT=Path('D:/project/cluster_project');REPO=ROOT/'Cluster'
sys.path.insert(0,str(TICK))
from anchor import guard as current_guard,EXPECTED
ANCHOR_SHA='42fb229630a4a27c760a02fe53c4ae7da9b2df406c92388cb03a31b1ad924b9c'
GIT=Path('C:/Program Files (x86)/Git/cmd/git.exe');DEST=ROOT/'pipeline/isolated_versions/apf_01b53a4e'
SOURCE=TICK/'new_candidate_prepare';REVIEW=TICK/'new_candidate_independent_review.json'
SOURCE_SHA='04993a8d0e6ffd6b95b1d5f0e1c9052b4efe726ff0fbfd69587668869068060a'
MANIFEST_SHA='0ef045c73d89c3c33200f31bb7eeb05667f81e2bf653f77aafb8951c6b6fd8e3'
REVIEW_SHA='ab88679a854a1ee31d96033b2c609f32ca7f3b6bc50e9ac814c005806039a1a2'
BASELINE=TICK/'protected_assets_before.json';BASELINE_SHA='b09446d92905ce6de765fc2b3c8e0586bab6d62df03a95032dbda420dbd43b67'
ALLOWED_PARENTS={'56b2a96dc48cc8a88f0f7105527ef448113b1060','d58576b396cfb54577652be972f3ffaffda508c9'}
CID='hierarchy-ancestry-path-factor-composition';EXP='M219-APF';MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_apf'
CONFIG='configs/Quard/ctf_hcg_csort_apf/'+MODEL+'.yaml'
PARENT=None;SOURCE_PATHS=();MESSAGE='Add APF ancestry path factor composition (native pending)'
BOUNDARY='Source-only exact-nine isolated child of the explicitly supplied actual current primary parent. Original0499 source/code/actualparent NULL and reference56 declarations remain unchanged. No primary ff, native result, admission, revision, queue or launch. Future primary advancement requires explicitly compatible packaging and actual testing; no sibling fast-forward assumed.'

def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p).resolve();need(p.is_relative_to(ROOT.resolve()),'Reference escaped project');return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def owner():
 need(sha(TICK/'anchor.py')==ANCHOR_SHA,'Reviewed current owner guard changed');actual=current_guard();need(actual==EXPECTED,'Actual original six owner fields required')
 need(EXPECTED['token']=='01b53a4e60c941719a2eb3bea379789b','Wrong current root tick')
 need(os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id'] and os.environ.get('GIT_OPTIONAL_LOCKS')=='0' and sys.dont_write_bytecode,'Actual root environment/python-B/GIT_OPTIONAL_LOCKS0 required; never override subthread identity')
 now=datetime.now(timezone.utc);need(datetime.fromisoformat(EXPECTED['generated_at'])<=now<datetime.fromisoformat(EXPECTED['deadline_at']),'Original unchanged owner deadline expired/future')
def save(name,value):
 owner();data=encoded(value)
 with (HERE/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def git(repo,*args):
 repo=Path(repo).resolve();need(repo in (REPO.resolve(),DEST.resolve()),'Git repository escaped scope')
 need(args and args[0] in {'rev-parse','status','diff','ls-tree','show','rev-list','check-attr','config','worktree','add','commit','diff-tree'},'Unsupported Git operation')
 if args[0]=='worktree':need(repo==REPO.resolve() and args==('worktree','add','--detach',str(DEST),PARENT),'Only exact detached worktree creation allowed')
 if args[0]=='add':need(repo==DEST.resolve() and args==('add','--',*SOURCE_PATHS),'Only exact nine isolated paths may be staged')
 if args[0]=='commit':need(repo==DEST.resolve() and args==('commit','-m',MESSAGE),'Only ordinary isolated candidate commit allowed')
 env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_LFS_SKIP_SMUDGE='1',GIT_ALLOW_PROTOCOL='file')
 command=[str(GIT),'--no-optional-locks','-c','core.autocrlf=false','-c','core.eol=lf','-c','core.fsmonitor=false','-c','submodule.recurse=false','-c','core.hooksPath='+str(HERE/'empty_hooks'),'-C',str(repo),*args]
 p=subprocess.run(command,capture_output=True,timeout=120,env=env);need(p.returncode==0,p.stderr.decode('utf8',errors='replace'));return p.stdout

def source_details():
 need(sha(SOURCE/'preparation.json')==SOURCE_SHA and sha(SOURCE/'source_manifest.json')==MANIFEST_SHA and sha(REVIEW)==REVIEW_SHA,'Actual frozen source/manifest/independent review changed')
 p=read(SOURCE/'preparation.json');m=read(SOURCE/'source_manifest.json');v=read(REVIEW)
 need(p['candidate_id']==CID and p['experiment_id']==EXP and all(p[k] is None for k in ['code_commit','source_commit','source_parent_commit']),'Original NULL source metadata must remain frozen')
 need(v['status']=='STATIC_APF_SOURCE_TOPOLOGY_AND_INTEGRATION_REVIEWED_NOT_NATIVE_PASS' and v['candidate_id']==CID and v['experiment_id']==EXP and v['code_commit'] is None and v['material_concerns']==[] and v['anchors']['preparation']==ref(SOURCE/'preparation.json'),'Actual source peer identity/hash failed')
 for name,digest in p['prepared_file_hashes'].items():
  f=(SOURCE/name).resolve();need(f.is_relative_to(SOURCE.resolve()) and sha(f)==digest,'Frozen payload changed: '+name)
 names={'__init__.py','backbone.py','dec.py','hier_postprocess.py','loss.py','ancestry_path_factor.py','network.py','sample_model.py'}
 exact={'framework/model/Quard_model/'+MODEL+'/'+n for n in names}|{CONFIG}
 frozen={n.removeprefix('staged_repository/'):h for n,h in p['prepared_file_hashes'].items() if n.startswith('staged_repository/')}
 need(set(frozen)==exact and len(frozen)==9 and frozen==p['source_files']==m['source_files']==v['source_files_exact9'],'Only exact frozen8model+YAML9 allowed')
 need(frozen[CONFIG]=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a','Original native YAML changed')
 return frozen

def snapshot():
 need(sha(BASELINE)==BASELINE_SHA,'Original protection inventory changed');b=read(BASELINE)
 need(len(b['files'])==28 and len(b['protected_ledgers'])==16,'Wrong protected inventory')
 head=git(REPO,'rev-parse','HEAD').decode().strip();need(head==PARENT,'Primary HEAD must exactly equal explicit --parent; no source promotion or inferred parent')
 status=git(REPO,'status','--porcelain=v1','-z','--untracked-files=all');need(status.hex()==b['status_hex'],'Original28 status changed')
 files={n:sha(REPO/n) for n in b['files']};need(files==b['files'],'Original28 bytes changed')
 index=Path(git(REPO,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else REPO/index
 staged=git(REPO,'diff','--cached','--name-only','-z')
 paths=set(b['protected_ledgers'])|{'experiments/M217-CRE.json','admissions/M217-CRE.json'}
 ledgers={n:sha(ROOT/'pipeline'/n) for n in sorted(paths) if (ROOT/'pipeline'/n).is_file()}
 need(set(b['protected_ledgers'])<=set(ledgers),'An existing protected lifecycle ledger disappeared')
 extra={n:sha(ROOT/n) for n in ['pipeline/research_work.json','pipeline/codex_memory.md','pipeline/closure_policy.json','pipeline/execution_mode.json','SERVERS.yaml']}
 return {'primary_HEAD':head,'status_hex':status.hex(),'primary_index_sha256':sha(index),'primary_staged_entries_hex':staged.hex(),'protected28':files,'current_lifecycle_ledgers':ledgers,'current_lifecycle_presence':{n:n in ledgers for n in sorted(paths)},'extra_shared_files':extra}

def execute(parent):
 global PARENT,SOURCE_PATHS
 owner();need(parent in ALLOWED_PARENTS,'Explicit --parent must be exact tested56 or compatibleCREd585');PARENT=parent;need(GIT.is_file(),'Reviewed Git executable missing')
 frozen=source_details();SOURCE_PATHS=tuple(sorted(frozen))
 need(DEST.resolve().is_relative_to((ROOT/'pipeline/isolated_versions').resolve()) and not DEST.exists(),'Existing/escaped isolated destination; preserve partial attempt, never replay or clean')
 for n in ['isolated_version_before.json','isolated_version_operation_intent.json','isolated_source_version.json','empty_hooks']:
  need(not (HERE/n).exists(),'Existing/partial APF save requires read-only reconcile: '+n)
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));need(lock is not None,'Canonical project lock busy; no mutation started')
 try:
  owner();before=snapshot()
  # Read-only configuration inspection uses raw Git because --get may validly return1.
  cp=subprocess.run([str(GIT),'--no-optional-locks','-c','core.fsmonitor=false','-C',str(REPO),'config','--get-regexp',r'^(core\.hooksPath|filter\..*)$'],capture_output=True,timeout=20,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'))
  need(cp.returncode in (0,1),'Cannot inspect Git filters/hooks');allowed={'filter.lfs.clean':'git-lfs clean -- %f','filter.lfs.smudge':'git-lfs smudge -- %f','filter.lfs.process':'git-lfs filter-process','filter.lfs.required':'true'}
  need(all(len(row.split(' ',1))==2 and allowed.get(row.split(' ',1)[0])==row.split(' ',1)[1] for row in cp.stdout.decode().splitlines()),'Unknown hooks/filters require separate review')
  need(not(set(frozen)&set(before['protected28'])),'Candidate paths overlap protected user files')
  for n in frozen:need(not git(REPO,'ls-tree',PARENT,'--',n) and not (REPO/n).exists(),'Candidate path already tracked/present')
  tracked=git(REPO,'ls-tree','-r','--name-only',PARENT).decode().splitlines();need(not any(Path(n).name==Path(CONFIG).name for n in tracked),'Native config basename already tracked')
  def mutation_guard():
   owner();need(snapshot()==before and source_details()==frozen,'Primary/index28/lifecycle/source changed; preserve partial attempt, never retry or rollback')
  mutation_guard();save('isolated_version_before.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'protected':before,'source_preparation':ref(SOURCE/'preparation.json'),'explicit_parent':PARENT})
  save('isolated_version_operation_intent.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'experiment_id':EXP,'operation':'One local detached worktree and ordinary exact9A candidate commit only','explicit_parent':PARENT,'worktree':str(DEST),'frozen_source_files':frozen,'source_preparation':ref(SOURCE/'preparation.json'),'independent_review':ref(REVIEW),'compatibility_boundary':BOUNDARY,'partial_policy':'Never reset/clean/stash/force/delete/replay; retain exact attempt for read-only reconciliation.'})
  mutation_guard();(HERE/'empty_hooks').mkdir(exist_ok=False);DEST.parent.mkdir(exist_ok=True)
  mutation_guard();git(REPO,'worktree','add','--detach',str(DEST),PARENT)
  need(git(DEST,'rev-parse','HEAD').decode().strip()==PARENT and not git(DEST,'status','--porcelain=v1','-z','--untracked-files=all'),'New detached worktree not clean exact parent')
  for n,h in frozen.items():
   mutation_guard();f=(DEST/n).resolve();need(f.is_relative_to(DEST.resolve()) and not f.exists(),'Unsafe isolated destination');f.parent.mkdir(parents=True,exist_ok=True)
   with f.open('xb') as stream:stream.write((SOURCE/'staged_repository'/n).read_bytes());stream.flush();os.fsync(stream.fileno())
   need(sha(f)==h,'Copied source bytes differ')
  need(not git(DEST,'check-attr','-a','--',*SOURCE_PATHS).strip(),'Target Git attributes require review')
  mutation_guard();git(DEST,'add','--',*SOURCE_PATHS)
  need(set(git(DEST,'diff','--cached','--name-status').decode().splitlines())=={'A\t'+n for n in frozen},'Staged diff is not exact9A')
  need({n:hashlib.sha256(git(DEST,'show',':'+n)).hexdigest() for n in frozen}==frozen,'Staged source blobs changed')
  mutation_guard();commit_output=git(DEST,'commit','-m',MESSAGE).decode('utf8',errors='replace')
  commit=git(DEST,'rev-parse','HEAD').decode().strip();need(re.fullmatch('[0-9a-f]{40}',commit) is not None,'New commit identity malformed')
  need(git(DEST,'rev-list','--parents','-n','1',commit).decode().split()==[commit,PARENT],'New commit is not one child of explicit parent')
  need(not git(DEST,'status','--porcelain=v1','-z','--untracked-files=all') and not git(DEST,'diff','--cached','--name-only','-z'),'Isolated worktree/index not clean')
  blobs={n:hashlib.sha256(git(DEST,'show',commit+':'+n)).hexdigest() for n in frozen}
  need(blobs==frozen and set(git(DEST,'diff-tree','--no-commit-id','--name-status','-r',commit).decode().splitlines())=={'A\t'+n for n in frozen},'Committed diff/blobs not exact frozen9A')
  mutation_guard();after=snapshot();need(after==before,'Protected source/index/lifecycle changed')
  save('isolated_source_version.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ISOLATED_APF_SOURCE_COMMIT_ONLY_NATIVE_NOT_RUN','candidate_id':CID,'experiment_id':EXP,'code_commit':commit,'parent_commit':PARENT,'explicit_parent_argument':PARENT,'worktree':str(DEST),'source_preparation':ref(SOURCE/'preparation.json'),'source_manifest':ref(SOURCE/'source_manifest.json'),'independent_source_review':ref(REVIEW),'native_protocol':ref(SOURCE/'native_protocol.md'),'frozen_source_files':frozen,'committed_blob_sha256':blobs,'source_file_count':9,'diff_exact9A':True,'isolated_worktree_and_index_clean':True,'primary_HEAD_before':before['primary_HEAD'],'primary_HEAD_after':after['primary_HEAD'],'primary_index_sha256_before':before['primary_index_sha256'],'primary_index_sha256_after':after['primary_index_sha256'],'protected_before':before,'protected_after':after,'primary_index_entries_source28_and_all_current_lifecycle_bytes_unchanged':True,'original_null_source_metadata_unchanged':True,'public_primary_or_runtime_promoted':False,'native_resources_remote_queue_launch':'NOT_RUN','implementation_revision_created':False,'compatibility_boundary':BOUNDARY,'commit_output':commit_output,'material_concerns':[]})
  print(json.dumps({'status':'ISOLATED_APF_SOURCE_COMMIT_ONLY_NATIVE_NOT_RUN','code_commit':commit,'parent_commit':PARENT}))
 finally:lock.close()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-root',action='store_true');p.add_argument('--parent',choices=sorted(ALLOWED_PARENTS));args=p.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_GIT_OR_SOURCE_WRITE');return
 need(args.parent is not None,'Explicit --parent is required for root source save');execute(args.parent)
if __name__=='__main__':main()
