"""Persist current measured progress and bounded preparation, before postflight."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
PES = 'hierarchy-palindromic-euler-state-composition'
AOC = 'hierarchy-ancestral-order-commutator-composition'
FCB = 'hierarchy-fine-coarse-complete-bipartite-composition'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    ap.add_argument('--occupation-label', required=True)
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_RECORD_MUTATION')
        return
    guard()
    baseline = u.read(HERE / 'protected_assets_before.json')
    u.primary_protection(baseline)
    u.lifecycle_protection(baseline)
    observation_path = HERE / 'pes_final_observer/pes_training_progress_observation.json'
    assert sha(observation_path) == 'a0f376bfedf71fb98106f58d901eb80bc03876ac73d01a94d0c236cc167aea9a'
    observation = u.read(observation_path)
    assert observation['owner'] == EXPECTED and observation['returncode'] == 0
    raw = observation['observation']
    assert raw['runtime_commit'] == u.SOURCE
    assert raw['identity_before'] == raw['identity_after']
    assert raw['identity_before']['pid'] == 2265073
    assert raw['identity_before']['start_ticks'] == '88396735'
    samples = raw['samples']
    assert samples[0]['last_native_step'] == [1, 4449]
    assert samples[-1]['last_native_step'] == [1, 4454]
    assert samples[-1]['log_size'] > samples[0]['log_size']
    assert all(observation['precise_native_validation'][k] is None for k in ('values', 'best', 'no_improve'))
    assert '2265073' in [x.split(',')[0].strip() for x in raw['GPU0_contexts'].splitlines()]
    assert u.read(HERE / 'fcb_registration_result.json')['candidate_count'] == 149
    assert u.read(HERE / 'aoc_promotion_record_result.json')['native_arms'] == 0
    collected = u.read(HERE / ('gpu0_occupation_' + a.occupation_label + '_result.json'))
    assert collected['owner'] == EXPECTED
    result = collected['result']
    assert result['candidate_ids'] == [AOC]
    assert result['state']['busy_gpu_ids'] == [0] and result['state']['idle_gpu_ids'] == []
    occupation = result['evidence']
    proof = u.read(ROOT / occupation['path'])
    assert sha(ROOT / occupation['path']) == occupation['sha256']
    assert proof['token'] == EXPECTED['token'] and proof['snapshot_sha256'] == EXPECTED['context_sha256']
    assert (datetime.now(timezone.utc) - datetime.fromisoformat(proof['observed_at'])).total_seconds() < 240
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
        assert len(old) == 149
        p = next(c for c in work['candidates'] if c['id'] == PES)
        c = next(c for c in work['candidates'] if c['id'] == AOC)
        f = next(c for c in work['candidates'] if c['id'] == FCB)
        assert p['stage'] == 'training' and p['code_commit'] == u.SOURCE
        assert c['stage'] == 'blocked' and c['blocker_kind'] == 'exclusive_gpu_slot'
        assert c['occupation_evidence'] == occupation
        assert f['stage'] == 'implementation' and f['code_commit'] is None and f['queued'] is False
        assert work['tick_attempt']['tick_started_at'] == EXPECTED['generated_at']
        assert work['tick_attempt']['kind'] == 'resource_check' and work['tick_attempt']['result'] == 'blocked'
        now = datetime.now(timezone.utc).isoformat()
        p['current_live_observation'] = {
            'recorded_at': now, 'evidence': u.ref(observation_path),
            'original_pid': 2265073, 'original_start_ticks': 88396735,
            'native_step_before': [1, 4449], 'native_step_after': [1, 4454],
            'precise_native_validation': copy.deepcopy(observation['precise_native_validation']),
            'scope': 'Actual unchanged strict observer of original formal PES process/log/source and native step growth; no validation printed, no new launch or efficacy claim.'}
        if u.ref(observation_path) not in p['evidence']:
            p['evidence'].append(u.ref(observation_path))
        c['current_resource_check'] = {
            'recorded_at': proof['observed_at'], 'result': 'ORIGINAL_PES_ON_SOLE_AUTHORIZED_GPU0',
            'evidence': occupation,
            'scope': 'Canonical fresh physical occupation only; AOC native/resources NOT_RUN.'}
        work['updated_at'] = now
        assert all(u.digest(x) == old[x['id']] for x in work['candidates'] if x['id'] not in (PES, AOC))
        assert all(u.digest(x) == baseline['candidate_digests'][x['id']] for x in work['candidates'] if x['id'] not in (PES, AOC, FCB))
        memory = f'''# Codex Research Memory

## Goal And Phase
- 当前f8d84d12 generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值；实际thread01a159c5-29ab-7a22-ba7f-e79174757253匹配foreground。Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。
- goal0441/standing2e892/GPU0auth94075/SERVERS2583/closure2993均不改；仅server4物理GPU0/max1，GPU1禁用。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50-maxiters70-patience10/10G口径/bans保持，后台Pipeline-cluster_project禁用不改。

## Champion And Baseline
- 最佳仍M95 .5020；历史DCE正常earlystop27/50/noimprove10，exactbest.4971300959587097，低M95 .0048699040412903。已在前轮14fea canonical归档a5a9，不是本轮新完成或失败，不重归档/重启。
- 当前PES截至UTC10:34:41首轮尚无验证输出，values/best/noimprove均None非0；早期训练步与技术准入不能证明效果。BEC.5001/24、AEF.495597243309021/23、CRE.4961479902267456/30历史保持。

## Active Hypotheses
- 正式M221-PES source/primary/runtime9c42fdc4e9168acec18980d782ee9c163e043bb7；原型0c3e/协议ef7f/nativef2fc/op7124/receipt6fce及前轮实际四arm/独审2b71保持。真实Euler+reverse4E receiver-only persistentcurrentstate、逆游不reset；原3LN/rawskip/HCG/CSORT/单inst不变，novelty/efficacy UNKNOWN。
- PES前轮两自然TRAIN/common835/155907386/hash5c80配对，loss9.176618576049805/13.907245635986328及wholecell原loss梯度/真实更新通过。资源9.758338124G vs9.762532428G、median45.457765 vs33.915601ms（+34.0320%）、P9049.526253 vs37.252200ms（+32.9485%）、alloc930981888 vs936763392（−.61718%）；15%条件false，纯TRAIN峰值未知，不称更快。本轮不重测。
- M222-AOC source0314b932a92a8cc7f67804068ecb1c1f7a5f2e33单父9c，原f7 NULL/ref5c/proof83d/c11/native9cf/op e45/release630保持。共享binary T的祖先两顺序diamond差q；fine q与原truefinepath直接uppermeans，原3LN/3skip/HCG单inst不动。父9c/PES技术receipt已就绪，原生与resources仍NOT_RUN。
- AOC本轮新增disabled五promotion helpers：原d3a34有shaaoc≠真实worker shapes接口错，peer d66a9拒签，原包/失败保留；新sibling38abf859只修schema并10静态核/独审，DRAFTTrue/actual raw-review-peerNone。不是模型修订、native失败或nativePASS；当前ref见aoc_promotion_record_result.json。
- 新M223-FCB CID hierarchy-fine-coarse-complete-bipartite-composition，原型44c63ca1/manifest95ae9872/协议3809eecd；每scene真fineF×真coarseC共享vectorq，fine/coarse取同q两侧等权marginal，middle沿原fineparent均值再双元组合；真支持来自原point→fine→mid→coarse，去重fine、无跨scene，原raw/3LN3skip/HCG单inst保持。
- FCB精确8模型+原YAML9source冻结，33作者生产AST/list软件核及独立最终源/软件审通过（具体ref见fcb_registration_result.json），code/source/actualparent仍NULL、参考9c。stageimplementation未入队；Torch/autograd/native/resources/效力/新颖性未测。先推进AOC，再按届时实际兼容main版本化，不盲siblingff。

## Closed Or Failed Directions
- APF/e759原DataLoader before-forward dtype crash、HPC73ba stopped_unknown/CTS14/BFC overlap及触发样本RNG/上游cause UNKNOWN保持；不因后续成功声称旧公共loader已修复。
- 旧10hold/146其他历史候选保持；M206用户暂停/dispatch_hold/noPID，PCE2+extra1/RSTR2已尽/HAP旧授权消费，无GPU0迁移或自动恢复。AOC私有准备脚本schema修正不计模型implementation revision。

## Running And Queue
- 唯一原PES PID2265073/start88396735，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pes_20261029_175027.log；本轮早期1/2325→2330，最新UTC10:34:38→41 TRAIN1/50 4449→4454/4686，native/log增长proofa0f376/源码9c8+部署YAML77e/原GPU0context保持，无val。
- queue launch_verifiedtrue/training_progress但dispatch_phase旧progress_pending，不能重放；M206waiting不ready。AOC blocked exclusive_gpu_slot/blocked_from validation，fresh canonical当轮physical GPU0占用proof见final_records_result.json，仍原PES占卡；FCBimplementation。GPU1不用，未驱逐/重启现有任务。

## Open Questions And Risks
- PES长链遗忘/串行kernel与收益未知，已实测慢约34%且不加新latency门。AOC差分可能丢共有语义/仿射fine项取消/b=c时q0；FCB同q双marginal存在代数耦合、全局平均洗平特征，原输入本可已global，不能称新信息或已修瓶颈。
- FCB线性MAC源估较原多.1048576G，不是wholemodel10G/延迟/显存PASS。未来只wholecore原loss梯度aggregate finite/nonzero与整体真实更新门；逐map/列/row/pair/bias零合法描述，不新增FP32守恒/Jacobian/逐map正性/多root覆盖门。

## Last Tick
- 本轮1新FCB软件储备/0模型修订/0新commit/0nativearm/0准入/0启动/0新归档，149ID；PES正常继续，不把历史DCE或前轮PES四arm重复算本轮成果。
- 本轮fresh canonical GPU0 resource_check绑定原owner/context并记真实busy，FCB原型软件证据已归候选；其他146候选、26生命周期文件、28用户字节/status/indexempty/source9c保持。原d3静态错保留、38ab仅disabled准备。
- 当前真实基线见post_tick_baseline.json（HEAD9c/26账/28用户/index/149候选digest/PES9source）。后续fresh tick复用该actual版本与原PES观察器，不回退5c/DCE旧PID；先AOC native，FCB后续兼容版本/工具。完整六段report/finish由root按原token完成，实际收尾以receipt为准。
'''
        assert len(memory.splitlines()) < 120
        notes = {
            'actions': [
                '上海18:34:38至18:34:41，原M221-PES在server4 GPU0的第1/50轮从4449增长到4454/4686，原PID/start/log/source/部署YAML保持；首轮验证尚未打印，mIoU/best/noimprove未知。',
                '优先补齐已有AOC原生检查后的disabled promotion五helper准备；发现原静态schema shapes被误替为shaaoc，原包与拒签审保留，新sibling只纠正接口并做真实worker键契约静态核及独审。不是模型/native修订，实际raw/review仍None，未激活或准入。',
                '新增唯一M223-FCB源原型：同scene真实fine×coarse向量消息，两个端点取同消息的均值，middle再沿原fineparent组合。精确8独立模型源和原YAML，33作者生产forward软件核及独立源/软件检查通过；尚未Torch/autograd/native TRAIN或resources，code/source/actual-parent仍NULL。',
                '本轮fresh canonical GPU0-only物理占用查询绑定当前owner/context，真实原PES计算PID仍占唯一授权卡；AOC原生检查保持等待。未使用GPU1、未停止或重放任何训练；原主线9c、26账、28用户字节和index保持。'],
            'decisions': [
                '项目最佳仍M95 .5020，目标.5100，差.0080；PES尚无验证值，不能把软件检查或技术准入当成涨点。DCE .4971300959587097是前轮已正常归档的历史结果，本轮不重复归档。',
                'PES继续原任务，AOC排在原生检查准备的最前；仅待GPU0自然释放且fresh owner/原deadline/source/UUID/三锁复核通过后执行原paired自然TRAIN2与同口径resources，实过才当轮准入派发并核原生步增。',
                'FCB属于跨层dense bipartite message-passing家族的一种待测计算图，未发现现有明确同图/ban阻断，不等于论文新颖性成立或收益可行。双marginal耦合/全局洗平/源MAC估算风险保留，不加数值门。只准备这一条，不凑额度。',
                'AOC disabled准备脚本接口纠正不消耗模型修订，不改既有native/op/模型/协议。FCB下一步按届时实际兼容主线版本化与原生工具准备；旧10hold/M206暂停/资源边界/调度不动，无需用户新增授权。']}
        u.save(HERE / 'final_records_intent.json', {
            'owner': EXPECTED, 'recorded_at': now, 'research_work_before_sha256': before,
            'changed_candidate_ids': [PES, AOC], 'latest_original_progress': u.ref(observation_path),
            'fresh_occupation': occupation, 'scope': 'Actual observation, memory and notes only; no native/queue/source/launch operation or pre-signed postflight.'})
        guard()
        assert sha(work_path) == before
        u.atomic(work_path, work)
        u.atomic(ROOT / 'pipeline/codex_memory.md', memory, text=True)
        u.save(HERE / 'report_notes.json', notes)
        u.primary_protection(baseline)
        u.lifecycle_protection(baseline)
        post = dict(baseline)
        post.update(recorded_at=now, owner=EXPECTED, candidate_digests={x['id']: u.digest(x) for x in work['candidates']},
                    research_work_sha256=sha(work_path), latest_original_progress=u.ref(observation_path),
                    source_only_FCB=u.ref(HERE / 'fcb_registration_result.json'), fresh_occupation=occupation)
        u.save(HERE / 'post_tick_baseline.json', post)
        u.save(HERE / 'final_records_result.json', {
            'owner': EXPECTED, 'status': 'CURRENT_PROGRESS_AND_PREPARATION_SAVED_POSTFLIGHT_NOT_YET_RUN',
            'candidate_count': 149, 'new_candidates': 1, 'model_revisions': 0, 'new_commits': 0,
            'native_arms': 0, 'admissions': 0, 'formal_launches': 0, 'terminal_archives': 0,
            'latest_original_progress': u.ref(observation_path), 'fresh_occupation': occupation,
            'post_tick_baseline': u.ref(HERE / 'post_tick_baseline.json'), 'memory_lines': len(memory.splitlines()),
            'other146_candidates_and26_ledgers_and28_user_paths_and_index_preserved': True})
        print(json.dumps({'status': 'Measured progress and one software reserve saved; postflight not yet run',
                          'memory_lines': len(memory.splitlines()), 'new_candidates': 1, 'native_arms': 0,
                          'baseline': u.ref(HERE / 'post_tick_baseline.json')}))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
