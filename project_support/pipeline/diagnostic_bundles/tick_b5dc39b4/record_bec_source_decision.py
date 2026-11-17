"""Record the actual local BEC source save, with no promotion or native test."""
from pathlib import Path
import hashlib,json,subprocess
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();assert not (HERE/'source_version_decision_record.json').exists()
    proof=HERE/'bec_version_execute/isolated_source_version.json';review=HERE/'bec_isolated_source_version_review.json'
    assert sha(proof)=='e2f3439ead898c3f8acdc8d54d929720515aa5783650850ae2c8d20666c30f44'
    assert sha(review)=='cb7ec9d87a8fabdc32a51ebdbc593557f42afd331a96c3d4cddc3cc7aa7dfd61'
    assert json.loads(review.read_text('utf8'))['material_concerns']==[]
    before=set((ROOT/'pipeline/decisions').glob('*_other.md'))
    args=['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
        'cluster_project','other','GPU验证受阻时推进既有BEC的哪个合法本地步骤？',
        '已将原2d06精确9blob保存为隔离源9b6782/单父实际已测48fc并独审；它与pendingCTS4e8为兄弟，不假定相互ff，不推进主线/运行源，不改原322c无版本禁用native包。',
        '本地Git保存不以GPU空闲为前提。实际树/父/9blob与保护28/index/13+4账/CTS4e8/native322c前后核准；0新模型图或调参，0native/准入/queue/launch。若实际main改变，须另建相同9blob的新兼容版本并按该版本真实检查，不能重标旧raw结果。额外未知双卡PID资源concern保持。',
        'pipeline/diagnostic_bundles/tick_b5dc39b4/bec_version_execute/isolated_source_version.json; pipeline/diagnostic_bundles/tick_b5dc39b4/bec_isolated_source_version_review.json; pipeline/diagnostic_bundles/tick_b5dc39b4/progress_and_readiness_review.json']
    r=subprocess.run(args,capture_output=True,text=True,encoding='utf8',check=True,timeout=30)
    added=set((ROOT/'pipeline/decisions').glob('*_other.md'))-before;assert len(added)==1
    p=added.pop();out={'returncode':r.returncode,'decision':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}}
    with (HERE/'source_version_decision_record.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(out['decision'],ensure_ascii=False))
if __name__=='__main__':main()
