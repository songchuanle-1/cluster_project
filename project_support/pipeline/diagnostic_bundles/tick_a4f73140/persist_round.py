"""Persist factual carryover and notes before canonical report/finish."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import sys

ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
TOKEN='a4f7314098ed4dbd8351aa005661583d'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x,text=False):
    t=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with t.open('x',encoding='utf-8') as f:
        f.write(x if text else json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n'); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)

def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    dispatch=read(HERE/'dispatch_result.json')
    assert dispatch['verified_native_progress'] and dispatch['task_after']['pid']==2502712
    final_review=HERE/'final_dispatch_independent_review.json'
    review=read(final_review)
    assert review['material_concerns']==[]
    admission_review=HERE/'psnc_execution_independent_review/psnc_admission_independent_review.json'
    assert sha(admission_review)=='da241b224f99964c0403efdcaffc3c9c50373c972bcf07a7e460b69c10a78c44'
    sys.path.insert(0,str(SKILL)); import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT)); assert lock is not None
    try:
        now=datetime.now(timezone.utc); queue=monitor.load_queue(str(ROOT))
        psnc=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M210-PSNC')
        m206=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA')
        assert psnc['status']=='running' and psnc['launch_verified'] is True and psnc['pid']==2502712
        assert m206['resume_authorized'] is False and m206['dispatch_hold']
        assert monitor.load_experiment(str(ROOT),'M209-PSBR')['status']=='done_earlystop'
        work=read(ROOT/'pipeline/research_work.json')
        candidate=next(c for c in work['candidates'] if c.get('experiment_id')=='M210-PSNC')
        assert candidate['stage']=='training' and candidate['native_execution_code_commit']=='43dce016c1a1713c2a5dab7061810dc2efde8954'
        proof_names=['psnc_native_operation_history.json','psnc_preexecution_boundary_review.json',
                     'psnc_primary_ff_before.json','psnc_primary_ff_command.json','psnc_primary_ff_result.json',
                     'psnc_admission_queue_result.json','dispatch_result.json','final_dispatch_independent_review.json']
        for path in [HERE/n for n in proof_names]+[admission_review]:
            item=ref(path)
            if item not in candidate['evidence']: candidate['evidence'].append(item)
        old=next(c for c in work['candidates'] if c.get('experiment_id')=='M209-PSBR')
        item=ref(HERE/'psbr_terminal_archive_review.json')
        if item not in old['evidence']: old['evidence'].append(item)
        btc=next(c for c in work['candidates'] if c.get('experiment_id')=='M211-BTC')
        assert btc['stage']=='blocked' and btc['blocker_kind']=='exclusive_gpu_slot' and btc['native_execution_code_commit'] is None
        btc['blocker']='Only authorized server4 GPU0 now runs verified M210-PSNC2502712, original native1/50 grew0->9/4686 at22:25:10UTC. PSBR naturally completed23/50/.4969. GPU1 remains released; M206 human-paused.'
        btc['retry_after']=(now+timedelta(hours=1)).isoformat()
        btc['unblock_condition']='Fresh current authorization/UUID/occupation/exclusive checks confirm server4 physicalGPU0 genuinely free after the exact active PSNC run ends naturally. Preserve its process/runtime checkout and M206 pause; no GPU1 use.'
        btc['next_action']='Retain frozen BTC00e and original YAML. Prepare its exact operational native worker/adapter without GPU work if useful; real M95/BTC TRAIN2 and original resource tests require a fresh owner/deadline and idle authorizedGPU0. Observe true supported n>=3 inside/outside/leaf paths, common initialization and finite updates. No native PASS/receipt/queue until actual checks pass; no tuning or disturbance of PSNC.'
        item=ref(HERE/'dispatch_result.json')
        if item not in btc['evidence']: btc['evidence'].append(item)
        work['historical_hold_boundary_review']=ref(HERE/'held_boundary_check.json')
        work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':candidate['id'],
            'kind':'native_smoke','result':'passed',
            'command':'python -B -X utf8 '+str(HERE.parent/'tick_42ce600b/psnc_operational_prepare/adapter.py')+' run --mode smoke --target candidate --execution-dir '+str(HERE/'psnc_execution'),
            'observation':'Actual paired native TRAIN2 loss/backward/spectral path and original resource pair reviewed; tested43 admitted and canonical single launch verified native0->9/4686. Efficacy UNKNOWN. Intermediate busy pre-request refusal reconciled; no request replay.',
            'evidence':[ref(HERE/'psnc_execution/smoke_candidate_execution.json'),ref(HERE/'psnc_native_resource_independent_review.json'),ref(HERE/'dispatch_result.json'),ref(final_review)]}
        work['updated_at']=now.isoformat()
        work['next_action']='Monitor exact M210-PSNC2502712/log on server4 GPU0 and natural validation outcome. BTC00e remains prepared, pending operational/native checks on a future freeGPU0. M209 complete23/.4969; M206 user-paused/GPU1 released. No protocol, goal, ban, resource or scheduler changes; no old holds reopened.'
        save(ROOT/'pipeline/research_work.json',work)
        memory='''# Codex Research Memory

## Goal And Phase
- 最新接管a4f7314098ed4dbd8351aa005661583d；actual CODEX_THREAD_ID/target=01a159c5-29ab-7a22-ba7f-e79174757253一致。generated2026-10-23T22:09:39.758328UTC/原deadline23:09:39.758328UTC不延长；前1265已FINALIZED/released并无owned lock/pending才begin。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100、M95.5020/gap.0080、baseline.4894。Phase1 hierarchy→inst_feats→query/masks；supervision辅助，Phase2仍需人类确认。
- 原seed1999/epochs50/maxiters70/YAML/data/optimizer和10G、bs1/lang1/warm20/repeat100、显存+15%条件保持。禁调参/gate/语言路由/大QKV/pointN²/重复注入/新残差/纯数值缩放/旧rejected改名。
- standing pipeline/authorizations/experiment_first_20261021.json(2e892959…)覆盖本项目常规实现、实测、相关版本、安全同步、准入训练；不授权旧hold重开/额外历史修订/受保护恢复/扩资源/改调度。技术准入不证明新颖性或效果。
- 最新人类资源：GPU1暂停给别人；server4 physicalGPU0/max1，grant server4_gpu0_only_20261022_gpu1_pause_105409.json(1871f8c9…)保持。GPU1不查不用，M206不自动恢复/迁移，其他服务器无allowed；Windows Pipeline-cluster_project Disabled。

## Champion And Baseline
- M95仍.5020；M205-MDC自然earlystop26/.4872，M207-HAP固定epoch18完整恢复后自然earlystop31/.5002，M208-HRC自然earlystop31/.4901，均未超M95，不调参重跑或泛化整假设失败。
- HAP原19轮DataLoader AttributeError根因UNKNOWN，原crash、snapshot、授权与prior_runs保留。本次人类epoch18恢复授权已执行完，不是新的restart许可；完整resume log17,244,478B/930e41c6…与archive a7c983…保持。
- M209-PSBR本轮原PID2372658/start35234267两次absent，精确原log完整Train23/50及10次未提升earlystop/best.4969；GPU0双41MiB/util0/no contexts，未signal/递增deathwatch/restart。
- canonical finalize_task(done_earlystop,.4969,23/50)已移出queue/running，candidate complete。低M95.0051、低目标.0131，仅此实现无冠军收益。
- PSBR完整原log30,985,906B、本地/远端SHA一致0204be90…，归档1082a73b…、独审85c9add7…；全证据见本轮psbr_terminal_archive/log_evidence/review。原74f/c85receipt/launch历史保留。

## Active Hypotheses
- M210-PSNC stable hierarchy-parent-spectral-nonlinear-token-coupling，tested/source/queued/live43dce016c1a1713c2a5dab7061810dc2efde8954；原middle FFN父组固定DCT-II共轭非线性Y=X+Qᵀ(f(QX)-f(0))+f(0)，原skip/fine/coarse/rawbanks/FPS/CSORT/HCG/单inst保持。true支持ids1[ids0]、原ids2父组、原xyz+ID顺序与逆散；f0同一次FFN私有零行、不detach、不入原ID。
- 原外置prep tick_e2742b06/psnc_prepare/preparation.json(302432f1…)8源+原YAML冻结；旧prep code_commitnull/base74f不重写。旧d6 disabled包不启用。42ce完整operational包/release/static测试保持，静态catalog不是GPU许可或lease。
- 本轮42ce实际fresh绑定a4f/context3741f249…/pending2978ce3d…/原deadline，stage psnc_a4f73140；诊断candidate包43、公共runtime74f，非旧结果重标。四原请求terminal/rc0，现workers[]/computecontexts空已只读reconcile留证。
- 初次run_pair完成champion后在candidate写请求前busy拒绝；原request ad14828c…reconcile terminal/identity，GPU0随后41MiB/idle/3locksavailable，才只运行缺失三臂，未重放pair/已完成臂、未绕busy/kill/延lease。见psnc_native_operation_history.json。
- PSNC实测原TRAIN2 loss9.536953926/13.908441544，原loss/backward/optimizer各2；两批数据及847 named params/157484090初始化hash49d11a83…与M95相同。每forward64真n>1组，DCT实际执行，原middle LN/FFN各1次、private f0路径、三FFN逐步有限梯度及更新、HCG→inst/ILA/mask观察通过。
- 实际analysis/synthesis只读reference误差0、QtQ max7.614125e-7仅观察，不新增/放宽阈值。原FFN参数/全模型157484090，新增参数0。empty/pad/unsupported/singleton均0，非平凡边界未行使；offdiag和零/仿射/identityQ完整FP32算子控制NOT_RUN。
- 原资源pair同input/handler、bs1/lang1/warm20/repeat100：PSNC9.763425612G vsM959.762532428G；median36.119888vs34.988335ms(+3.2341%)，P9038.128053vs38.878938ms(−1.9313%)。预测allocated936764416vs936763392、reserved同1191182336；观测显存15%条件未触发。cos/index等unsupported全披露，非全算子总成本。
- 四raw语义审69ca0aee…、独审41888b34…(117项)、正式准入独审da241b22…；本轮3standard真实字段、receipt pipeline/admissions/M210-PSNC.json SHA406e160dc9f8194e4a37254d50f3544b7874f23c06415179c7cb569f140c1130，canonical admission/budget通过。prepare原状在execution_preparation_history保留，当前native43/worker/adapter执行字段已真。
- M211-BTC stable hierarchy-parent-binary-tree-complement-composition，冻结source00e2b18c6b8d568a64edb496e6979d766440883c单父43；父组原几何平衡二叉inside/outside补集仅替middle FFN，原cf skip/fine/coarse/rawbanks/单inst保持。新3共享2C→C maps源码推断−131584参数，不称实际更快。
- BTC prep tick_2c25f38f/new_candidate_prepare/preparation.json(c36b4d09…)；589断言/42标签非589实验，独立11+22生产纯树/源码/集成检查保持。inside需真同父n>=3才loss可达，torch/native/TRAIN2/FP32/配对/实际成本/效果均NOT_RUN或UNKNOWN。
- BTC isolated_versions/btc_2c25f38f与PSNC isolated_versions/psnc_d6b400e3保留clean；BTC目前blocked/exclusive_gpu_slot/resumevalidation，先准备专属operationalworker工具，再待PSNC自然结束后的fresh空GPU0实测。无native_execution_commit/receipt/queue，不改冻源或借静态代签。

## Closed Or Failed Directions
- 本轮8旧hold仅元数据/声明655引用签名和13授权path-size-mtime有界复核，正文/重hash/exists-stat0、grant正文0；无新reopen/scope/extra revision。证据本轮held_boundary_check.json b1a99c5c…，非重审旧失败。
- 4supervision scope、2measurement implementation/inconclusive、PCE/RSTR修订上限保持；PCE默认2+额外1已尽/2.861e-6与13.86x，RSTR默认2已尽/R2mean1.027033878e-6>1e-6。禁PCE_R4/RSTR_R3/M201自动恢复；旧RSTR九文件本地提交授权非新修订许可。
- HRC真实TRAIN2/资源诊断及receipt4af51a3a…，PSBR真实TRAIN2/资源及c85ae4fe…保持；HRC9.762532428G，PSBR9.749949516G/−262912params但median+4.6277%/P90+11.5821%，计数低不代表更快。旧完整审查见tick_dfb6440d，不为新结果重跑。

## Running And Queue
- 当前唯一M210-PSNC running server4GPU0/PID2502712，原log train_*_psnc_20261024_062442.log；canonical真实Train1/50从0→9/4686，launch_verifiedtrue，无blind retry。GPU1未查未用，M209已complete移出队列。
- 本轮primary main74f→43只9新增已测文件ff-only，无新commit/重写/force/stash/reset/clean；原28dirty-untracked状态+字节前后保持、index空。见psnc_primary_ff_before/command/result及独审063a3641…。
- canonical safe_sync远端74f→43 ff-only并前后验证真实source，再仅候选YAML按既有映射适配；1次Popen/15transport，单次调用wrapper持3flock覆盖锁内UUID/idle到Popen返回，随后释放，不宣称整个训练持锁。最终dispatch独审见final_dispatch_independent_review.json(308b1cc9…)。
- pinned server4 songcl@192.168.1.115/dl04-MS-7E06，root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1；conda project_cluster/runtime server4_conda_4ca73fba.sh，data /home/songcl/data/data/。keys/strict hostkey，不用旧.137/密码/sudo；PYTHONDONTWRITEBYTECODE=1，根脚本python -B。
- M206-CGCA人工暂停：waiting但paused_by_user/dispatch_hold/resume_authorizedfalse，不计ready，不自动移GPU0。fullsnapshot meta24/best.4952535927295685/noimprove7，last.pth SHAe9b42b2632762dae5ca49d80b3272889809b1ffe3ec30dd377690af8cb2e8e9d；admitted898ff63/runtime43区别保留，无新恢复授权。

## Open Questions And Risks
- 正式PSNC验证效果UNKNOWN，诊断有限loss/梯度/计数准入不代表上涨。M95仍最佳.5020；不为达.5100调seed/schedule/阈值，不用test集选机制。
- PSNC配对只覆盖named参数/两批输入；完整buffer/RNG未逐值配对，跨目标rawbank/map字节不同且原因未量化，不能归因结构收益。真实empty/padding/singleton边界未行使、offdiag和完整FP32控制未跑；QtQ为观察。
- 所有fvcore为原口径含完整unsupported披露，CPU/Python几何排序不全计入；纯TRAIN峰值UNKNOWN，smoke含observer/reference，不等同完整训练显存。原no-cluster baseline此次未重测。
- HAP长期worker根因仍UNKNOWN，不改环境/worker/data规则或自动再恢复。HRC/PSBR早停仅对应各本次实现，不整体否定层级假设；历史失败、授权、源版本和数值限度均保留。
- 任何未知launch先原request/PID/log只读reconcile，不盲重启/删锁。旧PSNC诊断lease仅该tick原deadline可用，未来必须freshowner/assets/idle；BTC未获额外资源。

## Last Tick
- 本轮begin一次monitor/goal/既有派发；design预算2/reserve2/creation2。新确认PSBR23/.4969自然终态、精确全log归档；复用现成PSNC43而非造新候选。
- 真实M95/PSNC TRAIN2+原resource四进程完成；brief busy拒绝后exactreconcile并仅缺失臂继续；四raw/正式准入独审通过；实际本轮1项新准入、1次safe sync+verified launch，0新变体/0新commit/0旧hold重开。
- BTC00e仍准备未测，当前resource等待明确改为PSNC占唯一GPU0；不因compact排除blocked显示reserve0重复造候选。原所有协议/目标/资源/调度及M206pause保持。
- 本轮NOTIFY：PSBR完成且PSNC已验证运行，无需用户新增授权。七段memory/六段report在原ownedlease内保存；收尾实际结果核pipeline/tick_receipts/a4f7314098ed4dbd8351aa005661583d.json和lock/pending消失，写此条时尚未finish，不预签PASS或释放后回写。
'''
        assert len(memory.splitlines())<120
        save(ROOT/'pipeline/codex_memory.md',memory,text=True)
        notes={'actions':[
            '2026-10-24 06:09后双核原PSBR PID不存在及原日志完整23/50早停10次/best.4969，完整30,985,906B日志SHA匹配后canonical归档，无signal/restart，M206保持暂停。',
            '复用PSNC43冻结source/42ce完整工具，fresh本轮owner/context/deadline/GPU0绑定；原run_pair对照完成后busy预检拒绝，经exact原request只读reconcile及fresh idle核验，仅跑缺失三臂，四raw终态rc0且未重放。',
            '实际配对TRAIN2 loss9.536953926/13.908441544、847 named初始化与两批数据一致、真实DCT及三FFN梯度/更新；原资源9.763425612G/157484090params，median+3.2341%/P90−1.9313%，显存15%条件未触发，unsupported与未测控制完整披露；两项独立语义/正式准入审通过。',
            'primary74f→43仅9新增已测文件ff-only，原28状态/字节与index保护通过；真实3standard/receipt406e160d及canonical admission/budget通过并入队。',
            '2026-10-24 06:24:42唯一Popen启动M210-PSNC GPU0，canonical safe_sync远端74f→43及真实source核验；06:25:10原生Train1/50由0→9/4686，PID2502712/launch_verifiedtrue，当前唯一running。启动调用holder持3flock至Popen返回后释放，不宣称全程持锁。',
            '八旧hold仅有界元数据与授权文件元信息检查无变化；BTC00e保留冻结准备/未native，资源等待更新为PSNC；GPU1未查未用、M206暂停、无目标/禁用项/资源/调度变更。'],
            'decisions':[
            'PSBR本次best.4969低M95.5020差.0051，记录本实现无冠军收益，不泛化整机制反证、不调参重跑。M95仍best.5020距目标.5100差.0080。',
            'PSNC按真实技术检查准入并启动正式训练，效果UNKNOWN；保留raw/map字节差异、buffer/RNG未逐值配对、非平凡empty/singleton/padding与offdiag/完整FP32控制未跑、纯TRAIN峰值未知等限度，不夸大检查含义。',
            '后续仅监控原PSNC唯一进程/日志自然结果；BTC准备专属操作工具并待future fresh空闲GPU0实测，现无native PASS或receipt；新常规操作复用standing授权，M206恢复/旧hold重开不获授权。',
            '本轮有终态完成及真实新启动，NOTIFY；收尾由canonical report/finish实判，未提前宣称postflight通过。']}
        save(HERE/'tick_notes.json',notes)
        save(HERE/'round_persistence.json',{'recorded_at':now.isoformat(),'owner_token':TOKEN,
            'tick_attempt_evidence':work['tick_attempt']['evidence'],'final_review':ref(final_review),
            'memory_lines':len(memory.splitlines()),'M210':'running_verified','M209':'done_earlystop23/.4969',
            'M211':'blocked_resource_prepared_native_NOT_RUN','M206':'human_paused','report_or_finish_completed_by_this_script':False})
        print(json.dumps({'memory_lines':len(memory.splitlines()),'notes_saved':True,'current_tick_attempt':'actual_native_smoke_passed_admitted_and_launched','finish_yet':False}))
    finally: lock.close()

if __name__=='__main__': main()
