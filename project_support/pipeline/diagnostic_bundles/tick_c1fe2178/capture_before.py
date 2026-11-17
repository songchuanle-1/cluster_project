from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, subprocess

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
EXPECTED = 'c1fe217800894083b65baac45f79aa83'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
owner_all = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
owner = {k: owner_all[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}
assert owner['token'] == EXPECTED and owner['thread_id'] == os.environ['CODEX_THREAD_ID']
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
for name, key in (('.tick_context.json','context_sha256'),('.tick_context_state.next.json','pending_sha256')):
    assert sha(ROOT/'pipeline/headless'/name) == owner[key]
prior = read(ROOT/'pipeline/diagnostic_bundles/tick_4a0ed3c1/integrity_before.json')
repo = ROOT/'Cluster'
head = subprocess.check_output(['git','-c','safe.directory='+str(repo),'-C',str(repo),'rev-parse','HEAD'], text=True).strip()
assert head == prior['local_main_HEAD']
assert sha(repo/'.git/index') == prior['index_sha256']
assert all(sha(repo/name) == digest for name,digest in prior['dirty_sha256'].items())
assert sha(ROOT/'pipeline/goal.json') == prior['goal_sha256']
assert sha(ROOT/'SERVERS.yaml') == prior['servers_sha256']
baseline = dict(prior, owner=owner, captured_at=datetime.now(timezone.utc).isoformat())
for name in ('research_work.json','queue.json','codex_memory.md'):
    dest = HERE/(name+'.before')
    assert not dest.exists()
    dest.write_bytes((ROOT/'pipeline'/name).read_bytes())
save(HERE/'current_owner_binding.json', owner)
save(HERE/'integrity_before.json', baseline)
print(json.dumps(dict(owner=owner, integrity='PASS', protected_files=len(prior['dirty_sha256']), main_head=head)))
