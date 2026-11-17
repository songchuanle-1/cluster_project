"""Persist concise current memory and canonical report notes under the lease."""
import copy
from pathlib import Path
import repair

c = repair.c
ROOT, OUT = repair.ROOT, repair.OUT
c.guard(180)
memory = ROOT / 'pipeline/codex_memory.md'
with (OUT / 'memory_before.md').open('xb') as stream:
    stream.write(memory.read_bytes())
analysis = c.tick.load(OUT / 'analysis.json')
memory.write_text('''# Codex Research Memory

## Goal And Phase
- Current owner01a159c5-29ab-7a22-ba7f-e79174757253 verified against actual CODEX_THREAD_ID and execution_mode. This is the recovery chat; old01a04987-fdbe-7301-b2f0-f9b6ab60f74c history preserved.
- Tick a3495e4b780741f19b3c15cf3cb3c609 DESIGN; snapshot2026-10-20T22:47:38Shanghai, deadline23:47:38Shanghai. Scientific tests finished; tick finish not yet claimed. Pipeline-cluster_project Disabled; scheduler migration belongs to management chat.
- Prior53f399e3 interrupted owner reconciled: old chat systemError, local and pinned-server4 helpers absent; original-token abort saved receipt, owned lease/pending absence verified before fresh begin. Never replay old tokens.
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85;target.5100;25constraints/11bans. Point/inst_feats hierarchy mainline, supervision auxiliary. Seed1999/epochs50/max_iters70/default10G unchanged.

## Champion And Baseline
- Historical M95 best.5020; original no-cluster baseline.4894; target.5100;gap.0080. M203/FLE,M204/CPA,M201 not automatically restarted.
- Frozen M95epoch16 remains diagnostic only. Fresh same-GPU M95 predict33.578989ms median,36.788974ms P90,9.762532428G standardFVCore,936763392bytes inference peak. No new trained result.

## Active Hypotheses
- hierarchy-cross-leaf-physical-contact-exchange: final authorized R3 FAILED; blocked/numerical_control_failure/failure_scope implementation; scientific_admissionFALSE. Core mechanism not falsified by this implementation failure.
- Real human reply你继续 at2026-10-20 21:41, original user turn01a1598b-5a9e-7b12-bac1-669ba9e2c6da, was inspected and inherited through recovery. It authorized archival repair and exactly one extra SAME-PCE local revision, not commit/push/training. No repeated approval request.
- R2 archival classification repaired: all original5evidence entries/hashes/timestamps preserved, result_evidence contains actual outputs, result nowfailed. Candidate authorization binds current owner/goal/completedR1-R2digest; project default remains2,extra1 consumed. No automaticR4.
- R3 changes only checked-int64 membership/edge dedup, fixedCSR feature-bank pooling order, fixed readback global-mean order, and current-position argument passing. FPS, memberships, exchange/attention formulas, precision and1e-6 unchanged; 9source hashes/config/worker bound to manifest.
- R3native/synthetic graph edges exact(4272 and5/3); original8expression operator outputs/input gradients/row/delete/rotate maximum0. Identity full-source repeats all0.
- R3full-source row language1.9073486328125e-6/inst2.86102294921875e-6; deleted-parent inst2.86102294921875e-6; FAIL frozen1e-6. Unchanged LIA also has row reduction sensitivity; bank repair does not waive it. No further implementation edits.
- R3native loss2forwards/1backward,642finite parameter-gradient tensors, realinst_feats changevsdeleted.5668866634;optimizer_steps0. These establish activity,not efficacy/admission.
- R3predict465.451866ms/P90502.168630ms;20.895% fasterthanR2,13.8614x freshM95. Same counted9.762532428G/peak936763392bytes. Added elementwise/softmax/sum/CSR operations unsupported; equal count is not free compute or ParetoPASS.

## Closed Or Failed Directions
- Preserve originalPCE901.2897ms,R1degreebatched833.8442ms,R2geometry588.4056ms failures. R1input-gradient6.7353e-6;R2full-source2.861e-6. R1/R2/R3 allfailed and immutable; source/protocol input typing does not erase negatives.
- All old bans remain: no gate/language-routing/residual/largeQKV/N2/tuning/repeated-injection/canonical-seed repair/reopenedHDS/FLE/M201/M204. Two older numerical IDs remain scoped research holds; four supervision candidates remain auxiliary holds.
- Bounded independent-route review found no already-supported new mechanism in the inspected PCE evidence(2scenes/8expressions,mixedtaskreadouts,background-dominatedco-labelcontacts). This is NOT global route exhaustion or two independent executed candidates. Do not fabricate a filler candidate/early-stopcertificate.

## Running And Queue
-22:47Shanghai preflightactive0,target3,waiting0;pending7/8,reserve0/2,budget1;operational_issues empty. No queue entries,commit,push,production deployment,optimizer update or training added.
-22:51Shanghai pinned server4 dl04-MS-7E06/192.168.1.115 GPU0/1 UUIDs, idleness and all3locks checked. Diagnostics used authorizedGPU0 exclusively; final diagnostic-release evidence verifies noGPU0contexts and locksavailable. Preserve other jobs; never infer current idleness from this historical snapshot.
- server3GPU1 retained; server3GPU0/server6newdispatch unauthorized. No password file read; strictknownhost SSH keys used. No sudo assumption.

## Open Questions And Risks
- Current realization fails full controls and is13.9xM95; no trained benefit,novelty,populationharm,fulloptimizerpeak,originalbaseline delta or noisefloor claim. Coincidentphysicalcenters explicitly rejected; broader inputcoverage unverified.
- No extraPCErevision remains. SameID can resume only on materiallynewcontrol-preservingevidence; additionalcode revision needs newscopedhuman authorization, not an unchanged repeat of the old request. Independent prediction-blind point-feature diagnosis remains authorized, with its own evidence, not a renamedPCEpatch.
- Generic capacity-gap checker requires executable independent work or a validdesign-cycle stop. This scoped finalrepair has actualprogress but no truthful globalexhaustion certificate; do not invent a resourceblock,phasehold or elapseddeadline to finish. If checker cannot accept honest disposition, abort and recordexactreason.

## Last Tick
- Bundlepipeline/diagnostic_bundles/tick_a3495e4b contains authorization,archivalclassification,preregR3,sourceR2archive,manifest,combinedR3result,freshM95,analysis,release and boundedreview. Oldmemorybackupmemory_before.md retains outdated historical snapshots.
- Fresh M95 initial harness failed because candidate-only graphcheck imported unstagedPCE duringchampionsetup. Originalfailure retained; preregistered harness-only repair skipped thatcheck forchampion, then same counter/input/20warmup/100repeat measurementpassed. No candidate rerun or extra revision.
- Canonicalreportnotes authored before finish; do not claimCOMPLETED until verified receipt/command/release. Update disposition if currentfinishfails,thenabort; no project writes afterrelease. Usage available only in receipt(localwindow,notbilling).
''', encoding='utf-8')
assert len(memory.read_text(encoding='utf-8').splitlines()) < 120
c.save('report_notes.json', {
    'actions': [
        '核实当前owner绑定；旧会话报错结束且无本地/远端PCE helper后，用旧token中止遗留租约并核实释放，再取得本轮新快照。',
        '保留R2全部源码输入、原时间戳和失败结果，修复result_evidence分类；核实原用户21:41的你继续，登记仅同一PCE额外一次的授权，未改变全局修订上限。',
        '预注册并实现R3：仅整数去重、固定特征聚合归约及位置参数传递；AST确认FPS/接触交换/注意力公式未改，冻结worker与原1e-6不变。',
        '在已核实身份/UUID/空闲/独占锁的server4 GPU0执行R3完整测试：图边集及8表达算子误差0，重复误差0；行置换和删边最大2.861e-6仍失败；原生反向642个有限参数梯度。',
        '候选465.45ms/P90502.17ms，对同卡M9533.58ms/P9036.79ms，慢13.86倍；推理峰值显存相同，原FVCore9.7625G漏计新算子，不能声称轻量准入。',
        'M95测试夹具曾因候选专用建图检查导入失败；保留原失败，预注册仅修复夹具后完成同口径测量。全部GPU测试结束后核实上下文为空、三种锁可用。'],
    'decisions': [
        'PCE R1/R2/R3全部失败；本次授权已消耗完，无自动R4，未准入、未提交、未部署、未入队、未开训。',
        '完整控制失败属于实现范围，不能由局部算子PASS、有限梯度或重复误差0改写为科学准入/训练收益；不放宽FPS/注意力/精度/阈值。',
        '有限既有材料未提供一个已被独立数据支持的新主线机制。最后准备槽暂未创建候选，不把空槽当作授权，不声称全局路线穷尽。',
        '旧R3待授权design_cycle已保留到history并撤下当前状态。当前若容量缺口收尾规则不接受诚实的局部工作结果，保存具体校验失败后中止本轮，不伪造新的独立试验或资源/阶段阻塞。']})
print('Current seven-section memory and canonical report notes saved; completion not claimed.')
