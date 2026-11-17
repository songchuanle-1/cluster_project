"""Record original AOC progress and the existing ELC conditional capability."""
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
    args = parser.parse_args()
    if not args.execute_root:
        print('DEFAULT_NO_STATE_CHANGE')
        return
    guard()
    baseline = u.read(HERE / 'protected_assets_before.json')
    u.primary_protection(baseline)
    u.lifecycle_protection(baseline)
    obs_path = HERE / 'aoc_progress_observer/aoc_training_progress_observation.json'
    assert sha(obs_path) == '33d7d91aa9dc1494da1f78a7caf61eb37a5399f5f77cd684b9f41acd2711cf48'
    obs = u.read(obs_path)
    assert obs['owner'] == EXPECTED and obs['returncode'] == 0 and obs['observation']['runtime_commit'] == u.SOURCE
    samples = obs['observation']['samples']
    assert samples[0]['last_native_step'] == [25, 3710] and samples[-1]['last_native_step'] == [25, 3719]
    metrics = obs['precise_native_validation']
    assert len(metrics['values']) == 24 and metrics['best'] == 0.5000720620155334 and metrics['no_improve'] == 4
    progress_peer = HERE / 'current_aoc_wait_independent_review.json'
    assert sha(progress_peer) == '380f762682a791c1c3107e60e25f5b42b0abf163c1ab3900af7f476009fcc1b2'
    assert u.read(progress_peer)['material_concerns'] == []
    registration = u.read(HERE / 'elc_registration_result.json')
    assert registration['candidate_count'] == 151 and registration['new_candidates'] == 0 and registration['code_commit'] == COMMIT
    u.check_refs([registration['native_preparation'], registration['operational_preparation'], registration['independent_review']])
    local_guard_path = HERE / 'elc_local_parent_guard_observation.json'
    local_guard = u.read(local_guard_path)
    assert local_guard['status'] == 'EXPECTED_UNPROMOTED_PARENT_LOCAL_REFUSAL'
    assert local_guard['transport_calls'] == 0 and local_guard['active_execution_directory_created'] is False
    assert local_guard['SFC_admission_receipt_present'] is False
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
            'native_step_before': [25, 3710], 'native_step_after': [25, 3719],
            'precise_native_validation': copy.deepcopy(metrics),
            'scope': 'Exact original AOC native growth and twenty-four actual validation lines. Four no-improvement validations are not a terminal result or final efficacy.'}
        fcb['current_resource_check'] = {
            'recorded_at': proof['observed_at'], 'result': 'ORIGINAL_AOC_ON_SOLE_AUTHORIZED_GPU0', 'evidence': occupation,
            'scope': 'Fresh canonical physical occupation only; FCB native TRAIN2/resources NOT_RUN.'}
        elc['current_parent_guard_observation'] = {
            'evidence': u.ref(local_guard_path), 'result': local_guard['status'], 'transport_calls': 0,
            'scope': 'Actual current local guard refused absent SFC technical receipt before transport/active state. Not a native model failure.'}
        for candidate, refs in ((aoc, (u.ref(obs_path), u.ref(progress_peer))), (elc, (u.ref(local_guard_path),))):
            for ref in refs:
                if ref not in candidate['evidence']:
                    candidate['evidence'].append(ref)
        work['updated_at'] = now
        assert all(u.digest(c) == old[c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB, ELC))
        assert all(u.digest(c) == baseline['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in (AOC, FCB, ELC))
        memory_path = ROOT / 'pipeline/codex_memory.md'
        assert sha(memory_path) == baseline['memory_sha256']
        lines = memory_path.read_text(encoding='utf-8').splitlines()
        updated = []
        for line in lines:
            if line.startswith('- 当前87f03f29 generated'):
                line = f"- 当前692b4575 generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值；实际thread01a159c5-29ab-7a22-ba7f-e79174757253匹配foreground。Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。"
            elif line.startswith('- 最佳仍M95 .5020，baseline'):
                line = '- 最佳仍M95 .5020，baseline .4894；原AOC最新UTC2026-10-30T02:11:28 TRAIN25/50 3719/4686，24次实际验证，partialbest.5000720620155334/noimprove4，未完成/未早停，不作最终效果比较；本轮raw33d7d91a保留全部值。'
            elif line.startswith('- 新M225-ELC CID'):
                line = line.replace('- 新M225-ELC CID', '- M225-ELC CID', 1)
            elif line.startswith('- ELC的E个无向shared'):
                line = line.replace('；尚无真实Git版本/native工具/原生准入。', '；原c777/code-source-parentNULL/ref0314保持，本轮另存真实版本与条件工具，原生准入仍未执行。')
            elif line.startswith('- 原AOC PID3437349/start90046755，log '):
                line = '- 原AOC PID3437349/start90046755，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aoc_20261029_222527.log；本轮UTC02:11:25→28 TRAIN25 3710→3719/log32810086→32812786/proof33d7d91a，原8源/YAML77e/0314/GPU0context保持，24val best.5000720620155334/noimprove4，未完成。'
            elif line.startswith('- 本轮新增唯一M225-ELC软件原型'):
                line = '- 本轮0新candidate（仍151）/0模型revision/1 isolated ELC exact9A source commit/0nativearm/0准入/0启动/0归档；已有ELC补真实source及条件native/op与必要软件检查，actual refs见elc_registration_result.json。十activeNULL，无原生/资源或收益PASS，前轮27作者/151断言+25集成源审不重跑或重计。'
            elif line.startswith('- 28 lifecycle/28 user/status/indexempty/'):
                line = '- 28 lifecycle/28 user/status/indexempty/其他148候选、主线/runtime0314保持；canonical GPU0新proof绑定本owner/snapshot且原AOC仍占槽。fresh setup SOURCE0314/原AOC真实PID-start-log/新anchor，当前post_tick_baseline.json供下一轮。'
            updated.append(line)
            if line.startswith('- ELC首checker在25项后'):
                updated.extend([
                    '- 本692b ELC真实isolated18e64b8d95ed0ba5c1053ead114c0f91a4b0c324唯一父SFCc9be548699cd66bf68badff9ae6198a03eafa142，versionproofc1950ac3/actualsourcepeer及native-op合并refs见pipeline/diagnostic_bundles/tick_692b4575/elc_registration_result.json。exact9A/9blob=原c777，当前main/runtime0314不动；当前0314→18e累计27A不能盲ff。',
                    '- ELC条件能力actualsource18e/expectedparent-runtime c9、十activeNULL、无active manifest/lease/raw。init/step/GELU、exclusive-other mean/OLDedge-state单次更新和finalincidentmean的透明观察器只做必要软件核，非Torch/FP32/autograd/native/resource PASS；wholecore两map原loss聚合训练性/真实整体更新及原wholemodel资源函数口径保持，零map/edge/round/列/bias合法。',
                    '- ELC本轮实际local父门对缺M224-SFC技术receipt预期拒绝，transport0/无active目录。未来必须真M224-SFC/c9技术receipt+实际localmain/remote c9并fresh owner/原deadline/白名单GPU0空闲/三锁/资产，不加父训练完成或收益门；父未提升/main变就保留此版本并另存真实兼容未改9源再实测，禁累计27A或sibling盲ff。'])
        memory = '\n'.join(updated) + '\n'
        assert len(updated) < 120 and memory.count('## ') == 7
        notes = {'actions': [
            '上海10月30日10:11:25→28原AOC第25/50轮3710→3719/4686，24次验证partialbest0.5000720620155334/noimprove4；原PID/start/log/0314/8源/YAML/GPU0context保持，尚未终态，不改变原patience或训练。',
            '快照creation0/reserve0，本轮只推进已有ELC。原c777的8模型源+1原YAML保存真实isolated18e单父SFCc9，exact9A/9blob与原一致，actual Git/source独审通过；原型NULL/ref0314保持，主线/runtime0314与运行AOC未动。',
            'ELC补齐有条件native worker/runtime/template及op adapter真实hash绑定、必要局部软件验证与独立静态合并审。init/step/共享GELU/OLDedge均值与覆盖/finalincidentmean只透明捕获原调用，无重放；原wholecore两map聚合门、原wholemodel资源AST与口径不变。十activeNULL，无Torch/native/autograd/resources/准入或启动。',
            '实际本地父门因缺M224-SFC真技术receipt预期拒绝，transport0/无active目录。fresh canonical GPU0证据确认原AOC计算PID仍占唯一授权卡，FCB自然TRAIN2/resources待空槽；28账/28用户/index与其他148候选保持。'],
            'decisions': [
                '冠军M95 .5020/目标.5100不变。AOC最佳值未刷新、noimprove4是中间状态，不是失败或早停；ELC局部软件通过不代表原生梯度/资源/收益或新颖性成立。',
                '只server4物理GPU0/max1，GPU1不使用，不动原AOC/M206/旧holds/PES崩溃。GPU0自然释放且fresh身份/原deadline/实际source/UUID/assets/三锁复核通过后先FCB原YAML paired TRAIN2/resources，通过当轮按原安全提升/准入/派发并核原生增长。',
                'SFC仍需真FCB技术父提升；ELC需真M224-SFC技术receipt+实际main/remote c9，不要求父训练完成或收益。当前0314到ELC18e累计27A不能盲ff；父未提升/main变化则保留条件版本，另存真实兼容未改9源并实测。',
                '不新增候选、数值门或旧模型修订，不改资源/预算/数据/seed/schedule/bans/调度，不索要已覆盖的操作授权。旧10到期holds仅说明到期，不授权恢复，不作全路线重审。']}
        u.save(HERE / 'final_records_intent.json', {'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [AOC, FCB, ELC], 'progress': u.ref(obs_path), 'registration': u.ref(HERE / 'elc_registration_result.json'),
            'fresh_occupation': occupation, 'scope': 'Measured observations, conditional guard record, memory and notes only. No new source/Git/native/lifecycle/queue/launch or postflight pre-sign.'})
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
                    fresh_occupation=occupation, conditional_ELC=u.ref(HERE / 'elc_registration_result.json'))
        u.save(HERE / 'post_tick_baseline.json', post)
        u.save(HERE / 'final_records_result.json', {'owner': EXPECTED,
            'status': 'ACTUAL_PROGRESS_AND_EXISTING_ELC_CONDITIONAL_PREPARATION_SAVED_POSTFLIGHT_NOT_YET_RUN',
            'candidate_count': 151, 'new_candidates': 0, 'model_revisions': 0, 'new_commits': 1,
            'native_arms': 0, 'admissions': 0, 'formal_launches': 0, 'terminal_archives': 0,
            'memory_lines': len(updated), 'latest_original_progress': u.ref(obs_path), 'fresh_occupation': occupation,
            'other148_candidates_and28_lifecycle_and28_user_paths_and_index_preserved': True,
            'post_tick_baseline': u.ref(HERE / 'post_tick_baseline.json')})
        print({'status': 'Actual progress and existing conditional ELC capability saved; postflight pending',
               'memory_lines': len(updated), 'baseline': u.ref(HERE / 'post_tick_baseline.json')})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
