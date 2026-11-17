"""Persist one static-tested BCR reserve and unchanged protected BTC training."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
PACKET=HERE/'bcr_operational_prepare'; TOKEN='41eb62fa1d32436f859264a19b0d4049'
CID='hierarchy-parent-bidirectional-complement-recurrence'; COMMIT='11a811618179ab1ddc0cee299194667413b7fdb9'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
    q=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with q.open('x',encoding='utf-8') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(q,p)
owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
assert sha(ROOT/'pipeline/goal.json')=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85' and sha(ROOT/'SERVERS.yaml')=='9a8f9a03a1c72ba07cc428944424ae62dce7cb6c9678c17bfb90fef8c20593ba'
assert sha(PACKET/'preparation.json')=='12dcdebecb7ddf7411ab33cf945e39d1cde52aae0c3b6593e0111130f63cfd55'
assert sha(PACKET/'native/preparation.json')=='a7ba73ba7610fa3e0dbac6f4a496f1657e8cf09f725d2b88f24df1d97ecff604'
assert sha(PACKET/'adapter_release.json')==sha(PACKET/'release_template.json')=='4a66f6fbbedecaac56e7ef2ac3a3ed58e4c56a749d0f7d7b1f2e956577cf7d0b'
guard=read(HERE/'bcr_actual_local_guard_integration.json')
assert guard['actual_transport_calls']==0 and guard['subprocess_or_network_audit_events']==[] and not guard['torch_imported'] and not guard['active_binding_manifest_lease_or_execution_directory_created']
assert guard['refusals']['registered_GPU0_busy']=='Selected GPU has registered running task'
for n in ['bcr_integration_review.json','bcr_topology_review.json','bcr_isolated_version_review.json','bcr_operational_final_review.json']:
    assert read(HERE/n)['material_concerns']==[]
obs=read(HERE/'btc_progress_observation_later.json');a,b=[x['data'] for x in obs['observations']]
assert obs['same_exact_registered_process_and_native_TRAIN_growth'] and a['pid']==b['pid']==2784474 and a['start_ticks']==b['start_ticks']=='47557208' and not a['errors'] and not b['errors']
assert a['train_progress']==[4,50,1277,4686] and b['train_progress']==[4,50,1284,4686]
stamp=datetime.fromisoformat(obs['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
assert not (HERE/'bcr_execution').exists() and not (ROOT/'pipeline/admissions/M212-BCR.json').exists() and not (ROOT/'pipeline/experiments/M212-BCR.json').exists()
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
lock=monitor.acquire_lock(str(ROOT));assert lock is not None
try:
    names=['queue.json','running.json','experiments/M211-BTC.json','experiments/M210-PSNC.json','experiments/M206-CGCA.json','admissions/M211-BTC.json','admissions/M210-PSNC.json']
    protected={n:sha(ROOT/'pipeline'/n) for n in names}
    queue=monitor.load_queue(str(ROOT));live=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M211-BTC');assert live['status']=='running' and live['pid']==2784474 and live['launch_verified'] and str(live['gpu'])=='0'
    assert not any(t['id']=='M212-BCR' for ts in queue['gpu_queues'].values() for t in ts)
    m206=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA');assert m206['dispatch_hold'] and m206['resume_authorized'] is False
    assert monitor.load_running(str(ROOT))['server-4']=={'0':'M211-BTC'}
    work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
    assert c['stage']=='blocked' and c['resume_stage']=='validation' and c['code_commit']==COMMIT and c['native_execution_code_commit'] is None and c['operational_preparation_status']=='COMPLETE_STATIC_GUARDED_PACKET_NATIVE_NOT_RUN'
    evidence=[ref(HERE/n) for n in ['bcr_source_registration.json','bcr_static_anchor_result.json','bcr_actual_local_guard_integration.json','bcr_operational_final_review.json','btc_progress_observation_later.json']]+[ref(PACKET/n) for n in ['preparation.json','native/preparation.json','adapter_release.json','native_promotion.json','offline_tests/full_offline_run1.json']]
    for item in evidence:
        if item not in c['evidence']:c['evidence'].append(item)
    btc=next(x for x in work['candidates'] if x.get('experiment_id')=='M211-BTC');assert btc['stage']=='training'
    if ref(HERE/'btc_progress_observation_later.json') not in btc['evidence']:btc['evidence'].append(ref(HERE/'btc_progress_observation_later.json'))
    c['last_resource_check_at']=obs['recorded_at'];c['retry_after']=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    c['blocker']='Only authorized GPU0 runs exact BTC2784474/start47557208, observed native4/50 1277->1284 at '+obs['recorded_at']+'. BCR11a reviewed complete static operational tools are prepared; real native/resource checks NOT_RUN. Current local prepare refused registered busy slot before transport/dir/lease. GPU1 released and M206 paused.'
    c['next_action']='Reuse exact BCR11a source/native YAML and the reviewed frozen operational packet/static catalog. After original BTC naturally finishes and fresh actual GPU0 UUID/occupation/idle/three-lock/owner/context/deadline/assets checks pass, stage a new binding and run matched M95/BCR original TRAIN2 and resources. Require real n>=3/depth>=2/nonzero state, original-loss nonzero finite Ws token/state and Wf own/left/right block gradients and actual updates; coverage absence is inconclusive without resampling. Only real passing checks may produce summaries/receipt/queue and canonical dispatch. Current public runtime00e and candidate11a remain distinct; no GPU1, M206 resume, old lease/request replay, tuning or protocol change.'
    c['known_limits'].append('Complete static catalog/49 mocks/current local busy refusal do not prove real assets, GPU idleness, native numerical gradients, resource compliance, initialized parameter/batch pairing, full FP32 controls or accuracy. No active execution material was created.')
    work['tick_attempt']['observation']='One actual new BCR strict-exclusive graph fork statically implemented/tested and saved as isolated11a. Original production source/plan checks1334 assertions/62labels/22cases plus independent24 stdlib calls; complete guarded packet49 offline mock/source cases passed (not training experiments), independent source/version/packet reviews completed. Real current local owner/context/external-anchor guard passed and busyGPU0/GPU1/deadline refusal occurred before transport or active material. Original BTC4/50 1277->1284 healthy. BCR native/autograd/resources/efficacy NOT_RUN/UNKNOWN; no admission/queue/launch.'
    for item in evidence:
        if item not in work['tick_attempt']['evidence']:work['tick_attempt']['evidence'].append(item)
    work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']='Monitor only original BTC2784474/GPU0 and reuse the complete reviewed BCR11a preparation after actual authorized idleGPU0; no GPU1/M206/goal/protocol/resource/scheduler changes.'
    save(ROOT/'pipeline/research_work.json',work)
    memory=(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('\n## Last Tick\n',1)[0].replace('本轮','前ddb轮').replace('当前诊断lease','旧诊断lease').rstrip()
    lines=memory.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('- 最新接管'):
            lines[i]='- 最新接管'+TOKEN+'；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致；generated'+owner['generated_at']+'/原deadline'+owner['deadline_at']+'不延长。前ddb已FINALIZED/released且lock/pending消失才begin；本轮真实finish结果见receipt，不预签。'
        elif line.startswith('- 当前唯一M211-BTC'):
            lines[i]='- 当前唯一M211-BTC server4 GPU0/PID2784474/start47557208；'+stamp+'上海原argv/cwd/fd1唯一log/HEAD00e/UUID0双核，native4/50 1277→1284/4686增长且无error，GPU0为原进程context。proof pipeline/diagnostic_bundles/tick_41eb62fa/btc_progress_observation_later.json SHA76e8501767f48aa31d075482329bf70331f0f6cc36d03c5241a1b61f99ee90e5；GPU1未查询/使用。'
    memory='\n'.join(lines)
    addition='''
- 新准备M212-BCR stable hierarchy-parent-bidirectional-complement-recurrence，source11a811618179ab1ddc0cee299194667413b7fdb9单父00e；仅middleFFN换strict-exclusive双向共享scan与own/L/R线性读出，原LN/cfskip/fine-coarse/raw-CSORT/HCG/单inst保留。L/R不含own且union=同父其他真支持节点，按原detached xyz+ID顺序；Ws恰2(n−1)，Wf每父1模块调用/n行，n1无scan。源推断328192替525568(−197376)，实际inventory/FLOPs/延迟/显存/效果NOT_RUN或UNKNOWN。
- BCR仅为PSBR/BTC近邻新信息流因子化，不宣称独立新颖/新覆盖范围/PSBR单因素因果；原inclusive PSBR停支/负结果保持，不resume或调激活/skip重试。研究边界657c40dd…、源集成3442e846…明确此窄scope与未知项。
- BCR原prep tick_41eb62fa/new_candidate_prepare/preparation.json SHA faf3494d13c5026b21e1d235dab311cc4f9a9d88b9653c4726a5ccbdc8958615，原code_commitnull不改；17map/8独立源+1原YAML/原协议。真实1334断言62labels/22生产plan案例，独立24次stdlib调用(14有效+10非法)均通过，不是1334/24个训练实验。原9blob已isolated_versions/bcr_41eb62fa普通detached commit11a，primary/runtime00e/index/28bytes及既有账本保存前后不变，版本独审05fe725f…18项。
- BCR原disabled native包 bcr_native_prepare/prep d775d9bb…、worker a3b10169…/runtime df5c13b8…、12项本地检查含2真实stdlib拒绝子进程、7包检查均保留。新operational/native仅runtime DRAFT True→False一处受限materialization，runtime f60030ee…/nativeprep a7ba73ba…/template9be089d9…；全真实owner/manifest/lease/ctx/deadline/assets/三锁/GPU0守卫不改，原disabled拒绝不代签新执行。
- BCR完整工具 tick_41eb62fa/bcr_operational_prepare：outer12dcdebecb7ddf7411ab33cf945e39d1cde52aae0c3b6593e0111130f63cfd55(28map)/inner a7ba73ba…(14map)/12diagnostic；adapter85eecbe1…/remote805afced…；49离线mocks/源码检查实际PASS(原46+3，首11子集不重复计)，该suite审计0process/network/torch。最终独审22205318…42项仅静态，不是native PASS。
- Root已物化同字节static release4a66f6fb…并外锚worker/outer/native/release。实际当前root owner/context/外锚guard通过；NoTransport prepare因registered BTC忙在probe/目录/lease前拒绝，GPU1/超原deadline也拒绝；0transport/torch/GPU或activebinding，见bcr_actual_local_guard_integration.json。不是实际idle/assets/原生证据，未来必须fresh绑定。
- BCR stageblocked/exclusive_gpu_slot/resumevalidation，native_execution_commitnull、无receipt/queue/experiment；工具准备已完整，等待保护中的BTC自然释放GPU0。真实原TRAIN2要n>=3/depth>=2/nonzero state，Ws token/state两块与Wf own/L/R三块分别原loss非零有限梯度及实际更新，防weightdecay假覆盖；缺覆盖INCONCLUSIVE，不换样本/seed/order/dtype/阈值。资源原bs1/lang1/warm20/repeat100/fvcore全unsupported保持，native_protocol.md(3dfc2cee…)待真执行。
'''
    memory=memory.replace('## Active Hypotheses\n','## Active Hypotheses\n'+addition,1)
    memory=memory.replace('## Running And Queue\n','## Running And Queue\n- M212-BCR仅完整静态准备/blocked等待原生GPU检查，未入训练队列。所有旧hold本轮0due，未重读655正文/授权正文、未重hash/重开。\n',1)
    memory=memory.replace('## Open Questions And Risks\n','## Open Questions And Risks\n- BCR存在own/context联合非线性变弱、长链衰减/爆炸及方向/重复坐标ID敏感性；不宣称旋转或tie-ID不变。与PSBR激活/skip/readout亦有差异，M95对照只检验整体候选。实际torch/边界/配对/分块梯度/资源/效能均未知。\n',1)
    memory+='\n\n## Last Tick\n'
    memory+='- begin一次monitor/goal/已有派发，design预算2/reserve2/creation2；1running/0ready/0due/9heldnotdue，preflight M210终态仅上轮已通知的cached变化，不重复报新完成。BTC原进程3/50 3469→3476，后续'+stamp+'上海4/50 1277→1284，均健康。\n'
    memory+='- 本轮新增且仅新增M212-BCR一个严格exclusive结构准备，1新isolated source commit11a/0准入/0新queue/0launch，当前BTC不中断。原YAML/seed/schedule/data/bans/goal/SERVERS/调度/GPU边界不变；28保护证据见实际版本保存前后及独审。\n'
    memory+='- 完成源/plan实际检查、源/版本独审、专属native observer/runtime和守卫完整工具准备/49mocks与整包独审；实际current-local guard+registered忙卡/GPU1/deadline早拒绝，不执行远端或GPU。修正root自写anchor next_action遗留tree字样为真实Ws/Wf分块协议，源/阈值/guard均不改。\n'
    memory+='- tick_attempt实际implementation_test passed仅代码/stdlib/mocks，不是native或资源PASS；BCR数值/资源/训练效果仍未知。下一步复用已冻完整包，在BTC自然释放后的真正空GPU0 freshguard→原YAML TRAIN2/资源→真实通过才准入派发；GPU1继续让出，M206保持人工暂停。\n'
    memory+='- 七段memory/六段report后原token真实finish及FINALIZED/released、ownedlock/pending消失核验，释放后不回写。本轮新准备属实质变化，NOTIFY；无待用户确认事项，不为了budget2再造同族变体。\n'
    assert memory.count('\n## ')==7 and len(memory.splitlines())<120;save(ROOT/'pipeline/codex_memory.md',memory)
    notes={'actions':['核验actual owner/target、canonical前台技能/experiment-first、最新memory/goal/SERVERS/WindowsDisabled，前ddb已FINALIZED/released且无lock/pending后一次begin，原deadline不延长。','只读双核原BTC2784474/start47557208/原argv-cwd-fd1-log/HEAD00e/UUID0：先3/50 3469→3476，后'+stamp+'上海4/50 1277→1284/4686，均无error。GPU1不查不用；M210为上轮已归档变化，不重复报告为本轮新完成。','新增一个M212-BCR strict-exclusive结构fork，明确PSBR/BTC近邻及停支/新颖性/因果限制；8独立源+1原YAML冻结，真实生产source/plan检查1334断言62标签/22case、独立24次stdlib调用通过，未torch/native。','在独立detached worktree普通保存11a单父00e，仅9frozen新增blob精确；primary/liveBTC00e、原28dirty字节/status/index与队列运行收据账本保持，源/版本独审无concern。','制作BCR专属原TRAIN observer以观测Ws token/state和Wf own/L/R原loss分块梯度/更新；原resources整函数/实际guards保留。保存原disabled/refusal包，新副本仅受限单开关materialization与哈希重算；49离线mock/source cases实际通过，整包独审42项，均不代签native/GPU/资源表现。','Root materialize同字节static catalog及外锚后，实际current-local owner/context/外锚guard通过；NoTransport prepare因登记BTC忙在probe/目录/lease前拒绝，GPU1/deadline也拒绝，0transport/torch/GPU/activebinding。BCR完整准备blocked等待原生，0receipt/queue/launch。','0due旧holds不重读655正文/授权或重开；保持GPU1让出/M206暂停以及原goal/协议/禁用项/资源/调度。七段memory、六段报告与真实finish/释放核验收尾。'], 'decisions':['BCR为有界的新计算图因子化实验，不是inclusive PSBR换名/重试，不声称独立新颖或单因素因果。','静态/stdlib/mocks通过只说明准备可复用；原生n>=3及五分块原loss梯度/更新、配对/真实资源/准确率仍未测，GPU0忙时不入队或共享计算。','仅准备一个具体候选，不凑满额度或无限造路线；已有standing授权覆盖本次本地保存与工具准备，无新用户确认。']}
    save(HERE/'tick_notes.json',notes)
    assert {n:sha(ROOT/'pipeline'/n) for n in names}==protected
    save(HERE/'tick_persistence.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'new_candidates':1,'new_isolated_commits':1,'admissions':0,'new_queue':0,'launches':0,'native':'NOT_RUN','resources':'NOT_RUN','protected_registries_unchanged':True,'latest_actual_native_progress':[a['train_progress'],b['train_progress']],'evidence':evidence,'notification':'NOTIFY','finish_not_yet_claimed':True})
    print(json.dumps({'persisted':True,'new_candidates':1,'native':'NOT_RUN','admissions':0,'memory_lines':len(memory.splitlines()),'notification':'NOTIFY'},ensure_ascii=False))
finally:lock.close()
