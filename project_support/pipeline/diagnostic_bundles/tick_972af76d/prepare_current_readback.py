"""Bind existing read-only tools to the actual new root lease, without GPU work."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os, subprocess

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_f395f943'
EXPECTED = {'token':'972af76d45f74f6bb62167ad9a902616','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-27T10:06:40.840335+00:00','deadline_at':'2026-10-27T11:06:40.840335+00:00','context_sha256':'47d24d12fd0b3af03b9a8f5197fdfda086bcc493631cb3f4ddb4a2adff9021fe','pending_sha256':'b9d9b2ed434f5327475a52c2a9abf76c4d926d0e8fe022f92cf6b469a90b1a3b'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(c): return hashlib.sha256(json.dumps(c, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
def save(p, value):
    with p.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

def main():
    owner = json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
    assert {k:owner.get(k) for k in EXPECTED} == EXPECTED
    assert os.environ.get('CODEX_THREAD_ID') == EXPECTED['thread_id']
    assert datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED['deadline_at'])
    source = (OLD/'anchor.py').read_text('utf8')
    source = '\n'.join('EXPECTED='+repr(EXPECTED) if line.startswith('EXPECTED=') else line for line in source.splitlines())+'\n'
    ast.parse(source)
    with (HERE/'anchor.py').open('x', encoding='utf8') as f: f.write(source)
    from anchor import guard
    guard()
    git = lambda *args: subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*args])
    old = json.loads((OLD/'protected_assets_before.json').read_text('utf8'))
    assert git('rev-parse','HEAD').decode().strip() == old['head']
    assert git('status','--porcelain=v1','--untracked-files=all','-z').hex() == old['status_hex']
    assert not git('diff','--cached','--name-only','-z')
    assert all(sha(ROOT/'Cluster'/n)==h for n,h in old['files'].items())
    work = json.loads((ROOT/'pipeline/research_work.json').read_text('utf8'))
    before = {'recorded_at':datetime.now(timezone.utc).isoformat(), 'head':old['head'], 'status_hex':old['status_hex'], 'files':old['files'], 'index_empty':True, 'protected_ledgers':{n:sha(ROOT/'pipeline'/n) for n in old['protected_ledgers']}, 'candidate_digests':{c['id']:digest(c) for c in work['candidates']}}
    save(HERE/'protected_assets_before.json', before)
    source=(OLD/'observe_aef_final.py').read_text('utf8').replace('aef_training_progress_observation_final.json','aef_training_progress_observation.json')
    ast.parse(source)
    with (HERE/'observe_aef.py').open('x', encoding='utf8') as f: f.write(source)
    guard()
    print(json.dumps({'owner_verified':True,'source28_index_status_preserved':True,'protected_ledgers':len(before['protected_ledgers']),'candidate_count':len(before['candidate_digests']),'native_work':False}))

if __name__=='__main__': main()
