"""Read-only verification after final release; no shared or private writes."""
from pathlib import Path
from collections import Counter
import json,os,re
from anchor import ROOT,EXPECTED,CHECKS,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
assert os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
mode=u.read(ROOT/'pipeline/execution_mode.json');assert mode['mode']=='foreground' and mode['target_thread_id']==EXPECTED['thread_id']
receipt=u.read(ROOT/'pipeline/tick_receipts'/(EXPECTED['token']+'.json'))
assert receipt['status']=='FINALIZED' and receipt['postflight']=='PASS' and receipt['context_committed'] is True and receipt['lease_release']=='released' and receipt['lease_released_at']
assert not (ROOT/'pipeline/headless/.foreground.lockdir').exists() and not (ROOT/'pipeline/headless/.tick_context_state.next.json').exists()
for name,h in CHECKS.items():
 if name!='pipeline/headless/.tick_context_state.next.json':assert sha(ROOT/name)==h
b=u.read(HERE/'protected_assets_before.json');u.protect(b)
state=u.read(HERE/'preclosure_actual_state.json');assert sha(ROOT/'pipeline/research_work.json')==state['work_sha256'] and sha(ROOT/'pipeline/codex_memory.md')==state['memory_sha256']
work=u.read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==155 and all(u.digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'] if c['id']!='hierarchy-coupled-node-edge-state-composition')
for e in state['bound_artifacts']+[state['notes']]:assert sha(ROOT/e['path'])==e['sha256']
c=next(c for c in work['candidates'] if c['id']=='hierarchy-coupled-node-edge-state-composition');assert c['stage']=='validation' and c['native_status']==c['resource_status']=='NOT_RUN' and not c['queued'] and c['code_commit']=='6bc36adfe42764aac2209e6600fb3a783e2fa374'
assert not (ROOT/'pipeline/admissions/M228-NEC.json').exists() and not (HERE/'nec_execution').exists()
v=u.read(HERE/'nec_version_prepare/isolated_source_version.json');assert u.git('rev-parse',v['pinned_ref']).decode().strip()==v['code_commit']
report=ROOT/'pipeline/reports'/('summary_'+EXPECTED['token']+'.md');text=report.read_text('utf8');assert len(re.findall(r'^## [0-5]\. ',text,re.M))==6
memory=(ROOT/'pipeline/codex_memory.md').read_text('utf8');assert memory.count('\n## ')==7 and len(memory.splitlines())<120
print(json.dumps({'status':'READONLY_FINAL_REPORT_MEMORY_SOURCE_EVIDENCE_AND_RELEASE_VERIFIED','receipt':{k:receipt[k] for k in ['status','postflight','context_committed','lease_release','lease_released_at']},'report':str(report),'report_sections':6,'memory_sections':7,'memory_lines':len(memory.splitlines()),'stage_counts':dict(Counter(c['stage'] for c in work['candidates'])),'protected_user28_running_source18_lifecycle38_and_other154_candidates':True,'no_NEC_native_lease_receipt_queue_or_training_created':True,'outcomes':receipt.get('outcomes')},ensure_ascii=False))
