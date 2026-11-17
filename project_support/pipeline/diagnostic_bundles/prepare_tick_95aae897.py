"""Fresh private owner/protection files and unchanged original DCE observer."""
from pathlib import Path
from datetime import datetime,timezone
import ast,json,sys
ROOT=Path('D:/project/cluster_project');P=ROOT/'pipeline'
o=json.loads((P/'headless/.foreground.lockdir/owner.json').read_text('utf8'))
expected={k:o[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}
assert expected['token']=='95aae897f3a14899b6817e9034640d66'
dest=P/'diagnostic_bundles/tick_95aae897';assert not dest.exists();dest.mkdir()
prior=P/'diagnostic_bundles/tick_01d9102a';s=(prior/'anchor.py').read_text('utf8');tree=ast.parse(s)
n=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED' for t in n.targets))
lines=s.splitlines(True);lines[n.lineno-1:n.end_lineno]=['EXPECTED='+repr(expected)+'\n'];(dest/'anchor.py').write_text(''.join(lines),encoding='utf8')
sys.path.insert(0,str(dest));from anchor import guard,sha
guard();s=(prior/'record_utils.py').read_text('utf8').replace('.01d9102a.tmp','.95aae897.tmp').replace("SOURCE='d0e2f95712ed16446907706fbf6a65d34996a9ad'","SOURCE='5c0c211c8ecc9479ecb34dbb8118a95f4b20e391'")
(dest/'record_utils.py').write_text(s,encoding='utf8')
from record_utils import git,digest
b=json.loads((prior/'final_dce_records_before.json').read_text('utf8'));repo=ROOT/'Cluster'
head=git(repo,'rev-parse','HEAD').decode().strip();assert head==b['head']=='5c0c211c8ecc9479ecb34dbb8118a95f4b20e391'
assert git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and not git(repo,'diff','--cached','--name-only','-z')
assert len(b['files'])==28 and all(sha(repo/n)==h for n,h in b['files'].items())
assert all(sha(repo/n)==h for n,h in b['current_candidate_source_paths'].items())
index=Path(git(repo,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else repo/index
w=json.loads((P/'research_work.json').read_text('utf8'));assert len(w['candidates'])==148
baseline={'owner':expected,'recorded_at':datetime.now(timezone.utc).isoformat(),'head':head,'status_hex':b['status_hex'],'files':b['files'],'index_empty':True,'index_sha256':sha(index),'protected_ledgers':{n:sha(P/n) for n in b['protected_ledgers']},'candidate_digests':{c['id']:digest(c) for c in w['candidates']},'exact_tested_nine_source_paths':b['current_candidate_source_paths']}
guard()
with (dest/'protected_assets_before.json').open('x',encoding='utf8') as f:json.dump(baseline,f,ensure_ascii=False,indent=2);f.write('\n')
observer=dest/'dce_progress_observer';observer.mkdir();(observer/'observe_dce.py').write_bytes((prior/'dce_progress_observer_prepare/observe_dce.py').read_bytes())
catalogue=[{k:c.get(k) for k in ('id','experiment_id','stage','hypothesis','next_action') if c.get(k) is not None} for c in w['candidates']]
with (dest/'candidate_route_index.json').open('x',encoding='utf8') as f:json.dump(catalogue,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'owner':expected,'baseline_sha256':sha(dest/'protected_assets_before.json'),'protected_ledger_count':len(baseline['protected_ledgers']),'candidate_count':len(w['candidates'])}))
