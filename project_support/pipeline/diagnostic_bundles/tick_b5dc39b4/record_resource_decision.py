"""Record actual additional GPU occupancy without changing any process."""
from pathlib import Path
import hashlib,json,subprocess
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();assert not (HERE/'canonical_decision_record.json').exists()
    p=HERE/'additional_gpu_context_probe.json'
    assert sha(p)=='3eb859cd4be49b516f36576df29d50455719096470ca37dc4aeb1c63ae7f0552'
    d=json.loads(p.read_text('utf8'))
    assert d['current_project_queue_pid_matches']==[] and not d['signals_sent'] and not d['remote_file_writes']
    before=set((ROOT/'pipeline/decisions').glob('*_other.md'))
    args=['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
        'cluster_project','other','两原训练仍增长，但两张授权卡出现额外未登记进程时如何处理？',
        '保留BFC、BCR及不明PID1565126，不驱逐/暂停/迁卡；原生验证继续blocked。因新增占用实质变化通知用户，未识别进程用途前不做处置。',
        '两原PID/start/源码/log与步数保持。NVML实测PID1565126在GPU0/1占9594/9804MiB，两卡总占用约90%，不在当前项目queue。最小proc身份查询PermissionError后停止，不sudo/绕权限/再探查。未执行新的native/资源实验，无训练失败结论。',
        'pipeline/diagnostic_bundles/tick_b5dc39b4/active_runs_progress_observation.json; pipeline/diagnostic_bundles/tick_b5dc39b4/additional_gpu_context_probe.json; pipeline/diagnostic_bundles/tick_b5dc39b4/context_assumption_correction.json']
    result=subprocess.run(args,capture_output=True,text=True,encoding='utf8',check=True,timeout=30)
    added=set((ROOT/'pipeline/decisions').glob('*_other.md'))-before;assert len(added)==1
    p=added.pop();out={'command':args,'returncode':result.returncode,'decision':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}}
    with (HERE/'canonical_decision_record.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(out['decision'],ensure_ascii=False))
if __name__=='__main__':main()
