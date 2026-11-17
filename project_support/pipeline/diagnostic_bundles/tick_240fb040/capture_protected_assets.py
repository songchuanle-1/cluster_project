"""Read-only baseline of original source/staging and current lifecycle records."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, subprocess
from anchor import ROOT, EXPECTED, guard, sha
HERE=Path(__file__).resolve().parent
GIT='C:/Program Files (x86)/Git/cmd/git.exe'
def git(*args):
    return subprocess.check_output([GIT,'--no-optional-locks','-C',str(ROOT/'Cluster'),*args])
def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def main():
    guard()
    old=json.loads((ROOT/'pipeline/diagnostic_bundles/tick_01b53a4e/protected_assets_before.json').read_text('utf8'))
    head=git('rev-parse','HEAD').decode().strip()
    assert head=='d58576b396cfb54577652be972f3ffaffda508c9'
    status=git('status','--porcelain=v1','--untracked-files=all','-z').hex()
    assert status==old['status_hex']
    files={n:sha(ROOT/'Cluster'/n) for n in old['files']}
    assert files==old['files'] and len(files)==28
    assert not git('diff','--cached','--name-only','-z')
    index=Path(git('rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute(): index=ROOT/'Cluster'/index
    names=list(old['protected_ledgers'])+['experiments/M217-CRE.json','admissions/M217-CRE.json']
    ledgers={n:sha(ROOT/'pipeline'/n) for n in dict.fromkeys(names)}
    work=json.loads((ROOT/'pipeline/research_work.json').read_text('utf8'))
    candidates={c['id']:digest(c) for c in work['candidates']}
    assert len(candidates)==145
    record={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'head':head,
            'status_hex':status,'files':files,'index_empty':True,'index_sha256':sha(index),
            'protected_ledgers':ledgers,'candidate_digests':candidates}
    guard()
    with (HERE/'protected_assets_before.json').open('x',encoding='utf8') as f:
        json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'head':head,'original_user_files':len(files),'ledgers':len(ledgers),
                      'candidates':len(candidates),'index_empty':True,'sha256':sha(HERE/'protected_assets_before.json')}))
if __name__=='__main__': main()
