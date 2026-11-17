"""Read-only post-release audit; no mutation and no lease reacquisition."""
from pathlib import Path
from collections import Counter
import json,re,os,csv,io,copy
from anchor import ROOT,EXPECTED,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
assert os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
mode=u.read(ROOT/'pipeline/execution_mode.json');assert mode['target_thread_id']==EXPECTED['thread_id'] and mode['mode']=='foreground'
r=u.read(ROOT/'pipeline/tick_receipts'/(EXPECTED['token']+'.json'))
assert r['status']=='FINALIZED' and r['postflight']=='PASS' and r['context_committed'] is True and r['lease_release']=='released' and r['lease_released_at']
assert not (ROOT/'pipeline/headless/.foreground.lockdir').exists() and not (ROOT/'pipeline/headless/.tick_context_state.next.json').exists()
assert sha(ROOT/'pipeline/headless/.tick_context.json')==EXPECTED['context_sha256']
report=ROOT/'pipeline/reports'/('summary_'+EXPECTED['token']+'.md');text=report.read_text('utf8')
assert len(re.findall(r'^## [0-5]\. ',text,re.M))==6
memory=(ROOT/'pipeline/codex_memory.md').read_text('utf8');assert len(memory.splitlines())<120 and memory.count('\n## ')==7 and EXPECTED['token'] in memory
state=u.read(HERE/'preclosure_actual_state.json');base=u.read(HERE/'protected_assets_before.json');fresh=u.read(HERE/'lft_before_admission_lifecycle.json')
code=ROOT/'Cluster';assert u.git(code,'rev-parse','HEAD').decode().strip()==state['code_HEAD']=='4457a46f9075f61e83340aa0f0af87d5bf4e986c'
assert u.git(code,'status','--porcelain=v1','--untracked-files=all','-z').hex()==base['status_hex'] and not u.git(code,'diff','--cached','--name-only','-z')
assert all(sha(code/p)==h for p,h in base['files'].items())
for p in [HERE/'lft_root_ff_result.json',ROOT/'pipeline/diagnostic_bundles/tick_9bb5908b/wfc_root_ff_result.json']:
    assert all(sha(code/n)==h for n,h in u.read(p)['source_paths'].items())
work=u.read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==155
assert all(u.digest(c)==fresh['candidate_digests'][c['id']] for c in work['candidates'] if c['id']!='hierarchy-nonlinear-lifting-analysis-synthesis')
assert all(sha(ROOT/'pipeline'/n)==h for n,h in fresh['protected_ledgers'].items() if n not in ('queue.json','running.json','experiments.csv'))
q=u.read(ROOT/'pipeline/queue.json');norm=copy.deepcopy(q)
for rows in norm['gpu_queues'].values():rows[:]=[x for x in rows if x['id']!='M227-LFT']
assert norm==fresh['queue']
assert [x for x in csv.DictReader(io.StringIO((ROOT/'pipeline/experiments.csv').read_text('utf-8-sig'))) if x.get('id')!='M227-LFT']==fresh['csv_rows']
target=next(c for c in work['candidates'] if c['id']=='hierarchy-nonlinear-lifting-analysis-synthesis')
refs=[x for x in target['evidence'] if x['path'].startswith('pipeline/diagnostic_bundles/tick_d94467a9/')]
u.check_refs(refs)
print(json.dumps({'status':'READONLY_RELEASE_AND_FINAL_ARTIFACTS_VERIFIED','receipt':{'status':r['status'],'postflight':r['postflight'],'context_committed':r['context_committed'],'lease_release':r['lease_release'],'released_at':r['lease_released_at']},'six_report_sections':6,'memory_sections':7,'memory_lines':len(memory.splitlines()),'stage_counts':dict(Counter(c['stage'] for c in work['candidates'])),'bound_current_evidence_checked':len(refs),'protected_user_files':len(base['files']),'all154_nontarget_candidates_unchanged':True,'report':str(report),'outcomes':r.get('outcomes')},ensure_ascii=False))
