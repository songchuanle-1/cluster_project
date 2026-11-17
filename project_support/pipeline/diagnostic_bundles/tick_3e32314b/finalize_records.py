"""Record current original training and disabled SFC future tooling only."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
AOC = 'hierarchy-ancestral-order-commutator-composition'
FCB = 'hierarchy-fine-coarse-complete-bipartite-composition'
SFC = 'hierarchy-synchronous-full-neighbor-composition'
COMMIT = 'c9be548699cd66bf68badff9ae6198a03eafa142'
PARENT = 'd4d062ef075abfe7cde93d4b4347ce146572762f'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-root', action='store_true')
    parser.add_argument('--preparation-sha256')
    parser.add_argument('--review-sha256')
    parser.add_argument('--progress-review-sha256')
    args = parser.parse_args()
    if not args.execute_root:
        print('DEFAULT_NO_STATE_CHANGE')
        return
    guard()
    baseline = u.read(HERE / 'protected_assets_before.json')
    u.primary_protection(baseline)
    u.lifecycle_protection(baseline)
    obs_path = HERE / 'aoc_progress_observer/aoc_training_progress_observation.json'
    assert sha(obs_path) == '019a7dc998d7b396135ba8f8aca722ee7230733a539e4f5d6ce8e3cb69c8541d'
    obs = u.read(obs_path)
    assert obs['owner'] == EXPECTED and obs['returncode'] == 0
    assert obs['observation']['runtime_commit'] == u.SOURCE
    samples = obs['observation']['samples']
    assert samples[0]['last_native_step'] == [17, 1285] and samples[-1]['last_native_step'] == [17, 1294]
    metrics = obs['precise_native_validation']
    assert len(metrics['values']) == 16 and metrics['best'] == 0.49505752325057983 and metrics['no_improve'] == 0
    progress_peer = HERE / 'current_aoc_wait_independent_review.json'
    assert sha(progress_peer) == args.progress_review_sha256 and u.read(progress_peer)['material_concerns'] == []
    prep_path = HERE / 'sfc_promotion_prepare/preparation.json'
    peer_path = HERE / 'sfc_promotion_static_independent_review.json'
    assert sha(prep_path) == args.preparation_sha256 and sha(peer_path) == args.review_sha256
    prep, peer = u.read(prep_path), u.read(peer_path)
    assert prep['candidate_id'] == SFC and prep['experiment_id'] == 'M224-SFC'
    assert prep['code_commit'] == COMMIT and prep['source_parent_commit'] == PARENT
    assert prep['draft_execution_disabled'] is True
    assert all(prep[k] is None for k in ('actual_independent_review', 'actual_four_result_review', 'actual_raw_results'))
    for n, h in prep['prepared_file_hashes'].items():
        p = (prep_path.parent / n).resolve()
        assert p.is_relative_to(prep_path.parent.resolve()) and sha(p) == h, n
    assert peer['candidate_id'] == SFC and peer['code_commit'] == COMMIT and peer['material_concerns'] == []
    assert u.ref(prep_path) in peer['anchors'].values()
    occupation = u.read(HERE / 'gpu0_occupation_closure_result.json')['result']['evidence']
    proof = u.read(ROOT / occupation['path'])
    assert sha(ROOT / occupation['path']) == occupation['sha256']
    assert proof['token'] == EXPECTED['token'] and proof['snapshot_sha256'] == EXPECTED['context_sha256']
    assert 0 <= (datetime.now(timezone.utc) - datetime.fromisoformat(proof['observed_at'])).total_seconds() < 240
    assert not (ROOT / 'pipeline/admissions/M223-FCB.json').exists()
    assert not (ROOT / 'pipeline/admissions/M224-SFC.json').exists()
    assert not (HERE / 'sfc_execution').exists()
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
        assert len(old) == 150
        aoc, fcb, sfc = (next(c for c in work['candidates'] if c['id'] == cid) for cid in (AOC, FCB, SFC))
        assert aoc['stage'] == 'training' and aoc['code_commit'] == u.SOURCE
        assert fcb['stage'] == 'blocked' and fcb['blocker_kind'] == 'exclusive_gpu_slot' and fcb['occupation_evidence'] == occupation
        assert sfc['stage'] == 'validation' and sfc['code_commit'] == COMMIT and sfc['source_parent_commit'] == PARENT
        assert sfc['native_execution_code_commit'] is None and sfc['queued'] is False
        attempt = work['tick_attempt']
        assert attempt['tick_started_at'] == EXPECTED['generated_at'] and attempt['kind'] == 'resource_check' and attempt['result'] == 'blocked'
        now = datetime.now(timezone.utc).isoformat()
        aoc['current_live_observation'] = {
            'recorded_at': now, 'evidence': u.ref(obs_path), 'independent_review': u.ref(progress_peer),
            'original_pid': 3437349, 'original_start_ticks': 90046755,
            'native_step_before': [17, 1285], 'native_step_after': [17, 1294],
            'precise_native_validation': copy.deepcopy(metrics),
            'scope': 'Exact original AOC native growth and sixteen validation lines, incomplete training. No new launch or final efficacy claim.'}
        fcb['current_resource_check'] = {
            'recorded_at': proof['observed_at'], 'result': 'ORIGINAL_AOC_ON_SOLE_AUTHORIZED_GPU0',
            'evidence': occupation, 'scope': 'Canonical current physical occupation; original FCB TRAIN/resources NOT_RUN.'}
        sfc['future_promotion_preparation'] = {
            'status': 'DISABLED_FUTURE_NATIVE_RESULT_CONSUMERS_PREPARED_NOT_EXECUTED',
            'preparation': u.ref(prep_path), 'independent_static_review': u.ref(peer_path),
            'draft_execution_disabled': True, 'actual_four_result_review': None, 'actual_raw_results': None,
            'actual_independent_review': None, 'source_commit': COMMIT, 'source_parent_commit': PARENT,
            'native_or_resource_executed': False, 'standards_receipt_queue_or_launch_created': False,
            'scope': 'Only future original four-arm evidence, exact-nine tested-source promotion, admission and canonical once-dispatch templates. Current main/runtime0314 and missing FCB receipt cannot activate this conditional child; all original gates remain.'}
        for candidate, refs in ((aoc, (u.ref(obs_path), u.ref(progress_peer))), (sfc, (u.ref(prep_path), u.ref(peer_path), prep['static_validation']))):
            for ref in refs:
                if ref not in candidate['evidence']:
                    candidate['evidence'].append(ref)
        work['updated_at'] = now
        work['last_event_tick'] = EXPECTED['generated_at']
        assert all(u.digest(c) == old[c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB, SFC))
        assert all(u.digest(c) == baseline['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB, SFC))
        memory_path = ROOT / 'pipeline/codex_memory.md'
        assert sha(memory_path) == baseline['memory_sha256']
        memory_lines = memory_path.read_text(encoding='utf-8').splitlines()
        updated = []
        for line in memory_lines:
            if line.startswith('- 当前928313fd generated'):
                line = f"- 当前3e32314b generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值；实际thread01a159c5-29ab-7a22-ba7f-e79174757253匹配foreground。Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。"
            elif line.startswith('- 最佳仍M95 .5020，baseline'):
                line = '- 最佳仍M95 .5020，baseline .4894；原AOC最新UTC2026-10-29T22:10:53 TRAIN17/50 1294/4686，16次实际验证，partialbest.49505752325057983/noimprove0，训练未完成，不作最终效果比较；本轮raw019a7dc9保留全部值。'
            elif line.startswith('- 本轮SFC真实isolated'):
                line = line.replace('- 本轮SFC真实isolated', '- 前9283 SFC真实isolated', 1)
            elif line.startswith('- SFC本轮native/op'):
                line = line.replace('- SFC本轮native/op', '- 前9283 SFC native/op', 1)
                line = line.replace('见sfc_registration_result.json', '见pipeline/diagnostic_bundles/tick_928313fd/sfc_registration_result.json')
            elif line.startswith('- 原AOC PID3437349/start90046755，log '):
                line = '- 原AOC PID3437349/start90046755，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aoc_20261029_222527.log；本轮UTC22:10:50→53 TRAIN17 1285→1294/log21527794→21530134/proof019a7dc9，原8源/YAML77e/0314/GPU0context保持，16val partialbest.49505752325057983，未完成。'
            elif line.startswith('- 本轮0新candidate（仍150）'):
                line = '- 本轮0新candidate（仍150）/0模型revision/0新commit/0nativearm/0准入/0启动/0归档；只补SFC disabled未来5helpers与producer-schema对应，实际refs全None/DRAFTTrue，必要静态小核和独立审通过，非native/资源/收益PASS。上轮SFC source/native/op及历史AOC四臂/PES崩溃不重计。'
            elif line.startswith('- 28 lifecycle/28 user/status/indexempty/'):
                line = '- 28 lifecycle/28 user/status/indexempty/其他147候选、主线/runtime0314保持；canonical GPU0新proof绑定本owner/snapshot且原AOC仍占槽。fresh setup SOURCE0314/原AOC实际PID/start/log/新anchor，当前post_tick_baseline.json供下一轮使用。'
            updated.append(line)
            if line.startswith('- SFC mutation-only父门实拒绝：'):
                updated.append('- 本3e32314b新增SFC disabledpromotion完整refs见sfc_promotion_record_result.json：5helpers仅未来消费四actual arms后原技术四门/精确9A提升/原准入与once派发；真实SFC producer keys与可变直径round-count对应，非FCB pair/middle硬计数。raw/review None/DRAFTTrue，未来需新owner及实际d4保护baseline，当前0314 baseline不可执行；不改原worker/op/原型，不预签或激活当前0314→c9累计18A。')
        memory = '\n'.join(updated) + '\n'
        assert len(updated) < 120 and memory.count('## ') == 7
        notes = {'actions': [
            '上海10月30日06:10:50→53原AOC第17/50轮1285→1294/4686，16次原生验证partialbest0.49505752325057983/noimprove0；较前轮0.4873921573162079提高，但训练未完成。原PID/start/log/source0314/8源/YAML/GPU0context保持。',
            '继续已有SFC，补齐未来四个真实原生/资源结果之后的5个disabled promotion consumers，精确绑定c9/parentd4/native173e/op5e37，producer-schema映射及静态独立审完成。实际raw/review全部None、DRAFTTrue，未原生/激活/提升/准入/入队/派发。',
            'fresh canonical GPU0占用证据确认原AOC继续使用唯一授权卡，FCB原自然TRAIN2/resources仍等待物理空槽；SFC另需FCB真技术receipt与实际main/remote d4，当前0314不能激活。28账/28用户/index与其他147候选保持。'],
            'decisions': [
                '目标.5100/冠军M95 .5020不变。AOC当前best是未完成训练中间值，未得最终收益；SFC静态producer/consumer软件核不代表Torch/autograd/native/resource或论文创新成立。',
                'GPU1继续禁用，只server4 GPU0/max1；不动原AOC或M206/旧10holds/PES崩溃。GPU0真实释放后优先FCB原native YAML paired TRAIN2和原资源口径，当轮真实通过才安全提升/准入/派发并验证步增。',
                'SFC future mutation要求原FCB真技术receipt与实际main/remote d4，不加父训练完成/收益门；main变更则保留现条件版本，另存真实兼容未改9源再实测，禁累计18A盲ff。',
                '不凑新candidate/新科学门，不改预算/禁用项/数据/seed/schedule/调度或旧授权，不重复旧suite；无需新增用户审批。']}
        u.save(HERE / 'final_records_intent.json', {'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [AOC, FCB, SFC], 'progress': u.ref(obs_path), 'preparation': u.ref(prep_path),
            'independent_review': u.ref(peer_path), 'fresh_occupation': occupation,
            'scope': 'Existing measured progress and disabled future tooling refs/memory/notes only; no model/native/lifecycle/queue/launch or pre-signed postflight.'})
        guard()
        assert sha(path) == before and sha(memory_path) == baseline['memory_sha256']
        u.atomic(path, work)
        u.atomic(memory_path, memory, text=True)
        u.save(HERE / 'report_notes.json', notes)
        u.save(HERE / 'sfc_promotion_record_result.json', {'owner': EXPECTED,
            'status': 'DISABLED_SFC_FUTURE_TOOLING_REFS_RECORDED_NATIVE_NOT_RUN', 'candidate_id': SFC,
            'preparation': u.ref(prep_path), 'independent_review': u.ref(peer_path), 'native_arms': 0,
            'admissions': 0, 'queue_or_launch': 0, 'source_changes': 0, 'new_candidates': 0})
        u.primary_protection(baseline)
        u.lifecycle_protection(baseline)
        post = dict(baseline)
        post.update(owner=EXPECTED, recorded_at=now, candidate_digests={c['id']: u.digest(c) for c in work['candidates']},
                    research_work_sha256=sha(path), memory_sha256=sha(memory_path), latest_original_progress=u.ref(obs_path),
                    fresh_occupation=occupation, disabled_SFC_promotion=u.ref(HERE / 'sfc_promotion_record_result.json'))
        u.save(HERE / 'post_tick_baseline.json', post)
        u.save(HERE / 'final_records_result.json', {'owner': EXPECTED,
            'status': 'ACTUAL_PROGRESS_AND_DISABLED_SFC_PREPARATION_RECORDED_POSTFLIGHT_NOT_YET_RUN',
            'new_candidates': 0, 'model_revisions': 0, 'new_commits': 0, 'native_arms': 0,
            'admissions': 0, 'formal_launches': 0, 'terminal_archives': 0, 'candidate_count': 150,
            'memory_lines': len(updated), 'latest_original_progress': u.ref(obs_path), 'fresh_occupation': occupation,
            'other147_candidates_and28_lifecycle_and28_user_paths_and_index_preserved': True,
            'post_tick_baseline': u.ref(HERE / 'post_tick_baseline.json')})
        print({'status': 'Current measured progress and disabled tools recorded; postflight pending',
               'memory_lines': len(updated), 'baseline': u.ref(HERE / 'post_tick_baseline.json')})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
