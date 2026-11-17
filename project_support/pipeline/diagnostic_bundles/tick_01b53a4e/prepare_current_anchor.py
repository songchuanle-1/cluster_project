"""Bind this root research turn; preserve current primary/index/lifecycle baselines."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,subprocess
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OLD=ROOT/'pipeline/diagnostic_bundles/tick_0f02aaa2'
EXPECTED={'token':'01b53a4e60c941719a2eb3bea379789b','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-27T18:08:35.561778+00:00','deadline_at':'2026-10-27T19:08:35.561778+00:00','context_sha256':'519b8fe1dc2a55ef48b192861b751e6b62d88fe9306d3347bf8c5bd23ea50f0b','pending_sha256':'b207b43b6337a9c8ecdd0cc92de0d94d66da498139ffe7ba5c3627bfcce1879c'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(c):return hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def main():
    o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
    assert {k:o.get(k) for k in EXPECTED}==EXPECTED and os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
    s='\n'.join('EXPECTED='+repr(EXPECTED) if line.startswith('EXPECTED=') else line for line in (OLD/'anchor.py').read_text('utf8').splitlines())+'\n';ast.parse(s)
    with (HERE/'anchor.py').open('x',encoding='utf8') as f:f.write(s)
    from anchor import guard
    guard();old=json.loads((OLD/'protected_assets_before.json').read_text('utf8'))
    git=lambda *a:subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
    assert git('rev-parse','HEAD').decode().strip()==old['head']=='56b2a96dc48cc8a88f0f7105527ef448113b1060'
    assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==old['status_hex'] and not git('diff','--cached','--name-only','-z')
    assert all(sha(ROOT/'Cluster'/n)==h for n,h in old['files'].items())
    index=Path(git('rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else ROOT/'Cluster'/index
    prior=json.loads((OLD/'post_record_integrity_verification.json').read_text('utf8'));assert sha(index)==prior['primary_index_sha256']
    work=json.loads((ROOT/'pipeline/research_work.json').read_text('utf8'))
    before={'recorded_at':datetime.now(timezone.utc).isoformat(),'head':old['head'],'status_hex':old['status_hex'],'files':old['files'],'index_empty':True,'index_sha256':sha(index),'protected_ledgers':{n:sha(ROOT/'pipeline'/n) for n in old['protected_ledgers']},'candidate_digests':{c['id']:digest(c) for c in work['candidates']}}
    with (HERE/'protected_assets_before.json').open('x',encoding='utf8') as f:json.dump(before,f,ensure_ascii=False,indent=2);f.write('\n')
    guard();print(json.dumps({'actual_owner_verified':True,'source28_status_index_preserved':True,'lifecycle_baseline_count':len(before['protected_ledgers']),'candidate_count':len(before['candidate_digests']),'native_work':False}))
if __name__=='__main__':main()
