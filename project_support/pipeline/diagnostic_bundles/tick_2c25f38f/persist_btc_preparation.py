"""Register one reviewed static-only BTC reserve; preserve all live training."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

R=Path('D:/project/cluster_project');D=Path(__file__).resolve().parent;P=D/'new_candidate_prepare'
T='2c25f38f32af4c69b3def8130cc5399c';CID='hierarchy-parent-binary-tree-complement-composition'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def save(p,v):
    q=p.with_name(p.name+'.'+T+'.tmp')
    with q.open('x',encoding='utf-8') as f:
        f.write(v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(q,p)

o=read(R/'pipeline/headless/.foreground.lockdir/owner.json')
assert o['token']==T and o['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert datetime.now(timezone.utc)<datetime.fromisoformat(o['deadline_at'])
assert sha(R/'pipeline/headless/.tick_context.json')==o['context_sha256'] and sha(R/'pipeline/headless/.tick_context_state.next.json')==o['pending_sha256']
prep=read(P/'preparation.json');assert sha(P/'preparation.json')=='c36b4d095ee3d48510a1064f699b2fe41be33569aaefb917d873a45c484d0814'
assert prep['candidate_id']==CID and prep['source_file_count']==9 and prep['code_commit'] is None
for name,expected in prep['prepared_file_hashes'].items():assert sha(P/name)==expected
version=read(D/'isolated_source_version.json')
assert version['code_commit']=='00e2b18c6b8d568a64edb496e6979d766440883c' and version['parent_commit']=='43dce016c1a1713c2a5dab7061810dc2efde8954'
assert version['primary_HEAD_index_status_28_protected_bytes_unchanged']
for n in ['btc_topology_review.json','btc_integration_review.json','btc_isolated_version_review.json']:
    assert read(D/n)['material_concerns']==[]
obs=read(D/'psbr_training_progress_observation.json');a,b=[x['data'] for x in obs['observations']]
assert obs['exact_original_process_and_native_progress_increasing']
assert a['pid']==b['pid']==2372658 and a['starttime']==b['starttime']=='35234267'
assert a['progress']==[1,50,1296,4686] and b['progress']==[1,50,1304,4686]
assert not a['errors'] and not b['errors']
stamp=datetime.fromisoformat(obs['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
goal=sha(R/'pipeline/goal.json');assert goal=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
authorization=read(R/'pipeline/closure_policy.json')['experiment_first']['authorization'];assert sha(R/authorization['path'])==authorization['sha256']
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as pm
lock=pm.acquire_lock(str(R));assert lock is not None
try:
    names=['queue.json','running.json','experiments/M208-HRC.json','experiments/M209-PSBR.json','experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']
    before={n:sha(R/'pipeline'/n) for n in names}
    assert read(R/'pipeline/running.json')['server-4']=={'0':'M209-PSBR'}
    q=read(R/'pipeline/queue.json')['gpu_queues']['server-4'];psbr=next(t for t in q if t['id']=='M209-PSBR')
    assert psbr['pid']==2372658 and psbr['status']=='running' and psbr['launch_verified'] is True
    paused=next(t for t in q if t['id']=='M206-CGCA');assert paused['training_status']=='paused_by_user' and paused['resume_authorized'] is False
    w=read(R/'pipeline/research_work.json');assert not any(c['id']==CID or c.get('experiment_id')=='M211-BTC' for c in w['candidates'])
    now=datetime.now(timezone.utc);evidence=[ref(P/'preparation.json'),ref(P/'static_validation.json'),ref(P/'mechanism.md')]+[ref(D/n) for n in ['btc_topology_review.json','btc_integration_review.json','isolated_source_version.json','btc_isolated_version_review.json','psbr_training_progress_observation.json']]
    config='configs/Quard/ctf_hcg_csort_btc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc.yaml'
    candidate={
        'id':CID,'experiment_id':'M211-BTC','stage':'blocked','resume_stage':'validation','created_at':now.isoformat(),
        'hypothesis':'Original middle tokens within each unchanged coarse parent need nonlinear complement composition: a geometry-balanced binary tree summarizes proper subtrees bottom-up and combines ancestor-outside with sibling-inside top-down; each leaf receives exactly its same-parent other supported tokens. Replace only middle FFN operator while retaining original cf skip, fine/coarse/raw banks/CSORT/HCG and single inst_feats delivery.',
        'matched_control':'M95-CTF-HCG-CSORT original native YAML, seed1999/epochs50/max_iters70/data/split unchanged. Baseline source74f; candidate source00e2b18 child of frozen PSNC43. No tuning or validation selection; actual paired initialization, two TRAIN steps, gradients and resource measurements remain NOT_RUN.',
        'config':config,'code_commit':version['code_commit'],'base_reference_commit':prep['base_reference_commit'],'source_parent_commit':version['parent_commit'],'native_execution_code_commit':None,
        'goal_sha256':goal,'authorization':authorization,'source_preparation':ref(P/'preparation.json'),'source_version':ref(D/'isolated_source_version.json'),
        'source_version_history':[{'recorded_at':prep['prepared_at'],'code_commit':None,'preparation':ref(P/'preparation.json')},{'recorded_at':version['recorded_at'],'code_commit':version['code_commit'],'evidence':ref(D/'isolated_source_version.json')}],
        'offline_checks':{'status':'PASSED_STATIC_ONLY','assertions':589,'distinct_labels':42,'independent_topology_cases':[11,22],'not_independent_training_experiments':True,'evidence':ref(P/'static_validation.json')},
        'native_smoke_status':'NOT_RUN','resource_profile_status':'NOT_RUN','admission_status':'NOT_EVALUATED','efficacy':'UNKNOWN',
        'source_inference_parameter_change':{'new_middle_maps':393984,'removed_middle_FFN':525568,'delta':-131584,'actual_registered_inventory':'NOT_RUN'},
        'known_limits':['No torch/autograd/FP32/device/runtime/matched-batch or real resource execution.','Inside map is loss-reachable only if a real supported parent has at least3 leaves; n1 uses only leaf, n2 inside unused.','Geometry CPU synchronization and many small GEMMs may add latency; O(K) and lower inferred parameter count do not establish efficiency.','Static topology dependency sets do not measure numerical Jacobians or trained benefit.'],
        'blocker_kind':'exclusive_gpu_slot','required_server':'server-4','required_gpu':'0','blocked_at':now.isoformat(),'last_resource_check_at':now.isoformat(),'retry_after':(now+timedelta(hours=1)).isoformat(),
        'blocker':'Only authorized GPU0 occupied by exact original PSBR2372658/start35234267, native1/50 steps1296->1304 observed '+stamp+' Shanghai. New BTC source is frozen/reviewed/locally committed; actual native TRAIN2/resources have not run. GPU1 released to others, M206 paused.',
        'unblock_condition':'Fresh live authorization/UUID/occupation/exclusive leases confirm server4 physicalGPU0 genuinely free; preserve exact active PSBR process and runtime checkout until naturally complete. Existing prepared PSNC remains ahead; no GPU1 or M206 use.',
        'next_action':'Preserve exact frozen BTC source00e2b18 and original YAML. After current PSBR and prepared PSNC resource order safely allow, use fresh owner/deadline/runtime/asset/UUID/idle/lease checks for real M95/candidate TRAIN2 and original resource protocol. Observe actual inside/outside/leaf path and finite updates, real supported n>=3 groups, common initialization pairing, constraints and resources. Only actual passing checks may generate summaries/receipt/queue; no tuning, source mutation or native PASS from these static tests.',
        'evidence':evidence}
    w['candidates'].append(candidate)
    psnc=next(c for c in w['candidates'] if c['id']=='hierarchy-parent-spectral-nonlinear-token-coupling')
    resource=ref(D/'psbr_training_progress_observation.json')
    if resource not in psnc['evidence']:psnc['evidence'].append(resource)
    psnc['last_resource_check_at']=now.isoformat();psnc['retry_after']=(now+timedelta(hours=1)).isoformat()
    psnc['blocker']='Only authorized GPU0 occupied by exact PSBR2372658/start35234267, native1/50 1296->1304 observed '+stamp+' Shanghai. Reuse complete PSNC43 operational preparation; no native slot, GPU1 remains released.'
    live=next(c for c in w['candidates'] if c.get('experiment_id')=='M209-PSBR')
    if resource not in live['evidence']:live['evidence'].append(resource)
    w['tick_attempt']={'tick_started_at':o['generated_at'],'candidate_id':CID,'kind':'implementation_test','result':'passed','command':prep['static_check_command'],'observation':'Actual production topology/source offline checks:589 assertions/42labels, independent11+22cases. Frozen9 blob-identical isolated source00e2b18; original skip and YAML retained. No torch/native/resources/admission; sole GPU0 busy with live PSBR. Exactly1 new reserve; existing PSNC plus BTC give two concrete preparations, not two ready/admitted experiments.','evidence':evidence}
    w['updated_at']=now.isoformat();save(R/'pipeline/research_work.json',w)
    assert {n:sha(R/'pipeline'/n) for n in names}==before
    mem=(R/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('\n## Last Tick\n',1)[0];lines=mem.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('- 当前foreground'):
            lines[i]='- 当前foreground'+T+'；actual owner/target一致，generated06:18:00.269793UTC/原deadline07:18:00.269793不延长。前b96c已FINALIZED/released(14:16:18上海)且headless lock/pending消失才begin；本轮随后真实report/finish确认，不预写PASS。'
        elif line.startswith('- M208-HRC stable'):
            lines[i]=line.replace('本轮原PID','此前b96c原PID')
        elif line.startswith('- M209-PSBR stable'):
            lines[i]=line.replace('本轮begin按','此前b96c begin按')
        elif line.startswith('- HRC本实现最终best'):
            lines[i]='- HRC已知本实现best.4901未超过M95，PSBR最终效果UNKNOWN；既有真实准入保留。PSNC43完整51离线操作包复用；本轮新增BTC00e独立准备，当前两者均未native/资源检查或准入。静态/数学/模拟均不能代签实测。'
        elif line.startswith('- 当前2026-10-23 '):
            lines[i]='- 当前'+stamp+'上海精确原PSBR PID2372658/start35234267/argv/cwd/remoteHEAD74f/GPU0UUID相符，native1/50两次1296→1304/4686增长，无error/logfresh/GPU0原context；proof SHA'+sha(D/'psbr_training_progress_observation.json')+'。尚无已观测验证指标。GPU1未查未用，无signal/额外计算。'
        elif line.startswith('- PSNC当前blocked/'):
            lines[i]='- PSNC当前blocked/exclusive_gpu_slot/resumevalidation：既存source43/完整工具/静态release保持，现PSBR占唯一GPU0，不改活跃remote checkout。BTC新source00e为43子提交并另有detached worktree，主HEAD仍74f。两具体准备按PSNC→BTC顺序等真实空槽/freshbinding native TRAIN2+原资源，不凑计数再造候选。'
    idx=lines.index('## Closed Or Failed Directions')
    lines[idx:idx]=[
        '- M211-BTC stable '+CID+'：原父组内真实点支持middle几何平衡二叉树inside/outside补集组合，仅换middle FFN，原cf skip/fine/coarse/rawbanks/CSORT/HCG/单inst保留；原detached xyz+ID稳定分裂/逆散回ID，无query/gate/新残差/pointN²。',
        '- BTC冻结8模型源+原YAML prep SHA'+sha(P/'preparation.json')+'，589断言/42标签及独立11+22生产纯树测试通过，非589实验。两源码/集成独审无确定bug；inside需真实同父n>=3才loss可达，actual torch/梯度/配对/FP32/成本/效果均NOT_RUN或UNKNOWN。',
        '- BTC源推断3共享2C→C maps共393984替原525568(−131584)，不称更快/更低实际FLOPs。isolated commit00e2b18c6b8d568a64edb496e6979d766440883c单父43，'+str(R/'pipeline/isolated_versions/btc_2c25f38f')+'保留；9blob exact、primary74f/index/28bytes及运行账保持。原prep code_commitnull历史不改，native_execution_code_commit仍null。',
        '- compact reserve_count排除全部blocked，exclusive_gpu_slot有专门wake/验证但未覆盖resource计数集合；不能把0误解为无现成准备，不改checker/tag/政策。实际PSNC+BTC两准备足够，只有PSBR真训练。',
        '']
    mem='\n'.join(lines)+'\n\n## Last Tick\n'
    mem+='- 本轮2c25心跳：begin一次monitor/已有派发/goal，design/candidate2/reserve2/creation2，PSBR唯一running、0readywaiting；HRC新terminal是前b96c已归档且已向用户报告，不重复当新成果。goal/SERVERS/授权/WindowsDisabled不变。\n'
    mem+='- '+stamp+'上海精确原PSBR1/50 1296→1304/4686两次增长、无error，GPU0忙；不query/use GPU1、不动M206、无新remote/GPU计算。PSNC原工具/51mock不重做，旧8hold/655正文不重查。\n'
    mem+='- 本轮新增且仅新增M211-BTC一具体储备，与现成PSNC共两准备。生产源码/树589断言42标签真实离线通过，独立11+22拓扑案例与集成审通过，不代表native/资源/效果；三mapinside需真n>=3等边界完整保留。\n'
    mem+='- BTC隔离普通本地commit00e2b18以43为父，9源blob与冻结prep相同，主74f/index/28文件、PSNC43 worktree/全部原队列实验收据不变。初次版本helper误拒绝默认GitLFS配置，尚未写worktree/ledger即退出；核exact default+禁smudge网络/无相关attrs后通过，未改源码/科学阈值/修订预算。\n'
    mem+='- tick_attempt actual implementation_test passed仅静态；BTC及PSNC均blocked/exclusive_gpu_slot，native执行null、准入/资源NOT_RUN，无新queue/训练。仅保存版本而不动活跃checkout；后续fresh空GPU0按PSNC→BTC真实原YAML TRAIN2/原资源，通过当轮准入/派发。\n'
    mem+='- 新冻结结构/源码/离线测试/独立版本是实质准备进展，NOTIFY；不把本轮收尾或版本保存称为科学成功。七段memory/六段report后原token真实finish+receipt FINALIZED released/lock pending消失再确认，释放后不回写。\n'
    assert mem.count('\n## ')==7 and len(mem.splitlines())<120;save(R/'pipeline/codex_memory.md',mem)
    notes={'actions':['canonical实际owner/target、最新memory/授权、goalSHA0441/SERVERS未变和WindowsDisabled核验；前b96c收据FINALIZED released且无lock/pending，原deadline不延长。begin一次monitor/goal/已有派发，PSBR1/50运行，无新operationalissue；HRC终态前轮已通知。',stamp+'上海只读精确PSBR2372658/start35234267/原argv/cwd/74f/UUID与GPU0原context，两样本1/50 1296→1304/4686，无error。唯一授权GPU0忙，GPU1不查不用，M206继续暂停，PSNC现成51项完整工具不重造。','按预算新增且仅新增M211-BTC：父组真实支持middle几何平衡二叉树inside/outside补集组合，保留M95原cf skip/fine/coarse/rawbanks/CSORT/HCG/单inst，原YAML逐字不变。589静态断言42标签及独立11+22生产纯树案例通过，两源码独审无确定bug；无torch/native/梯度/资源实测。','通过standing grant普通本地isolated commit00e2b18接43，仅冻结9新文件，actual staged/final blob匹配；main74f/index/28原文件及原queue/running/experiment/receipt保持，原PSNC43保留。首次版本helper误拒绝defaultLFS在写worktree前停止，限定exactdefault+skip-smudge/无相关attrs后成功，未更改共享config或科学阈值/源码。','新候选stageblocked/exclusive_gpu_slot/resumevalidation，native_execution仍null；current tick_attempt是实际implementation_test静态passed且证据归属新候选。已备PSNC+BTC两具体准备，0新准入/queue/launch/remote sync，不以compact blocked排除后的reserve0继续无限造候选。','七段memory和完整六段report按真实证据更新，原tokenfinish及receipt/lock释放核验后才确认。当前bestM95.5020/目标.5100差.0080；下一步保持PSBR原run，真实GPU0空槽后freshbinding依序推进PSNC和BTC真实原YAML TRAIN2/原资源。'],'decisions':['保留BTC一个独立可证伪结构储备，与已完成准备的PSNC合计两项；不凑预算、重复审旧hold/655、或重造PSNC工具。','版本仅普通本地独立保存，不改活跃PSBR源码/原配置、资源/调度/禁用项。原生和资源尚未执行，不准入；不提出已有授权覆盖的重复权限问题。']}
    save(D/'tick_notes.json',notes)
    save(D/'btc_registration_result.json',{'recorded_at':now.isoformat(),'token':T,'candidate_id':CID,'code_commit':version['code_commit'],'new_candidates':1,'admissions':0,'native':'NOT_RUN','resources':'NOT_RUN','snapshot_budget_used':{'candidate_budget':2,'reserve_budget':2,'creation_budget':2,'new_created':1},'concrete_preparations':['M210-PSNC','M211-BTC'],'notification':'NOTIFY','protected_registry_unchanged':{n:sha(R/'pipeline'/n)==value for n,value in before.items()},'evidence':evidence})
    print(json.dumps({'registered':CID,'code_commit':version['code_commit'],'new_candidates':1,'stage':'blocked_exclusive_gpu_slot','native':'NOT_RUN','new_admissions':0,'notification':'NOTIFY'},ensure_ascii=False))
finally:lock.close()
