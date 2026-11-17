"""Use existing read-only observer under this exact current foreground lease."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,subprocess
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OLD=ROOT/'pipeline/diagnostic_bundles/tick_c7a49040'
EXPECTED={'token':'0f02aaa25b1a4f6e9d27cf8da33b8ca1','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-27T16:10:56.900706+00:00','deadline_at':'2026-10-27T17:10:56.900706+00:00','context_sha256':'d0c0fa7dc748ebc2c9d9cd1ac3f466f35185287b7434b9ebfdee61d497acb494','pending_sha256':'4cc49fd282d273dca352b7cf2d06c5fae7de6400b50684bdd00a1356a844e52e'}
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
    assert git('rev-parse','HEAD').decode().strip()==old['head']
    assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==old['status_hex'] and not git('diff','--cached','--name-only','-z')
    assert all(sha(ROOT/'Cluster'/n)==h for n,h in old['files'].items())
    work=json.loads((ROOT/'pipeline/research_work.json').read_text('utf8'))
    before={'recorded_at':datetime.now(timezone.utc).isoformat(),'head':old['head'],'status_hex':old['status_hex'],'files':old['files'],'index_empty':True,'protected_ledgers':{n:sha(ROOT/'pipeline'/n) for n in old['protected_ledgers']},'candidate_digests':{c['id']:digest(c) for c in work['candidates']}}
    with (HERE/'protected_assets_before.json').open('x',encoding='utf8') as f:json.dump(before,f,ensure_ascii=False,indent=2);f.write('\n')
    for n in ['observe_aef.py','check_cre_current_guard.py','check_hpc_current_guard.py']:
        s=(OLD/n).read_text('utf8');ast.parse(s);guard()
        with (HERE/n).open('x',encoding='utf8') as f:f.write(s)
    print(json.dumps({'actual_owner_verified':True,'source28_status_index_preserved':True,'lifecycle_baseline_count':len(before['protected_ledgers']),'candidate_count':len(before['candidate_digests']),'native_work':False}))
if __name__=='__main__':main()
