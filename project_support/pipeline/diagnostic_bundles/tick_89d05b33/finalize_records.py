"""Save measured progress and conditional tooling before foreground postflight."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
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
    ap.add_argument('--observation-sha256')
    ap.add_argument('--occupation-label', required=True)
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_RECORD_MUTATION')
        return
    guard()
    b = u.read(HERE / 'protected_assets_before.json')
    u.primary_protection(b)
    u.lifecycle_protection(b)
    latest = HERE / 'pes_final_observer/pes_training_progress_observation.json'
    assert sha(latest) == a.observation_sha256
    ob = u.read(latest)
    initial = u.read(HERE / 'pes_progress_observer/pes_training_progress_observation.json')
    assert ob['owner'] == EXPECTED and ob['returncode'] == 0
    raw = ob['observation']
    assert raw['runtime_commit'] == u.SOURCE and raw['signals_sent'] is False
    assert raw['identity_before'] == raw['identity_after']
    assert raw['identity_before']['pid'] == 2265073 and raw['identity_before']['start_ticks'] == '88396735'
    samples = raw['samples']
    assert samples[-1]['last_native_step'] > samples[0]['last_native_step']
    assert samples[-1]['log_size'] > samples[0]['log_size']
    assert samples[-1]['last_native_step'] >= initial['observation']['samples'][-1]['last_native_step']
    metrics = ob['precise_native_validation']
    assert metrics['values'][:2] == [0.2965591251850128, 0.3763071894645691]
    assert metrics['best'] == max(metrics['values']) and len(metrics['values']) >= 2
    assert '2265073' in [x.split(',')[0].strip() for x in raw['GPU0_contexts'].splitlines()]
    registration = u.read(HERE / 'fcb_registration_result.json')
    assert registration['candidate_count'] == 149 and registration['new_candidates'] == 0
    local = HERE / 'fcb_local_parent_guard_observation.json'
    local_ob = u.read(local)
    assert local_ob['owner'] == EXPECTED and local_ob['status'] == 'EXPECTED_UNPROMOTED_PARENT_LOCAL_REFUSAL'
    assert local_ob['transport_calls'] == 0 and local_ob['active_execution_directory_created'] is False
    collected = u.read(HERE / ('gpu0_occupation_' + a.occupation_label + '_result.json'))
    assert collected['owner'] == EXPECTED
    result = collected['result']
    assert result['candidate_ids'] == [AOC] and result['state']['busy_gpu_ids'] == [0] and result['state']['idle_gpu_ids'] == []
    occupation = result['evidence']
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
        u.primary_protection(b)
        u.lifecycle_protection(b)
        path = ROOT / 'pipeline/research_work.json'
        before = sha(path)
        work = u.read(path)
        old = {c['id']: u.digest(c) for c in work['candidates']}
        assert len(old) == 149
        p = next(c for c in work['candidates'] if c['id'] == PES)
        c = next(c for c in work['candidates'] if c['id'] == AOC)
        f = next(c for c in work['candidates'] if c['id'] == FCB)
        assert p['stage'] == 'training' and p['code_commit'] == u.SOURCE
        assert c['stage'] == 'blocked' and c['blocker_kind'] == 'exclusive_gpu_slot' and c['occupation_evidence'] == occupation
        assert f['stage'] == 'validation' and f['code_commit'] == 'd4d062ef075abfe7cde93d4b4347ce146572762f'
        assert f['source_parent_commit'] == '0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
        assert f['native_execution_code_commit'] is None and f['queued'] is False
        assert work['tick_attempt']['tick_started_at'] == EXPECTED['generated_at']
        assert work['tick_attempt']['kind'] == 'resource_check' and work['tick_attempt']['result'] == 'blocked'
        now = datetime.now(timezone.utc).isoformat()
        p['current_live_observation'] = {
            'recorded_at': now, 'evidence': u.ref(latest), 'earlier_native_step_growth': u.ref(HERE / 'pes_progress_observer/pes_training_progress_observation.json'),
            'original_pid': 2265073, 'original_start_ticks': 88396735,
            'native_step_before': samples[0]['last_native_step'], 'native_step_after': samples[-1]['last_native_step'],
            'precise_native_validation': copy.deepcopy(metrics),
            'scope': 'Actual unchanged strict observer of original process/log/source and native step growth; validation lines are partial, training incomplete. No new launch or final efficacy claim.'}
        c['current_resource_check'] = {
            'recorded_at': proof['observed_at'], 'result': 'ORIGINAL_PES_ON_SOLE_AUTHORIZED_GPU0', 'evidence': occupation,
            'scope': 'Fresh canonical physical occupation; AOC TRAIN/resources NOT_RUN.'}
        f['current_local_guard_observation'] = u.ref(local)
        for candidate, entries in ((p, (u.ref(latest),)), (c, (u.ref(latest),)), (f, (u.ref(local),))):
            for ref in entries:
                if ref not in candidate['evidence']:
                    candidate['evidence'].append(ref)
        work['updated_at'] = now
        work['last_event_tick'] = EXPECTED['generated_at']
        assert all(u.digest(x) == old[x['id']] for x in work['candidates'] if x['id'] not in (PES, AOC, FCB))
        assert all(u.digest(x) == b['candidate_digests'][x['id']] for x in work['candidates'] if x['id'] not in (PES, AOC, FCB))
        last = samples[-1]['last_native_step']
        best = metrics['best']
        stamp = samples[-1]['observed_at']
        count = len(metrics['values'])
        native_ref = f['worker_preparation']['preparation']
        op_ref = f['execution_adapter']['preparation']
        memory = f'''# Codex Research Memory

## Goal And Phase
- 当前89d05b33 generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值，实际thread01a159c5-29ab-7a22-ba7f-e79174757253匹配foreground；Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。
- goal0441/standing2e892/GPU0auth94075/SERVERS2583/closure2993不动；仅server4物理GPU0/max1，GPU1禁用，后台Pipeline-cluster_project禁用不改。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50-maxiters70-patience10/10G及bans保持。

## Champion And Baseline
- 最佳仍M95 .5020，baseline .4894；PES训练未完成。截至UTC{stamp}，共{count}次原native validation，partial best{best}/noimprove{metrics['no_improve']}，不与最终训练收益混同。
- 历史DCE正常earlystop27/50/noimprove10/best.4971300959587097，在14fea canonical归档a5a9/receipt4e2b；本轮不重归档/重启。BEC.5001/24、AEF.495597243309021/23、CRE.4961479902267456/30保持。

## Active Hypotheses
- 唯一正式M221-PES：source/primary/runtime9c42fdc4e9168acec18980d782ee9c163e043bb7；真实Euler+reverse4E receiver-only persistentcurrentstate，逆游不reset，原3LN/rawskip/HCG/CSORT/单inst保持；novelty/efficacy UNKNOWN。
- PES原型0c3e/协议ef7f/nativef2fc/op7124/receipt6fce、14fea实际四arm/peer2b71/正式launchgrowth保持；两自然TRAIN loss9.176618576049805/13.907245635986328、common835/155907386/hash5c80真实配对与wholecell原loss梯度/更新通过，本轮不重测。
- PES历史同口径资源9.758338124G vs9.762532428G、median45.457765 vs33.915601ms（+34.0320%）、P9049.526253 vs37.252200ms（+32.9485%）、alloc930981888 vs936763392（−.61718%）；15%条件false，纯TRAIN峰值UNKNOWN，不称更快。
- M222-AOC source0314b932a92a8cc7f67804068ecb1c1f7a5f2e33单父9c；祖先两顺序共享T diamond差q，fine q与原truefinepath直接uppermeans，原3LN3skip/HCG单inst。原f7 NULL/ref5c/proof83d/c11/native9cf/op e45/release630保持；父9c/PES技术receipt已就绪，但GPU0仍原PES占用，原生/resources NOT_RUN。
- AOC disabled promotion38ab/d9fa仅准备；原d3 shaaoc错/拒签d66a及修正原件保留，是私有准备接口修正，不是模型/native revision。实际raw/review/peer仍None；source/native/op/模型协议无修订。
- M223-FCB原型44c63/manifest95ae9872/协议3809eecd/源审c91f7完全不变，原code/source/actualparent NULL/ref9c不回填。真scene-local fine×coarse shared q，fine/coarse双marginal，middle原fineparent均值再组合，真支持从原point路径去重确定，无跨scene，原3LN3skip/HCG/单inst保持。
- 本轮FCB实际isolated commit d4d062ef075abfe7cde93d4b4347ce146572762f单父AOC0314；proof0a792/独审408dae，精确9A/9blob=44c63，isolated_versions/fcb_89d05b33 clean。main/runtime仍9c，9c→d4d累计18A不可直接ff；不是模型修订或已测版本。
- FCB条件native {native_ref['sha256']} /op {op_ref['sha256']} 已真实静态冻结并独审，正式capability False但10active字段全NULL；原DRAFTTrue/None草案保留。原resourceAST/handlers/unsupported/common动态schema保持；新hook两map+2GELU+3mean，wholecore原lossaggregate有限非零/整体真实更新为将来门。Torch/autograd/native TRAIN/resources均NOT_RUN。
- FCB stagevalidation/未入队/无receipt/exp；mutation需未来AOC真实技术receipt+actual main及remote runtime0314，然后fresh owner/原deadline/source-assets-idle-GPU0UUID-三锁。无需AOC训练结束/效果作为技术门。当前main9c，真实local guard因缺AOC技术receipt拒绝/transport0；若AOC不提升或main改父，保留条件原件另存实际兼容同9源版本，禁止盲18A/siblingff。

## Closed Or Failed Directions
- APF/e759原DataLoader before-forward dtype crash、HPC73ba stopped_unknown/CTS14/BFC overlap与触发样本/RNG/上游causeUNKNOWN保持，不因后续运行成功宣称旧公共loader已修复。
- 旧10hold不重开；M206用户暂停/dispatch_hold/noPID，PCE2+extra1/RSTR2已尽/HAP旧授权已消费，无GPU0迁移或自动恢复。其他146历史候选/旧负结果与冻结门保持。

## Running And Queue
- 原PES PID2265073/start88396735，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pes_20261029_175027.log；早期UTC12:07 TRAIN3 4020→4025、两val .2965591251850128/.3763071894645691，peer2fcf；最新UTC{stamp} TRAIN{last[0]}/50 {samples[0]['last_native_step'][1]}→{last[1]}/4686，原identity/8源/YAML77e/GPU0context保持，全部原metric lines如实partial。
- queue launch_verifiedtrue/training_progress但旧dispatch_phase progress_pending不能重放；M206waiting不ready。AOC blocked exclusive_gpu_slot/resumevalidation，当前canonical实际原PES GPU0busy证据见final_records_result；FCB validation条件源/工具准备，无新队列/启动/GPU1/驱逐/信号。

## Open Questions And Risks
- PES长链遗忘/串行kernel与最终收益未知；AOC q可能丢共有语义/仿射fine项取消/b=c零差。FCB同q双marginal有代数耦合/全局洗平风险，原输入本可能已global，不宣称新信息/已修瓶颈或新颖性。
- FCB线性MAC源估较原多.1048576G，不是wholemodel10G/延迟/显存PASS；纯TRAIN峰值未知。逐map/列/row/pair/bias零合法描述，无新FP32守恒/Jacobian/逐map正性/多root覆盖门。

## Last Tick
- 149ID不增，本轮0新候选/0模型修订/1实际isolated source commit/0nativearm/0准入/0启动/0新归档；完成已有FCB条件版本与原生/操作工具准备，不重复算旧PES原生或历史DCE。
- 当轮fresh canonical GPU0 physical resource_check绑定原owner/context，原PES计算PID仍在；26生命周期文件/28用户字节-status-indexempty/其他146候选/原型44c63 NULL与source9c主线保持。FCB实际技术依赖尚未满足，未造active binding/manifest/lease或actual结果。
- 当前基线post_tick_baseline.json含HEAD9c/26账/28用户/index/149digest/PES9source；后续fresh tick按真实PES原PID/start/log续观，先AOC native，再FCB条件父链，不能回退5c或重放旧dispatch。完整六段report/finish按原token收尾，实际完成以receipt为准。
'''
        assert len(memory.splitlines()) < 120
        local_stamp = datetime.fromisoformat(stamp).astimezone(timezone(timedelta(hours=8))).strftime('%m月%d日%H:%M:%S')
        notes = {'actions': [
            f'上海{local_stamp}，原M221-PES在GPU0第{last[0]}/50轮{samples[0]["last_native_step"][1]}→{last[1]}/4686，原PID/start/log/source9c/部署YAML与GPU0 context保持；已打印{count}次验证，partial best{best}，训练尚未完成。',
            '已有FCB精确9源保存为实际isolated d4d062单父AOC0314，9blob与原44c63完全相同，19次只读Git独审通过。主线/runtime9c保持，原NULL原型不回填；从当前主线到该child有18A，不直接跨未测父快进。',
            '完成FCB条件native与operational工具、原生schema/透明捕获/原resourceAST/版本完整性静态检查及独立审查；原生YAML/任务设置保持，正式capability虽已绑定真实版本但十个执行字段全NULL，未执行Torch/autograd/原生TRAIN或资源实测。',
            '当前实际local mutation guard拒绝未提升的父版本，transport0；当轮canonical GPU0-only物理占用看到原PES，AOC继续等待卡。保留全部既有运行/旧hold，未用GPU1或改调度，26账/28用户/index保持。'],
            'decisions': [
                '最佳仍M95 .5020，目标.5100；PES早期partial值不能证明最终上涨或机制失败，本轮没有完成的新训练。',
                '优先原PES自然完成后的AOC paired自然TRAIN2与同口径resources；真实通过才准入派发并核原生步增。FCB在后续实际AOC技术receipt及main/runtime0314提升后再执行，不新增AOC训练效果/完成的技术依赖门。',
                '若AOC未技术提升或主线变化，保留FCB条件源与历史证据，另存实际兼容同9源版本；严禁9c→d4d累计18A或sibling盲ff。代码保存/工具静态通过不冒充原生、10G、显存、创新或效力PASS。',
                '不为额度再造候选；先把已有FCB准备具体化。原数据/seed/schedule/主线/禁用项/资源和旧失败/暂停授权保持，无需用户重复授权。']}
        u.save(HERE / 'final_records_intent.json', {'owner': EXPECTED, 'recorded_at': now, 'research_work_before_sha256': before,
            'changed_candidate_ids': [PES, AOC, FCB], 'latest_original_progress': u.ref(latest), 'fresh_occupation': occupation,
            'scope': 'Actual observations, memory and report notes only. No primary/runtime/native/lifecycle/queue/launch operation or pre-signed postflight.'})
        guard()
        assert sha(path) == before
        u.atomic(path, work)
        u.atomic(ROOT / 'pipeline/codex_memory.md', memory, text=True)
        u.save(HERE / 'report_notes.json', notes)
        u.primary_protection(b)
        u.lifecycle_protection(b)
        post = dict(b)
        post.update(recorded_at=now, owner=EXPECTED, candidate_digests={x['id']: u.digest(x) for x in work['candidates']},
                    research_work_sha256=sha(path), latest_original_progress=u.ref(latest), fresh_occupation=occupation,
                    conditional_FCB=u.ref(HERE / 'fcb_registration_result.json'))
        u.save(HERE / 'post_tick_baseline.json', post)
        u.save(HERE / 'final_records_result.json', {'owner': EXPECTED, 'status': 'MEASURED_PROGRESS_AND_CONDITIONAL_TOOLS_SAVED_POSTFLIGHT_NOT_YET_RUN',
            'candidate_count': 149, 'new_candidates': 0, 'model_revisions': 0, 'isolated_source_commits': 1, 'native_arms': 0,
            'admissions': 0, 'formal_launches': 0, 'terminal_archives': 0, 'latest_original_progress': u.ref(latest),
            'fresh_occupation': occupation, 'post_tick_baseline': u.ref(HERE / 'post_tick_baseline.json'), 'memory_lines': len(memory.splitlines()),
            'other146_candidates_and26_ledgers_and28_user_paths_and_index_preserved': True})
        print(json.dumps({'status': 'Measured progress and conditional FCB capability saved; postflight not yet run',
                          'memory_lines': len(memory.splitlines()), 'PES_partial_best': best, 'PES_step': last,
                          'baseline': u.ref(HERE / 'post_tick_baseline.json')}))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
