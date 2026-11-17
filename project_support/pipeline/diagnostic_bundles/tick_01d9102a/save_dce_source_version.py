"""Exact-nine isolated DCE source save. Explicit root operation only; no deployment."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,subprocess,sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent;OUT=HERE/'dce_version_prepare';PREP=HERE/'new_candidate_prepare'
REPO=ROOT/'Cluster';DEST=ROOT/'pipeline/isolated_versions/dce_01d9102a';BASE=u.SOURCE
CID='hierarchy-directed-cavity-edge-composition';EXP='M220-DCE'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_dce';CONFIG='configs/Quard/ctf_hcg_csort_dce/'+NAME+'.yaml'
GIT='C:/Program Files (x86)/Git/cmd/git.exe'

def save(p,v):
 guard()
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def git(repo,*args):
 assert Path(repo).resolve() in (REPO.resolve(),DEST.resolve())
 guard();r=subprocess.run([GIT,'--no-optional-locks','-c','core.autocrlf=false','-c','core.eol=lf','-c','core.fsmonitor=false','-c','submodule.recurse=false','-c','core.hooksPath='+str(OUT/'empty_hooks'),'-C',str(repo),*args],capture_output=True,timeout=120,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_LFS_SKIP_SMUDGE='1',GIT_ALLOW_PROTOCOL='file'))
 assert r.returncode==0,r.stderr.decode('utf8',errors='replace');return r.stdout

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--preparation-sha256');ap.add_argument('--review-sha256');args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_GIT');return
 guard();assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
 assert sha(PREP/'preparation.json')==args.preparation_sha256
 prep=u.read(PREP/'preparation.json');peer=HERE/'dce_source_independent_review.json';assert sha(peer)==args.review_sha256
 review=u.read(peer);assert review['candidate_id']==CID and review['experiment_id']==EXP and review['material_concerns']==[]
 assert prep['candidate_id']==CID and prep['experiment_id']==EXP and prep['config']==CONFIG and all(prep[k] is None for k in ('code_commit','source_commit','source_parent_commit'))
 names={'__init__.py','backbone.py','dec.py','hier_postprocess.py','loss.py','network.py','sample_model.py','directed_cavity.py'}
 paths={'framework/model/Quard_model/'+NAME+'/'+n for n in names}|{CONFIG}
 frozen=prep['source_files'];assert set(frozen)==paths and len(frozen)==9 and review['source_files_exact9']==frozen
 assert frozen[CONFIG]=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
 for n,h in prep['prepared_file_hashes'].items():
  p=(PREP/n).resolve();assert p.is_relative_to(PREP.resolve()) and sha(p)==h,n
 for n,h in frozen.items():assert sha(PREP/'staged_repository'/n)==h
 assert not OUT.exists() and not DEST.exists(),'Existing/partial attempt requires read-only reconciliation; no replay/cleanup'
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b)
  def snapshot():
   u.primary_protection(b)
   return {'ledgers':{n:sha(ROOT/'pipeline'/n) for n in b['protected_ledgers']},'work_sha256':sha(ROOT/'pipeline/research_work.json'),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
  before=snapshot()
  def unchanged():
   guard();assert snapshot()==before and sha(PREP/'preparation.json')==args.preparation_sha256 and sha(peer)==args.review_sha256
   assert all(sha(PREP/'staged_repository'/n)==h for n,h in frozen.items())
  # No unknown checkout filters/hooks or target path attributes can run.
  c=subprocess.run([GIT,'--no-optional-locks','-C',str(REPO),'config','--get-regexp',r'^(core\.hooksPath|filter\..*)$'],capture_output=True,timeout=20,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
  allowed={'filter.lfs.clean':'git-lfs clean -- %f','filter.lfs.smudge':'git-lfs smudge -- %f','filter.lfs.process':'git-lfs filter-process','filter.lfs.required':'true'}
  assert c.returncode in (0,1) and all(len(x.split(' ',1))==2 and allowed.get(x.split(' ',1)[0])==x.split(' ',1)[1] for x in c.stdout.decode().splitlines())
  for n in paths:assert n not in b['files'] and not (REPO/n).exists() and not u.git(REPO,'ls-tree',BASE,'--',n)
  assert git(REPO,'rev-parse','HEAD').decode().strip()==BASE
  unchanged();OUT.mkdir();(OUT/'empty_hooks').mkdir()
  save(OUT/'isolated_version_operation_intent.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,'experiment_id':EXP,'explicit_parent':BASE,'source_preparation':u.ref(PREP/'preparation.json'),'independent_source_review':u.ref(peer),'source_files_exact9':frozen,'protected_before':before,'scope':'One isolated detached child and ordinary exact9A source commit only. No primary ff, runtime sync, native result, model revision, queue or launch. Partial replay/force/reset/stash/clean forbidden.'})
  unchanged();git(REPO,'worktree','add','--detach',str(DEST),BASE)
  assert git(DEST,'rev-parse','HEAD').decode().strip()==BASE and not git(DEST,'status','--porcelain=v1','-z','--untracked-files=all')
  for n,h in frozen.items():
   unchanged();p=(DEST/n).resolve();assert p.is_relative_to(DEST.resolve()) and not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('xb') as f:f.write((PREP/'staged_repository'/n).read_bytes());f.flush();os.fsync(f.fileno())
   assert sha(p)==h
  ordered=tuple(sorted(paths));assert not git(DEST,'check-attr','-a','--',*ordered).strip()
  unchanged();git(DEST,'add','--',*ordered)
  assert set(git(DEST,'diff','--cached','--name-status').decode().splitlines())=={'A\t'+n for n in paths}
  assert {n:hashlib.sha256(git(DEST,'show',':'+n)).hexdigest() for n in paths}==frozen
  unchanged();output=git(DEST,'commit','-m','Add independent directed cavity edge composition prototype (native pending)').decode('utf8',errors='replace')
  code=git(DEST,'rev-parse','HEAD').decode().strip();assert git(DEST,'rev-list','--parents','-n','1',code).decode().split()==[code,BASE]
  assert not git(DEST,'status','--porcelain=v1','-z','--untracked-files=all')
  assert set(git(DEST,'diff-tree','--no-commit-id','--name-status','-r',code).decode().splitlines())=={'A\t'+n for n in paths}
  blobs={n:hashlib.sha256(git(DEST,'show',code+':'+n)).hexdigest() for n in paths};assert blobs==frozen
  unchanged();save(OUT/'isolated_source_version.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ISOLATED_DCE_SOURCE_COMMIT_ONLY_NATIVE_NOT_RUN','candidate_id':CID,'experiment_id':EXP,'code_commit':code,'parent_commit':BASE,'worktree':str(DEST),'source_preparation':u.ref(PREP/'preparation.json'),'source_manifest':u.ref(PREP/'source_manifest.json'),'native_protocol':u.ref(PREP/'native_protocol.md'),'independent_source_review':u.ref(peer),'frozen_source_files':frozen,'committed_blob_sha256':blobs,'source_file_count':9,'diff_exact9A':True,'isolated_worktree_and_index_clean':True,'primary_HEAD_before':BASE,'primary_HEAD_after':BASE,'primary_index_source28_and_all_current_lifecycle_bytes_unchanged':True,'protected_before':before,'protected_after':snapshot(),'original_null_source_metadata_unchanged':True,'public_primary_or_runtime_promoted':False,'native_resources_remote_queue_launch':'NOT_RUN','implementation_revision_created':False,'commit_output':output})
  print(json.dumps({'code_commit':code,'parent_commit':BASE,'source_version':u.ref(OUT/'isolated_source_version.json')}))
 finally:lock.close()
if __name__=='__main__':main()
