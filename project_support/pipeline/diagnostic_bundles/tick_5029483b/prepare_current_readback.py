"""Reuse immutable read-only observation and busy-guard tools under a fresh lease."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,subprocess
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
OLD=ROOT/'pipeline/diagnostic_bundles/tick_972af76d'
EXPECTED={'token':'5029483b036443b895dd0b4f8853127d','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-27T12:06:28.502058+00:00','deadline_at':'2026-10-27T13:06:28.502058+00:00','context_sha256':'d34ed6958c46b4b043b1c38933ca92382107130a81fa8a04b0c0b3e77bd92388','pending_sha256':'74c02e7410e9cb85c151417d7c5f8309f65c83005ea8927ab6933c5eadab62d5'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(c):return hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def main():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
    assert {k:owner.get(k) for k in EXPECTED}==EXPECTED
    assert os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
    source=(OLD/'anchor.py').read_text('utf8')
    source='\n'.join('EXPECTED='+repr(EXPECTED) if line.startswith('EXPECTED=') else line for line in source.splitlines())+'\n'
    ast.parse(source)
    with (HERE/'anchor.py').open('x',encoding='utf8') as f:f.write(source)
    from anchor import guard
    guard()
    git=lambda *args:subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*args])
    old=json.loads((OLD/'protected_assets_before.json').read_text('utf8'))
    assert git('rev-parse','HEAD').decode().strip()==old['head']
    assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==old['status_hex']
    assert not git('diff','--cached','--name-only','-z')
    assert all(sha(ROOT/'Cluster'/n)==h for n,h in old['files'].items())
    work=json.loads((ROOT/'pipeline/research_work.json').read_text('utf8'))
    before={'recorded_at':datetime.now(timezone.utc).isoformat(),'head':old['head'],'status_hex':old['status_hex'],'files':old['files'],'index_empty':True,'protected_ledgers':{n:sha(ROOT/'pipeline'/n) for n in old['protected_ledgers']},'candidate_digests':{c['id']:digest(c) for c in work['candidates']}}
    with (HERE/'protected_assets_before.json').open('x',encoding='utf8') as f:json.dump(before,f,ensure_ascii=False,indent=2);f.write('\n')
    for name in ['observe_aef.py','check_cre_current_guard.py','check_hpc_current_guard.py']:
        source=(OLD/name).read_text('utf8');ast.parse(source);guard()
        with (HERE/name).open('x',encoding='utf8') as f:f.write(source)
    print(json.dumps({'actual_owner_verified':True,'protected_source28_index_status':True,'lifecycle_baseline_count':len(before['protected_ledgers']),'candidate_count':len(before['candidate_digests']),'model_or_native_change':False}))
if __name__=='__main__':main()
