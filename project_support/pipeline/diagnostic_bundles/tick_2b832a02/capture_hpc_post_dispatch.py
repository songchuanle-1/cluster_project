"""Fresh post-dispatch source/index/lifecycle baseline, no mutation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf8'))
def git(*args):return subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*args])
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def main():
    guard();b=read(HERE/'protected_assets_before.json');ff=read(HERE/'hpc_root_ff_result.json')
    head=git('rev-parse','HEAD').decode().strip();assert head==ff['HEAD']=='6282263d805c1741234f97afc981a05aca2ad6e3'
    assert git('rev-list','--parents','-n','1',head).decode().split()==[head,'d58576b396cfb54577652be972f3ffaffda508c9']
    assert set(git('diff-tree','--no-commit-id','--name-status','-r',head).decode().splitlines())=={'A\t'+n for n in ff['source_paths']}
    assert all(sha(ROOT/'Cluster'/n)==h for n,h in ff['source_paths'].items())
    assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex']
    assert all(sha(ROOT/'Cluster'/n)==h for n,h in b['files'].items()) and not git('diff','--cached','--name-only','-z')
    index=Path(git('rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else ROOT/'Cluster'/index
    names=list(b['protected_ledgers'])+['experiments/M218-HPC.json','admissions/M218-HPC.json']
    ledgers={n:sha(ROOT/'pipeline'/n) for n in dict.fromkeys(names)};assert len(ledgers)==20
    work=read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==145
    exp=read(ROOT/'pipeline/experiments/M218-HPC.json')
    assert exp['status']=='running' and exp['pid']==187081 and exp['code_commit']==head and exp['launch_verified'] is True
    out={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'head':head,'status_hex':b['status_hex'],
         'files':b['files'],'index_empty':True,'index_sha256':sha(index),'protected_ledgers':ledgers,
         'candidate_digests':{c['id']:digest(c) for c in work['candidates']},
         'exact_tested_nine_source_paths':ff['source_paths'],'legitimate_fast_forward_from':b['head'],
         'new_ADMITTED_HPC_original_pid':187081,'scope':'Post-dispatch 20 lifecycle files/source28/index are protected for final record-only edits; original begin index legitimately changed by exact9A ff.'}
    guard();p=HERE/'hpc_post_dispatch_protected_assets.json'
    with p.open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'sha256':sha(p),'head':head,'ledgers':len(ledgers),'hpc_small':{k:next(c for c in work['candidates'] if c['id']=='hierarchy-tree-resolvent-nonlinear-composition').get(k) for k in ['stage','training_status','native_status','resource_status','current_native_check']}}))
if __name__=='__main__':main()
