"""Current tick record helpers; importing has no filesystem mutation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, subprocess
from anchor import ROOT, EXPECTED, guard, sha
HERE=Path(__file__).resolve().parent
CRE='hierarchy-cross-root-directed-edge-broadcast'
HPC='hierarchy-tree-resolvent-nonlinear-composition'
APF='hierarchy-ancestry-path-factor-composition'
SOURCE='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
def read(path): return json.loads(Path(path).read_text('utf8'))
def ref(path): return {'path':Path(path).resolve().relative_to(ROOT).as_posix(),'sha256':sha(path)}
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def git(repo,*args):
    return subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(repo),*args])
def save(path,value):
    guard()
    with Path(path).open('x',encoding='utf8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def atomic(path,value,text=False):
    guard();path=Path(path);tmp=path.with_name(path.name+'.d45d66f9.tmp');assert not tmp.exists()
    with tmp.open('x',encoding='utf8') as f:
        f.write(value if text else json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        f.flush();os.fsync(f.fileno())
    guard();os.replace(tmp,path)
def primary_protection(baseline):
    guard();repo=ROOT/'Cluster'
    assert git(repo,'rev-parse','HEAD').decode().strip()==SOURCE==baseline['head']
    assert git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==baseline['status_hex']
    assert not git(repo,'diff','--cached','--name-only','-z')
    assert all(sha(repo/n)==h for n,h in baseline['files'].items())
    index=Path(git(repo,'rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute(): index=repo/index
    assert sha(index)==baseline['index_sha256']
    return sha(index)
def lifecycle_protection(baseline):
    assert all(sha(ROOT/'pipeline'/n)==h for n,h in baseline['protected_ledgers'].items())
def check_refs(entries):
    for entry in entries:
        path=(ROOT/entry['path']).resolve();assert path.is_relative_to(ROOT)
        assert sha(path)==entry['sha256'],entry['path']
