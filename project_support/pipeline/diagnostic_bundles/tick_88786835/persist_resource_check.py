"""Persist a real busy-card check; retain every source, job and held route."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import subprocess
import sys
from anchor_bfc_packet import guard

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN = '88786835ee7344aea8e08c68612733f6'
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
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)

def main():
    owner = guard()
    availability_path = HERE / 'bfc_native_resource_availability.json'
    availability = read(availability_path)
    assert availability['owner_token'] == TOKEN and availability['result'] == 'blocked'
    review_path = HERE / 'progress_and_resource_review.json'
    review = read(review_path)
    assert review['material_concerns'] == []
    held_path = HERE / 'held_boundary_check.json'
    held = read(held_path)
    assert held['material_concerns'] == [] and held['new_action'] is False and held['user_decision'] is False
    assert not (HERE / 'bfc_execution').exists()
    protected = ['queue.json', 'running.json', 'experiments/M211-BTC.json', 'experiments/M212-BCR.json', 'experiments/M206-CGCA.json', 'admissions/M211-BTC.json', 'admissions/M212-BCR.json']
    git = ['git', '-C', str(ROOT / 'Cluster')]
    assert subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip() == '11a811618179ab1ddc0cee299194667413b7fdb9'
    status = subprocess.check_output(git + ['status', '--porcelain=v1', '--untracked-files=all'])
    assert len(status.splitlines()) == 28
    assert not subprocess.check_output(git + ['diff', '--cached', '--name-only']).strip()
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        before = {name: sha(ROOT / 'pipeline' / name) for name in protected}
        work = read(ROOT / 'pipeline/research_work.json')
        bfc = next(c for c in work['candidates'] if c['id'] == BFC)
        cts = next(c for c in work['candidates'] if c['id'] == CTS)
        assert bfc['stage'] == 'validation' and bfc['code_commit'] == '48fc302c3c02ffef0b241be3593c386b6b65a72e'
        assert bfc['native_execution_code_commit'] is None and bfc['native_smoke_status'] == bfc['resource_profile_status'] == 'NOT_RUN'
        assert cts['stage'] == 'implementation' and cts['code_commit'] is None and cts['future_version_parent'] is None
        cts_digest = digest(cts)
        paths = [availability_path, review_path, HERE / 'btc_progress_observation.json', HERE / 'bcr_progress_observation.json', HERE / 'bfc_actual_local_guard_integration.json']
        for path in paths:
            entry = ref(path)
            if entry not in bfc['evidence']:
                bfc['evidence'].append(entry)
        bfc['resource_wait']['current_observation'] = ref(availability_path)
        bfc['resource_wait']['observed_at'] = availability['recorded_at']
        work['tick_attempt'] = {'tick_started_at': owner['generated_at'], 'candidate_id': BFC,
            'kind': 'resource_check', 'result': 'blocked',
            'command': 'python -B -X utf8 ' + str(HERE / 'check_native_resource_availability.py'),
            'observation': 'Fresh root read-only SSH/NVML and exact original native TRAIN growth confirm both authorized physical GPUs occupied by protected BTC/BCR jobs. Local current-owner guard refuses both before transport/materialization. This is actual availability evidence, not candidate resource profiling/native PASS; no safe diagnostic slot, new candidate or execution binding.',
            'evidence': [ref(path) for path in paths]}
        work['updated_at'] = datetime.now(timezone.utc).isoformat()
        assert digest(cts) == cts_digest
        save(ROOT / 'pipeline/research_work.json', work)
        memory_path = ROOT / 'pipeline/codex_memory.md'
        lines = memory_path.read_text('utf-8').splitlines()
        i = next(i for i, line in enumerate(lines) if line.startswith('- 最新接管'))
        lines[i] = '- 最新接管' + TOKEN + '；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致；generated' + owner['generated_at'] + '/原deadline' + owner['deadline_at'] + '不延长。前4694已核FINALIZED/released、lock/pending消失后begin；本轮真实finish以receipt为准，不预签。'
        for i, line in enumerate(lines):
            if line.startswith('- 本轮4694推进既有CTS'):
                lines[i] = line.replace('- 本轮4694推进既有CTS', '- 4694轮已推进既有CTS')
            elif line.startswith('- 本轮BFC原NoTransport guard在真实3824'):
                lines[i] = line.replace('- 本轮BFC原NoTransport', '- 3824轮BFC原NoTransport')
            elif line.startswith('- CTS196864参数'):
                lines[i] = line.replace('全部native/资源/效能UNKNOWN，无worker/lease/receipt/queue。', '全部native/资源/效能UNKNOWN；4694已备禁用worker，实际lease/receipt/queue仍无。')
            elif line.startswith('- 旧8hold本轮3824'):
                lines[i] = '- 旧8hold在8878轮到期仅一次有界canonical全记录digest、655声明path/hash pair签名及14授权目录path-size-mtime核，与3824/4a08基准一致；held_boundary_check.json SHA' + sha(held_path) + '。0个655正文read/hash/exists/stat及0旧grantbodyread/hash，new_action/user_decision均false；M206queue/exp完整digest同，无新scope/修订/恢复许可。'
        for short, eid, gpu, scientific in [('btc', 'M211-BTC', 0, '00e2b18c6b8d568a64edb496e6979d766440883c'), ('bcr', 'M212-BCR', 1, '11a811618179ab1ddc0cee299194667413b7fdb9')]:
            path = HERE / (short + '_progress_observation.json')
            proof = read(path)
            a, b = [sample['data'] for sample in proof['observations']]
            stamp = datetime.fromisoformat(proof['observations'][-1]['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
            i = next(i for i, line in enumerate(lines) if line.startswith('- ' + eid + ' GPU'))
            lines[i] = '- ' + eid + ' GPU' + str(gpu) + '原PID' + str(b['pid']) + '/start' + b['start_ticks'] + '，截至' + stamp + '上海，原argv/cwd/fd1/UUID/model8/YAML/公共HEAD11a保持，Train' + str(b['train_progress'][0]) + '/50 ' + str(a['train_progress'][2]) + '→' + str(b['train_progress'][2]) + '/4686；本轮proof ' + ref(path)['path'] + ' SHA' + sha(path) + '。科学source' + scientific + '与原receipt保持，无信号或重启。'
        i = next(i for i, line in enumerate(lines) if line.startswith('- BTC/BCR最终训练准确率'))
        lines[i] = '- BTC/BCR最终训练准确率UNKNOWN；本轮20:06上海preflight监控Best BTC.4914(27/50/noimprove5/10)、BCR.4848(10/50/noimprove0/10)，均非终态，不把验证游标当best。M95仍.5020，目标.5100/gap.0080；常规训练增长不是新机制或完成结论，不调seed/schedule/阈值或test集选机制。'
        last = lines.index('## Last Tick')
        lines = lines[:last + 1] + [
            '- 本轮8878 begin一次monitor/goal/已有合格派发；design/candidate_budget2/reserve2/creation0，2running/0ready/0新终态/0operationalissue；11due含2准备储备+旧9挂起，储备已满不新增候选或工具。',
            '- 原BTC27/50 3419→3425、BCR10/50 2189→2194，原PID/start/argv/cwd/fd1/UUID/model/YAML/HEAD均保持；NoTransport prepare0/1因注册忙槽早拒绝，当前真实两卡可用性判blocked，未创建executiondir/lease/manifest或GPU诊断计算。',
            '- 对到期旧8+M206做一次有界metadata复核，与3824一致；不读/hash/stat655正文或旧授权正文、不重开旧scope/失败/修订、不恢复M201/M206。当前独审及完整proof见tick_88786835，非旧结果重标。',
            '- 本轮无实质状态变化、新准备、失败或需用户处理事项；0新候选/准入/queue/launch/Git推进/原生诊断，1项真实availability resource_check blocked。原BFC48fc/8512/8839和CTS源bfab/禁用包ff7/版本null保持，不重跑52/61/42静态套件或凑额度；CTS canonical全记录未改。',
            '- 本轮无新增决策文件；完整六段notes/report留档，七段memory当前接管与原授权延续。goal0441/服务器d527/2e892+90f/10G/固定data-seed-schedule/YAML/禁项/Phase1/旧边界不变；两原run/M206pause/primary11a/28status/index保持。finish真实核FINALIZED/released与lock/pending消失后不回写；无变化选择DONT_NOTIFY。', '']
        memory = '\n'.join(lines)
        assert len(memory.splitlines()) < 120 and memory.count('\n## ') == 7
        save(memory_path, memory)
        notes = {'actions': [
            'preflight已查询进展、尝试派发合格队列；2running/0ready/0terminal/0operationalissue，BFC+CTS储备2已满、creation0，不新增候选。',
            '两组真实原PID/start/argv/cwd/fd1/source8/YAML/UUID/HEAD11a核验，BTC27/50 3419→3425、BCR10/50 2189→2194，未见错误；本轮20:06上海监控Best BTC.4914/BCR.4848是训练中记录，非终态或新champion。',
            '当前BFC owner/context/原deadline guard及忙槽早拒绝通过，0transport/0binding。真实资源可用性检查复用本轮NVML与native增长证据，两个授权槽均由原训练占用：resource_check blocked，不是候选FLOPs/延迟/显存profiling或native PASS。',
            '旧8hold canonical digest/655声明ref签名/14授权元数据与3824基准一致；M206queue/exp完整digest同且pause/resumefalse/noPID，new_action/user_decision false，未读/hash/stat655正文或旧grantbody，不复测或重开历史路线。',
            '现有BFC48fc源/worker/完整静态工具及CTS源bfab/禁用包ff7保持；不重跑旧52/61/42静态套件、不新建版本/adapter，不改资源、原YAML/data/seed/schedule/禁项、调度或两原运行；0新准入/队列/launch。'],
            'decisions': ['本轮没有新增研究或调度决策，也无新的需用户处理事项。保留既有BFC优先等待自然空卡、fresh owner/UUID/idle/三锁/assets核验后原生检查；CTS仍待未来兼容源版本及原生验证，M206保持暂停。完整报告留档，例行无变化保持静默。']}
        save(HERE / 'report_notes.json', notes)
        guard()
        assert before == {name: sha(ROOT / 'pipeline' / name) for name in protected}
        assert subprocess.check_output(git + ['status', '--porcelain=v1', '--untracked-files=all']) == status
        assert digest(next(c for c in read(ROOT / 'pipeline/research_work.json')['candidates'] if c['id'] == CTS)) == cts_digest
        with (HERE / 'resource_check_persisted.json').open('x', encoding='utf-8') as stream:
            json.dump({'recorded_at': datetime.now(timezone.utc).isoformat(), 'token': TOKEN,
                       'candidate_id': BFC, 'tick_attempt_result': 'blocked',
                       'resource_availability': ref(availability_path), 'independent_review': ref(review_path),
                       'held_boundary': ref(held_path), 'CTS_canonical_record_unchanged': True,
                       'protected_queue_runs_receipts_and_pause_unchanged': True,
                       'new_candidates_admissions_or_launches': 0, 'new_research_decision': False,
                       'notification': 'DONT_NOTIFY_ROUTINE_UNCHANGED', 'postflight': 'NOT_YET_CALLED'}, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps({'status': 'ROUTINE_RESOURCE_CHECK_BLOCKED_PERSISTED_NO_NEW_EXPERIMENT_OR_DECISION',
                          'memory_lines': len(memory.splitlines()), 'notification': 'DONT_NOTIFY'}, ensure_ascii=False))
    finally:
        lock.close()

if __name__ == '__main__':
    main()
