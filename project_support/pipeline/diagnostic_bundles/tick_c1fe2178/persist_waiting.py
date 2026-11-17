"""Keep the admitted tested CSO task waiting after actual prelaunch refusal."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SID='fine-leaf-full-covariance-shape-composition'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ref(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def main():
    p=argparse.ArgumentParser();p.add_argument('--execute-root',action='store_true');args=p.parse_args()
    if not args.execute_root:print('{"status":"DEFAULT_NOP"}');return
    owner=read(HERE/'current_owner_binding.json');live=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert {k:live[k] for k in owner}==owner and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    now=datetime.now(timezone.utc);assert now<datetime.fromisoformat(owner['deadline_at'])
    for name,key in (('.tick_context.json','context_sha256'),('.tick_context_state.next.json','pending_sha256')):assert sha(ROOT/'pipeline/headless'/name)==owner[key]
    actual_path=HERE/'cso_resource_refusal.actual.json';review_path=HERE/'peer_review/cso_resource_refusal_independent_review.json'
    actual=read(actual_path);r=read(review_path)
    assert actual['owner']==owner and r['owner']==owner and r['passed'] is True and r['material_concerns']==[]
    assert r['actual_sha256']==sha(actual_path) and r['resource_block_confirmed'] is True
    free=r['actual_free_mib'];assert isinstance(free,int) and free<20000
    assert r['original_minimum_free_mib']==20000 and r['marker_absent'] is True and r['no_project_training_launched'] is True
    assert not list(HERE.glob('**/*dispatch*intent*.json'))
    baseline=read(HERE/'integrity_before.json');repo=ROOT/'Cluster'
    assert sha(ROOT/'pipeline/goal.json')==baseline['goal_sha256'] and sha(ROOT/'SERVERS.yaml')==baseline['servers_sha256']
    assert subprocess.check_output(['git','-c','safe.directory='+str(repo),'-C',str(repo),'rev-parse','HEAD'],text=True).strip()==baseline['local_main_HEAD']
    assert sha(repo/'.git/index')==baseline['index_sha256'] and all(sha(repo/k)==v for k,v in baseline['dirty_sha256'].items())
    assert sha(ROOT/'pipeline/experiments/M235-SINC.json')=='8f8bc6c3791823ec4166a3097e6e9a5617820b9a2d97ce4809171f7d127c9c62'
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as monitor
    import closure
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        queue=read(ROOT/'pipeline/queue.json');prior_queue=read(HERE/'queue.json.before')
        task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M236-CSO')
        assert task['status']=='waiting' and not task.get('pid') and not task.get('launch_verified')
        remainder=json.loads(json.dumps(queue));remainder['gpu_queues']['server-4']=[t for t in remainder['gpu_queues']['server-4'] if t['id']!='M236-CSO']
        assert remainder==prior_queue
        hold=f'Actual server4 GPU0 memory.free {free}MiB below original 20000MiB; external job preserved. No dispatch intent or launch marker. Recheck allocation, then new owner must separately bind/review a fresh CSO production stage/lease and scoped source resolver; never use consumed SERVERS entry or replay this tick intent.'
        task['dispatch_hold']=hold
        task['resource_wait']=dict(owner=owner,kind='live_external_gpu_occupation',minimum_free_mib=20000,actual_free_mib=free,
            retry_after=(now+timedelta(hours=1)).isoformat(),actual=ref(actual_path),independent_review=ref(review_path),
            new_owner_execution_rebind_required=True,allow_external_overlay=True,require_empty_card=False)
        work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==SID)
        assert c['native_status']=='PASSED' and c['resource_status']=='PASSED' and c['source_commit'] is None and c['code_commit'] is None
        c.update(stage='deployment',updated_at=now.isoformat(),queued=True,full_training_started=False,training_repair_verified=False,
            blocker_kind='live_external_gpu_occupation',blocker=hold,retry_after=(now+timedelta(hours=1)).isoformat(),
            next_action='Keep successful native/resource/admission and safe_sync evidence. Recheck actual GPU0 memory.free>=20000, cap1 and original three locks. A future owner separately binds/reviews new execution stage/lease/source resolver against actual runtime541 and exact producer hashes; reuse validated implementation/protocol, no repeated native/resource tests for unchanged source. Never execute consumed SERVERS shim or replay old intents; launch only with real slot and verify native step growth.')
        if 'resource_disposition' in c:
            previous=c['resource_disposition']
            if previous not in c.setdefault('resource_disposition_history',[]):c['resource_disposition_history'].append(previous)
        c['resource_disposition']=dict(owner=owner,status='ACTUAL_PRELAUNCH_ALLOCATION_REFUSED_TESTED_MODEL_GATES_RETAINED',
            actual_free_mib=free,original_minimum_free_mib=20000,project_cap1_available=True,allow_external_overlay=True,
            native_gate_passed=True,model_resource_gate_passed=True,training_started=False,marker_absent=True,
            evidence=ref(actual_path),independent_review=ref(review_path))
        c['current_production_path']=dict(owner=owner,FROZEN=ref(HERE/'cso_production_prepare_v2/FROZEN.json'),
            render_result=ref(HERE/'cso_setup_execution_v2/render_result.json'),status='INSTALLED_UNCONSUMED_PRELAUNCH_RESOURCE_REFUSAL',
            new_owner_rebind_required=True,old_failed_collect_preserved=True)
        paths=[actual_path,review_path,HERE/'admission.actual.json',HERE/'cso_deployment_execution/sync.actual.json',
            HERE/'cso_setup_execution/collect_actual.json',HERE/'peer_review/cso_collect_failure_reconcile.actual.json',
            HERE/'cso_production_prepare_v2/FROZEN.json',HERE/'cso_setup_execution_v2/collect_actual.json',
            HERE/'cso_setup_execution_v2/render_actual.json',HERE/'cso_setup_execution_v2/render_result.json',
            HERE/'peer_review/cso_production_v2_independent_review.json',HERE/'peer_review/cso_collect_v2_actual_independent_review.json',
            HERE/'peer_review/cso_render_v2_actual_independent_review.json',HERE/'cso_dispatch_execution_v2/cso_dispatch_ssh_00.stderr']
        for path in paths:
            e=ref(path)
            if e not in c['evidence']:c['evidence'].append(e)
        previous=work.get('tick_attempt')
        if previous and previous not in work.setdefault('tick_attempt_history',[]):work['tick_attempt_history'].append(previous)
        work['tick_attempt']=dict(tick_started_at=owner['generated_at'],candidate_id=SID,kind='resource_check',result='blocked',
            command='python -B dispatch_cso_once.py --execute-root; independent read-only reconcile',
            observation=f'Tested and admitted M236 remains waiting. Before any dispatch intent/marker/launch, actual directfree{free}<original20000; external tasks preserved. Native and measured model resources remain passed; no efficacy or full-training claim.',
            evidence=[ref(actual_path),ref(review_path),ref(HERE/'cso_dispatch_execution_v2/cso_dispatch_ssh_00.stderr')])
        work['updated_at']=now.isoformat();save(ROOT/'pipeline/research_work.json',work);save(ROOT/'pipeline/queue.json',queue)
        closure.admission(ROOT,task)
    finally:lock.close()
    old={c['id']:c for c in read(HERE/'research_work.json.before')['candidates']};new={c['id']:c for c in work['candidates']}
    assert old.keys()==new.keys() and {k for k in old if old[k]!=new[k]}=={SID}
    memory=f"""# Codex Research Memory

## Goal And Phase
- 仅cluster_project；server4物理GPU0/UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c；共享允许，max_tasks_per_gpu1/启动实际directfree>=20000MiB/原training-diagnostic-exclusive三锁。无空卡/零context/低util要求。
- GPU1/其他服务器禁用，M206/M227独立人工暂停；不驱逐、信号、重启、迁移，不改目标、数据、seed1999、epochs50/max_iters70、原loss/optimizer、10G及条件15%显存门槛、bans或调度。
- Pipeline-cluster_project Disabled；ownerthread01a159c5-29ab-7a22-ba7f-e79174757253；canonical foreground/python-B/PROJECT_ROOT=D:/project。

## Champion And Baseline
- 原目标.5100，M95冠军.5020/baseline.4894保持；技术准入/partial不作效力或novelty证明。
- WFC完整epoch30 best.49711745977401733；NEC完整epoch23 best.49454113841056824；MIC完整epoch26 best.49881425499916077。均不重启。

## Active Hypotheses
- M236-CSO本轮actual sourceaf457(parentd214)/私有runtimeb1；两自然TRAIN loss9.573954582214355/13.908418655395508、common841完全相等、九core有限非零梯度/每步更新及HCG/inst/ILA/mask实际路径均独审通过。不重跑旧CPU21。
- 同原固定样本/bs1/lang1/warm20/repeat100资源9.645764684G FLOPs/allocated934827520B/median35.407514544ms/P9036.583361775ms独审通过；历史M95非同时，不声称结构加速；整optimizer训练峰值和无cluster delta未知。
- 既有integration5413102(parentb1)与af457 source9逐字节版本关联另存并独审，原NULL/owner不补签；技术准入receipt pipeline/admissions/M236-CSO.json SHA07b56b16948f7f7e1a4a0682fd6abc81d3eda586e05ae4424f89d16005d8be09。

## Closed Or Failed Directions
- M235-SINC crashed archiveb75c9152d7fd4ecea9af538101d777d4/sourceb1，partialepoch2/1870of4686，完整saved metadata仅epoch1；原Adam list.grad根因UNKNOWN，未修复、不自动恢复。
- NSD M232 partial1/1961无完整验证/pth；HVD M230 partial5/1449/saved4；PSC M231 partial2/984/saved1。旧CPU/短测不代表长期修复。
- 全部旧scope/numerical holds、已消费授权、失败/原NULL保留；不改名重开bans；M206/M227保持人工暂停。

## Running And Queue
- 当前无项目训练；M236已准入/入队waiting并真实safe_sync b1→5413。启动前directfree{free}MiB<20000拒绝；无dispatch intent/原生训练/新prod marker，外部任务未触碰。
- 新生产runtime/cso_path_prod_c1fe2178_v2已安装且未消费；source/collect/render独审通过。该owner有时限，未来owner必须另存绑定/stage/lease，不能沿旧owner重用；task专属资源/执行rebind hold保留。
- 主SERVERS仍旧已消费rvec入口；未来派发必须复用已审v2逻辑建立新scoped server-copy/source resolver，禁止直接调用原consumed shim。实际runtime HEAD5413，不重复sync b1。

## Open Questions And Risks
- 模型native及测量resources已PASS，当前是显存分配拒绝，不能改写为模型失败；精度/novelty仍UNKNOWN，未正式训练。原Torch/Adam长期故障未以两步PASS宣称修复。
- generator v1 batch schema错误另存v2修正/独审；生产v1 collect因text=True把CRLF归一化而已知终态拒绝，无Torch/GPU；只读reconcile后新v2以raw git_blob修正，旧失败/FROZEN/intent/stage保持。
- 新native/production直接memory.free，生产锁内source/cap1/free/deadline后才marker，解释器-B/原三FD继承；不续旧lease、不补NULL、不盲重放。strictkey仅pinned songcl@192.168.1.115/dl04，不读密码/旧IP/假设sudo。

## Last Tick
- c1fe2178：起初GPU0 directfree32016可用，完成最近M236真实缺项与独审，一项技术准入/入队、既有5413的真实safe_sync和新生产v2安装/collect/render均完成。
- 正式dispatch prelaunch因新外部任务占用、actualfree{free}<20000拒绝；未写dispatch intent/消耗marker/启动。已新实际reconcile和独审，仅M236保留资源+新owner绑定hold，1h复查；有效native/resource证据复用。
- goal/SERVERS/主HEAD0747/index/dirty37、其他161候选及M206/M227保持。证据pipeline/diagnostic_bundles/tick_c1fe2178；后续只在真实槽位和新绑定核验后启动并确认步数增长。
"""
    assert memory.count('\n## ')==7 and len(memory.splitlines())<120
    (ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf8')
    notes=dict(actions=[
        '先观察原生/终态，当前无项目训练；起初GPU0 directfree32016，18项runtime/assets/环境和cap1/原三锁真实检查通过。',
        'M236两自然TRAIN/common841/九core有限反向和更新、原HCG-mask路径及同口径9.645764684G/934827520B资源独审通过；不重测旧CPU，不重制模型。',
        '既有5413与af457 exact9版本关联独审后canonical技术准入/入队，实际safe_sync b1→5413；新生产v2 source/实际collect/render独审及安装完成。',
        f'正式启动前directfree守卫因实际{free}MiB<20000拒绝；无dispatch intent、marker或训练，独立实际reconcile确认，M236保持waiting并加资源/新owner绑定hold。'],
        decisions=['显存分配拒绝与已通过的模型native/resource门槛分开记录；不降低原预算、不驱逐/发信号或扩大GPU，不把技术准入当精度/novelty。',
        'generator schema及生产CRLF读取错误均保留实失败，仅新操作包修正；未来owner复用有效测量和v2逻辑，另存stage/lease/source/runtime/UUID/producer绑定，不盲重放或重复sync。',
        'M206/M227独立人工暂停及其他161候选保持；在原授权真实显存与cap1/三锁满足后再派发并验证步数增长。'])
    save(HERE/'report_notes.json',notes)
    save(HERE/'completion_audit.actual.json',dict(owner=owner,recorded_at=now.isoformat(),other161_candidates_unchanged=True,
        other_queue_tasks_and_manual_pauses_unchanged=True,goal_SERVERS_main_HEAD_index_dirty37_unchanged=True,M235_archive_unchanged=True,
        new_candidates=0,new_admissions=1,new_training=0,native='PASSED',model_resources='PASSED',allocation='BLOCKED',
        actual_free_mib=free,no_dispatch_intent_or_launch_marker=True,resource_actual=ref(actual_path),resource_review=ref(review_path),
        admission=ref(ROOT/'pipeline/admissions/M236-CSO.json'),producer_sha256=sha(Path(__file__))))
    print(json.dumps(dict(status='ADMITTED_WAITING_ACTUAL_RESOURCE_BLOCK',free_mib=free,new_training=0,notes=str(HERE/'report_notes.json'))))
if __name__=='__main__':main()
