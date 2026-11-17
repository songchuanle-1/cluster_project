"""Root-only local HPC exact-nine source version save. Default performs no Git or source write."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,re,subprocess,sys
ROOT=Path('D:/project/cluster_project');REPO=ROOT/'Cluster';HERE=Path(__file__).resolve().parent;TICK=HERE.parent
GIT=Path('C:/Program Files (x86)/Git/cmd/git.exe')
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_d08825b5/new_candidate_prepare';REVIEW=ROOT/'pipeline/diagnostic_bundles/tick_d08825b5/hpc_source_topology_independent_review_final.json'
sys.path.insert(0,str(TICK))
from anchor import guard as current_guard
DEST=ROOT/'pipeline/isolated_versions/hpc_f395f943'
CID='hierarchy-tree-resolvent-nonlinear-composition';EXP='M218-HPC'
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hpc'
CONFIG='configs/Quard/ctf_hcg_csort_hpc/'+MODEL+'.yaml'
BASE='56b2a96dc48cc8a88f0f7105527ef448113b1060'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
AUTH={'path':'pipeline/authorizations/experiment_first_20261021.json','sha256':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'}
OWNER={'token': 'f395f943dd534ede890abe929de52269', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-27T08:08:18.932684+00:00', 'deadline_at': '2026-10-27T09:08:18.932684+00:00', 'context_sha256': '13046012336ae1c64debaa28a1b507761bc8ba5f8f67b701ecc59aad41e0a7ef', 'pending_sha256': '1046fe04bb55e83737adf11e74f87acb8a46cab16c227c47984c94fa14b86363'}
BASELINE=TICK/'protected_assets_before.json';BASELINE_SHA='91ee2fdaf62aeac07ff83fbc7687d227c5724ebf98fc69f5088b346b64aeac18'
BOUNDARY='First isolated version of the unchanged c94f HPC nine-source prototype on actual tested AEF56 parent. Original source/code/actual-parent null declarations remain immutable. Existing CREd585 is another child of56 and remains untouched; no sibling ff, source deployment, native result, model revision or admission is implied. If primary advances before native preparation, select an explicitly compatible exact version and actually test it.'

def need(value,message):
 if not value:raise RuntimeError(message)
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p).resolve();need(p.is_relative_to(ROOT.resolve()),'Reference outside project');return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def save(name,value):
 owner_guard();data=encoded(value)
 with (HERE/name).open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
def owner_guard():
 current_guard()
 need(os.environ.get('GIT_OPTIONAL_LOCKS')=='0' and sys.dont_write_bytecode,'Require GIT_OPTIONAL_LOCKS=0 and python -B')
 owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json');mode=read(ROOT/'pipeline/execution_mode.json')
 need({k:owner.get(k) for k in OWNER}==OWNER,'Original six owner fields changed')
 need(mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==OWNER['thread_id'],'Actual foreground root required; do not override identity')
 now=datetime.now(timezone.utc);need(datetime.fromisoformat(OWNER['generated_at'])<=now<datetime.fromisoformat(OWNER['deadline_at']),'Original owner window expired or future')
 need(sha(ROOT/'pipeline/headless/.tick_context.json')==OWNER['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==OWNER['pending_sha256'],'Current context/pending changed')
 need(sha(ROOT/'pipeline/goal.json')==GOAL,'Goal changed');policy=read(ROOT/'pipeline/closure_policy.json')
 need(policy['enabled'] is True and policy['experiment_first']['enabled'] is True and policy['experiment_first']['authorization']==AUTH and sha(ROOT/AUTH['path'])==AUTH['sha256'],'Standing source-save authorization changed')
 need(GIT.is_file(),'Specified reviewed Git executable missing')
def git(repo,*args):
 repo=Path(repo).resolve();need(repo in (REPO.resolve(),DEST.resolve()),'Git repository escaped exact scope')
 need(args and args[0] in {'rev-parse','status','diff','ls-tree','show','rev-list','check-attr','config','worktree','add','commit','diff-tree'},'Unsupported Git command')
 if args[0]=='worktree':need(repo==REPO.resolve() and args==('worktree','add','--detach',str(DEST),BASE),'Only exact detached destination addition allowed')
 if args[0] in ('add','commit'):need(repo==DEST.resolve(),'No primary index or commit mutation')
 env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_LFS_SKIP_SMUDGE='1',GIT_ALLOW_PROTOCOL='file')
 command=[str(GIT),'--no-optional-locks','-c','core.autocrlf=false','-c','core.eol=lf','-c','core.fsmonitor=false','-c','submodule.recurse=false','-c','core.hooksPath='+str(HERE/'empty_hooks'),'-C',str(repo),*args]
 result=subprocess.run(command,capture_output=True,timeout=120,env=env);need(result.returncode==0,result.stderr.decode('utf8',errors='replace'))
 return result.stdout

def source_details(preparation_sha,review_sha):
 need(sha(SOURCE/'preparation.json')==preparation_sha and sha(REVIEW)==review_sha,'Frozen source or independent review hash changed')
 prep=read(SOURCE/'preparation.json');review=read(REVIEW)
 need(prep['candidate_id']==CID and prep['experiment_id']==EXP and prep.get('code_commit') is None and prep.get('source_commit') is None,'Only exact existing unversioned HPC frozen payload permitted')
 need(review['status']=='STATIC_HPC_SOURCE_TOPOLOGY_AND_INTEGRATION_REVIEWED_NOT_NATIVE_PASS' and review['candidate_id']==CID and review['experiment_id']==EXP and review['code_commit'] is None and review['material_concerns']==[] and review['anchors']['preparation']==ref(SOURCE/'preparation.json'),'Actual independent source review binding failed')
 need({'source_manifest.json','native_protocol.md'}<=set(prep['prepared_file_hashes']),'Frozen manifest/protocol must be in source map')
 for name,digest in prep['prepared_file_hashes'].items():
  path=(SOURCE/name).resolve();need(path.is_relative_to(SOURCE.resolve()) and sha(path)==digest,'Frozen preparation file differs: '+name)
 names={'__init__.py','backbone.py','dec.py','hier_postprocess.py','loss.py','hierarchy_resolvent.py','network.py','sample_model.py'}
 exact={'framework/model/Quard_model/'+MODEL+'/'+n for n in names}|{CONFIG}
 frozen={n.removeprefix('staged_repository/'):h for n,h in prep['prepared_file_hashes'].items() if n.startswith('staged_repository/')}
 need(set(frozen)==exact and len(frozen)==9,'Only isolated HPC8model+originalYAML9 allowed')
 need(frozen==read(SOURCE/'source_manifest.json')['source_files']==review['source_files_exact9'],'Frozen manifest/independent exact9 map differs')
 need(frozen[CONFIG]=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a','Original nativeYAML changed')
 need(all(re.fullmatch('[0-9a-f]{64}',h) for h in frozen.values()),'Invalid source hash')
 return frozen

def snapshots():
 need(sha(BASELINE)==BASELINE_SHA,'Fresh protection baseline changed');baseline=read(BASELINE)
 need(baseline['head']==BASE and baseline['index_empty'] is True and len(baseline['files'])==28 and len(baseline['protected_ledgers'])==16,'Wrong current protection inventory')
 need(git(REPO,'rev-parse','HEAD').decode().strip()==BASE,'Actual main no longer AEF56; preserve attempt and repackage only on explicitly selected compatible parent')
 status=git(REPO,'status','--porcelain=v1','-z','--untracked-files=all');need(status.hex()==baseline['status_hex'],'Protected28 status changed')
 files={n:sha(REPO/n) for n in baseline['files']};need(files==baseline['files'] and not git(REPO,'diff','--cached','--name-only','-z'),'Protected28 bytes/index changed')
 index=Path(git(REPO,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else REPO/index
 ledgers={n:sha(ROOT/'pipeline'/n) for n in baseline['protected_ledgers']};need(ledgers==baseline['protected_ledgers'],'Sixteen lifecycle ledgers changed')
 extra={n:sha(ROOT/n) for n in ['pipeline/research_work.json','pipeline/codex_memory.md','pipeline/closure_policy.json','pipeline/execution_mode.json','SERVERS.yaml']}
 old_packets={}
 for rel,prep_sha in [('pipeline/diagnostic_bundles/tick_65785aaf/new_candidate_prepare','c760d9fd353d2b3e208837b9489ba511918e73821c278d97b5067c14701a41fe'),('pipeline/diagnostic_bundles/tick_d08825b5/cre_compatible_tooling','dd7f12b3b3aa884caf90b4c5b1b8c02fce3791621677d9e0eb1541d227ac601b')]:
  packet=ROOT/rel;need(sha(packet/'preparation.json')==prep_sha,'Old frozen preparation changed');old_packets[rel+'/preparation.json']=prep_sha
  for n,h in read(packet/'preparation.json')['prepared_file_hashes'].items():
   file=(packet/n).resolve();need(file.is_relative_to(packet.resolve()) and sha(file)==h,'Old frozen packet member changed');old_packets[rel+'/'+n]=h
 cre_source=read(ROOT/'pipeline/diagnostic_bundles/tick_65785aaf/new_candidate_prepare/source_manifest.json')['source_files']
 for n,h in cre_source.items():
  rel='pipeline/isolated_versions/cre_d08825b5/'+n;need(sha(ROOT/rel)==h,'Existing compatible CRE worktree bytes changed');old_packets[rel]=h
 cre=[c for c in read(ROOT/'pipeline/research_work.json')['candidates'] if c['id']=='hierarchy-cross-root-directed-edge-broadcast'];need(len(cre)==1 and cre[0].get('code_commit')=='d58576b396cfb54577652be972f3ffaffda508c9','Protected compatible CRE registration changed')
 queue=read(ROOT/'pipeline/queue.json');aef=[x for ts in queue['gpu_queues'].values() for x in ts if x.get('id')=='M216-AEF']
 need(len(aef)==1 and all(aef[0].get(k)==v for k,v in {'status':'running','pid':759301,'gpu':'0','code_commit':BASE,'launch_verified':True}.items()),'Exact original AEF launch must remain untouched')
 w=read(ROOT/'pipeline/research_work.json');matches=[c for c in w['candidates'] if c['id']==CID];need(len(matches)==1 and matches[0].get('experiment_id')==EXP and matches[0].get('code_commit') is None and matches[0].get('source_commit') is None and matches[0].get('stage')=='implementation' and not matches[0].get('revision_history'),'Current HPC null implementation registration changed; no historical CRE commit eligibility gate or shared update is allowed')
 return {'primary_HEAD':BASE,'status_hex':status.hex(),'primary_index_sha256':sha(index),'protected28':files,'lifecycle16':ledgers,'extra_shared_files':extra,'protected_frozen_CRE_source_and_tool_files':old_packets,'HPC_registration_before':{'code_commit':matches[0]['code_commit'],'source_commit':matches[0]['source_commit'],'stage':matches[0]['stage']},'candidate_count':len(w['candidates'])}

def execute(preparation_sha,review_sha):
 owner_guard();frozen=source_details(preparation_sha,review_sha)
 need(DEST.resolve().is_relative_to((ROOT/'pipeline/isolated_versions').resolve()) and not DEST.exists(),'Exact destination exists or escaped scope; no replay/cleanup')
 for name in ['isolated_version_before.json','isolated_version_operation_intent.json','isolated_source_version.json','empty_hooks']:
  need(not (HERE/name).exists(),'Existing/partial HPC source save requires read-only reconciliation: '+name)
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));need(lock is not None,'Canonical project lock busy; remain pending')
 try:
  owner_guard();before=snapshots()
  # All commands suppress original hooks and optional index refresh; reject unknown filters.
  cfg=subprocess.run([str(GIT),'--no-optional-locks','-c','core.fsmonitor=false','-C',str(REPO),'config','--get-regexp',r'^(core\.hooksPath|filter\..*)$'],capture_output=True,timeout=20,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'))
  need(cfg.returncode in (0,1),'Cannot inspect filter configuration');allowed={'filter.lfs.clean':'git-lfs clean -- %f','filter.lfs.smudge':'git-lfs smudge -- %f','filter.lfs.process':'git-lfs filter-process','filter.lfs.required':'true'}
  need(all(len(row.split(' ',1))==2 and allowed.get(row.split(' ',1)[0])==row.split(' ',1)[1] for row in cfg.stdout.decode().splitlines()),'Unexpected hooks/filters require review')
  need(not(set(frozen)&set(before['protected28'])),'Source overlaps protected user files')
  for name in frozen:need(not git(REPO,'ls-tree',BASE,'--',name) and not (REPO/name).exists(),'HPC target already tracked/present')
  tracked=git(REPO,'ls-tree','-r','--name-only',BASE).decode().splitlines();need(not any(Path(n).name==Path(CONFIG).name for n in tracked),'Native YAML basename already exists')
  def mutation_guard():
   owner_guard();need(snapshots()==before and source_details(preparation_sha,review_sha)==frozen,'Public/source/lifecycle changed during isolated save; never retry/rollback')
  mutation_guard();save('isolated_version_before.json',{'owner':OWNER,'recorded_at':datetime.now(timezone.utc).isoformat(),'protected':before,'fresh_baseline':ref(BASELINE)})
  save('isolated_version_operation_intent.json',{'owner':OWNER,'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'experiment_id':EXP,'operation':'One detached worktree/exact9A ordinary local commit only','worktree':str(DEST),'required_parent':BASE,'source_preparation':ref(SOURCE/'preparation.json'),'independent_source_review':ref(REVIEW),'frozen_source_files':frozen,'compatibility_boundary':BOUNDARY,'partial_policy':'Never reset/clean/stash/delete/replay; preserve exact attempt for read-only reconciliation.'})
  mutation_guard();(HERE/'empty_hooks').mkdir(exist_ok=False);DEST.parent.mkdir(exist_ok=True)
  mutation_guard();git(REPO,'worktree','add','--detach',str(DEST),BASE)
  need(git(DEST,'rev-parse','HEAD').decode().strip()==BASE and not git(DEST,'status','--porcelain=v1','-z','--untracked-files=all'),'New detached worktree not clean exactAEF56')
  for name,digest in frozen.items():
   mutation_guard();path=(DEST/name).resolve();need(path.is_relative_to(DEST.resolve()) and not path.exists(),'Unsafe isolated file destination');path.parent.mkdir(parents=True,exist_ok=True)
   with path.open('xb') as stream:stream.write((SOURCE/'staged_repository'/name).read_bytes());stream.flush();os.fsync(stream.fileno())
   need(sha(path)==digest,'Copied source bytes differ')
  need(not git(DEST,'check-attr','-a','--',*sorted(frozen)).strip(),'Target Git attributes need review')
  mutation_guard();git(DEST,'add','--',*sorted(frozen))
  need(set(git(DEST,'diff','--cached','--name-status').decode().splitlines())=={'A\t'+n for n in frozen},'Staged changes are not exact9A')
  need({n:hashlib.sha256(git(DEST,'show',':'+n)).hexdigest() for n in frozen}==frozen,'Staged object bytes differ from frozen9')
  mutation_guard();commit_output=git(DEST,'commit','-m','Add HPC tree resolvent composition (native pending)').decode('utf8',errors='replace')
  commit=git(DEST,'rev-parse','HEAD').decode().strip();need(re.fullmatch('[0-9a-f]{40}',commit),'Invalid new commit')
  need(git(DEST,'rev-list','--parents','-n','1',commit).decode().split()==[commit,BASE],'Commit is not one exact child of AEF56')
  need(not git(DEST,'status','--porcelain=v1','-z','--untracked-files=all') and not git(DEST,'diff','--cached','--name-only','-z'),'Isolated HEAD/index/worktree must be clean')
  blobs={n:hashlib.sha256(git(DEST,'show',commit+':'+n)).hexdigest() for n in frozen}
  need(blobs==frozen and set(git(DEST,'diff-tree','--no-commit-id','--name-status','-r',commit).decode().splitlines())=={'A\t'+n for n in frozen},'Committed diff/blobs not exact frozen9A')
  mutation_guard();after=snapshots();need(after==before,'Protected source/lifecycle did not remain exact')
  result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ISOLATED_HPC_SOURCE_COMMIT_ONLY_NATIVE_NOT_RUN','candidate_id':CID,'experiment_id':EXP,'code_commit':commit,'parent_commit':BASE,'worktree':str(DEST),'source_preparation':ref(SOURCE/'preparation.json'),'independent_source_review':ref(REVIEW),'native_protocol':ref(SOURCE/'native_protocol.md'),'frozen_source_files':frozen,'committed_blob_sha256':blobs,'source_file_count':9,'diff_exact9A':True,'isolated_worktree_and_index_clean':True,'primary_HEAD_before':before['primary_HEAD'],'primary_HEAD_after':after['primary_HEAD'],'primary_HEAD_index_status_28_protected_bytes_unchanged':True,'protected_ledgers_before':before,'protected_ledgers_after':after,'public_primary_or_runtime_promoted':False,'native_resources_remote_queue_launch':'NOT_RUN','frozen_original_code_metadata_unchanged':True,'current_AEF_job_unchanged':True,'compatibility_repackaging_only':True,'implementation_revision_created':False,'compatibility_boundary':BOUNDARY,'commit_output':commit_output,'material_concerns':[]}
  save('isolated_source_version.json',result);print(json.dumps({'status':result['status'],'code_commit':commit,'parent_commit':BASE,'native_resources':'NOT_RUN'}))
 finally:lock.close()

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-root',action='store_true');parser.add_argument('--source-preparation-sha256');parser.add_argument('--independent-review-sha256');args=parser.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_GIT_OR_SOURCE_WRITE');return
 need(all(isinstance(x,str) and re.fullmatch('[0-9a-f]{64}',x) for x in (args.source_preparation_sha256,args.independent_review_sha256)),'Actual frozen source+independent review SHA arguments required')
 execute(args.source_preparation_sha256,args.independent_review_sha256)
if __name__=='__main__':main()
