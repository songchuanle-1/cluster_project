"""Preserve this fresh resource observation without replaying prepared native work."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import pipeline_monitor as monitor

def read(path): return json.loads(path.read_text(encoding='utf8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ref(path): return dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path))

owner=read(HERE/'current_owner_binding.json')
current=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert {k:current[k] for k in owner}==owner
assert owner['thread_id']==os.environ['CODEX_THREAD_ID']
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
for name,key in (('.tick_context.json','context_sha256'),('.tick_context_state.next.json','pending_sha256')):
    assert sha(ROOT/'pipeline/headless'/name)==owner[key]
actual=read(HERE/'gpu0_overlay_budget.actual.json')
assert actual['owner']==owner and actual['memory_budget_satisfied'] is False and actual['project_cap1_available'] is True
assert actual['observation']['memory_free_mib']==10535 and actual['minimum_free_mib']==20000
assert not actual['observation']['original_pid_exists']
assert all(not row['kernel_rows'] for row in actual['observation']['original_locks'])
review_path=HERE/'peer_review/gpu0_overlay_budget_independent_review.json'
review=read(review_path)
assert review['owner']==owner and review['passed'] is True
archive=ROOT/'pipeline/experiments/M235-SINC.json'
assert sha(archive)=='8f8bc6c3791823ec4166a3097e6e9a5617820b9a2d97ce4809171f7d127c9c62'
before=read(HERE/'research_work.json.before')
now=datetime.now(timezone.utc)
disposition=dict(owner=owner,recorded_at=now.isoformat(),kind='UNCHANGED_ORIGINAL_MEMORY_BUDGET_BLOCK_RECHECK',candidate_id='fine-leaf-full-covariance-shape-composition',original_minimum_free_mib=20000,actual_free_mib=10535,project_cap1_available=True,allow_external_overlay=True,require_empty_card=False,require_zero_contexts=False,require_low_utilization=False,actual=ref(HERE/'gpu0_overlay_budget.actual.json'),independent_review=ref(review_path),M235_terminal_unchanged=True,M235_archive=ref(archive),native='NOT_RUN',resources='NOT_RUN',new_native_binding_created=False,remote_stage_created=False,execution_lease_created=False,new_candidates=0,new_admissions=0,new_training=0,reason='Closest native packet is already prepared/reviewed. The missing original native/resource tests are blocked by actual memory.free below20000MiB. Rebuilding preparation or repeating old tests would not resolve this missing resource.')
save(HERE/'resource_disposition.actual.json',disposition)
lock=monitor.acquire_lock(str(ROOT));assert lock is not None
try:
    work=read(ROOT/'pipeline/research_work.json');assert work==before
    cso=next(c for c in work['candidates'] if c['id']==disposition['candidate_id'])
    assert cso['stage']=='blocked' and cso['blocker_kind']=='live_external_gpu_occupation'
    cso['updated_at']=now.isoformat()
    cso['last_resource_check_at']=actual['observation']['observed_at']
    cso['retry_after']=(now+timedelta(hours=1)).isoformat()
    cso['blocker']='Authorized server4 physicalGPU0 has actual memory.free10535MiB, below the original20000MiB startup budget. Project cap1 is free and original cooperative lock inodes retained/released. External tasks are preserved. Overlay is permitted; no empty-card, zero-context or low-utilization requirement.'
    cso['resource_disposition']=dict(owner=owner,project_cap1_available=True,original_minimum_free_mib=20000,actual_free_mib=10535,allow_external_overlay=True,require_empty_device=False,native_execution_allowed_now=False,evidence=ref(HERE/'gpu0_overlay_budget.actual.json'),independent_review=ref(review_path))
    for path in (HERE/'gpu0_overlay_budget.actual.json',review_path,HERE/'resource_disposition.actual.json'):
        entry=ref(path)
        if entry not in cso['evidence']:cso['evidence'].append(entry)
    old_attempt=work.get('tick_attempt')
    if old_attempt and old_attempt not in work.setdefault('tick_attempt_history',[]):work['tick_attempt_history'].append(old_attempt)
    work['tick_attempt']=dict(tick_started_at=owner['generated_at'],candidate_id=cso['id'],kind='resource_check',result='blocked',command='python -B -X utf8 '+str(HERE/'check_overlay_budget.py'),observation='Current server4GPU0 actualfree10535MiB<original20000MiB. Canonical projectcap1 free; original3locks retained/released; originalM235PID absent/archivedcrashed unchanged. No SSH staging/native test/admission/launch or new native lease attempted. Overlay allowed.',evidence=[ref(HERE/'gpu0_overlay_budget.actual.json'),ref(review_path)])
    work['updated_at']=now.isoformat()
    save(ROOT/'pipeline/research_work.json',work)
finally:lock.close()
memory=(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf8')
memory=memory.replace('原准备包cafab8dd复用；本轮仅owner/stage最小绑定包649d4aaa、独审98cbe260通过。','原准备包cafab8dd及91c85c42绑定包649d4aaa/独审98cbe260复用；本轮不重建native包。')
memory=memory.replace('GPU0本轮后续实际free10530MiB<原20000','GPU0本轮实际free10535MiB<原20000')
prefix=memory.split('## Last Tick')[0]
memory=prefix+'''## Last Tick
- 5101bb4d：canonical观察无项目训练；M235既有crashedarchiveb75c未变，未重新诊断旧错误、补签旧NULL或重放入口。
- 最近M236真实缺项仍为native TRAIN2/资源；本轮新owner只做read-only原预算检查，actualfree10535MiB<20000，独审通过；共享允许，原三锁保持，资源阻塞未变。
- 复用已审准备，不重制native包/创建lease/stage，不为配额新增变体；native/resources仍NOT_RUN，无准入、入队或训练。
- goal/SERVERS/主HEAD0747/index/dirty37、其他161候选及M206/M227人工暂停保持。本轮证据pipeline/diagnostic_bundles/tick_5101bb4d。
'''
assert len(memory.splitlines())<120 and memory.count('\n## ')==7
(ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf8')
notes=dict(actions=['先核canonical原生/终态：当前无项目训练，M235原crashed归档与部分结果保持；仅有M206/M227人工暂停项，无合格队列可派发。','对最近M236执行本owner真实原预算检查：GPU0实际free10535MiB<20000；项目cap1已释放、原三锁inode保留且无内核持锁；新观察及producer绑定独审通过。','复用已受审CSO源码和准备包，无需重复CPU测试或重制执行包；本轮未建native lease/stage，原生与资源仍NOT_RUN。'],decisions=['当前显存不足的真实阻塞未变；允许外部共享，不把空卡/零context/低利用率作为条件，不降低原预算或扩大GPU。','不重启M235或恢复人工暂停，不为额度新增候选；保留全部完整/partial及失败证据。无新可行动变化，按静默通知规则收尾。'])
save(HERE/'report_notes.json',notes)
baseline=read(HERE/'integrity_before.json');repo=ROOT/'Cluster'
assert sha(ROOT/'pipeline/goal.json')==baseline['goal_sha256'] and sha(ROOT/'SERVERS.yaml')==baseline['servers_sha256']
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==baseline['local_main_HEAD']
assert sha(repo/'.git/index')==baseline['index_sha256'] and all(sha(repo/name)==digest for name,digest in baseline['dirty_sha256'].items())
after=read(ROOT/'pipeline/research_work.json');old={c['id']:c for c in before['candidates']};new={c['id']:c for c in after['candidates']};changed={cid for cid in old if old[cid]!=new[cid]}
assert changed=={disposition['candidate_id']}
assert read(HERE/'queue.json.before')==read(ROOT/'pipeline/queue.json')
save(HERE/'completion_audit.actual.json',dict(owner=owner,other161_candidates_unchanged=True,queue_and_manual_pauses_unchanged=True,protected37_index_goal_SERVERS_unchanged=True,M235_archive_unchanged=True,new_candidates=0,new_admissions=0,new_training=0,native='NOT_RUN',resources='NOT_RUN',resource_disposition=ref(HERE/'resource_disposition.actual.json')))
print(json.dumps(dict(status='PERSISTED_UNCHANGED_ORIGINAL_RESOURCE_BLOCK',actual_free_mib=10535,other161_unchanged=True,queue_unchanged=True,protected37_unchanged=True,notes=str(HERE/'report_notes.json'))))
