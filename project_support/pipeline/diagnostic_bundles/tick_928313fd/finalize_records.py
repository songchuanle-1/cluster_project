"""Persist measured progress and the existing SFC conditional preparation only."""
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-root', action='store_true')
    parser.add_argument('--observation-sha256')
    args = parser.parse_args()
    if not args.execute_root:
        print('DEFAULT_NO_RECORD_MUTATION')
        return
    guard()
    baseline = u.read(HERE / 'protected_assets_before.json')
    u.primary_protection(baseline)
    u.lifecycle_protection(baseline)
    latest = HERE / 'aoc_final_observer/aoc_training_progress_observation.json'
    assert sha(latest) == args.observation_sha256
    observation = u.read(latest)
    assert observation['owner'] == EXPECTED and observation['returncode'] == 0
    assert observation['observation']['runtime_commit'] == u.SOURCE
    samples = observation['observation']['samples']
    first, last = samples[0]['last_native_step'], samples[-1]['last_native_step']
    assert tuple(first) < tuple(last)
    metrics = observation['precise_native_validation']
    assert len(metrics['values']) >= 12 and metrics['best'] == max(metrics['values'])
    registration = u.read(HERE / 'sfc_registration_result.json')
    assert registration['candidate_count'] == 150 and registration['new_candidates'] == 0
    assert registration['code_commit'] == 'c9be548699cd66bf68badff9ae6198a03eafa142'
    local_guard = u.read(HERE / 'sfc_local_parent_guard_observation.json')
    assert local_guard['status'] == 'EXPECTED_UNPROMOTED_PARENT_LOCAL_REFUSAL'
    assert local_guard['transport_calls'] == 0 and local_guard['active_execution_directory_created'] is False
    occupation = u.read(HERE / 'gpu0_occupation_closure_result.json')['result']['evidence']
    proof = u.read(ROOT / occupation['path'])
    assert sha(ROOT / occupation['path']) == occupation['sha256']
    assert proof['token'] == EXPECTED['token'] and proof['snapshot_sha256'] == EXPECTED['context_sha256']
    assert 0 <= (datetime.now(timezone.utc) - datetime.fromisoformat(proof['observed_at'])).total_seconds() < 240
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        u.primary_protection(baseline)
        u.lifecycle_protection(baseline)
        work_path = ROOT / 'pipeline/research_work.json'
        before = sha(work_path)
        work = u.read(work_path)
        old = {c['id']: u.digest(c) for c in work['candidates']}
        assert len(old) == 150
        aoc, fcb, sfc = (next(c for c in work['candidates'] if c['id'] == cid) for cid in (AOC, FCB, SFC))
        assert aoc['stage'] == 'training' and aoc['code_commit'] == u.SOURCE
        assert fcb['stage'] == 'blocked' and fcb['blocker_kind'] == 'exclusive_gpu_slot'
        assert fcb['occupation_evidence'] == occupation
        assert sfc['stage'] == 'validation' and sfc['code_commit'] == registration['code_commit'] and sfc['queued'] is False
        assert sfc['native_execution_code_commit'] is None and sfc['source_parent_commit'] == 'd4d062ef075abfe7cde93d4b4347ce146572762f'
        assert work['tick_attempt']['tick_started_at'] == EXPECTED['generated_at']
        assert work['tick_attempt']['kind'] == 'resource_check' and work['tick_attempt']['result'] == 'blocked'
        now = datetime.now(timezone.utc).isoformat()
        aoc['current_live_observation'] = {
            'recorded_at': now, 'evidence': u.ref(latest),
            'earlier_native_step_growth': u.ref(HERE / 'aoc_progress_observer/aoc_training_progress_observation.json'),
            'original_pid': 3437349, 'original_start_ticks': 90046755,
            'native_step_before': first, 'native_step_after': last,
            'precise_native_validation': copy.deepcopy(metrics),
            'scope': 'Exact original AOC native step growth and completed validation lines in incomplete training. No launch, final efficacy or PES crash-repair claim.'}
        fcb['current_resource_check'] = {
            'recorded_at': proof['observed_at'], 'result': 'ORIGINAL_AOC_ON_SOLE_AUTHORIZED_GPU0',
            'evidence': occupation, 'scope': 'Fresh canonical physical occupation; FCB TRAIN/resources remain NOT_RUN.'}
        sfc['current_parent_guard_observation'] = {
            'evidence': u.ref(HERE / 'sfc_local_parent_guard_observation.json'),
            'result': local_guard['status'], 'transport_calls': 0,
            'scope': 'Local guard correctly refused absent FCB technical receipt before transport or active state. This is not a native model failure.'}
        for candidate, ref in ((aoc, u.ref(latest)), (sfc, u.ref(HERE / 'sfc_local_parent_guard_observation.json'))):
            if ref not in candidate['evidence']:
                candidate['evidence'].append(ref)
        work['updated_at'] = now
        assert all(u.digest(c) == old[c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB, SFC))
        assert all(u.digest(c) == baseline['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB, SFC))
        observed_at = observation['observed_at']
        memory = f'''# Codex Research Memory

## Goal And Phase
- 当前928313fd generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值；实际thread01a159c5-29ab-7a22-ba7f-e79174757253匹配foreground。Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。
- goal0441/standing2e892/GPU0auth94075/SERVERS2583/closure2993保持；只server4物理GPU0/max1，GPU1禁用，Pipeline-cluster_project禁用不改。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50-maxiters70-patience10/10G/bans不变。

## Champion And Baseline
- 最佳仍M95 .5020，baseline .4894。原AOC最新观测{observed_at}，TRAIN{last[0]}/50 {last[1]}/4686，{len(metrics['values'])}次实际验证，partialbest{metrics['best']}/noimprove{metrics['no_improve']}，训练未完成，不作最终效果比较；完整值在当前raw observation。
- 历史DCE正常earlystop27/50/best.4971300959587097已14fea归档a5a9；BEC.5001/24、AEF.495597243309021/23、CRE.4961479902267456/30保留不重启。PES四次partialbest.4211066663265228为崩溃前值。

## Active Hypotheses
- 正式M222-AOC source/primary/runtime0314b932a92a8cc7f67804068ecb1c1f7a5f2e33单父9c；两祖先次序共享binary T diamond差q、fine q与同q两direct truefinepath means，原3LN/3rawskip/HCG/CSORT/单inst保持，novelty/efficacy UNKNOWN。
- AOC原型f7 NULL/ref5c/proof83d/源审c11/native9cf/op e45/release630/协议a041不改。5f3真实manifest77c0/leaseb013/四arm terminal0/common835-155907386匹配；candidate自然TRAIN2 loss9.172385215759277/13.90751838684082，2048真路径/两4096rows cell-GELU/同q均值及wholecell原loss梯度更新经actualpeer e42c。
- 5f3原AOC同口径9.724783692G vs M95 9.762532428G；median35.558438452426344 vs34.864016459323466ms（+1.9918%），P9037.69716832321137 vs36.14520003320649（+4.2937%），alloc930981888 vs936763392（−.61718%），15%条件false；fullunsupported与原bs1lang1/warm20repeat100保留，不称更快/纯TRAIN峰值或有效，本轮不重测。
- AOC真实active4f7/summary048c/smoke449685/resourcesa90bcc/constraints23932、exact9A localff/safe sync0314/receiptbf4426ca/oncecanonicaldispatch76bf唯一Popen/launchpeerb905/strictgrowth5106保留；旧disabled d3错与d66拒签/38ab修正/a1c原件不改，非模型修订。
- M223-FCB原型44c63/manifest95ae/协议3809/源审c91，原code/source/parentNULL/ref9c不回填；scene-local fine×coarse同q双marginal+middle原fineparent组合，原3LN3skip/HCG/单inst保持。isolated d4d062ef075abfe7cde93d4b4347ce146572762f单父0314/proof0a792/peer408dae/nativecc9/op5fcdc/peer1c1db原十activeNULL均未原生。
- FCB的实际AOC0314父/receipt已满足，5f3 localguardbf6a passes/transport0；前916 disabledpromotion556000b5/peer83c1c0f5的13map/raw-review-peerNone/DRAFTTrue保持。两map-GELU2-mean3/wholecore门未改；FCB仅等真实空闲GPU0，无父训练完成/收益门，无技术receipt或queue。
- M224-SFC原true support森林，h0=原3LN(raw)，每轮全邻居同OLDstate degree等权mean→共享cell/GELU→全部活跃receiver单次functional覆盖，双BFS实际组件直径D2或4各恰D轮，完成组件不fakeupdate，final hD直接delta→原3rawskip/HCG/CSORT/单inst。常见同步GNN家族，未证创新/新信息/效力或PES修复。
- SFC原型963dc214/manifest24aef46e/协议c651c4b2/core1a77779e/hpost8a921e4a/原源审caf4c883与NULL/ref0314不改。原35作者软件、410生产AST/list+63集成核是上轮证据；首oracle 1.39e-17累计序差保留，仅oracle orderedleftfold改，生产8hash/协议未改，无epsilon或模型revision。
- 本轮SFC真实isolated c9be548699cd66bf68badff9ae6198a03eafa142唯一父FCBd4，versionproof79e3f7b0/actualsourcepeer d1dbc9df/父边界peer e2593622。exact9A/9blob=原963dc，主线/runtime0314不动；0314→c9为累计18A不能盲ff。
- SFC本轮native/op正式静态封包与独立合并审见sfc_registration_result.json（真实refs），stagevalidation/code c9/parent-runtime d4，十activeNULL、无active执行。original mean/cell/GELU/OLDstate-write/scatter一次透传的局部软件检查非Torch/native/autograd/resources PASS；原wholemodel资源函数/handlers/口径保留。
- SFC mutation-only父门实拒绝：M223-FCB真技术receipt尚无，transport0/无active dir。未来须真FCB技术receipt+实际main及remote d4再复核fresh owner/原deadline/白名单GPU0空闲/三锁；不要求FCB训练完成或涨分。若FCB未提升/main变，保留当前版本，另存真实兼容未改9源并实测，禁sibling或累计18A盲ff。

## Closed Or Failed Directions
- 原PES2265073 TRAIN5/529在原clip_grad_norm→parameters/named_parameters/_named_members发生ValueError too many values to unpack(expected0)，rootcause UNKNOWN/failure_scope inconclusive。完整ownlog5731527B/hash358d、4val partialbest.4211066663265228/noimprove0无早停保留；5f3 terminalpeerf514/canonical crashed archivefab7b5b013ea4e858cf018f37233f6a2，stagecomplete仅归档。
- PES原source9c/技术四门/receipt6fce/launch/checkpoint保持，首observer断言1bd2与实际崩溃dbd471分开；AOC健康不证明PES原因修复。本轮不归档/patch/resume/coldstart；恢复需具体完整checkpoint/版本/runtime/资源计划及所需授权。
- APF/e759 DataLoader before-forward dtype crash、HPC73ba stopped_unknown/CTS14/BFC overlap/触发样本-RNG-上游原因UNKNOWN保留；旧10holds、M206用户暂停/dispatch_hold/noPID、PCE2+extra1/RSTR2已尽/HAP旧grant消费不重开或迁移。

## Running And Queue
- 原AOC PID3437349/start90046755，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aoc_20261029_222527.log；首本轮20:11 TRAIN13 249→258/b465b1d4，最新{observed_at} TRAIN{first[0]} {first[1]}→{last[1]}/4686，原8源/YAML77e/0314/GPU0context保持，未结束。
- launch_verifiedtrue/training_progress，旧dispatch_phase progress_pending不能重派。M206waiting不ready；PES已crashed无live槽。FCB blocked exclusive_gpu_slot/resumevalidation/current canonical owner/snapshot occupation见本轮proof；SFC有条件source/tooling待父真提升与GPU0，非已准入待跑。GPU1不用，无驱逐/信号/调度改变。

## Open Questions And Risks
- AOC差分丢共有语义/仿射fine项取消/b=c零差；FCB双marginal耦合/平均洗平；SFC过平滑/回传重复自信息/共享容量/sum-copy-CPU规划开销未知，原输入本可global，不称新信息或已修瓶颈。
- SFC C256cell131328替1576704、线性MAC上界4N*2C²=171966464与原三FFN上界同；FCB源MAC估多.1048576G，均非wholemodel资源PASS。原wholecore原loss aggregate finite/nonzero+真实整体weight/module更新门保留，逐round/node/map/列/bias零合法，无新增FP32收敛/Jacobian/强制D4多root覆盖门。纯TRAIN峰值和最终收益未知。

## Last Tick
- 本轮0新candidate（仍150）/0模型revision/1 isolated SFC exact9A source commit/0nativearm/0准入/0启动/0归档；已有SFC补真实版本与条件native/op，不把上轮SFC软件suite、历史AOC四臂/启动/PES崩溃再计成果。local父门预期拒绝非模型失败；canonical GPU0当前仍原AOC。
- 28 lifecycle/28 user/status/indexempty/其他147候选、主线/runtime0314保持。fresh setup SOURCE0314，使用原AOC真实PID/start/log与新anchor；post_tick_baseline.json给当前hash基线，不回退PES旧PID/重放dispatch。
- 原AOC继续自然训练；GPU0真实释放后优先FCB原native YAML paired TRAIN2/同口径resources，当轮通过才原安全提升/准入/派发+实际步增。SFC仅在真实FCBd4父提升后按条件运行；不凑额外候选/新门或用户审批。完整report/finish以原token及实际receipt为准。
'''
        assert len(memory.splitlines()) < 120
        notes = {'actions': [
            f'原AOC在{observed_at}确认第{last[0]}/50轮{first[1]}→{last[1]}/4686原生步数增长；已打印{len(metrics["values"])}次验证，partial best {metrics["best"]}，训练未完成。原PID/start/log/0314/8源/YAML/GPU0context不变。',
            '已有M224-SFC精确8模型源+1原YAML保存真实隔离c9be单父FCBd4，9blob与原963dc一致并经实际Git/source独立审；原型NULL/ref0314不回填，主线/runtime0314与AOC不动。',
            'SFC补齐条件native worker/runtime/template及operation adapter的真实source/hash绑定与必要软件验证、独立静态合并审。原mean/cell/GELU/OLDstate覆盖/scatter一次透传，原wholemodel资源口径保留；未执行Torch/native/autograd/resources，十active字段仍NULL。',
            '实际本地父门对缺失FCB技术receipt预期拒绝，transport0/无active目录。fresh canonical GPU0占用证明原AOC仍占卡；其他147候选、28生命周期、28用户路径与主索引保持，本轮无新候选/原生/准入/启动/归档。'],
            'decisions': [
                '目标.5100/冠军M95 .5020不变；AOC当前为未完成训练中间值，SFC静态软件通过不代表原生/资源或最终收益，新颖性未知。PES崩溃根因未定位，不自动恢复。',
                '只server4物理GPU0/max1，GPU1不用，保持原训练。GPU0真实释放且fresh owner/原deadline/source/UUID/资产/三锁通过后优先FCB原paired TRAIN2/resources，真实通过当轮提升/准入/派发并核原生增长。',
                'SFC需真M223-FCB技术receipt+实际main/remote d4才可mutation，不要求父训练完成/涨分。父未提升或main变化就保留当前条件版本，另存真实兼容未改9源并实测，不盲ff累计18A或sibling。',
                '不加FP32/Jacobian/强制D4多组件/逐param正梯度门；不改资源/数据/seed/schedule/禁用项/调度，不恢复旧10holds或M206，无需新增用户授权。']}
        u.save(HERE / 'final_records_intent.json', {'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [AOC, FCB, SFC], 'latest_original_progress': u.ref(latest), 'fresh_occupation': occupation,
            'scope': 'Measured progress, conditional preparation/guard record, memory and notes. No postflight pre-sign or new source/remote/lifecycle/queue/launch action.'})
        guard()
        assert sha(work_path) == before
        u.atomic(work_path, work)
        u.atomic(ROOT / 'pipeline/codex_memory.md', memory, text=True)
        u.save(HERE / 'report_notes.json', notes)
        u.primary_protection(baseline)
        u.lifecycle_protection(baseline)
        post = dict(baseline)
        post.update(owner=EXPECTED, recorded_at=now, candidate_digests={c['id']: u.digest(c) for c in work['candidates']},
                    research_work_sha256=sha(work_path), latest_original_progress=u.ref(latest), fresh_occupation=occupation,
                    conditional_SFC=u.ref(HERE / 'sfc_registration_result.json'))
        u.save(HERE / 'post_tick_baseline.json', post)
        u.save(HERE / 'final_records_result.json', {'owner': EXPECTED,
            'status': 'MEASURED_PROGRESS_AND_EXISTING_SFC_CONDITIONAL_PREPARATION_SAVED_POSTFLIGHT_NOT_YET_RUN',
            'candidate_count': 150, 'new_candidates': 0, 'model_revisions': 0, 'new_commits': 1,
            'native_arms': 0, 'admissions': 0, 'formal_launches': 0, 'terminal_archives': 0,
            'latest_original_progress': u.ref(latest), 'fresh_occupation': occupation,
            'post_tick_baseline': u.ref(HERE / 'post_tick_baseline.json'), 'memory_lines': len(memory.splitlines()),
            'other147_candidates_and28_lifecycle_and28_user_paths_and_index_preserved': True})
        print({'status': 'Measured progress and conditional source/tools saved; postflight not yet run',
               'memory_lines': len(memory.splitlines()), 'baseline': u.ref(HERE / 'post_tick_baseline.json')})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
