"""Save routine original progress and disabled ELC future-result consumers."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
AOC = 'hierarchy-ancestral-order-commutator-composition'
FCB = 'hierarchy-fine-coarse-complete-bipartite-composition'
ELC = 'hierarchy-undirected-edge-state-line-graph-composition'
COMMIT = '18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
PARENT = 'c9be548699cd66bf68badff9ae6198a03eafa142'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-root', action='store_true')
    parser.add_argument('--preparation-sha256')
    parser.add_argument('--review-sha256')
    args = parser.parse_args()
    if not args.execute_root:
        print('DEFAULT_NO_STATE_CHANGE')
        return
    guard()
    baseline = u.read(HERE / 'protected_assets_before.json')
    u.primary_protection(baseline)
    u.lifecycle_protection(baseline)
    obs_path = HERE / 'aoc_progress_observer/aoc_training_progress_observation.json'
    assert sha(obs_path) == '6c41d2c079867027a7fbb55bd71e387702c517987ab0f56ac8327323ff15aa41'
    obs = u.read(obs_path)
    assert obs['owner'] == EXPECTED and obs['returncode'] == 0 and obs['observation']['runtime_commit'] == u.SOURCE
    samples = obs['observation']['samples']
    assert samples[0]['last_native_step'] == [29, 3852] and samples[-1]['last_native_step'] == [29, 3860]
    metrics = obs['precise_native_validation']
    assert len(metrics['values']) == 28 and metrics['best'] == 0.5000720620155334 and metrics['no_improve'] == 8
    progress_peer = HERE / 'current_aoc_wait_independent_review.json'
    assert sha(progress_peer) == '2f5570d95d01cb4c4e81afd407c354f48c2c4d9451447b99cbdad21fb4b7ec40'
    assert u.read(progress_peer)['material_concerns'] == []
    prep_path = HERE / 'elc_promotion_prepare/preparation.json'
    peer_path = HERE / 'elc_promotion_static_independent_review.json'
    assert sha(prep_path) == args.preparation_sha256 and sha(peer_path) == args.review_sha256
    prep, peer = u.read(prep_path), u.read(peer_path)
    assert prep['candidate_id'] == ELC and prep['experiment_id'] == 'M225-ELC'
    assert prep['code_commit'] == COMMIT and prep['source_parent_commit'] == PARENT
    assert prep['draft_execution_disabled'] is True
    assert all(prep[k] is None for k in ('actual_independent_review', 'actual_four_result_review', 'actual_raw_results'))
    for n, h in prep['prepared_file_hashes'].items():
        p = (prep_path.parent / n).resolve()
        assert p.is_relative_to(prep_path.parent.resolve()) and sha(p) == h, n
    assert peer['candidate_id'] == ELC and peer['code_commit'] == COMMIT and peer['material_concerns'] == []
    assert u.ref(prep_path) in peer['anchors'].values()
    occupation = u.read(HERE / 'gpu0_occupation_closure_result.json')['result']['evidence']
    proof = u.read(ROOT / occupation['path'])
    assert sha(ROOT / occupation['path']) == occupation['sha256']
    assert proof['token'] == EXPECTED['token'] and proof['snapshot_sha256'] == EXPECTED['context_sha256']
    assert 0 <= (datetime.now(timezone.utc) - datetime.fromisoformat(proof['observed_at'])).total_seconds() < 240
    assert not any((ROOT / 'pipeline/admissions' / (exp + '.json')).exists() for exp in ('M223-FCB', 'M224-SFC', 'M225-ELC'))
    assert not (HERE / 'elc_execution').exists()
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
        aoc, fcb, elc = (next(c for c in work['candidates'] if c['id'] == cid) for cid in (AOC, FCB, ELC))
        assert aoc['stage'] == 'training' and aoc['code_commit'] == u.SOURCE
        assert fcb['stage'] == 'blocked' and fcb['blocker_kind'] == 'exclusive_gpu_slot' and fcb['occupation_evidence'] == occupation
        assert elc['stage'] == 'validation' and elc['code_commit'] == COMMIT and elc['source_parent_commit'] == PARENT
        assert elc['native_execution_code_commit'] is None and elc['queued'] is False
        attempt = work['tick_attempt']
        assert attempt['tick_started_at'] == EXPECTED['generated_at'] and attempt['kind'] == 'resource_check' and attempt['result'] == 'blocked'
        now = datetime.now(timezone.utc).isoformat()
        aoc['current_live_observation'] = {
            'recorded_at': now, 'evidence': u.ref(obs_path), 'independent_review': u.ref(progress_peer),
            'original_pid': 3437349, 'original_start_ticks': 90046755,
            'native_step_before': [29, 3852], 'native_step_after': [29, 3860],
            'precise_native_validation': copy.deepcopy(metrics),
            'scope': 'Original native growth and twenty-eight validations. Eight no-improvement validations are still incomplete training, not early-stop or physical release.'}
        fcb['current_resource_check'] = {
            'recorded_at': proof['observed_at'], 'result': 'ORIGINAL_AOC_ON_SOLE_AUTHORIZED_GPU0', 'evidence': occupation,
            'scope': 'Current canonical physical occupation; FCB natural TRAIN2/resources NOT_RUN.'}
        elc['future_promotion_preparation'] = {
            'status': 'DISABLED_FUTURE_NATIVE_RESULT_CONSUMERS_PREPARED_NOT_EXECUTED',
            'preparation': u.ref(prep_path), 'independent_static_review': u.ref(peer_path),
            'draft_execution_disabled': True, 'actual_four_result_review': None, 'actual_raw_results': None,
            'actual_independent_review': None, 'source_commit': COMMIT, 'source_parent_commit': PARENT,
            'native_or_resource_executed': False, 'standards_receipt_queue_or_launch_created': False,
            'scope': 'Future four-actual-arm evidence and original exact-nine promotion/admission/once-dispatch consumers only. Current0314 and absent SFC technical receipt cannot activate this conditional child; original gates unchanged.'}
        for candidate, refs in ((aoc, (u.ref(obs_path), u.ref(progress_peer))), (elc, (u.ref(prep_path), u.ref(peer_path), prep['static_validation']))):
            for ref in refs:
                if ref not in candidate['evidence']:
                    candidate['evidence'].append(ref)
        work.update(updated_at=now, last_event_tick=EXPECTED['generated_at'])
        assert all(u.digest(c) == old[c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB, ELC))
        assert all(u.digest(c) == baseline['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB, ELC))
        memory_path = ROOT / 'pipeline/codex_memory.md'
        assert sha(memory_path) == baseline['memory_sha256']
        lines = memory_path.read_text(encoding='utf-8').splitlines()
        updated = []
        for line in lines:
            if line.startswith('- 当前692b4575 generated'):
                line = f"- 当前1179a5bb generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值；实际thread01a159c5-29ab-7a22-ba7f-e79174757253匹配foreground。Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。"
            elif line.startswith('- 最佳仍M95 .5020，baseline'):
                line = '- 最佳仍M95 .5020，baseline .4894；原AOC最新UTC2026-10-30T04:06:30 TRAIN29/50 3860/4686，28次实际验证，partialbest.5000720620155334/noimprove8，未终态/未早停，不作最终效果比较；本轮raw6c41d2c0保留全部值。'
            elif line.startswith('- 本692b ELC真实isolated'):
                line = line.replace('- 本692b ELC真实isolated', '- 前692b ELC真实isolated', 1)
            elif line.startswith('- ELC本轮实际local父门'):
                line = line.replace('- ELC本轮实际local父门', '- ELC前692b实际local父门', 1)
            elif line.startswith('- 原AOC PID3437349/start90046755，log '):
                line = '- 原AOC PID3437349/start90046755，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aoc_20261029_222527.log；本轮UTC04:06:27→30 TRAIN29 3852→3860/log38160814→38163230/proof6c41d2c0，原8源/YAML77e/0314/GPU0context保持，28val best.5000720620155334/noimprove8，未终态。'
            elif line.startswith('- 本轮0新candidate（仍151）'):
                line = '- 本轮0新candidate（仍151）/0模型revision/0新commit/0nativearm/0准入/0启动/0归档；只补ELC disabled未来5consumer及真实producer-key对应，raw/review全None/DRAFTTrue，必要局部软件核和独立审通过，非原生/资源/收益PASS。前692b source/native/op与既往模型软件suite不重跑或重计。'
            elif line.startswith('- 28 lifecycle/28 user/status/indexempty/'):
                line = '- 28 lifecycle/28 user/status/indexempty/其他148候选、主线/runtime0314保持；canonical GPU0新proof绑定本owner/snapshot且原AOC仍占槽。fresh setup SOURCE0314/原AOC真实PID-start-log/新anchor，当前post_tick_baseline.json供下一轮；noimprove8不等于PID结束或允许复用显卡。'
            updated.append(line)
            if line.startswith('- ELC前692b实际local父门'):
                updated.append('- 本1179a5bb ELC disabledpromotion完整refs见pipeline/diagnostic_bundles/tick_1179a5bb/elc_promotion_record_result.json：5consumers仅未来真实四arm/peer后按原技术四门、exact9A提升/原准入和once FIFO派发；精确ELC初始化1/动态R step与共享GELU R+1/OTHER mean R/incidentmean1/wholecore聚合/3scatter producer-schema，非SFC node旧键。raw/review None/DRAFTTrue；未来需fresh owner与实际c9保护baseline，当前0314不可执行，不能盲ff累计27A。')
        memory = '\n'.join(updated) + '\n'
        assert len(updated) < 120 and memory.count('## ') == 7
        notes = {'actions': [
            '上海10月30日12:06:27→30原AOC第29/50轮3852→3860/4686，28次实际验证partialbest0.5000720620155334/noimprove8；原PID/start/log/0314/8源/YAML/GPU0context保持。尚未终态或早停，未改patience/原训练。',
            '快照creation0/reserve0，不新增候选。为已有ELC18e/parentc9/native28ec/op3ef93补未来四真实arm后的5个disabledconsumer，按actual producer字段核初始化/动态step/GELU/incident均值/wholecore更新，必要小软件检查和静态独审通过；raw/review全None、DRAFTTrue，不激活，不原生/提升/准入/派发。',
            'fresh canonical GPU0实际占用确认原AOC仍在唯一授权卡上。FCB自然TRAIN2/resources仍待物理空槽；SFC/ELC还各需真实技术父提升。28账/28用户/index和其他148候选保持；当前source/kernel/native/op与所有原失败记录未改。'],
            'decisions': [
                '目标.5100/冠军M95 .5020不变；AOC .500072/noimprove8是未完成训练中间状态，保留原native自然结束行为，不据此提前停/归档或声称最终收益。',
                '只server4物理GPU0/max1，GPU1不用；不碰现有AOC/M206/旧holds/PES崩溃。GPU0真实释放后复核fresh owner/原deadline/source/UUID/assets/三锁，先FCB原native YAML paired TRAIN2与同口径资源，通过当轮安全提升/准入/派发并核原生增长。',
                'ELC需真M224-SFC/c9技术receipt+实际main/remote c9，当前0314累计27A不能盲ff；未来要fresh c9保护baseline及真实四arm peer再reviewed activation。父未提升/main变就保存现有条件证据并另存实际兼容未改9源再实测，无父训练效果/完成门。',
                '本轮无新增训练结论或用户事项；disabled模板/字段核对不作为通知理由。原始native/资源口径和wholecore聚合训练性门保持，不加逐map/edge/round/bias正门、FP32守恒/Jacobian或强制D3覆盖，不改资源/数据/seed/schedule/bans/调度，无需新增授权。']}
        u.save(HERE / 'final_records_intent.json', {'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [AOC, FCB, ELC], 'progress': u.ref(obs_path), 'preparation': u.ref(prep_path),
            'independent_review': u.ref(peer_path), 'fresh_occupation': occupation,
            'scope': 'Current measured observations, disabled tooling refs, memory and notes only. No source/Git/native/lifecycle/queue/launch or postflight pre-sign.'})
        guard()
        assert sha(path) == before and sha(memory_path) == baseline['memory_sha256']
        u.atomic(path, work)
        u.atomic(memory_path, memory, text=True)
        u.save(HERE / 'report_notes.json', notes)
        u.save(HERE / 'elc_promotion_record_result.json', {'owner': EXPECTED,
            'status': 'DISABLED_ELC_FUTURE_TOOLING_REFS_RECORDED_NATIVE_NOT_RUN', 'candidate_id': ELC,
            'preparation': u.ref(prep_path), 'independent_review': u.ref(peer_path), 'native_arms': 0,
            'admissions': 0, 'queue_or_launch': 0, 'source_changes': 0, 'new_candidates': 0})
        u.primary_protection(baseline)
        u.lifecycle_protection(baseline)
        post = dict(baseline)
        post.update(owner=EXPECTED, recorded_at=now, candidate_digests={c['id']: u.digest(c) for c in work['candidates']},
                    research_work_sha256=sha(path), memory_sha256=sha(memory_path), latest_original_progress=u.ref(obs_path),
                    fresh_occupation=occupation, disabled_ELC_promotion=u.ref(HERE / 'elc_promotion_record_result.json'))
        u.save(HERE / 'post_tick_baseline.json', post)
        u.save(HERE / 'final_records_result.json', {'owner': EXPECTED,
            'status': 'ROUTINE_PROGRESS_AND_DISABLED_ELC_TOOLING_SAVED_POSTFLIGHT_NOT_YET_RUN',
            'candidate_count': 151, 'new_candidates': 0, 'model_revisions': 0, 'new_commits': 0,
            'native_arms': 0, 'admissions': 0, 'formal_launches': 0, 'terminal_archives': 0,
            'memory_lines': len(updated), 'latest_original_progress': u.ref(obs_path), 'fresh_occupation': occupation,
            'other148_candidates_and28_lifecycle_and28_user_paths_and_index_preserved': True,
            'post_tick_baseline': u.ref(HERE / 'post_tick_baseline.json')})
        print({'status': 'Routine progress and disabled tooling saved; postflight pending',
               'memory_lines': len(updated), 'baseline': u.ref(HERE / 'post_tick_baseline.json')})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
