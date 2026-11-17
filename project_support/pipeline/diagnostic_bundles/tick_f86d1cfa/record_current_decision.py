"""Record actual tool preparation for existing candidates with the canonical helper."""
from pathlib import Path
import hashlib,json,subprocess
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/project/cluster_project')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();assert not (HERE/'canonical_decision_record.json').exists()
    for n in ['cts_checker_final_review.json','bec_native_preparation_final_review.json']:
        assert json.loads((HERE/n).read_text('utf8'))['material_concerns']==[]
    before=set((ROOT/'pipeline/decisions').glob('*_other.md'))
    args=['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
        'cluster_project','other','两个既有准备名额已满且两原训练占卡，本轮如何推进原生检查缺口？',
        '不增模型候选；完成CTS原四结果只读语义checker与BEC禁用无版本原生observer工具，两原运行和M206暂停保持。实际原生和资源检查等待自然空卡及fresh完整绑定。',
        'snapshot creation/reserve0；本轮原BFC6与BCR19真实增长、当前CTS注册busy拒绝；CTS软件8逻辑/84拒绝及BEC实际本地软件检查/两项独审完成。软件fixture不是Torch反传/原数据配对/资源/效能证据，不产标准PASS或入队。',
        'pipeline/diagnostic_bundles/tick_f86d1cfa/cts_execution_review_prepare/preparation.json; pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_prepare/preparation.json; pipeline/diagnostic_bundles/tick_f86d1cfa/progress_and_guard_independent_review.json']
    result=subprocess.run(args,capture_output=True,text=True,encoding='utf8',timeout=30,check=True)
    added=set((ROOT/'pipeline/decisions').glob('*_other.md'))-before;assert len(added)==1
    p=added.pop();out={'command':args,'returncode':result.returncode,'decision':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}}
    with (HERE/'canonical_decision_record.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(out['decision'],ensure_ascii=False))
if __name__=='__main__':main()
