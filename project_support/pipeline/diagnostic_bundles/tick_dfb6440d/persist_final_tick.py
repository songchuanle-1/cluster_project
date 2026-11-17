"""Persist actual two admissions, single verified launch, and bounded handoff."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib
import json
import os
import sys

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='dfb6440d1b69401da8e932239883e613'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):return {'path':Path(path).relative_to(ROOT).as_posix(),'sha256':sha(path)}
def save(path,data):
    path=Path(path);tmp=path.with_name(path.name+'.'+TOKEN+'.tmp')
    with tmp.open('x',encoding='utf-8') as stream:
        if isinstance(data,str):stream.write(data)
        else:json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())
    os.replace(tmp,path)

def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    final_review=HERE/'final_dispatch_independent_review.json'
    assert sha(final_review)=='f1700ced9cde0f3f118e22aa2bbe35affda1774c9d4ce14cae508244ddfc9069'
    assert read(final_review)['status']=='FINAL_CANONICAL_SINGLE_GPU_DISPATCH_AND_ACTUAL_PROGRESS_RECORD_REVIEW_PASS'
    progress=read(HERE/'hrc_training_progress_observation.json')
    assert progress['exact_original_process_and_native_progress_increasing'] is True
    observations=progress['observations'];a,b=[x['data'] for x in observations]
    assert a['pid']==b['pid']==2780804 and a['starttime']==b['starttime']=='29604100'
    assert a['progress']==[1,50,240,4686] and b['progress']==[1,50,250,4686]
    local_time=(datetime.fromisoformat(observations[-1]['observed_at'])+timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    raw_psbr=read(HERE/'psbr_execution/smoke_candidate_execution.json')['result']
    clarification={
        'recorded_at':datetime.now(timezone.utc).isoformat(),'id':'M209-PSBR',
        'scope':'Precision clarification of generic prose in already hashed standard artifacts; no measured value, source, raw evidence or receipt overwritten.',
        'actual_smoke_memory_scope':raw_psbr['smoke_memory_scope'],
        'auxiliary_autograd_grad_or_backward_used':raw_psbr['auxiliary_autograd_grad_or_backward_used'],
        'PSBR_has_no_HRC_coarse_dependency_autograd_probe':True,
        'actual_resource_comparison':'Counted9.749949516G vsM95 9.762532428G, median+4.6277% andP90+11.5821%. Lower counted FLOPs is not a claim of lower complete cost or faster execution.',
        'actual_common_initialization_scope':{k:v for k,v in raw_psbr['common_initialized_parameters'].items() if k!='names'},
        'full_state_including_buffers':'NOT_RECORDED','pure_TRAIN_memory':'UNKNOWN','efficacy':'UNKNOWN',
        'evidence':[ref(HERE/'psbr_execution/smoke_candidate_execution.json'),ref(HERE/'psbr_execution/resources_candidate_execution.json'),ref(HERE/'psbr_admission_independent_review.json')]}
    save(HERE/'psbr_result_scope_clarification.json',clarification)
    paths_by_exp={
      'M207-HAP':['hap_progress_observation.json','hap_native_earlystop_log_evidence.json','hap_terminal_archive.json','hap_terminal_independent_review.json'],
      'M208-HRC':['hrc_current_external_anchor_check.json','hrc_execution/execution_binding.json','hrc_execution/native_manifest.json','hrc_execution/execution_lease.json',
                  'hrc_execution/stage_execution.json','hrc_execution/smoke_champion_execution.json','hrc_execution/smoke_candidate_execution.json',
                  'hrc_execution/resources_champion_execution.json','hrc_execution/resources_candidate_execution.json',
                  'hrc_result_review/preparation.json','hrc_result_review/actual_four_result_review_v2.json','hrc_native_resource_independent_review.json',
                  'hrc_native_smoke.json','hrc_resource_comparison.json','hrc_constraints_independence.json','hrc_admission_queue_result.json',
                  'hrc_admission_independent_review.json','dispatch_local_precheck_failure.json','dispatch_result.json','dispatch_transport_calls.json',
                  'hrc_training_progress_observation.json','final_dispatch_independent_review.json','run_hrc_current.py','admit_hrc.py','dispatch_admitted.py','observe_hrc_training.py'],
      'M209-PSBR':['psbr_current_external_anchor_check.json','psbr_execution/execution_binding.json','psbr_execution/native_manifest.json','psbr_execution/execution_lease.json',
                   'psbr_execution/stage_execution.json','psbr_execution/smoke_champion_execution.json','psbr_execution/smoke_candidate_execution.json',
                   'psbr_execution/resources_champion_execution.json','psbr_execution/resources_candidate_execution.json',
                   'psbr_result_review/preparation.json','psbr_result_review/actual_four_result_review.json','psbr_result_review/actual_observation_limits.json',
                   'psbr_native_resource_independent_review.json','psbr_native_smoke.json','psbr_resource_comparison.json','psbr_constraints_independence.json',
                   'psbr_admission_queue_result.json','psbr_admission_independent_review.json','psbr_result_scope_clarification.json','run_psbr_current.py','admit_psbr.py','final_dispatch_independent_review.json']}
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor;import closure
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        queue=monitor.load_queue(str(ROOT));tasks={t['id']:t for t in queue['gpu_queues']['server-4']}
        assert tasks['M208-HRC']['status']=='running' and tasks['M208-HRC']['launch_verified'] and tasks['M208-HRC']['pid']==2780804
        assert tasks['M209-PSBR']['status']=='waiting' and 'pid' not in tasks['M209-PSBR']
        assert tasks['M206-CGCA']['resume_authorized'] is False and tasks['M206-CGCA']['training_status']=='paused_by_user'
        assert 'M207-HAP' not in tasks
        for exp in ['M208-HRC','M209-PSBR']:closure.admission(ROOT,tasks[exp]);closure.validate_foreground_dispatch_budget(ROOT,queue,tasks[exp])
        work=read(ROOT/'pipeline/research_work.json');byexp={c.get('experiment_id'):c for c in work['candidates'] if c.get('experiment_id')}
        for exp,names in paths_by_exp.items():
            c=byexp[exp]
            for name in names:
                item=ref(HERE/name)
                if item not in c['evidence']:c['evidence'].append(item)
        hap=byexp['M207-HAP']
        assert hap['stage']=='complete' and hap['training_status']=='done_earlystop'
        hap['previous_interruption_failure_scope']=hap.pop('failure_scope',None)
        hap.pop('resume_stage',None)
        hap['resume_authorization_execution_history']={
            'authorization':hap.get('resume_authorization'),'granted_and_executed':True,'native_start_epoch':19,
            'final_state':'done_earlystop','final_epoch':31,'final_best_rounded4dp':0.5002,
            'terminal_archive':ref(HERE/'hap_terminal_archive.json'),'new_resume_authorized':False}
        hap['resume_authorized']=False
        hap['completion_outcome']='native_earlystop_no_champion_gain_this_realization'
        hrc=byexp['M208-HRC'];psbr=byexp['M209-PSBR']
        hrc['native_launch_progress']=ref(HERE/'hrc_training_progress_observation.json')
        hrc['dispatch_review']=ref(final_review)
        psbr['result_scope_clarification']=ref(HERE/'psbr_result_scope_clarification.json')
        work['held_boundary_review']=ref(HERE/'held_boundary_check.json')
        work['tick_attempt']={
            'tick_started_at':owner['generated_at'],'candidate_id':hrc['id'],'kind':'native_smoke','result':'passed',
            'command':'python -B pipeline/diagnostic_bundles/tick_dfb6440d/run_hrc_current.py run smoke candidate',
            'observation':'HRC/M95 each actual nativeTRAIN2 finite loss/backward/path/mean controls plus original paired resources passed and independently reviewed. PSBR also completed its actual paired native/resource checks. Two honest74f receipts admitted/queued within budget2; canonical ff-only sync/current-source checks and singleGPU0 HRC launch verified, additional exactnative1/50 step240->250. PSBRwaiting; HAP native31 earlystop archived; M206paused/GPU1released.',
            'evidence':[ref(HERE/'hrc_native_smoke.json'),ref(HERE/'hrc_resource_comparison.json'),ref(HERE/'psbr_native_smoke.json'),ref(HERE/'psbr_resource_comparison.json'),ref(HERE/'dispatch_result.json'),ref(HERE/'hrc_training_progress_observation.json')]}
        work['updated_at']=datetime.now(timezone.utc).isoformat()
        save(ROOT/'pipeline/research_work.json',work)
        memory=f'''# Codex Research Memory

## Goal And Phase
- 当前foreground{TOKEN}；actual owner01a159c5-29ab-7a22-ba7f-e79174757253与execution_mode target一致。generated UTC14:04:13.975758/原deadline15:04:13.975758，未延长；前轮37695e94已FINALIZED/released(12:31:42UTC)且无lock/pending才begin。本轮最终状态以真实report/finish/receipt/lease释放为准，不预写PASS。
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，championM95.5020/gap.0080，baseline.4894。Phase1 hierarchy→inst_feats→query/masks；supervision辅助，Phase2仍需确认。
- 原native seed1999/epochs50/maxiters70及统一default10G、bs1/lang1/warm20/repeat100/显存+15%保留条件不改；禁调参/gate/语言路由/大QKV/pointN²/重复注入/新残差系/纯数值缩放/旧rejected改名。
- standing experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖本项目常规实现/检查/保存版本/安全同步/准入训练。技术准入不证明新颖性/效果；不授权旧hold重开/额外修订/受保护重启/资源或调度扩张。
- 最新人类资源“GPU1可以先暂停训练了 给别人腾出来一张卡”：仅server4 physicalGPU0/max1，grant server4_gpu0_only_20261022_gpu1_pause_105409.json SHA1871f8c9777c548acfda87b9e91b72c2d5fc94ac78920430c52bdceea1cbd51e。GPU1不查询/计算，M206不迁移恢复，server3/server6无allowed，Windows Pipeline-cluster_project Disabled保持。

## Champion And Baseline
- M207-HAP本次恢复run已自然earlystop：原PID1063355消失，原native log明确epoch31/50、10次不刷新、best0.5002(终态行4位)。低M95.5020约.0018、低目标.5100约.0098；保留此实现无冠军收益结果，不泛化整条层级假设失败、不调参重跑。
- 原生早停发生在根额外观察前；begin仍登记1running，不能用登记代替活进程。本轮22:05上海精确原PID不存在/唯一原log早停、GPU0 41MiB/util0/no contexts，两次只读核后canonical finalize_task(done_earlystop)归档，无signal/deathwatch递增。
- 新resume完整log17,244,478字节已拉本地，SHA930e41c6以hap_native_earlystop_log_evidence.json全hash为准；archive SHAa7c9830289f166a262606c3a3e0aa4459d07b41e26d8f10d949f88b44bc3bd47，独审8211261935b1d7c2f48bc84c271db2850e64074c6890b76eb533708536aed820。原crash prior_runs/CSV旧行/source/receipt/human授权历史保持。
- M205-MDC原done_earlystop26/noimprove10/best.4872保持；M206-CGCA人工暂停full meta24/best.4952535927295685/noimprove7，非失败，不自动迁移GPU0。

## Active Hypotheses
- M208-HRC stable hierarchy-bottom-up-refined-token-composition，tested/queued/live commit74fcd21df0af9a971792038ffe251af1ffea2604，当前training/running物理GPU0 PID2780804/start29604100。原3FFN各一次，refined fine经原fixed-child mean进入middle，再经原mean进入coarse；rawbanks/FPS/IDs/CSORT/HCG/单inst保持，新增参数0。
- HRC本轮真M95/candidate TRAIN2及原资源pair共4进程完成；两TRAIN输入/原seed+pretrain/3FFN初值hash匹配，candidate loss9.45667839050293/13.928205490112305、有限backward/逐级FFN更新，4mean误差max5.00679e-7≤冻结1e-6。coarse依赖fine/middle梯度非零而M95均None，.grad/opt/sched/RNG probe隔离通过。
- HRC原计数9.762532428G两者相同、157484090参数，median35.58357vs35.92329ms(-.946%)、P9037.75154vs37.18611ms(+1.521%)。prediction allocated/reserved相同；smoke allocated+.00806%/reserved+.02235%，无15%条件触发；新增scatter等unsupported完整披露，不称零实际成本。
- HRC标准smoke/resource/constraints位于tick_dfb6440d/hrc_*.json；receipt pipeline/admissions/M208-HRC.json SHA4af51a3ae3b77525a820e292db4ce5fa7f26f634665321441aa31ad748fdee96。四raw独审42eb6f8abde465ca0ae55a26fcb39f08b87975a8e86ac137f22db77468520607，正式准入独审759c130cb864e8611b2de2c37491ee0f4b4ad673289a879d098dd566f7001887。
- HRC旧实现9e543af623acd7fa9bd4a3f81ce79c932e98774a与新74f绑定历史完整在version_binding_history；旧准备包/worker不改。本轮新真实raw确绑定74f，运行诊断时runtimeHEAD真实f518，后canonical ff-only至74f及前后source核通过；不是旧结果重标。
- M209-PSBR stable hierarchy-parent-segmented-bidirectional-token-state，commit同74f；已真实准入并FIFO waiting GPU0，无PID/正式训练步数。middle原FFN被原父组/原坐标+ID排序的Wx/Wh双向tanh零边界状态和Wo逆散回原ID替换，fine/coarse/原raw-CSORT/HCG/单inst保持。
- PSBR真M95/candidate TRAIN2及资源pair4进程完成；两TRAIN/seed/pretrain/loader一致；排除替换middle/新module的843个common named参数(156958522参数)names/count/hash实际相同。loss9.569498062133789/13.913694381713867；WxWhWo每步有限非零梯度且更新，每forward64真nonsingleton父组、1024Wh调用/896非边界非零输入，双向组界零态及inst→ILA→mask路径实测。
- PSBR计数9.749949516G vsM95 9.762532428G、157221178参数(−262912)；median37.1181vs35.4764ms(+4.6277%)、P9041.0930vs36.8276ms(+11.5821%)，预测allocated935713280vs936763392/reserved1189085184vs1191182336；无15%条件触发。tanh128/index_select8/index_copy8等unsupported保留；计数更低但实测更慢，不称整体成本更低。
- PSBR标准smoke/resource/constraints位于tick_dfb6440d/psbr_*.json；receipt pipeline/admissions/M209-PSBR.json SHAc85ae4fe82f83720330ca5b1bca176492bcc8fa82f9c2ddad98d49712c6416a2。四raw独审4bddd224d76cb8c387755e77441e2254980577d65b4e8ee38bf1b4ef52bdc585，正式准入独审8f051315c8ed6a0f84d72dc796423188d9161014a32f344e9a0169c3f8f4a316。
- HRC/PSBR所有运行效果仍UNKNOWN。此次只完成技术首筛/准入及HRC启动，不提前证明完整期稳定、验证收益或机制创新。已满足本轮2个准入预算，不新增结构/改模型/消耗修订。

## Closed Or Failed Directions
- 8旧hold本轮due仅有界核完整元数据/引用签名：与tick2f基准同8候选、无新scope/reopen/extra revision授权；报告a4684e9a10195574d2f1c38fff68b16128dd7833e7e6f4e14003d263408b045a。655旧证据本轮正文读取/重hash/exists-mtime复查均0，历史全body核沿用，不冒称新字节证明。
- 4supervision scope、2measurement实现/未定hold、PCE/RSTR修订上限保持；PCE默认2+额外1耗尽/2.861e-6与13.86x延迟，RSTR默认2耗尽/R2 mean1.027033878e-6>1e-6。禁PCE R4/RSTR R3、M201自动恢复；36b59daa九文件提交授权不是新修订。
- HAP旧19轮DataLoader AttributeError crash底因UNKNOWN，原log SHA794be0ab616954c28ec8b120f57309c6443f7ba87133c983e2f506887ad84a59/固定epoch18全状态及原失败归档保持。本次resume正常earlystop不证明已修复；不把环境实现中断归为整假设反证。

## Running And Queue
- current queue：M208-HRC running GPU0/launch_verifiedtrue；M209-PSBR waiting GPU0/已准入非hold；M206-CGCA waiting但paused_by_user/dispatch_hold/resumefalse，不计readywaiting。HAP从queue/running移除、experiment done_earlystop/researchcomplete，原prior_runs未覆盖。
- 新HRC原argv为python tools/train.py configs/Quard/ctf_hcg_csort_hrc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hrc.yaml --gpu_ids 0 --num_gpus 1；新日志后缀20261022_223140.log。{local_time}上海额外精确PID/start/argv/cwd/remoteHEAD74f及GPU0UUID核，native1/50步240→250/4686，无error，仅HRC context；proof SHA20e473ae380ca9a4db6609860a0e87dd6b46699301fb2b51cb52e48e59faef82。
- pinned server4 192.168.1.115/dl04-MS-7E06；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster；keys/strict hostkey，不用旧.137或密码/sudo。canonical safe_sync先核f518实际源、只新增HRC/PSBR18文件ff-only至74f，再核74f实际源，1次nativePopen/8次进度只读poll；GPU1不查询使用。
- 本轮dispatch_result SHA615b9b93f0430147b32897eb3262d96734bfb288c8b54657597ccba7d2b06bad；最终派发独审f1700ced9cde0f3f118e22aa2bbe35affda1774c9d4ce14cae508244ddfc9069，无实质问题。实际launch前UUID/idle/3flocks可取得探测后已释放，不宣称整个训练持该三锁。
- localHEAD74f/index空/原28dirty-untracked字节/status由本轮两次独审核实保持；无新Gitcommit/stash/reset/clean/force。同步只push既测commit/ff-only并按既有映射适配HRC的部署YAML，无更改seed/schedule/dataset/环境。
- HAP21799完整resume授权已执行至自然终态，原人类grant/固定18 snapshot/完整optimizer+scheduler和历史留存；candidate当前不再有新resume许可，不自动重启。M206仍需未来专属human授权及exact source/fullstate合同，不能借HAP授权。
- M206 fullsnapshot /data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261022_gpu1_pause_105409/20261021_232736/last.pth SHAe9b42b2632762dae5ca49d80b3272889809b1ffe3ec30dd377690af8cb2e8e9d，admitted898ff63与当前remote74f区别保留；无授权不迁移/重置共享checkout/恢复。

## Open Questions And Risks
- HRC全common初始state hash未记录；只实核两batch/seed+pretrain/3FFN初值；PSBRcommon named参数实际匹配，完整buffers/fullstate未记录。跨目标raw/ID/map字节存在差异，未量化幅度或确证原因，不新增exactbank输出门或冒称数值等价。
- 两批actual HRC内部empty child/padding与PSBR真实unsupported/padding计数均0，断言通过不能代表非平凡空槽边界已实测。PSBR offdiagonal/resetstate干预未做，不新造准入门。
- HRC smoke含autograd.grad dependency probe并已核隔离；PSBR smoke只有observer/reference，无该HRC辅助autograd probe。纯TRAIN峰值均UNKNOWN，预测profile不等于完整训练。psbr_result_scope_clarification.json补泛化文案精度，未覆盖既存hashed标准证据/receipt。
- 所有FLOPs均原fvcore口径而非全算子完整成本，unsupported披露不可忽略；原no-cluster baseline此次未重测，相对M95的数值只限本次固定资源输入/原协议，不宣称泛化性能/完整训练收益。
- HAP原长期worker根因/失败样本UNKNOWN；旧freshCPU torch2.8.0+cu128/np1.26.4合成检查不是native失败复现，不改workers/np.where/环境。HAP旧pinv max|Gplus|1308527.125与幂等误差.114782333保留，不加ridge/改精度阈值。
- 诊断当前stage/manifest/lease只绑定本tick原deadline；finish后不得重放/续租旧stage。2个已准入训练任务按各自receipt/current source与资源保护派发；未知launch保留PID/log/claim，只读reconcile不盲重试/kill。

## Last Tick
- dfb6440d begin只一次monitor/已有派发/goal，actualowner/goal/资源/Disabled不变；初登记1HAPrunning/0claiming、M206paused waiting，0新终态/operationalissue。后额外精确核native早停并canonical归档HAP31；原crash/授权/检查点历史完整。
- 按已准备候选推进，先HRC/M95真TRAIN2+原资源，再利用本地审核时间完成PSBR/M95真TRAIN2+原资源；8独立GPU进程均完整确定终态、原token/UUID/三锁/双idle/资产守卫通过，无并行占卡或GPU1用量。
- 新HRC failclosed reviewer14离线拒绝测试、PSBR reviewer18离线测试及两份四raw独审完成；真实标准smoke/resource/constraints生成、canonical admission+budget核验通过，HRC/PSBR共2个新收据/2入队，精确用完本轮预算2。0新候选结构/0模型修订/0新Gitcommit/0旧hold重开。
- canonical单次FIFO派发前source ff-only f518→74f、前后源核通过，唯一HRC nativePopen成功并有240→250额外步数proof；PSBRwaiting/M206paused，HAPcomplete。root第一次driver只读normalizedserver键KeyError在0SSH/0mutation前已修复并留档，不是训练失败/重试。
- HRC正式43项/PSBR正式45项独审与最终单GPU派发独审均无阻断；原28dirty/emptyindex/旧失败保持。所有真实证据/decision/receipt引用已归candidate；本轮technical进展通知，不把未测效益写PASS或等到deadline。
- 六段report和finish随后按真实返回/FINALIZED/released与lock/pending消失确认，释放后不回写。本轮NOTIFY：HAP完成、两候选准入、HRC已运行/PSBR排队，无新用户处理事项。下一轮先核同HRC进度/终态/队列，正常时继续原协议；GPU0自然可用后已有PSBR按原收据同入口派发，不新增审批或改调度。
'''
        assert len(memory.splitlines())<120 and memory.count('\n## ')==7
        save(ROOT/'pipeline/codex_memory.md',memory)
        notes={'actions':[
          '仅cluster_project，实际会话/target一致，前轮37695e94已FINALIZED/released且无lock/pending；current generated14:04:13.975758UTC/原deadline15:04:13.975758不改。原goal/Phase1/白名单GPU0 max1/禁用项/Disabled保持。',
          'begin先monitor/已有派发/goal一次，初登记HAPrunning、M206paused waiting，0claiming/新终态/operationalissue；extra strict pinned精确原PID/log核实HAP已自然31/50 earlystop/noimprove10/best.5002，GPU0空闲。原日志拉本地hash核后canonical finalize_task归档，无signal/deathwatch递增；旧crash/prior_runs与M206完整暂停队列保持。HAP此实现未超过M95.5020，不宣称整假设失败或旧loader根因已修复。',
          '8旧hold due仅有界元数据/引用签名/有限授权核，原8签名不变，无新reopen/scope/extra revision。655旧body本轮读取/重hash/exists-mtime复查均0，不把旧全body核冒充新测；M206无新恢复许可/GPU1继续别人。',
          '外锚核HRC新74f冻结native/adapter后，当前owner/context/pending/goal/原deadline/物理0 UUID/双idle/三flocks及实际资产守卫通过，隔离stage运行M95/HRC两TRAIN2与原资源pair4进程；全部有确定原始结果。candidate74f/runtime诊断时真实f518分开，不重标旧9e或改模型/协议。',
          'HRC两batch/seed1999/pretrain/3FFN初值匹配，候选两loss9.45667839/13.92820549、有限梯度/每级更新，mean最大5.00679e-7≤原1e-6，coarse→fine/mid候选非零而M95None，probe隔离核通过。原资源9.762532428G/参数相同，median−.946%/P90+1.521%，无15%内存条件；完整commonstate/非平凡空槽/pureTRAIN/效果未知，unsupported如实。',
          '在HRC本地审核阶段推进已冻结PSBR：同当前owner/物理0 guard，4真TRAIN/resource进程完成且确定终态。两batch、843个common named参数初值匹配；WxWhWo每步有限非零梯度/更新，每forward64nonsingleton父组与原mask路径实测。计数9.749949516G/参数−262912，median+4.6277%/P90+11.5821%，无15%内存条件；新增tanh/index操作unsupported保留，不称完整成本更低。空槽/padding/offdiag/resetstate/fullbuffers/pureTRAIN/效果未知。',
          '两套新failclosed reviewer分别实际14与18离线拒绝检查通过，两个真实四结果独审完成。root按真实optimizer_steps整数2/data_source.train生成native_smoke、原资源比较与独立性/约束证据；canonical closure.admission及本tick预算核通过，分别生成M208-HRC/M209-PSBR哈希收据入队。正式准入独审43/45项通过，无把mock或raw completed代签准入。',
          '仅一次canonical _process_queue FIFO实际派发：严格hostname/GPU0-only/UUID/idle/三flocks前检，先核f518实际源，再既测commit ff-only到74f并核新源；1次nativePopen、无盲重试/驱逐/GPU1操作。root首个driver本地normalizedserver可选键KeyError在0SSH/0mutation时已纠正留档，不是训练重启。',
          f'{local_time}上海额外原PID2780804/start29604100/原HRC argv/cwd/remoteHEAD74f/UUID核，正式native1/50步240→250/4686，无errors，仅HRC占GPU0。M208 running/launch_verifiedtrue，M209 waiting无PID；M206仍人工暂停、HAPdone_earlystop。最终派发独审无实质问题。',
          '本轮2既有候选完成真实准入/2入队/1验证启动、HAP1自然终态；0新模型结构/0修订/0Gitcommit/0旧hold重开；一次既有ff-only同步，无seed/schedule/data/环境/资源/调度改变。原28dirty字节/status/空index保持；PSBR泛化文案边界另补澄清证据，不覆盖已hash记录。',
          '七段memory与六段report留档后按原token finish并实核FINALIZED/released和lock/pending消失，不预写PASS、释放后不回写。本轮有完成/准入/启动实质进展，NOTIFY简报；无需人类新确认。后续先核HRC进展，GPU0自然空闲后派发已准入PSBR；M206不恢复/GPU1不借用。'
        ],'decisions':[
          '按本轮实际原生/资源与独审证据，常规experiment_first授权下技术准入HRC74f与PSBR74f，canonical预算2严格核验后FIFO入队；HRC先在唯一GPU0训练、PSBRwaiting。完整效益待原训练，不为准入预先要求验证上涨，不放宽10G/数据/资源/禁用或旧修订。',
          'HAP原生31轮earlystop作为该实现无冠军收益终态归档；不人工kill/重启、不把共享加载器旧crash根因写成已修复或整层级机制已证伪。8旧hold保持、M206人类暂停优先、GPU1继续留给别人。'
        ]}
        save(HERE/'tick_notes.json',notes)
        save(HERE/'final_tick_evidence_summary.json',{
            'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'new_admissions':2,'new_queue_items':2,
            'verified_formal_launches':1,'new_structures_or_model_revisions':0,'natural_terminal_runs':1,
            'HRC_status':'running_verified_native_progress','PSBR_status':'waiting_admitted','M206_status':'paused_by_user','HAP_status':'done_earlystop',
            'memory_lines':len(memory.splitlines()),'six_section_report_and_finish':'PENDING_ACTUAL_CANONICAL_CALLS',
            'evidence':{'HRC_receipt':ref(ROOT/'pipeline/admissions/M208-HRC.json'),'PSBR_receipt':ref(ROOT/'pipeline/admissions/M209-PSBR.json'),
                        'dispatch':ref(HERE/'dispatch_result.json'),'extra_progress':ref(HERE/'hrc_training_progress_observation.json'),'final_review':ref(final_review)}})
        print(json.dumps({'persisted':True,'memory_lines':len(memory.splitlines()),'formal_launch_verified':True,'HRC_progress_verified_at_shanghai':local_time,'new_admissions':2,'report_finish':'PENDING'},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
