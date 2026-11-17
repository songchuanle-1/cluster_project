from pathlib import Path
import hashlib,json,os,subprocess
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def digest(c):return hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def git(*a,env=None,data=None):
 return subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a],input=data,env=env)
def save(p,v):
 guard()
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def atomic(p,v):
 guard();p=Path(p);temp=p.with_name(p.name+'.94c2ad26.tmp');assert not temp.exists()
 with temp.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 guard();os.replace(temp,p)
def protect(b):
 assert git('rev-parse','HEAD').decode().strip()==b['head']
 assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and not git('diff','--cached','--name-only','-z')
 idx=Path(git('rev-parse','--git-path','index').decode().strip());idx=idx if idx.is_absolute() else ROOT/'Cluster'/idx
 assert sha(idx)==b['index_sha256']
 for files in [b['files'],b['WFC_source_paths'],b['LFT_source_paths']]:assert all(sha(ROOT/'Cluster'/n)==h for n,h in files.items())
 assert all(sha(ROOT/'pipeline'/n)==h for n,h in b['protected_ledgers'].items())

