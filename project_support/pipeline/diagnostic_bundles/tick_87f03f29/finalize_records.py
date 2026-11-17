"""Save exact original progress and one source-only ELC reserve before finish."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
AOC = 'hierarchy-ancestral-order-commutator-composition'
FCB = 'hierarchy-fine-coarse-complete-bipartite-composition'
CID = 'hierarchy-undirected-edge-state-line-graph-composition'
EXP = 'M225-ELC'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-root', action='store_true')
    args = parser.parse_args()
    if not args.execute_root:
        print('DEFAULT_NO_STATE_CHANGE')
        return
    guard()
    baseline = u.read(HERE / 'protected_assets_before.json')
    u.primary_protection(baseline)
    u.lifecycle_protection(baseline)
    obs_path = HERE / 'aoc_progress_observer/aoc_training_progress_observation.json'
    assert sha(obs_path) == '097c490798290db74b0c9114a36b72970ac85d9684f5c6af6a3368095804e144'
    obs = u.read(obs_path)
    assert obs['owner'] == EXPECTED and obs['returncode'] == 0 and obs['observation']['runtime_commit'] == u.SOURCE
    samples = obs['observation']['samples']
    assert samples[0]['last_native_step'] == [21, 1980] and samples[-1]['last_native_step'] == [21, 1989]
    metrics = obs['precise_native_validation']
    assert len(metrics['values']) == 20 and metrics['best'] == 0.5000720620155334 and metrics['no_improve'] == 0
    progress_peer = HERE / 'current_aoc_wait_independent_review.json'
    assert sha(progress_peer) == '510576d00ad5783d3f788499fb4b71449677d1876bb96fade01293586a0945c3'
    assert u.read(progress_peer)['material_concerns'] == []
    registration = u.read(HERE / 'new_variant_registration_result.json')
    assert registration['candidate_id'] == CID and registration['experiment_id'] == EXP and registration['candidate_count'] == 151
    assert all(registration[k] is None for k in ('code_commit', 'source_commit', 'source_parent_commit'))
    u.check_refs([registration['source_preparation'], registration['independent_review']])
    prep = u.read(ROOT / registration['source_preparation']['path'])
    assert prep['candidate_id'] == CID and prep['base_reference_commit'] == u.SOURCE
    assert all(prep[k] is None for k in ('code_commit', 'source_commit', 'source_parent_commit'))
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
        path = ROOT / 'pipeline/research_work.json'
        before = sha(path)
        work = u.read(path)
        old = {c['id']: u.digest(c) for c in work['candidates']}
        assert len(old) == 151
        aoc, fcb, elc = (next(c for c in work['candidates'] if c['id'] == cid) for cid in (AOC, FCB, CID))
        assert aoc['stage'] == 'training' and aoc['code_commit'] == u.SOURCE
        assert fcb['stage'] == 'blocked' and fcb['blocker_kind'] == 'exclusive_gpu_slot' and fcb['occupation_evidence'] == occupation
        assert elc['stage'] == 'implementation' and elc['code_commit'] is None and elc['queued'] is False
        assert elc['native_execution_code_commit'] is None
        attempt = work['tick_attempt']
        assert attempt['tick_started_at'] == EXPECTED['generated_at'] and attempt['kind'] == 'resource_check' and attempt['result'] == 'blocked'
        now = datetime.now(timezone.utc).isoformat()
        aoc['current_live_observation'] = {
            'recorded_at': now, 'evidence': u.ref(obs_path), 'independent_review': u.ref(progress_peer),
            'original_pid': 3437349, 'original_start_ticks': 90046755,
            'native_step_before': [21, 1980], 'native_step_after': [21, 1989],
            'precise_native_validation': copy.deepcopy(metrics),
            'scope': 'Exact original process/log/source native growth and twenty completed validation lines; training incomplete. No final efficacy, new launch or PES repair claim.'}
        fcb['current_resource_check'] = {
            'recorded_at': proof['observed_at'], 'result': 'ORIGINAL_AOC_ON_SOLE_AUTHORIZED_GPU0', 'evidence': occupation,
            'scope': 'Fresh canonical physical occupation only. FCB matched natural TRAIN2/resources remain NOT_RUN.'}
        for ref in (u.ref(obs_path), u.ref(progress_peer)):
            if ref not in aoc['evidence']:
                aoc['evidence'].append(ref)
        work['updated_at'] = now
        assert all(u.digest(c) == old[c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB))
        assert all(u.digest(c) == baseline['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB, CID))
        memory_path = ROOT / 'pipeline/codex_memory.md'
        assert sha(memory_path) == baseline['memory_sha256']
        memory_lines = memory_path.read_text(encoding='utf-8').splitlines()
        updated = []
        for line in memory_lines:
            if line.startswith('- 当前3e32314b generated'):
                line = f"- 当前87f03f29 generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值；实际thread01a159c5-29ab-7a22-ba7f-e79174757253匹配foreground。Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。"
            elif line.startswith('- 最佳仍M95 .5020，baseline'):
                line = '- 最佳仍M95 .5020，baseline .4894；原AOC最新UTC2026-10-30T00:08:24 TRAIN21/50 1989/4686，20次实际验证，partialbest.5000720620155334/noimprove0，训练未完成，不作最终效果比较；本轮raw097c4907保留全部值。'
            elif line.startswith('- 本3e32314b新增SFC'):
                line = line.replace('- 本3e32314b新增SFC', '- 前3e32314b SFC', 1).replace('见sfc_promotion_record_result.json', '见pipeline/diagnostic_bundles/tick_3e32314b/sfc_promotion_record_result.json')
            elif line.startswith('- 原AOC PID3437349/start90046755，log '):
                line = '- 原AOC PID3437349/start90046755，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aoc_20261029_222527.log；本轮UTC00:08:21→24 TRAIN21 1980→1989/log27013779→27016227/proof097c4907，原8源/YAML77e/0314/GPU0context保持，20val partialbest.5000720620155334，未完成。'
            elif line.startswith('- 本轮0新candidate（仍150）'):
                line = '- 本轮新增唯一M225-ELC软件原型（151ID）/0模型revision/0新commit/0nativearm/0准入/0启动/0归档；实际生产plan/forward与集成软件小核、独立源审见new_variant_registration_result.json。code/source/actualparentNULL/ref0314，Torch/autograd/native/resources均NOT_RUN；前轮SFC工具/历史AOC四臂/PES崩溃不重计。'
            elif line.startswith('- 28 lifecycle/28 user/status/indexempty/'):
                line = '- 28 lifecycle/28 user/status/indexempty/其他148旧候选、主线/runtime0314保持；canonical GPU0新proof绑定本owner/snapshot且原AOC仍占槽。fresh setup SOURCE0314/原AOC真实PID-start-log/新anchor，当前post_tick_baseline.json供下一轮，不盲ff或回退旧PES PID。'
            updated.append(line)
            if line.startswith('- 前3e32314b SFC'):
                updated.extend([
                    '- 新M225-ELC CID hierarchy-undirected-edge-state-line-graph-composition：原true support树每无向child-parent边一个E*C持久state，e0=GELU(U[zchild,zparent])；每轮对所有共享端点的其它旧edge逐边等权mean，e\'=GELU(R[e,mean])同步覆盖，按组件原treeD−1=linegraphD1/3恰轮数，完成不fakeupdate；finalnode incident edge均值直接delta→原3rawskip/HCG/CSORT/单inst，原3LN各一次。',
                    '- ELC的E个无向shared两端state和incident读出不同DCE 2E定向cavity/SFC-PES N节点state；无新信息/创新/效力或PES修复声称。精确8模型+原YAML及实际小软件核/独立审refs见pipeline/diagnostic_bundles/tick_87f03f29/new_variant_registration_result.json；尚无真实Git版本/native工具/原生准入。',
                    '- ELC首checker在25项后读中文源遭GBK解码失败，原checker/失败JSON/当时9sourcehash保留；只将checker读取显式UTF8后27项通过，生产9hash与先冻proposal/protocol未动，非模型revision或Torch/native失败。'])
            if line.startswith('- SFC C256cell'):
                updated.append('- ELC C256两共享2C→C maps共262656参数，bs1每scene E≤320/R≤3的linearMAC上界167772160，均仅源代数非10G/latency/memory PASS；真实OTHER mean用按degree分组exclusive prefix/suffix，非显式边对特征矩阵。三节点路径finaldelta_mid=(fine+coarse)/2是实数表达限制，另有过平滑/回返重复信息/edge-degree混合与CPU开销风险；不设FP32守恒/Jacobian/强制D3覆盖或逐map/edge/列/轮正梯度门，未来仍只wholecore原loss聚合训练性和整体真实更新。')
        memory = '\n'.join(updated) + '\n'
        assert len(updated) < 120 and memory.count('## ') == 7
        notes = {'actions': [
            '上海10月30日08:08:21→24原AOC第21/50轮1980→1989/4686，20次原生验证partialbest0.5000720620155334/noimprove0；原PID/start/log/0314/8源/YAML/GPU0context保持，训练未完成，尚未超过冠军.5020。',
            '现FCB/SFC的CPU source/native/op/disabledpromotion准备已完整且原字节保持，GPU0仍原AOC使用。本轮按creation1/reserve1仅新增M225-ELC：原层级无向边持久state、linegraph全邻边同步组合及incident node读出，8独立源+原YAML与实际小软件检查、独立审完成。',
            'ELC code/source/actualparent均NULL、参考当前0314，无真实Git版本/Torch/autograd/native/resource或准入结果；DCE/SFC/PES的状态域与完整DAG差异已界定，效力新颖性未知。首checker的GBK解码失败原件已保留，仅checker显式UTF8修正、生产9源与协议未动，非模型revision。fresh canonical GPU0占用证明原AOC仍占卡，FCB原TRAIN2/resources未执行。28账/28用户/index与其他148旧候选保持。'],
            'decisions': [
                '目标.5100/冠军M95 .5020不变；AOC .500072是训练中间最佳值，不是最终有效性。ELC所属edge-message-passing家族，模型软件正确性不是论文创新、原生梯度或资源PASS。',
                '只server4物理GPU0/max1，GPU1不用，不动原AOC/M206或旧holds/PES崩溃。GPU0真实释放且fresh owner/原deadline/source/UUID/assets/三锁通过后优先FCB原native YAML paired TRAIN2及同口径resources，过后当轮安全提升/准入/派发并核步增。',
                'SFC仍须真FCB技术receipt+实际main/remote d4，未来ELC按届时真实兼容主线保存未改9源并原生检查，禁止sibling/累计18A盲ff；不加父训练完成/收益门。',
                'ELC邻边逐边等权而非两端均值再平均，直径轮数由真拓扑确定；其三节点线性读出约束只记表达风险，无新增FP32守恒/Jacobian/强制D3或逐map正门。不改seed/schedule/data/bans/资源/调度，无需新增用户审批。']}
        u.save(HERE / 'final_records_intent.json', {'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [AOC, FCB], 'progress': u.ref(obs_path), 'registered_prototype': u.ref(HERE / 'new_variant_registration_result.json'),
            'fresh_occupation': occupation, 'scope': 'Measured progress, memory and report notes only; no new source/Git/native/lifecycle/queue/launch or pre-signed postflight.'})
        guard()
        assert sha(path) == before and sha(memory_path) == baseline['memory_sha256']
        u.atomic(path, work)
        u.atomic(memory_path, memory, text=True)
        u.save(HERE / 'report_notes.json', notes)
        u.primary_protection(baseline)
        u.lifecycle_protection(baseline)
        post = dict(baseline)
        post.update(owner=EXPECTED, recorded_at=now, candidate_digests={c['id']: u.digest(c) for c in work['candidates']},
                    research_work_sha256=sha(path), memory_sha256=sha(memory_path), latest_original_progress=u.ref(obs_path),
                    fresh_occupation=occupation, source_only_ELC=u.ref(HERE / 'new_variant_registration_result.json'))
        u.save(HERE / 'post_tick_baseline.json', post)
        u.save(HERE / 'final_records_result.json', {'owner': EXPECTED,
            'status': 'ACTUAL_PROGRESS_AND_ONE_ELC_SOURCE_RESERVE_SAVED_POSTFLIGHT_NOT_YET_RUN',
            'candidate_count': 151, 'new_candidates': 1, 'model_revisions': 0, 'new_commits': 0,
            'native_arms': 0, 'admissions': 0, 'formal_launches': 0, 'terminal_archives': 0,
            'memory_lines': len(updated), 'latest_original_progress': u.ref(obs_path), 'fresh_occupation': occupation,
            'other148_old_candidates_and28_lifecycle_and28_user_paths_and_index_preserved': True,
            'post_tick_baseline': u.ref(HERE / 'post_tick_baseline.json')})
        print({'status': 'Actual progress and one source prototype saved; postflight pending',
               'memory_lines': len(updated), 'baseline': u.ref(HERE / 'post_tick_baseline.json')})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
