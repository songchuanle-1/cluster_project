"""Current foreground private owner/protection tools; no remote or lifecycle operation."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,sys
ROOT=Path('D:/project/cluster_project');P=ROOT/'pipeline'
o=json.loads((P/'headless/.foreground.lockdir/owner.json').read_text('utf8'))
expected={k:o[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}
assert expected['token']=='01d9102a850b4715bba0f9036e5fabb1'
dest=P/'diagnostic_bundles/tick_01d9102a';assert not dest.exists();dest.mkdir()
prior=P/'diagnostic_bundles/tick_8e092010';s=(prior/'anchor.py').read_text('utf8');tree=ast.parse(s)
n=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED' for t in n.targets))
lines=s.splitlines(True);lines[n.lineno-1:n.end_lineno]=['EXPECTED='+repr(expected)+'\n']
(dest/'anchor.py').write_text(''.join(lines),encoding='utf8')
sys.path.insert(0,str(dest));from anchor import guard,sha
guard();s=(prior/'record_utils.py').read_text('utf8').replace('.8e092010.tmp','.01d9102a.tmp').replace("SOURCE='6282263d805c1741234f97afc981a05aca2ad6e3'","SOURCE='d0e2f95712ed16446907706fbf6a65d34996a9ad'")
(dest/'record_utils.py').write_text(s,encoding='utf8')
from record_utils import git,digest
b=json.loads((prior/'final_apf_records_before.json').read_text('utf8'));repo=ROOT/'Cluster'
head=git(repo,'rev-parse','HEAD').decode().strip();assert head==b['head']=='d0e2f95712ed16446907706fbf6a65d34996a9ad'
assert git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and not git(repo,'diff','--cached','--name-only','-z')
assert len(b['files'])==28 and all(sha(repo/n)==h for n,h in b['files'].items())
assert all(sha(repo/n)==h for n,h in b['current_candidate_source_paths'].items())
index=Path(git(repo,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else repo/index
w=json.loads((P/'research_work.json').read_text('utf8'));assert len(w['candidates'])==145
baseline={'owner':expected,'recorded_at':datetime.now(timezone.utc).isoformat(),'head':head,'status_hex':b['status_hex'],'files':b['files'],'index_empty':True,'index_sha256':sha(index),'protected_ledgers':{n:sha(P/n) for n in b['protected_ledgers']},'candidate_digests':{c['id']:digest(c) for c in w['candidates']},'exact_tested_nine_source_paths':b['current_candidate_source_paths']}
guard()
with (dest/'protected_assets_before.json').open('x',encoding='utf8') as f:json.dump(baseline,f,ensure_ascii=False,indent=2);f.write('\n')
observer=dest/'apf_progress_observer';observer.mkdir()
(observer/'observe_apf.py').write_bytes((prior/'apf_progress_observer_prepare/observe_apf.py').read_bytes())
catalogue=[{k:c.get(k) for k in ('id','experiment_id','stage','hypothesis','next_action') if c.get(k) is not None} for c in w['candidates']]
with (dest/'candidate_route_index.json').open('x',encoding='utf8') as f:json.dump(catalogue,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'owner':expected,'baseline_sha256':sha(dest/'protected_assets_before.json'),'protected_ledger_count':len(baseline['protected_ledgers']),'candidate_count':len(w['candidates'])}))
