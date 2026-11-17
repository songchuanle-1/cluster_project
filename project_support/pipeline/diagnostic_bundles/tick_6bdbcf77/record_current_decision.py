"""Record one actual preparation decision with the canonical shell helper."""
from pathlib import Path
import hashlib,json,subprocess
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();assert not (HERE/'canonical_decision_record.json').exists()
    assert sha(HERE/'new_candidate_prepare/preparation.json')=='2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d'
    assert json.loads((HERE/'bec_final_source_review.json').read_text('utf8'))['material_concerns']==[]
    root=Path('D:/project/cluster_project');before=set((root/'pipeline/decisions').glob('*_next_batch.md'))
    args=['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
          'cluster_project','next_batch','两原训练占卡时如何推进本轮唯一准备额度？',
          '保留BFC0/BCR1和M206暂停，CTS完成受审4e8版本静态工具与真实busy拒绝；新建一个跨层角色分工BEC源级储备，原生测试等待自然空卡。',
          'snapshot creation1/reserve1；CTS真实guard零transport/active，BEC独立8源+原字节YAML与生产stdlib检查已实完成并独审；不把软件检查、源MAC推断或准备数量写作原生/资源/准确率PASS。',
          'pipeline/diagnostic_bundles/tick_6bdbcf77/cts_actual_local_guard_integration.json; pipeline/diagnostic_bundles/tick_6bdbcf77/new_candidate_prepare/preparation.json; pipeline/diagnostic_bundles/tick_6bdbcf77/bec_final_source_review.json']
    result=subprocess.run(args,text=True,encoding='utf8',capture_output=True,check=True,timeout=30)
    added=set((root/'pipeline/decisions').glob('*_next_batch.md'))-before;assert len(added)==1
    p=added.pop();out={'actual_command':args,'returncode':result.returncode,'decision':{'path':p.relative_to(root).as_posix(),'sha256':sha(p)}}
    with (HERE/'canonical_decision_record.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(out['decision'],ensure_ascii=False))
if __name__=='__main__':main()
