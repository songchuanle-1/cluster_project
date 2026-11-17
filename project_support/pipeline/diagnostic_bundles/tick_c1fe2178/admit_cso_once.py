"""Default NOP. Admit only the independently reviewed actual current CSO results."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, os, sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
SID='fine-leaf-full-covariance-shape-composition'; ID='M236-CSO'
COMMIT='5413102c57b526035f3920b5e7a81f3b58ad764d'
CONFIG='configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml'
SKILL='C:/Users/chuanle song/.codex/skills/songcl_research_pipeline'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save_new(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ref(p): return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--execute-root',action='store_true'); args=ap.parse_args()
    if not args.execute_root: print(json.dumps(dict(status='DEFAULT_NOP'))); return
    assert sys.dont_write_bytecode and os.environ['PROJECT_ROOT']=='D:/project'
    owner=read(HERE/'current_owner_binding.json'); current=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert {k:current[k] for k in owner}==owner and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>300
    for name,key in (('.tick_context.json','context_sha256'),('.tick_context_state.next.json','pending_sha256')): assert sha(ROOT/'pipeline/headless'/name)==owner[key]
    baseline=read(HERE/'integrity_before.json')
    assert sha(ROOT/'pipeline/goal.json')==baseline['goal_sha256'] and sha(ROOT/'SERVERS.yaml')==baseline['servers_sha256']
    version=HERE/'cso_version_binding/version_bound_evidence.json'; smoke=HERE/'cso_version_binding/native_smoke.version_bound.json'
    resource=HERE/'cso_version_binding/resources.version_bound.summary.json'
    checks={
        'source': (HERE/'peer_review/cso_native_bound_independent_review.json','source_and_native_protocol_review_passed'),
        'smoke': (HERE/'peer_review/cso_native_smoke_actual_independent_review.json','native_smoke_passed'),
        'resources': (HERE/'peer_review/cso_resources_actual_independent_review.json','resource_gate_passed'),
        'version': (HERE/'peer_review/cso_version_binding_actual_independent_review.json','version_association_passed')}
    for p,key in checks.values():
        v=read(p); assert v['owner']==owner and v['passed'] is True and v['material_concerns']==[] and v[key] is True
        assert v['reviewer_thread_id'] not in (owner['thread_id'],'/root','/root/cso_native_ops','/root/cso_readiness')
    association=read(version); ns=read(smoke); rs=read(resource)
    assert association['owner']==owner
    assert ns['id']==ID and ns['config']==CONFIG and ns['code_commit']==COMMIT and ns['goal_sha256']==baseline['goal_sha256']
    assert ns['steps']==2 and len(ns['losses'])==2
    assert rs['resource_gate_passed'] is True and rs['flops_g']<=10
    assert rs['peak_allocated_bytes']<=936763392*1.15
    vr=read(checks['version'][0]); assert vr['version_bound_evidence_sha256']==sha(version) and vr['native_smoke_sha256']==sha(smoke) and vr['resources_summary_sha256']==sha(resource)
    receipt_path=ROOT/'pipeline/admissions/M236-CSO.json'; assert not receipt_path.exists()
    sys.path.insert(0,SKILL); import pipeline_monitor as monitor; import closure
    lock=monitor.acquire_lock(str(ROOT)); assert lock is not None
    try:
        work=read(ROOT/'pipeline/research_work.json'); queue=read(ROOT/'pipeline/queue.json')
        assert queue==read(HERE/'queue.json.before')
        c=next(c for c in work['candidates'] if c['id']==SID); assert c['stage']=='implementation'
        assert c['source_commit'] is None and c['code_commit'] is None
        now=datetime.now(timezone.utc).isoformat()
        decision=ROOT/'pipeline/decisions'/('20261114-'+datetime.now(timezone.utc).strftime('%H%M%S')+'_M236_admission.md')
        decision.write_text('# M236-CSO 技术准入\n\n'+
            '本轮新owner原生两自然TRAIN步、实际common841初始化一致、九core有限梯度及更新均独立复核通过。'+
            '同一冻结YAML、数据、seed1999、原损失/optimizer和epochs50/max_iters70保持。\n\n'+
            f'固定样本资源实测 {rs["flops_g"]:.9f}G FLOPs，allocated peak {rs["peak_allocated_bytes"]}B，median {rs["median_ms"]:.6f}ms / P90 {rs["p90_ms"]:.6f}ms。'+
            '原10G及M95峰值+15%门槛通过；历史M95非同时测量，不以当前时延差声称架构加速。完整optimizer训练峰值与无cluster资源增量未知。\n\n'+
            '实际私有原生源码af457/runtimeb1与拟部署integration541之间的九文件字节一致另存推导证明；不改原始actual/code/owner/NULL。'+
            '这是experiment_first技术准入，精度与novelty仍UNKNOWN。仅server4物理GPU0、cap1、直接free>=20000及三原锁；M206/M227保持人工暂停。'+
            '先以hold入队；经过真实safe_sync和新生产入口复核后才可清本任务hold并canonical派发。\n',encoding='utf-8')
        auth=read(ROOT/'pipeline/closure_policy.json')['experiment_first']['authorization']
        receipt=dict(id=ID,config=CONFIG,code_commit=COMMIT,goal_sha256=baseline['goal_sha256'],profile='experiment_first',authorization=auth,
            candidate_id=SID,recorded_at=now,owner=owner,native_smoke=ref(smoke),decision=ref(decision),version_association=ref(version),
            version_association_review=ref(checks['version'][0]),
            efficacy='UNKNOWN',novelty='UNKNOWN',gates={
                'native_backward':dict(passed=True,evidence=[ref(smoke),ref(checks['smoke'][0]),ref(checks['version'][0])]),
                'resources':dict(passed=True,evidence=[ref(resource),ref(checks['resources'][0]),ref(version)]),
                'independence':dict(passed=True,evidence=[ref(checks['source'][0]),ref(version),ref(checks['version'][0])]),
                'constraints':dict(passed=True,evidence=[ref(ROOT/'pipeline/goal.json'),ref(ROOT/'SERVERS.yaml'),auth,ref(checks['resources'][0]),ref(version)])})
        save_new(receipt_path,receipt)
        c.update(stage='admission',updated_at=now,native='PASSED',native_status='PASSED',resources='PASSED',resource_status='PASSED',
            full_forward='PASSED',technical_admission=True,scientific_admission=False,efficacy='UNKNOWN',novelty='UNKNOWN',queued=True,
            full_training_started=False,admission_receipt=receipt_path.relative_to(ROOT).as_posix(),
            next_action='Canonical ff-only safe_sync b1 to reviewed integration541 from exact existing detached worktree; independently verify actual deployment and fresh CSO production path. Clear only this task hold then canonical dispatch GPU0 and verify native step growth. Preserve all old consumed stages and manual pauses.')
        c['native_observation']=dict(owner=owner,status='PASSED',actual_passed=True,reviewed=True,evidence=[ref(smoke),ref(checks['smoke'][0])])
        c['resource_observation']=dict(owner=owner,status='PASSED',actual_passed=True,reviewed=True,evidence=[ref(resource),ref(checks['resources'][0])])
        c['latest_exact_version_association']=dict(owner=owner,evidence=ref(version),independent_review=ref(checks['version'][0]),associated_commit=COMMIT,raw_execution_source_commit='af45707d7b6089f764843337c5f88af285383f88')
        for p in (smoke,resource,version,checks['smoke'][0],checks['resources'][0],checks['version'][0],decision,receipt_path):
            e=ref(p)
            if e not in c['evidence']: c['evidence'].append(e)
        task=dict(id=ID,config=CONFIG,candidate_id=SID,code_commit=COMMIT,admission_receipt=receipt_path.relative_to(ROOT).as_posix(),profile='experiment_first',
            server='server-4',gpu='0',status='waiting',requires_exclusive_ownership=False,
            dispatch_hold='Current-owner CSO production path and runtime source verification required before canonical dispatch.')
        work['updated_at']=now
        work['tick_attempt']=dict(tick_started_at=owner['generated_at'],candidate_id=SID,kind='native_smoke',result='passed',
            command='python -B run_native_once.py --execute-root --mode smoke/resources --target candidate',
            observation='Actual two natural TRAIN steps, common841, nine core parameter updates and same-protocol measured resources independently passed; exact-byte integration version association reviewed. Technical admission only; accuracy and novelty unknown.',
            evidence=[ref(smoke),ref(resource),ref(checks['smoke'][0]),ref(checks['resources'][0])])
        save(ROOT/'pipeline/research_work.json',work)
        closure.admission(ROOT,task)
        queue['gpu_queues']['server-4'].append(task)
        closure.validate_tick_admissions(ROOT,read(ROOT/'pipeline/headless/.tick_context.json'),queue)
        save(ROOT/'pipeline/queue.json',queue)
        save_new(HERE/'admission.actual.json',dict(owner=owner,recorded_at=now,receipt=ref(receipt_path),decision=ref(decision),task=task,canonical_admission_passed=True,new_training=False,other_tasks_unchanged=True))
        print(json.dumps(dict(status='ADMITTED_WAITING_ON_NEW_PRODUCTION_PATH',receipt_sha256=sha(receipt_path),task=ID,code_commit=COMMIT,new_training=False)))
    finally: lock.close()
if __name__=='__main__': main()
