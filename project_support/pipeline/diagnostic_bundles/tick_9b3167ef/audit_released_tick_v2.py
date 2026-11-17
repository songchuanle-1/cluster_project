"""Read-only final release and unchanged-job/artifact audit."""
from pathlib import Path
import os,re,json
from anchor import ROOT,EXPECTED,CHECKS,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
assert os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
r=u.read(ROOT/'pipeline/tick_receipts'/(EXPECTED['token']+'.json'))
assert r['status']=='FINALIZED' and r['postflight']=='PASS' and r['context_committed'] is True and r['lease_release']=='released'
assert not (ROOT/'pipeline/headless/.foreground.lockdir').exists() and not (ROOT/'pipeline/headless/.tick_context_state.next.json').exists()
for n,h in CHECKS.items():
 if n!='pipeline/headless/.tick_context_state.next.json':assert sha(ROOT/n)==h
mode=u.read(ROOT/'pipeline/execution_mode.json');assert mode['mode']=='foreground' and mode['target_thread_id']==EXPECTED['thread_id']
b=u.read(HERE/'protected_assets_before.json');u.protect(b)
s=u.read(HERE/'preclosure_actual_state_v2.json');assert sha(ROOT/'pipeline/research_work.json')==s['work_sha256'] and sha(ROOT/'pipeline/codex_memory.md')==s['memory_sha256']
for e in s['evidence']+[s['notes']]:assert sha(ROOT/e['path'])==e['sha256']
w=u.read(ROOT/'pipeline/research_work.json');assert len(w['candidates'])==155
assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in w['candidates'] if c['id']!='hierarchy-coupled-node-edge-state-composition')
assert w['tick_attempt']['tick_started_at']==EXPECTED['generated_at'] and w['tick_attempt']['kind']=='resource_check' and w['tick_attempt']['result']=='blocked'
report=ROOT/'pipeline/reports'/('summary_'+EXPECTED['token']+'.md');assert len(re.findall(r'^## [0-5]\. ',report.read_text('utf8'),re.M))==6
memory=(ROOT/'pipeline/codex_memory.md').read_text('utf8');assert memory.count('\n## ')==7 and len(memory.splitlines())<120
assert s['notify']=='DONT_NOTIFY'
print(json.dumps({'status':'QUIET_RESOURCE_WAIT_POST_RELEASE_READONLY_AUDIT_PASSED','receipt':{k:r[k] for k in ['status','postflight','context_committed','lease_release','lease_released_at']},'report_sections':6,'memory_sections':7,'memory_lines':len(memory.splitlines()),'protected_user28_running18_lifecycle38_other154':True,'new_scientific_or_implementation_result':False,'notify':'DONT_NOTIFY','outcomes':r.get('outcomes')},ensure_ascii=False))
