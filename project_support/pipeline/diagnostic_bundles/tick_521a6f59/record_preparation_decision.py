"""Record completed preparation for the existing BEC source version only."""
from pathlib import Path
import hashlib,json,subprocess
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();assert not (HERE/'canonical_decision_record.json').exists()
    for n,h in [('bec_operational_final_review.json','c8ee1830b5e7bb26e0f9ceb7b9c7d934d28d18a334c229d75c6f93708aa228e6'),
                ('bec_checker_final_review.json','b1f27cf80b759c66896b1cfa8cdd17dc7b8d39ead1505498ccbb648bf0377352')]:
        p=HERE/n;assert sha(p)==h and json.loads(p.read_text('utf8'))['material_concerns']==[]
    assert sha(HERE/'bec_actual_local_guard_integration.json')=='24c8719aa56a1e5cc22bb4f94a8d30f5d68bd20deb7862a7421a979869969488'
    before=set((ROOT/'pipeline/decisions').glob('*_other.md'))
    args=['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
        'cluster_project','other','两项既有准备储备已满且GPU仍忙时如何推进BEC9b678？',
        '已完成对应source9b678/parent-live48fc的新native/operational静态包与原四结果checker，独审后仅物化静态catalog并做真实current-owner零transport busy验证；下一步为真正空卡后的原生对照检查。',
        '61mocks/71静态/7CLI拒绝、checker8逻辑98软件拒绝及独审完成；原worker7e/模型2d06/YAMLa18/协议6555/资源AST不变。旧322c null/DRAFTTrue保留，新十active字段null；没有原生data/backward/resources或标准PASS/准入/queue。两原训练与额外1565126均保护，资源为旧问题延续不重复索权。',
        'pipeline/diagnostic_bundles/tick_521a6f59/bec_operational_prepare/preparation.json; pipeline/diagnostic_bundles/tick_521a6f59/bec_execution_review_prepare/preparation.json; pipeline/diagnostic_bundles/tick_521a6f59/bec_actual_local_guard_integration.json']
    r=subprocess.run(args,capture_output=True,text=True,encoding='utf8',check=True,timeout=30)
    added=set((ROOT/'pipeline/decisions').glob('*_other.md'))-before;assert len(added)==1
    p=added.pop();out={'returncode':r.returncode,'decision':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}}
    with (HERE/'canonical_decision_record.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(out['decision'],ensure_ascii=False))
if __name__=='__main__':main()
