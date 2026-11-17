"""Record the actual PSNC terminal result and verified BTC admission/launch."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
TOKEN='ddb531fb89824389b3b2e2df5779a5ef'
COMMIT='00e2b18c6b8d568a64edb496e6979d766440883c'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
    t=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with t.open('x',encoding='utf-8') as f:
        f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n'); f.flush(); os.fsync(f.fileno())
    os.replace(t,p)

owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
assert sha(ROOT/'pipeline/goal.json')=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
assert sha(ROOT/'SERVERS.yaml')=='9a8f9a03a1c72ba07cc428944424ae62dce7cb6c9678c17bfb90fef8c20593ba'
for name in ['psnc_terminal_independent_review.json','btc_native_resource_independent_review.json','btc_admission_independent_review.json','btc_pre_dispatch_review.json','btc_final_dispatch_independent_review.json']:
    assert read(HERE/name)['material_concerns']==[],name
assert sha(ROOT/'pipeline/admissions/M211-BTC.json')=='93756329046cf30357c258848d6b3287c25b4b0c96ef69b0ffd5f3b8710f2a36'
dispatch=read(HERE/'btc_dispatch_result.json'); assert dispatch['verified_native_progress'] and dispatch['canonical_dispatch_invoked_once'] and dispatch['m206_queue_unchanged']
obs=read(HERE/'btc_progress_observation.json'); a,b=[o['data'] for o in obs['observations']]
assert obs['same_exact_registered_process_and_native_TRAIN_growth'] and a['pid']==b['pid']==2784474 and a['start_ticks']==b['start_ticks']=='47557208' and not a['errors'] and not b['errors']
assert a['train_progress']==[1,50,123,4686] and b['train_progress']==[1,50,131,4686] and b['runtime_HEAD']==COMMIT
held=read(HERE/'held_boundary_check.json'); assert held['material_concerns']==[]
stamp=datetime.fromisoformat(obs['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline'); import pipeline_monitor as monitor
lock=monitor.acquire_lock(str(ROOT)); assert lock is not None
try:
    protected_names=['queue.json','running.json','experiments/M211-BTC.json','experiments/M210-PSNC.json','experiments/M206-CGCA.json','admissions/M211-BTC.json','admissions/M210-PSNC.json']
    before={n:sha(ROOT/'pipeline'/n) for n in protected_names}
    q=monitor.load_queue(str(ROOT)); t=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M211-BTC')
    assert t==dispatch['task_after'] and t['status']=='running' and t['launch_verified'] and t['code_commit']==COMMIT and t['pid']==2784474 and t['gpu']=='0'
    m206=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M206-CGCA'); assert m206['dispatch_hold'] and m206['resume_authorized'] is False and m206['status']=='waiting' and not m206.get('pid')
    assert monitor.load_running(str(ROOT))['server-4']=={'0':'M211-BTC'}
    assert monitor.load_experiment(str(ROOT),'M210-PSNC')['status']=='done_earlystop'
    work=read(ROOT/'pipeline/research_work.json'); c=next(c for c in work['candidates'] if c.get('experiment_id')=='M211-BTC'); p=next(c for c in work['candidates'] if c.get('experiment_id')=='M210-PSNC')
    assert c['stage']=='training' and c['native_execution_code_commit']==COMMIT and p['stage']=='complete' and p['final_best_miou']==0.5001
    names=['btc_native_smoke.json','btc_resource_comparison.json','btc_constraints_independence.json','btc_native_operation_history.json','btc_native_resource_independent_review.json','btc_primary_ff_result.json','btc_admission_queue_result.json','btc_admission_independent_review.json','btc_pre_dispatch_review.json','btc_dispatch_result.json','btc_progress_observation.json','btc_final_dispatch_independent_review.json']
    evidence=[ref(HERE/n) for n in names]+[ref(HERE/'btc_execution'/(m+'_'+s+'_execution.json')) for m,s in [('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')]]
    for item in evidence:
        if item not in c['evidence']:c['evidence'].append(item)
    terminal_evidence=[ref(HERE/n) for n in ['psnc_terminal_idle_observation.json','psnc_native_earlystop_log_evidence.json','psnc_terminal_archive.json','psnc_terminal_independent_review.json']]
    for item in terminal_evidence:
        if item not in p['evidence']:p['evidence'].append(item)
    c['next_action']='Monitor only original BTC2784474/start47557208/unique native log on server4 physicalGPU0, preserving tested00e/receipt9375/source/runtime identity and original seed1999/YAML/schedule. Formal efficacy UNKNOWN. No GPU1 use, M206 resume, restart, tuning or source mutation.'
    work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':c['id'],'kind':'native_smoke','result':'passed','command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_7dcc29e8/btc_operational_prepare/adapter.py run --mode smoke --target candidate --execution-dir '+str(HERE/'btc_execution'),'observation':'Actual original TRAIN2 and matched four-arm resource diagnostics independently reviewed; native tree inside/outside/leaf gradients and updates observed. Tested00e admitted and canonical dispatch once verified; exact original native TRAIN1/50 123->131. Diagnostic PASS is not efficacy; counted9.758338124G, median+13.3134%, P90+19.3694%.','evidence':evidence}
    work['historical_hold_boundary_review']=ref(HERE/'held_boundary_check.json'); work['updated_at']=datetime.now(timezone.utc).isoformat(); work['next_action']=c['next_action']; save(ROOT/'pipeline/research_work.json',work)
    memory=f'''# Codex Research Memory

## Goal And Phase
- 最新接管{TOKEN}；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner['generated_at']}/原deadline{owner['deadline_at']}不延长。前f34已FINALIZED/released、无lock/pending才begin。本轮真实finish/释放结果见receipt，不预签。
- goal0441fecda…；ScanRefer目标.5100、M95最佳.5020/gap.0080、baseline.4894。Phase1 hierarchy→inst_feats→query/masks主线；supervision辅助，Phase2仍需人类确认。
- 原seed1999/epochs50/maxiters70/native YAML/data/optimizer和10G原口径、bs1/lang1/warm20/repeat100/显存+15%条件保持。禁调参/gate/语言路由/大QKV/pointN²/重复注入/新残差/纯缩放/旧rejected改名。
- standing pipeline/authorizations/experiment_first_20261021.json SHA2e892959…覆盖常规实现/实测/相关版本/安全同步/准入训练；不授旧hold重开/额外修订/受保护恢复/扩资源/改调度。
- 最新人类资源server4 physicalGPU0/max1、grant server4_gpu0_only_20261022_gpu1_pause_105409.json SHA1871f8c9…；GPU1暂停给别人且不查不用，M206不自动恢复或迁移。其他服务器无allowed，Windows Pipeline-cluster_project Disabled。

## Champion And Baseline
- M95仍.5020；M205-MDC自然earlystop26/.4872，M207-HAP人类授权epoch18完整恢复后自然earlystop31/.5002，M208-HRC自然earlystop31/.4901，M209-PSBR自然earlystop23/.4969；均未超M95，不调参重跑或泛化整假设失败。
- HAP原19轮DataLoader AttributeError根因UNKNOWN；epoch18恢复授权已消费，不是再restart许可。原crash/snapshot/prior_runs及resume完整log17,244,478B/930e…、archive a7c983…保留。HRC完整log41,105,155B/31b8…与receipt4af5…保留。
- PSBR原PID2372658/start35234267精确原log完整30,985,906B/0204be90…归档于tick_a4f73140，receipt c85a…与source74f保持；canonical done_earlystop23/.4969。
- 本轮M210-PSNC原PID2502712/start41082267已自然消失；双核GPU0空闲/no contexts，精确原log earlystop31/10次未提升/best.5001；完整log本远SHA一致见本轮psnc_native_earlystop_log_evidence.json。canonical finalize_task已done_earlystop、candidate complete、移出queue/running，source43/receipt406e…/launch历史保持。
- PSNC归档a1aab97d…及独审de7d2fcf…29项无阻断，低M95.0019、低目标.0099，仅此实现无冠军收益。原PSNC TRAIN2/资源/准入完整证据仍在tick_a4f73140，不为新结果重跑或重标。

## Active Hypotheses
- 当前M211-BTC stable hierarchy-parent-binary-tree-complement-composition，tested/source/queued/live00e2b18c6b8d568a64edb496e6979d766440883c，单父43dce016c1a1713c2a5dab7061810dc2efde8954。原middle FFN换为原几何父组平衡二叉inside/outside补集，原cf skip/middle LN/fine-coarse FFN/raw-CSORT/HCG/单inst保留。
- 冻结原prep tick_2c25f38f/new_candidate_prepare/preparation.json SHA c36b4d09…的8模型+1原YAML不改；原589断言/42标签和11+22独立stdlib检查不是训练实验，本轮未重跑。isolated_versions/btc_2c25f38f及psnc_d6b400e3保留。
- 复用tick_7dcc29e8/btc_operational_prepare完整catalog：outer9be7386a…/native82b7ae52…/manifest template4a28e488…/staticrelease765beabf…，worker a39fbffa…/runtime dd2ac226…/adapter c83d9e88…/remote97192f56…不改。46离线与10 AST等历史检查不冒充本轮native。
- 本轮fresh actual owner/context/pending/deadline与GPU0 UUID/实际idle/3锁/runtime43/assets后prepare+stage btc_ddb531fb；native manifest c2bac7c3…、lease858d3266…；诊断candidate00e/runtime43区别保留，不回写旧prep。原null/未执行metadata已存execution_preparation_history，当前actual字段已真。
- 实际原TRAIN2 loss9.507390975952148/13.910472869873047，原loss/backward/optimizer各2；与M95两batch及common843 named tensors/156958522参数/hash04231c23…配对（双方排除旧middle FFN与新middle_tree，保留LN）。actual total157352506 vs157484090，差-131584，三map393984替525568。
- 每forward真实64个n>=3支持父组，inside384/outside896/leaf512/rootinside0；全部384 proper-inside输出收到原loss非零有限梯度，三map与FFN0/2每步weight更新，原HCG→inst/ILA/mask观察成立。空/unsupported/pad/singleton均0，未行使；非全FP32算子或offdiagonal控制。
- 实际原资源口径BTC9.758338124G vsM959.762532428G；median38.3591485vs33.8522580ms(+13.3134%)，P9042.3771437vs35.5008325ms(+19.3694%)，延迟变慢。预测allocated936238592vs936763392、reserved1189085184vs1191182336，15%条件未触发；unsupported全披露，非完整CPU/Python总成本。
- 四原请求均terminal/rc0且只读reconcile完整result/identity/hash与本地相同；workers[]/GPU0 contexts空，operationhistory03bbca16…，无重放/kill/续lease。语义15e19fbf…、独审dc03f6cd…133项、准入独审e0127ddd…39项；receipt pipeline/admissions/M211-BTC.json SHA93756329046cf30357c258848d6b3287c25b4b0c96ef69b0ffd5f3b8710f2a36。

## Closed Or Failed Directions
- 本轮8旧hold到期仅核完整canonical元数据/655声明引用字符串签名及13授权path-size-mtime，均等2747基准；proof {ref(HERE/'held_boundary_check.json')['path']} SHA{sha(HERE/'held_boundary_check.json')}。0证据正文read/hash/exists-stat，0grantbody读，无新scope/reopen/extra revision或用户事项，不是科学复测。
- 4supervision scope、2measurement implementation/inconclusive、PCE/RSTR修订限度保持；PCE默认2+额外1已尽/2.861e-6与13.86x；RSTR默认2已尽/R2mean1.027033878e-6>1e-6。禁PCE_R4/RSTR_R3/M201自动恢复；旧RSTR九文件localcommit授权不是新修订许可。
- 原HRC/PSBR/HAP/PSNC全部负结果、原失败/源版本/收据/日志保持，不整体否定hierarchy主机制或用已完成诊断重新选样/seed。

## Running And Queue
- 当前唯一M211-BTC server4 GPU0/PID2784474/start47557208；{stamp}上海双核原argv/cwd/fd1唯一log/HEAD00e/GPU0UUID，Train1/50 123→131/4686，原进程context且无error。proof本轮btc_progress_observation.json SHA2168848ec1de7d9adf2bc6e2e26c1f2b967ef55a1fd62b4defb404f29203acee；未查询/使用GPU1。
- 本轮primary43→00e只9已测新增ff-only，无新commit/force/stash/reset/clean；原28dirty/untracked status和字节前后保持、index空。原disabled草稿保留，root sibling btc_promotion_execute仅绑定真实审阅path/SHA并启用显式入口，materialization留原/新SHA。
- canonical safe_sync远端43→00e并前后验证实际source，候选YAML仅既有确定性路径适配；唯一_process_queue/一次Popen/15transport，启动wrapper持3flock覆盖UUID/idle至Popen返回后释放，不声称全程训练锁。pre-dispatch审616d84f1…采样在launch前，launch后另有真实result/progress及最终独审。
- pinned songcl@192.168.1.115/dl04-MS-7E06，GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster/runtime server4_conda_4ca73fba.sh，data /home/songcl/data/data/；keys/strict hostkey，不用旧.137/密码/sudo，python -B。
- M206-CGCA waiting但人工paused_by_user/dispatch_hold/resume_authorizedfalse，无PID、不计ready、不自动移GPU0。fullsnapshot meta24/best.4952535927295685/noimprove7，last.pth SHAe9b42b2632762dae5ca49d80b3272889809b1ffe3ec30dd377690af8cb2e8e9d；admitted898ff63/runtime00e区别保留，无新恢复授权。

## Open Questions And Risks
- BTC正式训练准确率UNKNOWN；有限loss/梯度/资源准入不证明上涨或新颖性。当前目标.5100仍差.0080，不为达标调seed/schedule/阈值或用test集选机制；本轮BTC预测中位和P90明确更慢。
- 配对覆盖common named params与两批输入，完整buffer/RNG未逐值配对；rawbank跨目标digest不同，不作因果归因。实际empty/padding/singleton未行使、offdiag及完整FP32算子控制NOT_RUN。
- 原fvcore口径完整unsupported保留，CPU/Python几何树工作不全计；纯TRAIN峰值UNKNOWN，smoke包含observer/topology开销，不等同完整训练显存或部署准确率。
- HAP长期worker根因UNKNOWN，不改环境/worker/data规则或自动恢复。所有未知launch先原request/PID/log只读reconcile，不盲重启或删锁。当前诊断lease仅原deadline，后续新诊断须fresh owner/assets/idle，static catalog不是GPU许可。

## Last Tick
- begin一次monitor/goal/既有派发，design budget2/reserve2/creation2，前置1running/0ready/9due。先精确核PSNC自然终态并完整归档，再完成既有BTC四臂实测、版本、准入及当轮已授权启动，未凑满额度或新建占位候选。
- 实际新增准入1/verified launch1、新candidate0/新commit0/implementationrevision0；复用既有BTC实现，主仓9文件ff-only，本轮4真实诊断请求均terminal/rc0、两步原TRAIN+完整资源pair通过，并非新增准确率结论。
- 实际原BTC1/50 123→131增长；M95仍.5020，PSNC本轮归档.5001。GPU1/M206/goal/SERVERS/原seed/YAML/schedule/禁用项/调度不变；旧hold仅有界元数据复核。
- 完整证据在本轮diagnostic_bundles/tick_ddb531fb及receipt9375。下一步仅监测原BTC训练与自然终态；无待用户确认事项。六段report/七段memory后原token真实finish并核FINALIZED/released和lock/pending消失，释放后不回写。
'''
    assert memory.count('\n## ')==7 and len(memory.splitlines())<120; save(ROOT/'pipeline/codex_memory.md',memory)
    notes={'actions':['核验actual owner/target、canonical前台规则/experiment-first及最新memory、goal/SERVERS/WindowsDisabled，前f34已释放后一次begin，原deadline不延长。','原PSNC进程已自然结束；只读双核精确原log/emptyGPU0，完整本远日志hash一致；canonical finalize_task done_earlystop31/.5001，原source43/receipt406/launchhistory与M206保护，独审29项。','复用既有BTC00e完整工具，fresh owner/assets/runtime43/UUID0/idle/三锁后stage；实际M95/BTC TRAIN2及原资源pair四请求terminal/rc0，全result身份与本地原raw只读reconcile，无重放/kill/续lease。','BTC实际两批/common843初始化配对；每forward64个n>=3父组、proper-inside原loss梯度及三map/FFN0,2更新、原HCG-inst路径；9.758338124G、参数-131584，median慢13.3134%/P90慢19.3694%，显存15%条件未触发，未知项保留。','原main43→已测00e仅9新增ff-only，28dirty/untracked字节和status及空index保持；3标准/receipt9375与canonical admission/budget通过，独审133+39项。唯一canonical派发安全sync后启动BTC，'+stamp+'上海原PID2784474/start47557208/argv/cwd/fd1/HEAD00e/UUID0，Train1/50 123→131/4686增长，最终独审留档。','8旧hold仅核元数据/655声明引用与13授权文件元数据，无新授权或科学复测；GPU1继续让出、M206保持暂停，原goal/协议/禁用项/调度不变。真实收尾report/finish并核释放。'], 'decisions':['PSNC本次best.5001低于M95.5020，仅归档此实现结果，不重启或整体否定hierarchy。','BTC仅技术准入并真实训练启动，效果仍UNKNOWN；推理延迟变慢如实保留。已有项目级授权覆盖本次常规操作，无新确认事项。','本轮1次真实准入/启动后可收尾，不为凑满额度或reserve计数造变体；后续监测原BTC及自然终态。']}
    save(HERE/'tick_notes.json',notes)
    assert {n:sha(ROOT/'pipeline'/n) for n in protected_names}==before
    save(HERE/'tick_persistence.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'actual_admissions':1,'verified_launches':1,'new_candidates':0,'new_commits':0,'native_progress':[a['train_progress'],b['train_progress']],'evidence':evidence+terminal_evidence,'protected_registries_unchanged_by_persistence':True,'notification':'NOTIFY','finish_not_yet_claimed':True})
    print(json.dumps({'recorded':True,'actual_admissions':1,'verified_launches':1,'memory_lines':len(memory.splitlines()),'notification':'NOTIFY'},ensure_ascii=False))
finally:
    lock.close()
