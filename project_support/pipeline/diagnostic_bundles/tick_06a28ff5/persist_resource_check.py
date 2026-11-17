"""Record the current occupied-slot check without changing frozen research."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re
import subprocess
import sys
from anchor_bfc_packet import guard

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN = '06a28ff5b75f44a2a8ae1be627d90aec'
BFC = 'hierarchy-parent-butterfly-token-composition'
CTS = 'hierarchy-parent-cyclic-triadic-state-composition'

def read(path):
    return json.loads(Path(path).read_text('utf-8'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()

def save(path, value):
    tmp = path.with_name(path.name + '.' + TOKEN + '.tmp')
    with tmp.open('x', encoding='utf-8') as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)

def main():
    owner = guard()
    av_path = HERE / 'bfc_native_resource_availability.json'
    availability = read(av_path)
    assert availability['owner_token'] == TOKEN and availability['result'] == 'blocked'
    review_path = HERE / 'progress_and_resource_review.json'
    assert read(review_path)['material_concerns'] == []
    first_path = HERE / 'btc_progress_observation.json'
    first = read(first_path)
    assert first['same_exact_registered_process_and_native_TRAIN_growth'] is False
    assert all(s['data']['train_progress'] == [29, 50, 4686, 4686] and not s['data']['errors'] for s in first['observations'])
    paths = {'btc': HERE / 'btc_progress_after_boundary_observation.json', 'bcr': HERE / 'bcr_progress_observation.json'}
    proofs = {short: read(path) for short, path in paths.items()}
    assert all(proof['same_exact_registered_process_and_native_TRAIN_growth'] is True for proof in proofs.values())
    assert not (HERE / 'bfc_execution').exists()
    factual = (ROOT / 'pipeline/reports' / ('summary_' + TOKEN + '.md')).read_text('utf-8')
    metrics = {}
    for short in paths:
        match = re.search(r'\[model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_' + short + r'\] Best=([0-9.]+) (\d+)/50 no_improve=(\d+)/10', factual)
        assert match
        metrics[short] = {'best': match[1], 'epoch': int(match[2]), 'no_improve': int(match[3])}
    git = ['git', '-C', str(ROOT / 'Cluster')]
    assert subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip() == '11a811618179ab1ddc0cee299194667413b7fdb9'
    status = subprocess.check_output(git + ['status', '--porcelain=v1', '--untracked-files=all'])
    assert len(status.splitlines()) == 28 and not subprocess.check_output(git + ['diff', '--cached', '--name-only']).strip()
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT)); assert lock is not None
    try:
        guard()
        protected = ['queue.json', 'running.json', 'experiments/M211-BTC.json', 'experiments/M212-BCR.json', 'experiments/M206-CGCA.json', 'admissions/M211-BTC.json', 'admissions/M212-BCR.json']
        before = {name: sha(ROOT / 'pipeline' / name) for name in protected}
        work = read(ROOT / 'pipeline/research_work.json')
        bfc = next(c for c in work['candidates'] if c['id'] == BFC)
        untouched = {c['id']: digest(c) for c in work['candidates'] if c['id'] != BFC}
        cts = next(c for c in work['candidates'] if c['id'] == CTS)
        assert bfc['stage'] == 'validation' and bfc['code_commit'] == '48fc302c3c02ffef0b241be3593c386b6b65a72e'
        assert bfc['native_execution_code_commit'] is None and bfc['native_smoke_status'] == bfc['resource_profile_status'] == 'NOT_RUN'
        assert cts['stage'] == 'implementation' and cts['code_commit'] is None and cts['future_version_parent'] is None
        evidence_paths = [av_path, review_path, first_path, *paths.values(), HERE / 'bfc_actual_local_guard_integration.json']
        for path in evidence_paths:
            entry = ref(path)
            if entry not in bfc['evidence']: bfc['evidence'].append(entry)
        bfc['resource_wait']['current_observation'] = ref(av_path)
        bfc['resource_wait']['observed_at'] = availability['recorded_at']
        work['tick_attempt'] = {'tick_started_at': owner['generated_at'], 'candidate_id': BFC,
            'kind': 'resource_check', 'result': 'blocked',
            'command': 'python -B -X utf8 ' + str(HERE / 'check_native_resource_availability.py'),
            'observation': 'Actual current physical0/1 NVML contexts belong to protected original BTC/BCR processes. First BTC samples at completed TRAIN29/VAL29 boundary had no TRAIN increment and were preserved. One exact-process follow-up establishes TRAIN30 95-to100; BCR TRAIN12 3613-to3620. Both authorized slots remain occupied; current local guard refuses before execution transport. This is availability evidence, not native backward/resource-profile PASS.',
            'evidence': [ref(path) for path in evidence_paths]}
        work['updated_at'] = datetime.now(timezone.utc).isoformat()
        assert untouched == {c['id']: digest(c) for c in work['candidates'] if c['id'] != BFC}
        save(ROOT / 'pipeline/research_work.json', work)
        memory_path = ROOT / 'pipeline/codex_memory.md'
        lines = memory_path.read_text('utf-8').splitlines()
        i = next(i for i, line in enumerate(lines) if line.startswith('- 最新接管'))
        lines[i] = '- 最新接管' + TOKEN + '；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致；generated' + owner['generated_at'] + '/原deadline' + owner['deadline_at'] + '不延长。前8878已核FINALIZED/released、lock/pending消失后begin；本轮真实finish以receipt为准，不预签。'
        if not any('用户询问当前创新设计' in line for line in lines):
            i = lines.index('## Champion And Baseline')
            lines.insert(i, '- 2026-10-25用户询问当前创新设计：已说明BFC/CTS只改中层，fine/coarse沿用M95，按层分工的完整注意力设计尚未落地，新颖性/收益未证。此问答未改变项目目标、资源、暂停、授权或候选创建预算。')
            lines.insert(i + 1, '')
        summary = []
        for short, eid, gpu, scientific in [('btc', 'M211-BTC', 0, '00e2b18c6b8d568a64edb496e6979d766440883c'), ('bcr', 'M212-BCR', 1, '11a811618179ab1ddc0cee299194667413b7fdb9')]:
            proof = proofs[short]; a, b = [sample['data'] for sample in proof['observations']]
            stamp = datetime.fromisoformat(proof['observations'][-1]['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
            progress = str(b['train_progress'][0]) + '/50 ' + str(a['train_progress'][2]) + '→' + str(b['train_progress'][2]) + '/4686'
            summary.append(eid + ' Train' + progress)
            i = next(i for i, line in enumerate(lines) if line.startswith('- ' + eid + ' GPU'))
            lines[i] = '- ' + eid + ' GPU' + str(gpu) + '原PID' + str(b['pid']) + '/start' + b['start_ticks'] + '，截至' + stamp + '上海，原argv/cwd/fd1/UUID/model8/YAML/公共HEAD11a保持，Train' + progress + '；本轮proof ' + ref(paths[short])['path'] + ' SHA' + sha(paths[short]) + '。科学source' + scientific + '与原receipt保持，无信号或重启。'
        i = next(i for i, line in enumerate(lines) if line.startswith('- BTC/BCR最终训练准确率'))
        lines[i] = '- BTC/BCR最终训练准确率UNKNOWN；本轮22:03上海preflight监控Best BTC' + metrics['btc']['best'] + '(29/50/noimprove7/10)、BCR' + metrics['bcr']['best'] + '(12/50/noimprove2/10)属采集时训练中记录。BTC后续已自然Train30，首Val29完成游标不当best。M95仍.5020，目标.5100/gap.0080；常规增长无新完成结论，不改seed/schedule/阈值或test集选机制。'
        last = lines.index('## Last Tick')
        lines = lines[:last + 1] + [
            '- 本轮06a2 begin一次monitor/goal/已有合格派发；design/candidate_budget2/reserve2/creation0，2running/0ready/0新终态/0operationalissue；due仅BFC/CTS，旧9notdue不重查，沿用8878有界metadata记录。',
            '- 首BTC在Train29 4686/4686和Val29 363/363交界，3秒窗TRAIN增长false已保留d4d16f…且非训练故障；一次同原PID/start/源/UUID/唯一log复核后Train30 95→100，710f237d…。BCR原Train12 3613→3620，efdccbe9…。两卡原NVML context忙，0信号/重启/共享overlay。',
            '- 实际BFC availability resource_check blocked f5b8ce…；current owner/context/原deadline本地busy guard在probe/dir/manifest/lease前拒绝，0transport。无GPU诊断计算/新候选/版本/准入/queue/launch，保留BFC先原生与CTS后续封装顺序，不重跑52/61/42静态套件或凑额度。',
            '- 仅BFC资源证据追加，CTS、两训练candidate及其他全部candidate canonical digest保持；M206 pause/resumefalse/noPID及queue/running/原exp/receipt、primary11a/28status/index空保持。旧scope/失败/修订/资源边界/目标/调度/data-seed-schedule/YAML/禁项不变。',
            '- 无新增研究决策文件或实质状态变化、失败、需用户处理事项；完整六段notes/report和七段memory留档。finish真实核FINALIZED/released与lock/pending消失后不回写；例行健康/等待资源选择DONT_NOTIFY。', '']
        memory = '\n'.join(lines)
        assert len(memory.splitlines()) < 120 and memory.count('\n## ') == 7
        save(memory_path, memory)
        notes = {'actions': [
            'preflight查询/派发既有合格队列后，仍2running/0ready/0terminal/0operationalissue；现有BFC+CTS储备已满、creation0，不新增候选或新研究工具。',
            'BTC首双样本原Train29及Val29都完成，3秒窗口无TRAIN增长并原样保存；没有据此推断失败。一轮边界复核确认原PID/start/argv/cwd/fd1/source/YAML/UUID不变，Train30 95→100；BCR Train12 3613→3620正常增长。',
            '22:03上海preflight Best BTC.4914/BCR.4848是训练中采集值，BTC后续自然进30；无新champion/终态，验证完成游标不当best，当前最终效能未知。',
            'BFC当前资源可用性复用本轮真实NVML/原native进度，两个授权物理卡仍有原任务；本地current-owner/context/原deadline busy拒绝0transport。resource_check blocked只指无安全空槽，不代表FLOPs/显存/延迟profile或原生PASS。',
            '既有BFC源48fc/worker8839与CTS源bfab/禁用包ff7及未来parent null保持；旧9未到期不复测/读655正文或旧grantbody。M206暂停、旧科学状态及所有授权边界不变；0新版本/准入/queue/launch/运行变更。'],
            'decisions': ['本轮没有新增研究或调度决策、失败或需用户处理事项。沿用BFC优先等自然空卡后fresh owner/UUID/idle/三锁/assets复核及原生测试；CTS保留准备，M206暂停。完整留档后例行无变化保持静默。']}
        save(HERE / 'report_notes.json', notes)
        guard()
        assert before == {name: sha(ROOT / 'pipeline' / name) for name in protected}
        assert subprocess.check_output(git + ['status', '--porcelain=v1', '--untracked-files=all']) == status
        after = read(ROOT / 'pipeline/research_work.json')
        assert untouched == {c['id']: digest(c) for c in after['candidates'] if c['id'] != BFC}
        with (HERE / 'resource_check_persisted.json').open('x', encoding='utf-8') as stream:
            json.dump({'recorded_at': datetime.now(timezone.utc).isoformat(), 'token': TOKEN,
                       'candidate_id': BFC, 'tick_attempt_result': 'blocked', 'resource_availability': ref(av_path),
                       'independent_review': ref(review_path), 'original_boundary_proof_preserved': ref(first_path),
                       'all_other_candidate_records_unchanged': True, 'protected_queue_runs_receipts_pause_unchanged': True,
                       'new_candidates_admissions_or_launches': 0, 'new_research_decision': False,
                       'notification': 'DONT_NOTIFY_ROUTINE_UNCHANGED', 'postflight': 'NOT_YET_CALLED'}, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps({'status': 'ROUTINE_BUSY_CARD_CHECK_AND_NATIVE_PHASE_RECONCILIATION_PERSISTED',
                          'memory_lines': len(memory.splitlines()), 'notification': 'DONT_NOTIFY'}, ensure_ascii=False))
    finally:
        lock.close()

if __name__ == '__main__':
    main()
