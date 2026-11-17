"""Final exact index and independent source9 integrity; no tests or model execution."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
GIT='C:/Program Files (x86)/Git/cmd/git.exe'
def git(path,*args):return subprocess.check_output([GIT,'--no-optional-locks','-C',str(path),*args])
guard()
old=json.loads((HERE/'aef_lifecycle_prepare/aef_lifecycle_result.json').read_text('utf8'))
repo=ROOT/'Cluster';index=Path(git(repo,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else repo/index
assert sha(index)==old['after']['index_sha256']==old['before']['index_sha256']
sources={}
for short,worktree,commit in [('cre','cre_d08825b5','d58576b396cfb54577652be972f3ffaffda508c9'),('hpc','hpc_f395f943','2f7eff19ca59cc4586e13ca81a547a18ea7e313d')]:
    wt=ROOT/'pipeline/isolated_versions'/worktree;m=json.loads((HERE/(short+'_execution/native_manifest.json')).read_text('utf8'))
    assert git(wt,'rev-parse','HEAD').decode().strip()==commit and not git(wt,'status','--porcelain=v1','--untracked-files=all','-z')
    files={'framework/model/Quard_model/'+m['candidate_name']+'/'+n:h for n,h in m['candidate_source_hashes'].items()}
    files[m['config']]=m['candidate_config_sha256'];assert len(files)==9
    for n,h in files.items():assert sha(wt/n)==h,n
    sources[short]={'code_commit':commit,'isolated_worktree':str(wt),'clean':True,'exact_original_source9_sha256':files,'candidate_graph_tested':False}
guard()
out={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'primary_index_sha256':sha(index),'same_as_before_and_after_AEF_lifecycle':True,'independent_source_versions':sources,'new_source_commit_or_native_test':False}
with (HERE/'post_record_integrity_verification.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'index_exact':True,'CRE_HPC_source9_exact_clean':True,'sha256':sha(HERE/'post_record_integrity_verification.json')}))
