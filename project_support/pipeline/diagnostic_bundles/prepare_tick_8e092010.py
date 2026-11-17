"""Fresh owner, read-only original HPC observation tools, and current protection baseline."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,subprocess,sys
ROOT=Path('D:/project/cluster_project');P=ROOT/'pipeline'
owner=json.loads((P/'headless/.foreground.lockdir/owner.json').read_text('utf8'))
expected={k:owner[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}
assert expected['token']=='8e092010aac34f61874a1ee9bbec69dd'
dest=P/'diagnostic_bundles/tick_8e092010';assert not dest.exists();dest.mkdir()
prior=P/'diagnostic_bundles/tick_2b832a02';s=(prior/'anchor.py').read_text('utf8');tree=ast.parse(s)
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED' for t in n.targets))
lines=s.splitlines(True);lines[node.lineno-1:node.end_lineno]=['EXPECTED='+repr(expected)+'\n']
(dest/'anchor.py').write_text(''.join(lines),encoding='utf8')
sys.path.insert(0,str(dest));from anchor import guard,sha
guard();util=(prior/'record_utils.py').read_text('utf8').replace('.2b832a02.tmp','.8e092010.tmp')
util=util.replace("SOURCE='d58576b396cfb54577652be972f3ffaffda508c9'","SOURCE='6282263d805c1741234f97afc981a05aca2ad6e3'")
(dest/'record_utils.py').write_text(util,encoding='utf8')
obs=(prior/'observe_hpc.py').read_text('utf8');(dest/'observe_hpc.py').write_text(obs,encoding='utf8')
from record_utils import git,digest
b=json.loads((prior/'hpc_post_dispatch_protected_assets.json').read_text('utf8'))
repo=ROOT/'Cluster';head=git(repo,'rev-parse','HEAD').decode().strip();assert head==b['head']=='6282263d805c1741234f97afc981a05aca2ad6e3'
assert git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex']
assert all(sha(repo/n)==h for n,h in b['files'].items()) and not git(repo,'diff','--cached','--name-only','-z')
assert all(sha(repo/n)==h for n,h in b['exact_tested_nine_source_paths'].items())
idx=Path(git(repo,'rev-parse','--git-path','index').decode().strip());idx=idx if idx.is_absolute() else repo/idx
w=json.loads((P/'research_work.json').read_text('utf8'));assert len(w['candidates'])==145
out={'owner':expected,'recorded_at':datetime.now(timezone.utc).isoformat(),'head':head,'status_hex':b['status_hex'],'files':b['files'],
     'index_empty':True,'index_sha256':sha(idx),'protected_ledgers':{n:sha(P/n) for n in b['protected_ledgers']},
     'candidate_digests':{c['id']:digest(c) for c in w['candidates']},'exact_tested_nine_source_paths':b['exact_tested_nine_source_paths']}
guard();f=dest/'protected_assets_before.json'
with f.open('x',encoding='utf8') as stream:json.dump(out,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'owner':expected,'baseline_sha256':sha(f),'protected_ledger_count':len(out['protected_ledgers'])}))
