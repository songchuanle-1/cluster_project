"""Finish the audit narrative only after reviewed preparation registration."""
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
TOKEN = '4694ba96c2da476291160b2883ce3c7a'

def read(path):
    return json.loads(Path(path).read_text('utf-8'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}

def save(path, value):
    tmp = path.with_name(path.name + '.' + TOKEN + '.tmp')
    with tmp.open('x', encoding='utf-8') as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)

def main():
    owner = guard()
    reg = read(HERE / 'native_preparation_registration.json')
    assert reg['token'] == TOKEN and reg['native_resources'] == 'NOT_RUN'
    prep = ROOT / reg['preparation']['path']
    review = ROOT / reg['independent_review']['path']
    assert sha(prep) == reg['preparation']['sha256'] and sha(review) == reg['independent_review']['sha256']
    packet = prep.parent
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        protected = ['queue.json', 'running.json', 'experiments/M211-BTC.json', 'experiments/M212-BCR.json', 'experiments/M206-CGCA.json', 'admissions/M211-BTC.json', 'admissions/M212-BCR.json']
        before = {name: sha(ROOT / 'pipeline' / name) for name in protected}
        evidence = '; '.join(str(ROOT / x['path']) + ' SHA' + x['sha256'] for x in [reg['preparation'], reg['independent_review'], reg['resource_availability'], ref(HERE / 'progress_and_boundary_review.json')])
        command = ['C:/Program Files (x86)/Git/bin/bash.exe', str(SKILL / 'log_decision.sh'), 'cluster_project', 'other',
                   '两卡持续训练、现有2项储备已满且CTS原生工具待补齐',
                   '继续原BTC0/BCR1；保存CTS禁用原生检查包与实际本地检查，BFC优先等空卡原生验证',
                   '不新增候选或入队；CTS原9源/YAML冻结且code/parent仍null，真实TRAIN2、资源及准确率未测；不把脚本检查当训练准入，不恢复M206、不改资源调度或旧hold。', evidence]
        done = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True, env=dict(os.environ, PROJECT_ROOT='D:/project', PYTHONDONTWRITEBYTECODE='1'))
        decision_path = Path(done.stdout.strip().split(' -> ', 1)[1])
        assert decision_path.is_file() and decision_path.is_relative_to(ROOT / 'pipeline/decisions')
        work = read(ROOT / 'pipeline/research_work.json')
        assert work['tick_attempt']['tick_started_at'] == owner['generated_at']
        for cid in ['hierarchy-parent-butterfly-token-composition', 'hierarchy-parent-cyclic-triadic-state-composition']:
            c = next(c for c in work['candidates'] if c['id'] == cid)
            entry = ref(decision_path)
            if entry not in c['evidence']:
                c['evidence'].append(entry)
        work['updated_at'] = datetime.now(timezone.utc).isoformat()
        save(ROOT / 'pipeline/research_work.json', work)
        memory_path = ROOT / 'pipeline/codex_memory.md'
        memory = memory_path.read_text('utf-8')
        lines = memory.splitlines()
        goal = next(i for i, line in enumerate(lines) if line.startswith('- 最新接管'))
        lines[goal] = '- 最新接管' + TOKEN + '；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致；generated' + owner['generated_at'] + '/原deadline' + owner['deadline_at'] + '不延长。前3824收据已核FINALIZED/released，lock/pending消失后才begin；本轮真实finish状态以receipt为准，不预签。'
        active = lines.index('## Active Hypotheses') + 1
        lines.insert(active, '- 本轮4694推进既有CTS而非新增候选：禁用native包 ' + reg['preparation']['path'] + ' SHA' + reg['preparation']['sha256'] + '；独审 ' + reg['independent_review']['path'] + ' SHA' + reg['independent_review']['sha256'] + '。实际本地syntax/observer/拒绝入口检查已完成；DRAFT=True、10active与code/parent仍null，资源函数沿用原口径，非Torch/native/效能证明。原bfab9源与7036协议不变；无adapter/实际binding/版本/receipt/queue。')
        for short, eid in [('btc', 'M211-BTC'), ('bcr', 'M212-BCR')]:
            proof_path = HERE / (short + '_progress_observation.json')
            proof = read(proof_path)
            a, b = [o['data'] for o in proof['observations']]
            stamp = datetime.fromisoformat(proof['observations'][-1]['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
            i = next(i for i, line in enumerate(lines) if line.startswith('- ' + eid) and '截至' in line or line.startswith('- ' + eid + ' GPU'))
            gpu = 0 if short == 'btc' else 1
            scientific = '00e2b18c6b8d568a64edb496e6979d766440883c' if short == 'btc' else '11a811618179ab1ddc0cee299194667413b7fdb9'
            lines[i] = '- ' + eid + ' GPU' + str(gpu) + '原PID' + str(b['pid']) + '/start' + b['start_ticks'] + '，截至' + stamp + '上海，原argv/cwd/fd1/UUID/model8/YAML与公共HEAD11a保持，Train' + str(b['train_progress'][0]) + '/50 ' + str(a['train_progress'][2]) + '→' + str(b['train_progress'][2]) + '/4686；本轮proof ' + ref(proof_path)['path'] + ' SHA' + sha(proof_path) + '。科学source' + scientific + '；原receipt保持，不重启或信号。'
        i = next(i for i, line in enumerate(lines) if line.startswith('- BTC/BCR正式训练准确率'))
        lines[i] = '- BTC/BCR最终训练准确率UNKNOWN；本轮18:05上海preflight监控Best BTC.4914(25/50/noimprove3/10)、BCR.4682(8/50/noimprove0/10)，均非终态，当前验证游标不当best。M95仍.5020，目标.5100/gap.0080；工具/原生门通过不证明上涨或新颖，不调seed/schedule/阈值或test集选机制。'
        last = lines.index('## Last Tick')
        lines = lines[:last + 1] + [
            '- 本轮4694 begin一次monitor/goal/已有合格派发；design/candidate_budget2/reserve2/creation0，2running/0ready/0新终态/0operationalissue；due仅BFC与CTS，旧9notdue未重开或复测。',
            '- 原BTC25/50 1462→1467、BCR8/50 694→699，原PID/start/argv/cwd/fd1/source/YAML/UUID保持；两卡真实NVML context均占用。进度独审1d085feb…，BFC availability25533dc0…复用这些原真实观测，不重复GPUquery；NoTransport prepare0/1忙槽早拒绝，未绑定/执行。',
            '- 本轮仅补现有CTS禁用native检查包与独审，未新建候选或Git版本；code/source/futureparent仍null，BFC48fc及原模型/worker/协议保持。CTS原生TRAIN2/资源/效果未测，不能入队；BFC原生验证仍优先。',
            '- 0新候选/0新准入/0新queue/0launch/0GPU诊断计算/0源主线推进；1项真实本地implementation_test完成，无Torch，不强凑预算、不等待整场训练。M206pause/resumefalse、2active/原收据及primary11a/28status/index空保持。',
            '- 决策' + decision_path.relative_to(ROOT).as_posix() + '；当前新证据tick_4694ba96。goal0441/服务器d527/2e892+90f/10G/固定data-seed-schedule/YAML/禁项/Phase1/旧失败修订边界不变。七段memory、notes后canonical六段report与原token真实finish核FINALIZED/released及lock/pending消失；释放后不回写。', '']
        memory = '\n'.join(lines)
        assert len(lines) < 120 and memory.count('\n## ') == 7
        save(memory_path, memory)
        notes = {'actions': [
            'preflight已观察/派发既有合格队列；2running/0ready/0terminal，现有BFC+CTS储备已满、creation0；不新增候选，旧9挂起未到期不复测或索授权。',
            '真实原BTC25/50 1462→1467、BCR8/50 694→699，两样本原PID/start/argv/cwd/fd1/UUID/模型8/YAML/HEAD保持；36项独审无concern。18:05上海监控Best BTC.4914、BCR.4682是训练中记录，非终态或新champion。',
            'BFC实际本地current-owner/context/原deadline与忙槽拒绝检查通过，0transport；当前两卡资源判定复用本轮真实NVML/进度证据，均有原训练占用，无额外query、GPU诊断计算、活动binding/lease或native PASS。',
            '既有CTS补齐禁用native worker/runtime/template及必要本地检查和独立审查；原bfab9独立源/原YAML与7036协议保留，不造Git版本或固定未来父提交。真实源版本、操作adapter和实际原生测试仍未完成。',
            'CTS未来原TRAIN2 observer按真实同父循环同步旧状态/三路输入、r>=1和三W列块原loss梯度及更新记录；逐call零允许，缺覆盖INCONCLUSIVE不换样本/seed/precision/阈值。原resources口径不变，本地检查不签10G/原生/准确率。',
            '保护两原运行及M206暂停；无新admission/queue/launch/主线源码推进，不抢占、迁卡、overlay、改资源/调度/禁项或历史修订。'],
            'decisions': [
                'BFC保持优先：自然空卡并canonical处理真实终态后，fresh owner/原deadline/UUID/idle/三锁/assets核验才能跑原M95/BFC TRAIN2及同口径资源，通过真实结果审后再准入。',
                'CTS只记录现有候选工具准备推进，仍implementation、code/parent null。未来选择兼容实际main包装原9blob，再审核操作副本；本轮DRAFT与null拒绝执行，准备时间和旧lease不授权未来计算。',
                '尚无新训练准确率结论；无需用户决定或重复授权，已有范围内继续。完整六段留档，本轮finish实际结果由canonical收据确认，未发生前不预签。']}
        save(HERE / 'report_notes.json', notes)
        guard()
        assert before == {name: sha(ROOT / 'pipeline' / name) for name in protected}
        print(json.dumps({'status': 'NOTES_MEMORY_DECISION_PERSISTED_POSTFLIGHT_NOT_YET_CALLED',
                          'decision': ref(decision_path), 'memory_lines': len(lines)}, ensure_ascii=False))
    finally:
        lock.close()

if __name__ == '__main__':
    main()
