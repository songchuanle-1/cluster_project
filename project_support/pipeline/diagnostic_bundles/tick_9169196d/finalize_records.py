"""Save actual AOC progress and one source-only SFC reserve before postflight."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
AOC = 'hierarchy-ancestral-order-commutator-composition'
FCB = 'hierarchy-fine-coarse-complete-bipartite-composition'
SFC = 'hierarchy-synchronous-full-neighbor-composition'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_RECORD_MUTATION')
        return
    guard()
    b = u.read(HERE / 'protected_assets_before.json')
    u.primary_protection(b)
    u.lifecycle_protection(b)
    latest = HERE / 'aoc_final_observer/aoc_training_progress_observation.json'
    assert sha(latest) == '44512391de9fceddabb1233a62e4d1c1465c9df1a5c4c15ea0ad9c15cfed16c6'
    ob = u.read(latest)
    assert ob['owner'] == EXPECTED and ob['returncode'] == 0 and ob['observation']['runtime_commit'] == u.SOURCE
    samples = ob['observation']['samples']
    assert samples[0]['last_native_step'] == [5, 1011] and samples[-1]['last_native_step'] == [5, 1019]
    metrics = ob['precise_native_validation']
    assert metrics['values'] == [0.33546924591064453, 0.376327246427536, 0.41503071784973145, 0.42323046922683716]
    assert metrics['best'] == 0.42323046922683716 and metrics['no_improve'] == 0
    assert u.read(HERE / 'sfc_registration_result.json')['candidate_count'] == 150
    assert u.read(HERE / 'fcb_promotion_record_result.json')['native_arms'] == 0
    occupation = u.read(HERE / 'gpu0_occupation_closure_result.json')['result']['evidence']
    proof = u.read(ROOT / occupation['path'])
    assert sha(ROOT / occupation['path']) == occupation['sha256'] == '699cef0f3e98ad1e47cf1c99a6a2121950f099535dbaf13c131cab70f5795d9e'
    assert proof['token'] == EXPECTED['token'] and proof['snapshot_sha256'] == EXPECTED['context_sha256']
    assert 0 <= (datetime.now(timezone.utc) - datetime.fromisoformat(proof['observed_at'])).total_seconds() < 240
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        u.primary_protection(b)
        u.lifecycle_protection(b)
        path = ROOT / 'pipeline/research_work.json'
        before = sha(path)
        work = u.read(path)
        old = {c['id']: u.digest(c) for c in work['candidates']}
        assert len(old) == 150
        c = next(c for c in work['candidates'] if c['id'] == AOC)
        f = next(c for c in work['candidates'] if c['id'] == FCB)
        s = next(c for c in work['candidates'] if c['id'] == SFC)
        assert c['stage'] == 'training' and c['code_commit'] == u.SOURCE
        assert f['stage'] == 'blocked' and f['blocker_kind'] == 'exclusive_gpu_slot' and f['occupation_evidence'] == occupation
        assert s['stage'] == 'implementation' and s['code_commit'] is None and s['queued'] is False
        assert work['tick_attempt']['tick_started_at'] == EXPECTED['generated_at']
        assert work['tick_attempt']['kind'] == 'resource_check' and work['tick_attempt']['result'] == 'blocked'
        now = datetime.now(timezone.utc).isoformat()
        c['current_live_observation'] = {
            'recorded_at': now, 'evidence': u.ref(latest),
            'earlier_native_step_growth': u.ref(HERE / 'aoc_progress_observer/aoc_training_progress_observation.json'),
            'original_pid': 3437349, 'original_start_ticks': 90046755,
            'native_step_before': [5, 1011], 'native_step_after': [5, 1019],
            'precise_native_validation': copy.deepcopy(metrics),
            'scope': 'Exact unchanged strict observer of original AOC process/log/source; real native step growth and four completed validation lines, training incomplete. No final efficacy or repair of PES root cause inferred.'}
        if u.ref(latest) not in c['evidence']:
            c['evidence'].append(u.ref(latest))
        f['current_resource_check'] = {
            'recorded_at': proof['observed_at'], 'result': 'ORIGINAL_AOC_ON_SOLE_AUTHORIZED_GPU0', 'evidence': occupation,
            'scope': 'Canonical fresh physical occupation only; FCB TRAIN/resources remain NOT_RUN.'}
        work['updated_at'] = now
        assert all(u.digest(x) == old[x['id']] for x in work['candidates'] if x['id'] not in (AOC, FCB))
        assert all(u.digest(x) == b['candidate_digests'][x['id']] for x in work['candidates'] if x['id'] not in (AOC, FCB, SFC))
        memory = f'''# Codex Research Memory

## Goal And Phase
- 当前9169196d generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值，thread01a159c5-29ab-7a22-ba7f-e79174757253实配foreground；Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。
- goal0441/standing2e892/GPU0auth94075/SERVERS2583/closure2993不动；仅server4物理GPU0/max1，GPU1禁用，后台Pipeline-cluster_project禁用不改。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50-maxiters70-patience10/10G与bans保持。

## Champion And Baseline
- 最佳仍M95 .5020，baseline .4894；原AOC最新UTC16:26:27 TRAIN5/50 1019/4686，4次val[.33546924591064453,.376327246427536,.41503071784973145,.42323046922683716]，partialbest.42323046922683716/noimprove0，训练未完成，不作最终效果比较。
- 历史DCE正常earlystop27/50/noimprove10/best.4971300959587097已14fea归档a5a9；BEC.5001/24、AEF.495597243309021/23、CRE.4961479902267456/30不重启/重复归档。PES崩溃时4val partialbest.4211066663265228非完成效果。

## Active Hypotheses
- 唯一正式M222-AOC source/primary/runtime0314b932a92a8cc7f67804068ecb1c1f7a5f2e33单父9c；两祖先次序共享binaryT diamond差q、fine q和原truefinepath两directmeans，原3LN3rawskip/HCG/CSORT/单inst保持，novelty/efficacy UNKNOWN。
- 原f7 NULL/ref5c/proof83d/c11/native9cf/op e45/release630/协议a041不改。前轮5f3 actualmanifest77c0/leaseb013/四arm terminal0，common动态835/155907386匹配；candidate2loss9.172385215759277/13.90751838684082，2048真路径/two4096-row cell-GELU/two sameqmeans/wholecell原loss梯度与weight-module更新经actualpeer e42c。
- 前轮AOC同口径9.724783692G vs M95 9.762532428G；median35.558438452426344 vs34.864016459323466ms（+1.9918%），P9037.69716832321137 vs36.14520003320649（+4.2937%），alloc930981888 vs936763392（−.61718%），15%条件false。fullunsupported/原bs1lang1/warm20repeat100保留，不称更快/纯TRAIN峰值或最终有效，本轮不重测。
- 前轮active4f7/summary048c/smoke449685/resourcesa90bcc/constraints23932、exact9A localff与safe sync0314、receiptbf4426ca、oncecanonicaldispatch76bf唯一Popen/launchpeerb905/strictgrowth5106真实链保持。原d3 shaaoc错/拒签d66a/38ab修正及a1c disabled原件保留，不是模型修订。
- M223-FCB原型44c63/manifest95ae/协议3809/源审c91不改，原code/source/actualparentNULL/ref9c不回填；真scene-local fine×coarse q双marginal+middle原fineparent组合，原3LN3skip/HCG单inst保持，效力新颖性未知。
- FCB实际isolated d4d062ef075abfe7cde93d4b4347ce146572762f单父0314/proof0a792/peer408dae，原nativecc9/op5fcdc/peer1c1db十activeNULL未原生。实际AOC0314父/receipt已满足、前轮localguardbf6a passes/transport0；本轮新增disabledpromotion556000b5/peer83c1c0f5，13map/raw-review-peerNone/DRAFTTrue，两map-GELU2-mean3/wholecore门与真实producer keys核，非native PASS。
- 新M224-SFC CID hierarchy-synchronous-full-neighbor-composition：每true support森林组件h0=原LN(raw)，每轮对全部真邻居OLDstate取degree等权mean，再共享T同步覆盖全部活跃receiver；两BFS真直径D2或4各恰D轮，完成组件不fakeupdate，最终hD直接作delta→原3rawskip/HCG/单inst。不是PES单边有序覆盖，属于常见同步GNN家族，无已证新信息/创新/效果或PES修复声称。
- SFC原型963dc214/manifest24aef46e/协议c651c4b2/core1a77779e/hpost8a921e4a冻结，精确8源+原YAML/21map（含软件首负面）；作者35软件核、独立410生产AST/list+63集成核/peercaf4c883通过；code/source/actualparentNULL/ref0314，stageimplementation/未入队，Torch/autograd/native/resources均NOT_RUN。
- SFC首软件oracle一middle标量1.39e-17差的run1源码/负面/诊断保留，仅oracle builtin sum改原ID orderedleftfold，生产8源hash与首次失败相同，无epsilon/选样/模型或协议变化；FCB producer-key checker首漏AST keyword失败也保留，均为软件检查器问题，不计模型revision或native失败。

## Closed Or Failed Directions
- 原PES2265073 TRAIN5/529参数迭代ValueError: too many values to unpack(expected0)，原ownlog5731527B/hash358d完整；4val partialbest.4211066663265228/noimprove0、无早停，rootcause UNKNOWN/failure_scope inconclusive。前轮terminalpeerf514/canonicalcrashed archivefab7b5b013ea4e858cf018f37233f6a2，stagecomplete仅终态归档，本轮不重归档/恢复。
- 原PES source9c/技术四门/receipt6fce/launch/checkpoint保留，首proc断言观察失败1bd2与实际crash证据dbd471分开。AOC当前健康不等于定位/修复PES原因；任何恢复需具体完整checkpoint/版本/运行时/资源计划和所需授权，不自动resume/coldstart。
- APF/e759旧DataLoader before-forward dtype crash、HPC73ba stopped_unknown/CTS14/BFC overlap及触发样本/RNG/上游原因UNKNOWN；旧10hold、M206用户暂停/dispatch_hold/noPID、PCE2+extra1/RSTR2已尽/HAP旧授权消费均不重开或迁移。

## Running And Queue
- 原AOC PID3437349/start90046755，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aoc_20261029_222527.log；本轮16:07 TRAIN4 2889→2897初审3f3f，最新16:26:24→27 TRAIN5 1011→1019/4686/log5578647→5580679/proof44512391，原8源/YAML77e/0314/GPU0context保持，4val partial如上。
- queue launch_verifiedtrue/training_progress但旧dispatch_phase progress_pending不能重派；M206waiting不ready，PES已crashed无live槽。FCB blocked exclusive_gpu_slot/resumevalidation，当前canonicalproof699cef0f绑定本owner/snapshot且原AOC计算PID真实占卡；SFCimplementation source-only，GPU1不用/无信号/驱逐。

## Open Questions And Risks
- AOC差分丢共有语义/仿射fine项取消/b=c零差；FCB双marginal耦合/平均洗平；SFC过平滑/反馈重复自信息/共享map容量与sum/copy/CPU规划开销未知，原输入本可global，不称新信息或已修瓶颈。
- SFC C256 cell131328替1576704，线性MAC上界4N*2C²=171966464与原三FFN上界同；FCB源MAC估多.1048576G，均非wholemodel10G/延迟/显存PASS。纯TRAIN峰值和最终收益未知；未来only wholecore原loss aggregate finite/nonzero+整体真实更新，逐round/node/map/列/bias零合法，无新FP32收敛/守恒/Jacobian/多root覆盖门。

## Last Tick
- 本轮新增1个SFC软件储备（150ID），0模型revision/0新commit/0nativearm/0准入/0启动/0新归档；FCB只补disabled后处理工具，AOC原训练健康继续，不把前轮PES崩溃/AOC四臂和启动再算本轮成果。
- 主线/runtime0314、user28/status/indexempty、28生命周期文件与其他147旧candidate保持；新SFC仍NULL/ref0314无Git版本。最新baseline见post_tick_baseline.json；未来freshsetup SOURCE保持0314、使用AOC实际PID/start/log/新anchor，不回退PES旧PID或重放旧dispatch。
- 先监控原AOC自然完成，GPU0真实释放后优先原FCB d4 pairedTRAIN2/resources及当时source/receipt/UUID/assets/三锁/原deadline复核；SFC后续按实际兼容主线版本化与native工具，禁盲siblingff。不凑第二候选或新门，完整report/finish按原token收尾，结果以receipt为准。
'''
        assert len(memory.splitlines()) < 120
        notes = {'actions': [
            '上海10月30日00:26:24至27，原AOC第5/50轮1011→1019/4686，已打印4次验证，partial best0.42323046922683716/noimprove0；原PID/start/log/8源/YAML和GPU0 context保持，训练未完成。',
            '优先补齐已有FCB未来四actual结果之后的五个disabled promotion helpers，真实d4/parent0314/nativecc9/op5fcdc绑定，producer-schema和独立静态审通过；actual refs全None/DRAFTTrue，未激活、原生、准入或改队列。',
            '新增唯一M224-SFC同步全邻居状态组合原型：真森林组件按实际直径2或4轮同步读OLDstates、degree等权邻居均值、共享cell覆盖；精确8模型+原YAML，35作者软件核及410独立生产AST/list和63集成核通过。code/source/actual-parent仍NULL，Torch/原生/资源未测。',
            '保留SFC首软件oracle累计序1.39e-17差与修正证据，无epsilon/生产模型/协议改动；当轮freshcanonical GPU0实际看到原AOC计算PID，FCB继续等卡。28账/28用户/index/其他147旧candidate保持，无GPU1或调度改动。'],
            'decisions': [
                '最佳仍M95 .5020，目标.5100；当前AOC值是未完成训练的partial，软件检查不是训练收益、新颖性或资源PASS。历史PES崩溃已归档，根因UNKNOWN不自动恢复。',
                '原AOC继续；唯一授权GPU0自然释放且fresh owner/原deadline/source/UUID/assets/三锁通过后，优先FCB原自然TRAIN2与同口径resources，实过才准入派发并核原生增长。SFC按届时真实兼容main版本化，不预签父或盲ff。',
                'SFC为常见同步GNN家族中的待测结构图，未发现当前明确ban/同DAG阻断不等于论文创新成立。保留过平滑/重复自信息/容量/开销风险，原wholecore训练性门和预算不变，不加数值门。',
                '本轮只准备一个新原型，不凑2候选；不改资源/禁用项/数据/seed/schedule/旧失败与授权，不恢复M206或旧10hold；无需用户新增授权。']}
        u.save(HERE / 'final_records_intent.json', {'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [AOC, FCB], 'latest_original_progress': u.ref(latest), 'fresh_occupation': occupation,
            'scope': 'Measured observations, memory and report notes only; no new native/source/lifecycle/queue/launch action or pre-signed postflight.'})
        guard()
        assert sha(path) == before
        u.atomic(path, work)
        u.atomic(ROOT / 'pipeline/codex_memory.md', memory, text=True)
        u.save(HERE / 'report_notes.json', notes)
        u.primary_protection(b)
        u.lifecycle_protection(b)
        post = dict(b)
        post.update(owner=EXPECTED, recorded_at=now, candidate_digests={c['id']: u.digest(c) for c in work['candidates']},
                    research_work_sha256=sha(path), latest_original_progress=u.ref(latest), fresh_occupation=occupation,
                    source_only_SFC=u.ref(HERE / 'sfc_registration_result.json'))
        u.save(HERE / 'post_tick_baseline.json', post)
        u.save(HERE / 'final_records_result.json', {'owner': EXPECTED,
            'status': 'ACTUAL_PROGRESS_AND_ONE_SFC_SOFTWARE_RESERVE_SAVED_POSTFLIGHT_NOT_YET_RUN',
            'candidate_count': 150, 'new_candidates': 1, 'model_revisions': 0, 'new_commits': 0,
            'native_arms': 0, 'admissions': 0, 'formal_launches': 0, 'terminal_archives': 0,
            'latest_original_progress': u.ref(latest), 'fresh_occupation': occupation,
            'post_tick_baseline': u.ref(HERE / 'post_tick_baseline.json'), 'memory_lines': len(memory.splitlines()),
            'other147_candidates_and28_lifecycle_and28_user_paths_and_index_preserved': True})
        print({'status': 'Actual progress and one software prototype saved; postflight not yet run',
               'memory_lines': len(memory.splitlines()), 'baseline': u.ref(HERE / 'post_tick_baseline.json')})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
