from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import pipeline_monitor as monitor
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ref(p): return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
owner=read(HERE/'current_owner_binding.json')
current=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert {k:current[k] for k in owner}==owner
assert owner['thread_id']==os.environ['CODEX_THREAD_ID']
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
actual=HERE/'runtime_readiness.actual.json'; review=HERE/'peer_review/runtime_readiness_actual_independent_review.json'
assert read(actual)['owner']==owner and read(actual)['passed'] is True
assert read(review)['owner']==owner and read(review)['passed'] is True and read(review)['material_concerns']==[]
before=read(HERE/'research_work.json.before')
lock=monitor.acquire_lock(str(ROOT)); assert lock is not None
try:
    work=read(ROOT/'pipeline/research_work.json'); assert work==before
    c=next(c for c in work['candidates'] if c['id']=='fine-leaf-full-covariance-shape-composition')
    c.update(stage='implementation',updated_at=datetime.now(timezone.utc).isoformat(),
        next_action='Current startup readiness is independently verified. Execute fresh-owner reviewed native TRAIN2/common841/9core, then original resource arm and independent reviews. Admit/queue only after actual gates pass; preserve all consumed stages and historical NULL fields.')
    for key in ('blocker','blocker_kind','retry_after','blocked_from_stage','unblock_condition'): c.pop(key,None)
    c['latest_startup_readiness']=dict(owner=owner,actual=ref(actual),independent_review=ref(review),
        status='STARTUP_READINESS_PASSED_NATIVE_AND_PERFORMANCE_NOT_RUN',
        native_gate_passed=False,performance_gate_passed=False)
    for p in (actual,review):
        r=ref(p)
        if r not in c['evidence']: c['evidence'].append(r)
    old=work.get('tick_attempt')
    if old and old not in work.setdefault('tick_attempt_history',[]): work['tick_attempt_history'].append(old)
    work['tick_attempt']=dict(tick_started_at=owner['generated_at'],candidate_id=c['id'],kind='resource_check',result='passed',
        command='python -B -X utf8 '+str(HERE/'run_runtime_readiness.py'),
        observation='Fresh readonly server4 GPU0 directfree32016>=20000; cap1 and original three lock inodes available. Eighteen runtime/environment/assets hashes passed and independently reviewed. Native and measured model resources still NOT_RUN.',evidence=[ref(actual),ref(review)])
    work['updated_at']=datetime.now(timezone.utc).isoformat(); save(ROOT/'pipeline/research_work.json',work)
finally: lock.close()
assert read(ROOT/'pipeline/queue.json')==read(HERE/'queue.json.before')
print(json.dumps(dict(status='READINESS_PERSISTED',native='NOT_RUN',performance='NOT_RUN',queued=False)))
