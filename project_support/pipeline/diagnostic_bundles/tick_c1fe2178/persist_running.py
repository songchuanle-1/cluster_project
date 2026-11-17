"""Persist only an actually launched, independently checked progressing run."""
from pathlib import Path
from datetime import datetime, timezone
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
SID='fine-leaf-full-covariance-shape-composition'; COMMIT='5413102c57b526035f3920b5e7a81f3b58ad764d'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ref(p): return dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p))
def main():
    a=argparse.ArgumentParser();a.add_argument('--execute-root',action='store_true');args=a.parse_args()
    if not args.execute_root: print('{"status":"DEFAULT_NOP"}');return
    owner=read(HERE/'current_owner_binding.json');current=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert {k:current[k] for k in owner}==owner and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    for name,key in (('.tick_context.json','context_sha256'),('.tick_context_state.next.json','pending_sha256')):assert sha(ROOT/'pipeline/headless'/name)==owner[key]
    before=read(HERE/'integrity_before.json');repo=ROOT/'Cluster'
    assert sha(ROOT/'pipeline/goal.json')==before['goal_sha256'] and sha(ROOT/'SERVERS.yaml')==before['servers_sha256']
    assert subprocess.check_output(['git','-c','safe.directory='+str(repo),'-C',str(repo),'rev-parse','HEAD'],text=True).strip()==before['local_main_HEAD']
    assert sha(repo/'.git/index')==before['index_sha256'] and all(sha(repo/k)==v for k,v in before['dirty_sha256'].items())
    assert sha(ROOT/'pipeline/experiments/M235-SINC.json')=='8f8bc6c3791823ec4166a3097e6e9a5617820b9a2d97ce4809171f7d127c9c62'
    queue=read(ROOT/'pipeline/queue.json'); prior=read(HERE/'queue.json.before')
    task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M236-CSO')
    assert task['status']=='running' and task['launch_verified'] is True and not task.get('dispatch_hold')
    assert str(task['gpu'])=='0' and task['code_commit']==COMMIT
    remainder=json.loads(json.dumps(queue))
    remainder['gpu_queues']['server-4']=[t for t in remainder['gpu_queues']['server-4'] if t['id']!='M236-CSO']
    assert remainder==prior
    progress_path=HERE/'cso_training_progress.actual.json';progress=read(progress_path)
    assert progress['owner']==owner and progress['returncode']==0
    observation=progress['observation'];assert observation['native_progress_increased'] is True
    first,last=observation['samples']
    assert first['pid']==last['pid']==int(task['pid']) and (last['epoch'],last['batch'])>(first['epoch'],first['batch'])
    assert not first['fatal_markers'] and not last['fatal_markers']
    for sample in (first,last):
        assert all(any(' '+str(task['pid'])+' ' in row for row in item['kernel_rows']) for item in sample['original_locks'])
    review_path=HERE/'peer_review/cso_training_progress_independent_review.json';pr=read(review_path)
    assert pr['owner']==owner and pr['passed'] is True and pr['material_concerns']==[]
    assert pr['actual_sha256']==sha(progress_path) and pr['native_progress_increased'] is True
    paths=[progress_path,review_path,HERE/'admission.actual.json',HERE/'cso_deployment_execution/sync.actual.json',
        HERE/'cso_setup_execution/collect_actual.json',HERE/'peer_review/cso_collect_failure_reconcile.actual.json',
        HERE/'cso_production_prepare_v2/FROZEN.json',HERE/'cso_setup_execution_v2/collect_actual.json',
        HERE/'cso_setup_execution_v2/render_actual.json',HERE/'cso_setup_execution_v2/render_result.json',
        HERE/'peer_review/cso_production_v2_independent_review.json',
        HERE/'peer_review/cso_collect_v2_actual_independent_review.json',
        HERE/'peer_review/cso_render_v2_actual_independent_review.json']
    evidence=[ref(p) for p in paths]
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        work=read(ROOT/'pipeline/research_work.json')
        c=next(c for c in work['candidates'] if c['id']==SID)
        assert c['source_commit'] is None and c['code_commit'] is None
        c.update(stage='training',updated_at=datetime.now(timezone.utc).isoformat(),queued=True,
            full_training_started=True,training_repair_verified=False,
            next_action='Monitor current M236-CSO native training/validation/terminal on server4 GPU0. Preserve original source/protocol/negative evidence and manual pauses; never replay consumed stage/entry or auto-restart. Accuracy/novelty remain unknown until real validation and terminal evidence.')
        c['current_training']=dict(owner=owner,source_commit=COMMIT,server='server-4',physical_gpu=0,pid=task['pid'],log=task['log'],
            launch_verified=True,progress=ref(progress_path),independent_review=ref(review_path),
            native_progress_start=dict(epoch=first['epoch'],batch=first['batch']),native_progress_end=dict(epoch=last['epoch'],batch=last['batch']),
            complete_training=False,efficacy='UNKNOWN',novelty='UNKNOWN')
        c['current_production_path']=dict(owner=owner,FROZEN=ref(HERE/'cso_production_prepare_v2/FROZEN.json'),
            render_result=ref(HERE/'cso_setup_execution_v2/render_result.json'),original_failed_producer_preserved=True)
        c['current_memory_guard_adoption']=dict(owner=owner,status='ADOPTED_AND_LAUNCH_OBSERVED',
            current_production_review=ref(HERE/'peer_review/cso_production_v2_independent_review.json'),
            native_source_review=ref(HERE/'peer_review/cso_native_bound_independent_review.json'),
            direct_free_mib_required=20000,original_three_lock_inodes_retained=True)
        for item in evidence:
            if item not in c['evidence']:c['evidence'].append(item)
        work['updated_at']=datetime.now(timezone.utc).isoformat()
        save(ROOT/'pipeline/research_work.json',work)
    finally:lock.close()
    original=read(HERE/'research_work.json.before');old={c['id']:c for c in original['candidates']};new={c['id']:c for c in work['candidates']}
    assert old.keys()==new.keys() and {k for k in old if old[k]!=new[k]}=={SID}
    memory=f"""# Codex Research Memory

## Goal And Phase
- 仅cluster_project；server4物理GPU0/UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c，可与外部任务共享；max_tasks_per_gpu1/原启动directfree>=20000MiB/原training-diagnostic-exclusive三锁。无空卡/零context/低util要求。
- GPU1/其他服务器禁用，M206/M227独立人工暂停；不驱逐、信号、重启、迁移任务，不改目标、数据、seed1999、epochs50/max_iters70、原损失/optimizer、10G及条件15%显存门槛、bans或调度。
- Pipeline-cluster_project Disabled；ownerthread01a159c5-29ab-7a22-ba7f-e79174757253；canonical foreground/python-B/PROJECT_ROOT=D:/project。

## Champion And Baseline
- 原目标.5100，M95冠军.5020/baseline.4894保持；技术准入/partial训练不作效力或novelty证明。
- WFC完整epoch30 best.49711745977401733；NEC完整epoch23 best.49454113841056824；MIC完整epoch26 best.49881425499916077。均不重启。

## Active Hypotheses
- M236-CSO actual native sourceaf45707d(parentd214)/private runtimeb1；本轮两自然TRAIN步loss9.573954582214355/13.908418655395508、common841实际完全相等、九core每步有限非零梯度和更新及原HCG/inst/ILA/mask路径独审通过，不重测旧CPU21。
- 原同口径固定样本资源9.645764684G FLOPs/allocated934827520B/median35.407514544ms/P9036.583361775ms独审通过；历史M95非同时测量，不声称结构加速；完整optimizer训练峰值及无cluster delta未知。
- 既有integration5413102(parentb1)与af457 source9逐字节推导关联另存并独审，旧NULL/owner不补签。receipt pipeline/admissions/M236-CSO.json SHA07b56b16948f7f7e1a4a0682fd6abc81d3eda586e05ae4424f89d16005d8be09。

## Closed Or Failed Directions
- M235-SINC crashed archiveb75c9152d7fd4ecea9af538101d777d4/sourceb1；partialepoch2/1870of4686，完整saved metadata仅epoch1，非完整训练效力。原Adam list.grad错误根因UNKNOWN，未修复、不自动恢复。
- NSD M232 partialepoch1/1961无完整验证/pth；HVD M230 partialepoch5/1449/saved4；PSC M231 partialepoch2/984/saved1。旧CPU/短测不代表长期修复。
- 全部旧scope/numerical holds、已消费授权、失败/原NULL保留，bans不改名重开；M206/M227保持人工暂停。

## Running And Queue
- M236-CSO在server4 GPU0运行，PID{task['pid']}，runtime /data/songcl/Project/Cluster_project/Cluster_nsd_20261107 HEAD5413102；canonical safe_sync/safe_launch及原生递增已核，未完成训练/完整验证。
- 本轮12s有界双采样epoch{first['epoch']} batch{first['batch']}→epoch{last['epoch']} batch{last['batch']}/{last['total_batches']}，三原锁inode92537152/53/54/dev66308由该PID持有；不复跑/迁移。
- 新入口 runtime/cso_path_prod_c1fe2178_v2 已消费，仅用于该次已启动训练，禁止重放；主SERVERS仍旧消费入口，未来新owner需新绑定，不能直接当新入口调用。

## Open Questions And Risks
- 本轮是真实技术准入和启动，精度/novelty仍UNKNOWN，原Torch/Adam长期问题未以两步PASS宣称修复；监控原生验证和终态。
- 版本generator v1误读batch forward schema，另存v2修正并独审；旧失败不抹除。生产v1 collect因text=True把YAML CRLF归一化而已知终态拒绝，无Torch/GPU/训练；只读reconcile后新_v2 raw git_blob修正，原源码/YAML及旧stage/intent原样。
- 新native/production均直接memory.free，锁后再次核source/cap1/free，正式解释器带-B且原三FD继承；不续旧lease、不补NULL、不重放意图。SSH仅strictkey至pinned songcl@192.168.1.115/dl04，不读密码/旧IP/假设sudo。

## Last Tick
- c1fe2178：新真实快照先观察无项目训练/无ready队列，再完成最近M236原缺项；一项技术准入/入队/真实safe_sync b1→5413及GPU0启动。
- 新生产v2经source/collect/render独审、锁内directfree>=20000及cap1/三锁后启动；当前原生{first['epoch']}/{first['batch']}→{last['epoch']}/{last['batch']}，无完整训练效力声明。
- goal/SERVERS/主HEAD0747/index/dirty37、其他161候选及M206/M227保持。全部证据pipeline/diagnostic_bundles/tick_c1fe2178；待report/finish真实核验后收尾。
"""
    assert memory.count('\n## ')==7 and len(memory.splitlines())<120
    (ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf8')
    notes=dict(actions=[
        '先观察真实原生/终态：无项目训练，仅M206/M227人工暂停，无合格待跑；GPU0 directfree32016MiB、cap1/原三锁及18项实际环境哈希通过。',
        'M236两自然TRAIN步/common841/九core更新和HCG-mask真实路径及同口径9.645764684G/934827520B资源均独审通过；旧CPU/准备证据复用，不重制模型。',
        '既有5413与实际af457 source9逐字节版本关联独审后canonical技术准入入队；实际safe_sync b1→5413，安装新生产v2并canonical启动GPU0。',
        f'启动后有界双采样epoch{first["epoch"]} batch{first["batch"]}→epoch{last["epoch"]} batch{last["batch"]}/{last["total_batches"]}，PID及三原内核锁核验通过。'],
        decisions=['原generator schema与生产CRLF读取错误均保留实失败，只修新操作绑定；不改源码/YAML、不复测模型、不重放旧stage。',
        '原free>=20000/cap1/三锁/共享授权保持；GPU1/他服及M206/M227禁用/暂停不变，未信号、重启、迁移、改调度或目标。',
        '技术准入及partial训练不作精度/novelty或长期错误已修复证明；继续观察原生验证与终态。'])
    save(HERE/'report_notes.json',notes)
    save(HERE/'completion_audit.actual.json',dict(owner=owner,recorded_at=datetime.now(timezone.utc).isoformat(),
        other161_candidates_unchanged=True,other_queue_tasks_and_manual_pauses_unchanged=True,goal_SERVERS_main_HEAD_index_dirty37_unchanged=True,
        M235_archive_unchanged=True,new_candidates=0,new_admissions=1,new_training=1,full_training_complete=False,
        actual_progress=ref(progress_path),progress_review=ref(review_path),receipt=ref(ROOT/'pipeline/admissions/M236-CSO.json'),
        producer_sha256=sha(Path(__file__))))
    print(json.dumps(dict(status='RUNNING_PERSISTED',id=task['id'],pid=task['pid'],epoch=last['epoch'],batch=last['batch'],notes=str(HERE/'report_notes.json'))))
if __name__=='__main__':main()
