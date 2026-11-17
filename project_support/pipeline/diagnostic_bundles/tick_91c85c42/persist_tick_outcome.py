"""Persist only this tick's evidenced terminal and memory-budget dispositions."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import pipeline_monitor as monitor

def read(path):
    return json.loads(path.read_text(encoding='utf8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def ref(path):
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)}

raw = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
owner = {k:raw[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}
assert owner == read(HERE/'current_owner_binding.json')
assert owner['thread_id'] == os.environ['CODEX_THREAD_ID']
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
for name,key in (('.tick_context.json','context_sha256'),('.tick_context_state.next.json','pending_sha256')):
    assert sha(ROOT/'pipeline/headless'/name) == owner[key]
assert not (HERE/'outcome_persisted.actual.json').exists()
resource = read(HERE/'gpu0_overlay_budget.actual.json')
assert resource['owner'] == owner and resource['memory_budget_satisfied'] is False
assert resource['project_cap1_available'] is True
assert resource['observation']['memory_free_mib'] < 20000
assert datetime.now(timezone.utc)-datetime.fromisoformat(resource['observation']['observed_at']) < timedelta(minutes=5)
archive_path = ROOT/'pipeline/experiments/M235-SINC.json'
archive = read(archive_path)
assert archive['status']=='crashed' and archive['archive_id']=='b75c9152d7fd4ecea9af538101d777d4'
fatal = read(HERE/'m235_fatal_frames.actual.json')
assert fatal['observation']['exception_lines']==["AttributeError: 'list' object has no attribute 'grad'"]
diagnosis = read(HERE/'m235_optimizer_source_diagnosis/diagnosis_summary.json')
assert diagnosis['current_source_cache_mismatch_observed'] is False and diagnosis['root_cause']=='UNKNOWN'
review = read(HERE/'peer_review/cso_native_bound_independent_review.json')
assert review['passed'] is True and review['owner']==owner
collection = read(HERE/'m235_terminal_log_collection.actual.json')
assert sha(ROOT/collection['local']['path'])==collection['local']['sha256']==collection['remote']['sha256']
now = datetime.now(timezone.utc)
terminal = dict(owner=owner,observed_at=now.isoformat(),experiment_id='M235-SINC',canonical_archive=ref(archive_path),canonical_archive_unchanged=True,run_status='crashed',complete_saved_epoch_metadata=1,partial_epoch=2,partial_batch=1870,batches_per_epoch=4686,checkpoint_tensors_verified=False,fresh_exact_best_miou_verified=False,canonical_rounded_best=archive['final_best'],prior_exact_best_miou=dict(value=0.2787637412548065,epoch=1,observation_time='2026-11-10T13:13:27.710775+00:00',evidence=ref(ROOT/'pipeline/diagnostic_bundles/tick_2020a21f/m235_native_state.actual.json')),error="AttributeError: 'list' object has no attribute 'grad'",error_location='tools/train.py:130 optimizer.step -> torch/optim/adam.py:237/191',failure_scope='implementation',root_cause='UNKNOWN',current_source_cache_mismatch_observed=False,training_repair_verified=False,restart_performed=False,efficacy='UNKNOWN_INCOMPLETE_TRAINING',novelty='UNKNOWN',log_collection=ref(HERE/'m235_terminal_log_collection.actual.json'),diagnosis=ref(HERE/'m235_optimizer_source_diagnosis/diagnosis_summary.json'))
save(HERE/'m235_terminal_disposition.actual.json',terminal)
analysis = ROOT/'pipeline/analyses/M235-SINC_crashed_b75c9152d7fd4ecea9af538101d777d4_supplement.md'
assert not analysis.exists()
analysis.write_text('''# Experiment Result Analysis — cluster_project

Experiment: M235-SINC | State: crashed | Archive: b75c9152d7fd4ecea9af538101d777d4

## 1. Basic Info
- Server4 physical GPU0; source b1e639b3ceb14bb5c65d9f81a084d41c834b951c.
- Canonical three-observation reconciliation archived the run at 2026-11-10 23:15:49 +08:00; PID2248650 absent in two additional direct samples.
- Canonical archive is unchanged. Its empty log_local is supplemented by a separately collected, remote/local SHA-verified 1938280-byte log under Checkpoints/server_4/M235-SINC/b75c9152d7fd4ecea9af538101d777d4/.

## 2. Best Metrics
| Metric | Value | Evidence scope |
|---|---|---|
| mIoU | 0.2790 | Canonical rounded log/archive value; no new exact metric claim |
| Prior exact saved mIoU | 0.2787637412548065 | Historical 13:13Z metadata observation at epoch1 |
| Fresh saved checkpoint epoch | 1 for best and last | ZIP/pickle scalar metadata; tensors/optimizer contents unverified |
| Acc@50 / spmIOU | UNKNOWN | Not newly measured |

## 3. Convergence Summary
- One complete saved epoch is established by metadata. The run ended during epoch2 at batch1870/4686, not after two complete epochs.
- No convergence, full training efficacy or resume-eligibility conclusion follows from this partial run.

## 4. Comparison
- Baseline/champion deltas are not an efficacy comparison because this training is incomplete. M95 champion remains unchanged.
- Technical native TRAIN2/resource admission remains historical evidence; it did not establish long-run stability.

## 5. Conclusion
- Runtime failure with implementation scope; the structural hypothesis and novelty remain unresolved.
- Preserve checkpoints, original admission and all failure evidence. No automatic restart, resume or consumed-entry replay.
- Closest prepared M236-CSO remains unmeasured natively; fresh GPU0 free10530MiB is below its original20000MiB startup budget. Overlay is permitted; no empty-card/context/utilization condition is imposed.

## 6. Crash Info (if crashed)
- tools/train.py130 optimizer.step() -> torch.optim.Adam.step/_init_group -> AttributeError: 'list' object has no attribute 'grad'.
- Fresh static diagnosis finds current installed Adam source/cache/header/bytecode/line mapping consistent. The reported line191 does not directly load .grad; this does not establish the exit-time code object or local optimizer objects. Root cause UNKNOWN.
- No Torch import, GPU computation, package/source repair, signals, restart or native retest was performed for the diagnosis. See pipeline/diagnostic_bundles/tick_91c85c42/m235_optimizer_source_diagnosis/diagnosis_summary.json.
''',encoding='utf8')
lock = monitor.acquire_lock(str(ROOT))
assert lock is not None
try:
    work = read(ROOT/'pipeline/research_work.json')
    before = read(HERE/'research_work.json.before')
    assert work == before
    decision = Path(monitor.log_decision(str(ROOT),'other','M235自然崩溃后，是否重启或借外部占用插入M236测试？','归档M235并保留运行失败/机制未定；不重启。M236复用已审包，当前仅按GPU0原20GB预算等待。','两次PID缺失/静态日志与canonical三次确认；Adam新异常已定位，当前source/cache一致但根因未知；free10530MiB<20000，项目槽位释放不等于满足显存预算。','pipeline/diagnostic_bundles/tick_91c85c42/m235_terminal_disposition.actual.json; pipeline/diagnostic_bundles/tick_91c85c42/gpu0_overlay_budget.actual.json'))
    sinc = next(c for c in work['candidates'] if c['id']=='fine-leaf-geometric-simplex-incidence-composition')
    cso = next(c for c in work['candidates'] if c['id']=='fine-leaf-full-covariance-shape-composition')
    sinc.update(stage='blocked',blocked_from_stage='training',blocker_kind='runtime_implementation_failure',failure_scope='implementation',blocker="M235 exited at partial epoch2/1870 with Adam AttributeError: 'list' object has no attribute 'grad'. Current disk source/cache match; exit-time frame/optimizer object evidence is missing; root cause UNKNOWN. Not a hypothesis rejection.",retry_after=(now+timedelta(hours=4)).isoformat(),unblock_condition='A fresh scoped diagnosis must obtain actual exit-time code/object evidence and establish an evidence-backed repair; source review or old CPU success does not authorize restart/resume. Any future computation also requires fresh owner, original GPU0 memory budget and three locks.',next_action='保留crashed原运行、完整savedepoch1及partialepoch2/1870；当前Adam源码/pyc不支持磁盘缓存不一致解释，缺退出时frame/optimizer对象证据。仅有新实际诊断再推进，不自动重启/恢复/重放。',updated_at=now.isoformat(),runtime_failure=ref(HERE/'m235_terminal_disposition.actual.json'),training_repair_verified=False,efficacy='UNKNOWN_INCOMPLETE_TRAINING',novelty='UNKNOWN')
    sinc_refs=[HERE/'m235_native_state.actual.json',HERE/'m235_fatal_frames.actual.json',HERE/'m235_terminal_log_collection.actual.json',HERE/'m235_optimizer_source_diagnosis/static_probe.actual.json',HERE/'m235_optimizer_source_diagnosis/diagnosis_summary.json',HERE/'m235_terminal_disposition.actual.json',HERE/'peer_review/m235_terminal_independent_review.json',analysis,decision]
    for path in sinc_refs:
        entry=ref(path)
        if entry not in sinc['evidence']: sinc['evidence'].append(entry)
    cso.update(stage='blocked',blocked_from_stage='implementation',blocker_kind='live_external_gpu_occupation',required_server='server-4',required_gpu=0,blocker='M235 has naturally terminated and the project cap1 slot is free, but the authorized GPU0 currently has only10530MiB actual free memory, below the original20000MiB startup budget. External tasks are preserved. Overlay is allowed; no empty-card, zero-context or low-utilization requirement applies.',retry_after=(now+timedelta(hours=1)).isoformat(),unblock_condition='Fresh pinned server4 physicalGPU0 UUID958e741a-e5cf-127e-ffe8-9b984e1f404c actual memory.free>=20000MiB, project cap1 available and all three original cooperative locks acquirable; verify current owner/source/runtime/root/producer before native execution. External contexts may remain.',next_action='复用已独审CSO sourceaf457/原YAML/worker；当前仅显存不足，native TRAIN2/common841/九core更新/同口径资源仍NOT_RUN。有真实原预算授权槽位后另存新owner执行绑定，完成实测和独审才准入入队。',updated_at=now.isoformat(),last_resource_check_at=resource['observation']['observed_at'])
    cso['resource_disposition']=dict(owner=owner,project_cap1_available=True,original_minimum_free_mib=20000,actual_free_mib=10530,allow_external_overlay=True,require_empty_device=False,native_execution_allowed_now=False,evidence=ref(HERE/'gpu0_overlay_budget.actual.json'))
    cso['latest_execution_preparation']=dict(owner=owner,status='PREPARED_NOT_RUN_ORIGINAL_MEMORY_BUDGET_BLOCKED',FROZEN=ref(HERE/'cso_native_bound/FROZEN.json'),source_review=ref(HERE/'peer_review/cso_native_bound_independent_review.json'),actual_native_gate_passed=False,actual_resource_gate_passed=False,remote_stage_created=False,execution_lease_created=False)
    for path in (HERE/'cso_native_bound/FROZEN.json',HERE/'peer_review/cso_native_bound_independent_review.json',HERE/'gpu0_overlay_budget.actual.json',HERE/'m235_terminal_disposition.actual.json',decision):
        entry=ref(path)
        if entry not in cso['evidence']: cso['evidence'].append(entry)
    old_attempt=work.get('tick_attempt')
    if old_attempt:
        history=work.setdefault('tick_attempt_history',[])
        if old_attempt not in history: history.append(old_attempt)
    work['tick_attempt']=dict(tick_started_at=owner['generated_at'],candidate_id=cso['id'],kind='resource_check',result='blocked',command='python -B -X utf8 '+str(HERE/'check_overlay_budget.py'),observation='M235 canonical crashed archiveb75c; project GPU0 cap1 free and original locks retained. Fresh actual memory.free10530MiB<original20000MiB; no native/GPU test or admission attempted. Overlay remains permitted.',evidence=[ref(HERE/'gpu0_overlay_budget.actual.json')])
    work['next_action']=cso['next_action']
    work['updated_at']=now.isoformat()
    save(ROOT/'pipeline/research_work.json',work)
finally:
    lock.close()
memory='''# Codex Research Memory

## Goal And Phase
- 仅cluster_project；server4物理GPU0/UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c，可与外部任务共享；max_tasks_per_gpu1/原启动free>=20000MiB/原training-diagnostic-exclusive三锁。无空卡/零context/低util要求。
- GPU1/其他服务器禁用，M206/M227独立人工暂停；不驱逐、信号、重启、迁移任务，不改目标、数据、seed1999、epochs50/max_iters70、原损失/optimizer、10G及条件15%显存门槛、bans或调度。
- Pipeline-cluster_project Disabled；ownerthread01a159c5-29ab-7a22-ba7f-e79174757253；canonical foreground/python-B/PROJECT_ROOT=D:/project。

## Champion And Baseline
- 原目标.5100，M95冠军.5020/baseline.4894保持；技术准入/partial训练不作效力或novelty证明。
- WFC完整epoch30/noimp10早停，best.49711745977401733；NEC完整epoch23/noimp10早停best.49454113841056824；MIC完整epoch26/noimp10早停best.49881425499916077。均不重启。

## Active Hypotheses
- M236-CSO sourceaf45707d(parentd214)；CPU21/九core已独审不重跑。原生TRAIN2/common841/九core真实原loss更新、同口径资源仍NOT_RUN，尚未准入/入队。
- 原准备包cafab8dd复用；本轮仅owner/stage最小绑定包649d4aaa、独审98cbe260通过。新stage未创建/actuallease未创建，不表示远端producer实测通过；未来新owner另存绑定。

## Closed Or Failed Directions
- M235-SINC原生自然崩溃，archiveb75c9152d7fd4ecea9af538101d777d4；sourceb1/PID2248650消失。partialepoch2/1870of4686，完整savedmetadata仅epoch1，非完整两轮/训练终态效力。
- 新错误train.py130 optimizer.step→Adam.step/_init_group191，AttributeError:list object has no attribute grad。当前磁盘Adam.py/pyc/header/bytecode/linemap一致；191无直接grad读取，退出时frame/code/object缺失，根因UNKNOWN，未修复、不自动恢复。
- NSD M232 partialepoch1/1961无完整验证/pth；HVD M230 partialepoch5/1449/saved4；PSC M231 partialepoch2/984/saved1。原Torch错误根因仍未知；旧128CPU/短测通过不代表长期修复。
- 全部旧scope/numerical holds、已消费授权、失败/原NULL保留，bans不改名重开；M206/M227保持人工暂停。

## Running And Queue
- 当前无GPU0项目训练；M235经canonical三次缺失确认crashed归档，原三锁inode92537152/53/54/dev66308保留且无内核持锁记录；无重启/新入队/新训练。
- M235 best/last新ZIP元数据epoch1/无tensor完整内容验证，exactbest本轮未重新确立；历史13:13Z exact.2787637412548065@1仅保留历史口径，canonicalrounded.2790不改账。
- GPU0本轮后续实际free10530MiB<原20000，项目cap1释放仍不能插入CSO；允许外部共享但不降低原显存预算。

## Open Questions And Risks
- Adam报错行与当前磁盘字节码的直接grad位置不一致仍未解释；当前source/cache一致不能证明退出时实际code/locals或排除native内存问题，不重复旧CPU模拟冒充根因。
- Canonicalpull_log传错PROJECT_DIR导致缺D:/SERVERS.yaml/目的地偏移，实际旧subprocessstderr未留存；本轮仅read-only精确scp补取1938280B日志，远近SHA123abcdf一致，原archive空log_local保持并另存补充分析，不改共享helper。
- SINC/旧NSD生产shim及旧lease/intent均已消费或过期，不重放；新运行先reconcile并核source/runtime/root/UUID/producer哈希。SSH仅strictkey至pinned songcl@192.168.1.115/dl04，不读密码/连旧IP/假设sudo。

## Last Tick
- 91c85c42：发现M235自然崩溃并归档，取回原日志、完整保存错误帧及source/pyc静态诊断；只缩小解释范围，根因UNKNOWN，机制效力/novelty未定。
- M236已审冻结源码/协议复用；仅本轮owner重绑定并独审；真实原预算resource_check blocked，native/resources均NOT_RUN。未新增变体或为额度造候选。
- goal/SERVERS/主HEAD0747/index/dirty37及其他160候选保持；原完整/partial结果、暂停和所有失败保留。证据目录pipeline/diagnostic_bundles/tick_91c85c42。
'''
assert len(memory.splitlines())<120 and memory.count('\n## ')==7
(ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf8')
notes=dict(actions=['先核原生进度/终态：M235同PID两次消失、日志静止epoch2/1870；canonical三次确认并归档crashed，完整savedepoch1与partialepoch2区分保存。','原Adam错误帧及精确训练日志取回并校验远近SHA；新静态诊断当前source/pyc一致，缺退出时frame/optimizer对象，根因仍UNKNOWN，未修复/重启。','复用M236已审源码/协议，仅本owner最小执行绑定并独审通过；原预算真实资源检查free10530MiB<20000，native/resources均NOT_RUN。'],decisions=['M235运行失败不是机制证伪或完整训练；保留所有checkpoint/准入/失败记录，不自动恢复或消费旧入口。','GPU0项目槽位释放但原显存预算未满足，外部任务保持；允许overlay，不要求空卡/零context/低利用率，不扩GPU/改暂停/改调度。','最近CSO缺项需实际GPU验证，当前真实受阻；无新变体、准入、入队或训练，不为配额新增。'])
save(HERE/'report_notes.json',notes)
before_integrity=read(HERE/'integrity_before.json')
assert sha(ROOT/'pipeline/goal.json')==before_integrity['goal_sha256'] and sha(ROOT/'SERVERS.yaml')==before_integrity['servers_sha256']
repo=ROOT/'Cluster'
assert subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==before_integrity['local_main_HEAD']
assert sha(repo/'.git/index')==before_integrity['index_sha256']
assert all(sha(repo/name)==expected for name,expected in before_integrity['dirty_sha256'].items())
current=read(ROOT/'pipeline/research_work.json');old_by={c['id']:c for c in before['candidates']};new_by={c['id']:c for c in current['candidates']}
changed={key for key in old_by if old_by[key]!=new_by[key]}
assert changed=={sinc['id'],cso['id']}
qbefore=read(HERE/'queue.json.before');qafter=read(ROOT/'pipeline/queue.json')
for name in ('M206-CGCA','M227-LFT'):
    a=next(t for t in qbefore['gpu_queues']['server-4'] if t['id']==name)
    b=next(t for t in qafter['gpu_queues']['server-4'] if t['id']==name)
    assert a==b
assert not any(t.get('id')=='M235-SINC' for t in qafter['gpu_queues']['server-4'])
save(HERE/'outcome_persisted.actual.json',dict(owner=owner,changed_candidate_ids=sorted(changed),other160_candidates_unchanged=True,protected37_index_goal_SERVERS_unchanged=True,manual_pauses_unchanged=True,canonical_archive_unchanged=sha(archive_path)==terminal['canonical_archive']['sha256'],memory_lines=len(memory.splitlines()),new_candidates=0,new_admissions=0,new_training=0,native_resources='NOT_RUN',decision=ref(decision),analysis=ref(analysis),resource=ref(HERE/'gpu0_overlay_budget.actual.json')))
print(json.dumps(dict(status='PERSISTED_HONEST_TERMINAL_AND_ORIGINAL_MEMORY_BLOCK',changed_candidates=sorted(changed),protected37_unchanged=True,other160_unchanged=True,new_training=0,notes=str(HERE/'report_notes.json')),ensure_ascii=False))
