"""Bounded HDS continuity and due auxiliary-scope checks; no GPU computation."""
import argparse,json,os,subprocess,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
CID='m95-hierarchical-mask-feature-path-audit'
IDS=('m95-native-relation-other-sign-conflict','m95-native-main-role-weight-precedence','m95-native-secondary-positive-mass','m95-native-between-pair-support')
GOAL='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0,str(SKILL))
import foreground_tick as tick,pipeline_monitor as monitor
def now():return datetime.now(timezone.utc).isoformat()
def main(token):
    def guard():
        owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
        assert ROOT.name=='cluster_project' and owner['token']==token
        assert owner['thread_id']==os.environ['CODEX_THREAD_ID']
        assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
        assert tick.digest(ROOT/'pipeline/goal.json')==GOAL
        return owner
    def save(path,value):
        guard();path.parent.mkdir(parents=True,exist_ok=True);tick.save(path,value)
    def ev(path):return {'path':path,'sha256':tick.digest(ROOT/path)}
    def add(candidate,path):
        entry=ev(path)
        if entry not in candidate.setdefault('evidence',[]):candidate['evidence'].append(entry)
    guard();view=tick.load(ROOT/'pipeline/headless/.tick_model_view.json')
    assert view['mode']=='design' and view['preflight']['goal_rc']==0
    assert not view.get('design_bootstrap',{}).get('required')
    assert view['research']['reserve_budget']==0
    assert set(item['id'] for item in view['research']['shown'])==set(IDS)
    work=tick.load(ROOT/'pipeline/research_work.json')
    selected=[next(c for c in work['candidates'] if c['id']==i) for i in IDS]
    assert all(c['stage']=='blocked' and c.get('blocker_kind')=='human_authorization' and c.get('research_role')=='auxiliary_scope_hold' for c in selected)
    before=[{k:c.get(k) for k in ('id','stage','research_role','blocker_kind','blocker','retry_after','unblock_condition','next_action')} for c in selected]
    queue=monitor.load_queue(str(ROOT));matches=[t for group in queue['gpu_queues'].values() for t in group if t.get('id')=='M202-HDS']
    assert len(matches)==1;task=matches[0]
    assert task['pid']==216566 and task['server']=='server-4' and str(task['gpu'])=='0'
    assert task['launch_verified'] is True
    program=f"""
import json,os,pathlib,re,subprocess
from datetime import datetime,timezone
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
pid=216566;p=pathlib.Path('/proc')/str(pid);console=pathlib.Path({task['log']!r})
assert console.stat().st_size<40*1024*1024;text=console.read_text(errors='replace')
train=[list(map(int,row)) for row in re.findall(r'Train\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)]
val=[list(map(int,row)) for row in re.findall(r'Val\\[(\\d+)/(\\d+)\\]:[^\\r\\n]*?\\|\\s*(\\d+)/(\\d+)',text)]
run=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1/20261016_173442')
log=run/'20261016_173442.log';content=log.read_text(errors='replace')
metrics=[float(x) for x in re.findall(r'mIoU\\s*:\\s*([0-9]+(?:\\.[0-9]+)?(?:e[-+]?\\d+)?)',content)]
counts=[int(x) for x in re.findall(r'Evaluate referring segmentation:\\s*(\\d+)',content)]
contexts=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader,nounits'],text=True)
own=[r for r in contexts.splitlines() if int(r.split(',')[0])==pid]
locks=[]
if p.exists():
    for fd in (p/'fd').iterdir():
        try:target=os.readlink(fd)
        except OSError:continue
        if 'cluster_project_gpu0_' in target and target.endswith('.lock'):locks.append(target)
files=[dict(name=f.name,bytes=f.stat().st_size,mtime=f.stat().st_mtime) for f in (run/'best.pth',run/'last.pth') if f.is_file()]
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),pid=pid,alive=p.exists(),native_train_last=train[-8:],native_val_last=val[-8:],native_miou=metrics,expression_counts=counts,native_log=str(log),checkpoint_stats=files,own_contexts=own,locks=locks,crash_markers=[m for m in ('Traceback','CUDA out of memory','RuntimeError') if m in text or m in content],gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip())))
"""
    options=['-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','-o','PasswordAuthentication=no']
    process=subprocess.run(['ssh',*options,'server-4','/home/songcl/.conda/envs/project_cluster/bin/python -B -'],input=program.encode('utf-8'),capture_output=True,timeout=60)
    relative='pipeline/diagnostic_bundles/tick_'+token[:8];bundle=ROOT/relative
    if process.returncode:
        save(bundle/'native_probe_failure.json',{'recorded_at':now(),'returncode':process.returncode,'stderr':process.stderr.decode(errors='replace')});raise RuntimeError('Read-only native probe failed; evidence retained.')
    result=json.loads(process.stdout.decode('utf-8'))
    result['confirmed']=bool(result['alive'] and len(set(tuple(s) for s in result['native_train_last']))>=2 and len(result['locks'])==3 and len(result['own_contexts'])==1 and 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in result['own_contexts'][0] and not result['crash_markers'])
    assert not (bundle/'native_continuity.json').exists();save(bundle/'native_continuity.json',result)
    assert result['confirmed'],'Unverified run; do not claim healthy or blindly restart.'
    goal=tick.load(ROOT/'pipeline/goal.json');assert goal['research_mainline']['primary_axis']=='hierarchical_attention_point_feature_update'
    retry=(datetime.now(timezone.utc)+timedelta(hours=4)).isoformat()
    scope={'recorded_at':now(),'goal_sha256':GOAL,'research_mainline':goal['research_mainline'],'checked_due_candidates':before,'decision':'Original four auxiliary human-scope holds remain. No new human authorization or separately justified mainline-required auxiliary test. Due timer and resource permission do not authorize promotion; no new M201 recovery, gate/route reopening, scientific rejection or GPU-block claim.','retry_after':retry,'authorization_basis':'Unchanged latest project goal and direct user instructions in this owning thread; source-bound FLOPs/resource exceptions apply to SAME M202 only.','new_model_variants':0,'new_implementation_revisions':0,'new_admissions':0,'new_gpu_computations':0,'native_evidence':ev(relative+'/native_continuity.json')}
    save(bundle/'scope_recheck.json',scope)
    for candidate in selected:
        candidate['retry_after']=retry;add(candidate,relative+'/scope_recheck.json')
    primary=next(c for c in work['candidates'] if c['id']==CID);assert primary['stage']=='training'
    add(primary,relative+'/native_continuity.json')
    primary['next_action']='Monitor unchanged native train/validation and frozen evaluation plan. Early aggregate curve is not efficacy/uncertainty evidence; no tuning, duplicate launch, automatic restart or auxiliary promotion.'
    work['design_cycle']={'stop_reason':'external_resource_blocked','attempted_ids':[CID,*IDS],'evidence':[ev(relative+'/scope_recheck.json'),ev(relative+'/native_continuity.json')],'resume_condition':'Continue current primary training; auxiliary due IDs resume only on actual explicit authorization or a justified mechanism-matched mainline need. Four-hour recheck does not grant GPU or scientific PASS.','scope':'Only remaining four human-scope blocks, not a claim all primary routes are exhausted, physical GPUs unavailable or the deadline elapsed.'}
    save(ROOT/'pipeline/research_work.json',work)
    latest=result['native_train_last'][-1];best=max(result['native_miou']) if result['native_miou'] else None
    notes={'actions':[f"本轮快照{view['generated_at']}为design，活跃1/容量2、等待0、准入预算1、储备4/2、储备预算0；续做4个到期既有范围保留，没有新建候选或重复preflight。",f"实测{result['observed_at']}：同一server4物理GPU0 PID216566原生Train[{latest[0]}/{latest[1]}]至{latest[2]}/{latest[3]}，最近8条有实际步数增长；UUID及3个生命周期锁正确，无采样Traceback/OOM。GPU瞬时读数{result['gpu']}，不当全程峰值。",f"本次原生验证序列{result['native_miou']}；每轮表达数{result['expression_counts']}，当前best={best}。训练轮次不是已完成验证轮数，只按真实数值与historical champion0.5020/baseline0.4894比较，不把早期曲线当最终机制结论；官方目标0.5100及既有目标检查结果不由此脚本改写。",'按4个稳定ID各一次有界查询复核human_authorization/auxiliary_scope_hold，保留原负证据、gate、范围和unblock条件；只追加本轮真实范围复核及4小时重查。没有把定时到期、可用容量或M202专用FLOPs例外当辅助路线授权。', '本轮只有真实连续性/验证摘要与到期范围复核；未重跑已完成checkpoint/schema/20项等价测试，没有新的研究结论。新模型变体/候选/准入/启动/模型修订/额外GPU计算/目标或调度变更均0。完整六段留档，用量仅收据的begin到receipt局部窗口，缓存不重复相加，不当账单。'], 'decisions':['既有主线M202-HDS按冻结模型、seed1999、batch2、loss/optimizer及epochs50/max_iters70继续原生训练；不因早期曲线调整、不重启、不占满空槽。','四项辅助路线仍待真正的范围授权或主线必要性证据，不把保留当科学证伪或物理GPU阻塞。design_cycle仅描述这些既有外部范围保留，不宣称独立路线耗尽。','checkpoint完整字段和逐场景输出缺口仅引用18:15-18:18已有审计，不重复耗费原生计算；当前新checkpoint内容未重新反序列化，不能用旧哈希冒充当前文件。后续按冻结评估计划处理不确定性。','完成须以实际finish和租约释放核验为准；正常推进没有需用户处理的新变化时保持安静，不修改通知策略或自动化。']}
    save(bundle/'report_notes.json',notes)
    print(json.dumps({'native':result,'due_scope_rechecked':len(selected),'next_scope_recheck':retry,'notes':str(bundle/'report_notes.json')}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--token',required=True);args=parser.parse_args();main(args.token)
