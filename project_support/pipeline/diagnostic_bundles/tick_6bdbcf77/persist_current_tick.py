"""Register actual CTS local checks and one source-only BEC reserve."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,hashlib,json,os,subprocess,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='6bdbcf775b4b4239933ce966f98664d2'
CTS='hierarchy-parent-cyclic-triadic-state-composition'
BEC='hierarchy-cross-level-bipartite-edge-composition'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
    tmp=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with tmp.open('x',encoding='utf8') as f:
        if isinstance(x,str):f.write(x)
        else:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def add(c,paths):
    for p in paths:
        item=ref(p)
        if item not in c.setdefault('evidence',[]):c['evidence'].append(item)
def main():
    owner=guard();prep_path=HERE/'new_candidate_prepare/preparation.json';prep=read(prep_path)
    bec_review_path=HERE/'bec_final_source_review.json';br=read(bec_review_path)
    assert br['material_concerns']==[]
    assert prep['candidate_id']==BEC and prep['experiment_id']=='M215-BEC'
    assert sha(prep_path)=='2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d'
    assert prep['code_commit'] is None and prep['source_commit'] is None and prep['future_version_parent'] is None
    assert any(x==ref(prep_path) for x in br['anchors'].values())
    for name,h in prep['prepared_file_hashes'].items():
        p=(prep_path.parent/name).resolve()
        assert p.is_relative_to(prep_path.parent.resolve()) and sha(p)==h
    tests_path=HERE/'new_candidate_prepare/static_validation_final.json';tests=read(tests_path)
    assert tests['assertions']==10643 and tests['production_plan_valid_cases']==133 and tests['production_forward_provenance_cases']==42 and tests['invalid_metadata_refusals']==14
    assert tests['native']==tests['resources']=='NOT_RUN'
    staged=HERE/'new_candidate_prepare/staged_repository'
    model=staged/'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bec'
    assert {p.name:sha(p) for p in model.glob('*.py')}==tests['source_sha256']
    config='configs/Quard/ctf_hcg_csort_bec/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bec.yaml'
    assert sha(staged/config)==tests['config_sha256']=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
    local_path=HERE/'cts_actual_local_guard_integration.json';local=read(local_path)
    assert sha(local_path)=='a9946e21a5a020fa868fd929e7254e40e51a09db711e3e31abd778e5a0a94ce1'
    assert local['actual_transport_calls']==0 and local['active_binding_manifest_lease_or_execution_directory_created'] is False
    assert local['native_execution']==local['resources']=='NOT_RUN'
    actual_review_path=HERE/'cts_static_anchor_and_busy_guard_review.json';ar=read(actual_review_path);assert ar['material_concerns']==[]
    observation_path=HERE/'active_runs_progress_observation.json';observation=read(observation_path)
    progress_review_path=HERE/'active_runs_progress_independent_review.json'
    assert read(progress_review_path)['material_concerns']==[] and all(x['native_TRAIN_growth'] for x in observation['summary'])
    snapshot=read(ROOT/'pipeline/headless/.tick_model_view.json')
    assert snapshot['research']['creation_budget']==snapshot['research']['reserve_budget']==1
    assert snapshot['experiment_first']['enabled'] is True and snapshot['queue']['ready_waiting_count']==0
    assert read(HERE/'cts_anchor_execute/cts_static_anchor_result.json')['active_binding_manifest_lease_created'] is False
    assert sha(HERE/'cts_operational_prepare/adapter_release.json')=='eaa3e84f0b07ccb4c5dc7cdd732995894d7c00d079562847611b57bdb118fa99'
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();before=read(HERE/'protected_assets_before.json')
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        work=read(ROOT/'pipeline/research_work.json');old=copy.deepcopy(work)
        assert not any(c.get('id')==BEC or c.get('experiment_id')=='M215-BEC' for c in work['candidates'])
        assert not (ROOT/'pipeline/admissions/M215-BEC.json').exists() and not (ROOT/'pipeline/experiments/M215-BEC.json').exists()
        cts=next(c for c in work['candidates'] if c['id']==CTS)
        assert cts['code_commit']=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d' and cts['stage']=='validation'
        assert cts['native_execution_code_commit'] is None
        cts['execution_adapter'].update(actual_current_local_guard=ref(local_path),actual_static_anchor=ref(HERE/'cts_anchor_execute/cts_static_anchor_result.json'),actual_anchor_guard_review=ref(actual_review_path))
        cts['implementation_status']='FROZEN_CTS4E8_REVIEWED_VERSION_BOUND_STATIC_CATALOG_AND_ACTUAL_LOCAL_BUSY_GUARDS_COMPLETE_NATIVE_NOT_RUN'
        cts['native_status']='NOT_RUN_BOTH_REGISTERED_CARDS_RUNNING_PROTECTED_NATIVE_TRAINING'
        cts.setdefault('resource_wait_history',[]).append(copy.deepcopy(cts.get('resource_wait',{})))
        cts['resource_wait']={'allowed_server':'server-4','allowed_physical_gpus':[0,1],
            'observed_tasks':{'0':{'id':'M213-BFC','pid':219369,'start_ticks':'56265957'},'1':{'id':'M212-BCR','pid':1215422,'start_ticks':'51717921'}},
            'observed_at':observation['observations'][-1]['observed_at'],'evidence':[ref(observation_path),ref(local_path)],
            'scope':'Live original TRAIN growth plus current registered-busy refusal; no GPU lease, native test or future idle grant. Keep validation reserve, not parked historical resource hold.'}
        cts_evidence=[local_path,actual_review_path,progress_review_path,observation_path,HERE/'cts_guard_helper_review.json',HERE/'cts_anchor_prepare/preparation.json',HERE/'cts_anchor_execute/execution_preparation.json',HERE/'cts_anchor_execute/cts_static_anchor_result.json']
        add(cts,cts_evidence)
        new={'id':BEC,'experiment_id':'M215-BEC','stage':'implementation','created_at':datetime.now(timezone.utc).isoformat(),
            'hypothesis':'Original fine/middle membership edges jointly transform child and parent before private true-child equal means. Split upward evidence and retained branches; original coarse FFN composes upward messages, then middle/fine nonlinear synthesis carries context downward before original HCG and the single inst_feats writeback. Whole-graph role separation may improve native mask features; efficacy unknown.',
            'matched_control':'M95 original native byte YAML, seed1999/epochs50/max_iters70/data/pretrain/optimizer/precision; actual common named initialization and two fixed TRAIN inputs must be measured, not inferred.',
            'mechanism_scope':'Bipartite message passing family whole-graph alternative, not attention/novelty/new coverage/single-factor causal claim or reopening M206/CCP/REAG/HRC.',
            'config':config,'code_commit':None,'source_commit':None,'native_execution_code_commit':None,'future_version_parent':None,
            'goal_sha256':'0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85',
            'authorization':snapshot['experiment_first']['authorization'],'resource_authorization':cts['resource_authorization'],
            'source_preparation':ref(prep_path),'staged_repository':staged.relative_to(ROOT).as_posix(),
            'source_status':'EIGHT_INDEPENDENT_MODEL_FILES_AND_ORIGINAL_YAML_FROZEN_PRIVATE_ONLY_NO_GIT_VERSION',
            'offline_checks':{'status':tests['status'],'assertions':tests['assertions'],'production_plan_valid_cases':133,'production_forward_provenance_cases':42,'invalid_metadata_refusals':14,'Torch_autograd_native_tested':False,'proof':ref(tests_path)},
            'source_inference_parameter_change':{'new_four_Linear':787968,'removed_fine_middle_FFN':1051136,'delta':-263168,'actual_dynamic_inventory':'NOT_RUN'},
            'source_inference_cost':'For supported fine and middle each joint up/down uses6C^2 versus original8C^2; original coarse FFN8C^2 unchanged. Original raw bank construction remains. Source inference excludes CPU metadata, private means, real latency/unsupported handlers; actual full resources NOT_RUN.',
            'implementation_status':'PRIVATE_SOURCE_STDLIB_PLAN_FORWARD_PROVENANCE_AND_MEAN_CHECKS_REVIEWED_NO_TORCH',
            'native_status':'NOT_RUN','native_smoke_status':'NOT_RUN','resource_status':'NOT_RUN','admission_status':'NOT_EVALUATED','efficacy':'UNKNOWN',
            'future_native_protocol':ref(HERE/'new_candidate_prepare/native_protocol.md'),
            'known_limits':['No true data loading, two-step original-loss backward, actual initialization/batch pairing, GELU/FP32 numerical or full FLOPs/latency/memory/accuracy measurement.',
                'Finite near-neighbor source checks distinguish this graph from CCP/REAG_CASC/HRC; they do not prove general novelty. No checkpoint/seed/sample/threshold tuning or M206 resume.',
                'Future source version must use then compatible actually tested main; never create sibling of pendingCTS and assume ff promotion or backfill a null frozen declaration.'],
            'next_action':'Preserve exact private eight model sources and byte-original YAML. Under then current tested main, save a compatible isolated source version and prepare exact native observer/worker; on a genuinely idle authorized server4 card, fresh owner/context/original deadline/UUID/assets/three locks then paired M95/BEC fixed TRAIN2 and original resources. Derive actual common parameter set rather than copying843; measure both U split branches, four new maps and original coarse transform original-loss gradients/updates, legal unsupported/pad zeros. No admission/queue before real passing gates.',
            'evidence':[]}
        add(new,[prep_path,tests_path,HERE/'new_candidate_prepare/static_check.py',HERE/'new_candidate_prepare/mechanism.md',HERE/'new_candidate_prepare/native_protocol.md',bec_review_path,HERE/'independent_review/bec_research_boundary.json'])
        work['candidates'].append(new)
        for eid in ['M213-BFC','M212-BCR']:
            c=next(c for c in work['candidates'] if c.get('experiment_id')==eid)
            add(c,[observation_path,progress_review_path])
            c['latest_runtime_observation']={'evidence':ref(observation_path),'independent_review':ref(progress_review_path),'shared_runtime_commit':'48fc302c3c02ffef0b241be3593c386b6b65a72e','admitted_source_unchanged':c['code_commit'],'scope':'Original PID/start/argv/log/native growth and exact model8/YAML/UUID; no operation on running jobs.'}
        work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CTS,'kind':'implementation_test','result':'passed',
            'command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_6bdbcf77/check_cts_actual_guard.py',
            'observation':'Actual CTS4e8 externally anchored adapter passed current owner/context/raw whitelist/version/deadline guards. Both registered occupied cards refused before transport;14 invalid selected entries and insufficient original deadline refused. Zero process/network/Torch/active artifacts. Native backward/resources remain NOT_RUN. Also one new BEC source-only reserve has real stdlib checks and independent source review.',
            'evidence':[ref(local_path),ref(actual_review_path),ref(HERE/'cts_guard_helper_review.json')]}
        work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']=cts['next_action']+' Then advance frozen source-only BEC without changing pendingCTS history.'
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        permitted={CTS,'hierarchy-parent-butterfly-token-composition','hierarchy-parent-bidirectional-complement-recurrence'}
        assert [x for x in work['candidates'] if x['id'] not in permitted|{BEC}]==[x for x in old['candidates'] if x['id'] not in permitted]
        save(ROOT/'pipeline/research_work.json',work)
        memory_path=ROOT/'pipeline/codex_memory.md'
        with (HERE/'codex_memory_before_finalization.md').open('xb') as f:f.write(memory_path.read_bytes())
        stamp=datetime.fromisoformat(observation['observations'][-1]['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
        memory=f'''# Codex Research Memory

## Goal And Phase
- 最新接管{TOKEN}；实际owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner['generated_at']}/原deadline{owner['deadline_at']}不延长。前336 FINALIZED/released且lock/pending消失后begin，本轮finish仅以真实receipt为准。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020/gap.0080，baseline.4894。Phase1不同层级分工→inst_feats→query/masks，supervision辅助，Phase2需人工确认。
- seed1999/epochs50/max_iters70/原YAML/data/pretrain/optimizer/precision不变；原同口径10G、bs1/lang1/warm20/repeat100 median/P90/fullunsupported，峰值显存+15%需≥+.003mIoU。禁止调参、gate/cag/cfe/layerscale、语言路由、大QKV/N²attention、重复inst注入、旧rejected改名、无图改变微调。
- standing pipeline/authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖普通实现/测试/相关版本/安全同步/准入训练，不授旧hold重开/额外修订/受保护恢复/扩大资源/改调度。
- 最新人类资源“server4 GPU1也可以用了”：pipeline/authorizations/server4_gpu1_20261025.json SHA90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8；SERVERS d5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2允许server4 physical[0,1]/每卡1，其他allowed[]。M206暂停保持；Pipeline-cluster_project Disabled。

## Champion And Baseline
- M95仍.5020；M205-MDC26/.4872、M207-HAP授权epoch18恢复后31/.5002、M208-HRC31/.4901、M209-PSBR23/.4969、M210-PSNC31/.5001、M211-BTC31/.4914均自然earlystop且未超M95。不调参重跑或整体否定hierarchy。
- BTC在前336已canonical archive_id73e3038e744b4f6a9bffb68a7b43e8f8，原source00e2b18c6b8d568a64edb496e6979d766440883c/receipt93756329…/launch保持；42038211B原log本远SHA2b4032d0b705ae7f5e8ebdba81f14d5ed7eb55da491b4b9fec2ba78342aba38c。当前snapshot new_terminal仅识别前轮归档，不是本轮新完成，未重复archive。
- HAP原epoch19 DataLoader AttributeError根因UNKNOWN，epoch18恢复授权已消费；原crash/snapshot/prior_runs保留。既有负结果/恢复/版本/归档细节见前336 memory及其证据，不重写或再启动。

## Active Hypotheses
- M213-BFC正式training，tested/admitted/primary/runtime48fc302c3c02ffef0b241be3593c386b6b65a72e/parent11a811618179ab1ddc0cee299194667413b7fdb9；receipt812454a819702e8f4d53080c1b479617d605f2175bf44a3422905688253ca01c。只替middle同父true-supported几何token，bit-up/down配对共享2C→2C/GELU同步双输出。fine/coarse/LN/cfskip/rawmeans/FPS/IDs/CSORT/HCG/单inst原件保持，非可逆/无损/新颖/收益结论。
- BFC前336实际4nativearms terminal/rc0；两原TRAIN loss9.5372838974/13.9084777832，共同843张量/156958522参数/hash04231c23…，原2batch配对；64n3多stage/56nonpower/四W quadrant原loss非零有限grad+每步slice更新。逐call/row/half零合法，singleton/empty/pad NOT_EXERCISED。实际审b8fa/43af/419f及4reconcile/status历史保持，不拿旧诊断lease再用。
- BFC真资源9.775377484G vsM959.762532428G，参数157221178（−262912）；同GPU0 median42.218151968 vs42.311575031ms（−.2208%），P9062.910521450 vs60.952819872ms（+3.2118%更慢），预测allocated−.1121%，observer-smoke+.00214%，15%条件未触发。fullunsupported保持，pureTRAIN峰值/新颖性/准确率未知。
- 前336仅已测BFC9A ff-only primary/safe runtime同步至48fc；首dispatch normalized UUID-map KeyError发生在0intent/transport，新受审raw-map执行copy才一次canonical Popen，实际result9e453fb4/最终审069833d3…；本轮不重放、不推进公共源或修改BCR8/YAML/原进程。保护28/index/账实际核保持。
- M212-BCR tested/admitted scientific source11a811618179ab1ddc0cee299194667413b7fdb9/receiptb8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac，公共runtime48fc仅BFC9 additions；原strict-exclusive双向scan/own-L-R/独立8源/映射YAML77e不变。前7526真TRAIN2/资源/准入/launch沿用，不代签CTS/BEC。
- M214-CTS validation，隔离source4e80006047d5cb3dcdfb9c1102e02c33f354a07d/唯一parent48fc，worktree pipeline/isolated_versions/cts_336ca5d7；前336源证明6b666a8c8e9d0f5bed8422fa02e6e2ea17192b1114c6eda5ecf28affb409c2d0/独审5f3eb45e…保持。原bfab八model+原YAML9A仍冻结原code/parent null，不回填。
- CTS同父几何cycle同步old own/±3^r，经共享3C→C/原GELU，最小3^k>=n轮；重复minus私有0，n1W[x,0,0]，无支持/pad delta0，nC状态保留。原LN/cfskip/finecoarse/rawmean/FPS/IDs/CSORT/HCG/单inst保持。dense3tap dilated circular Conv1D家族整体图替代，非新覆盖/单因素因果/新颖/重开MDC。
- 本轮新CTS版本绑定operational packet tick_6bdbcf77/cts_operational_prepare/preparation.json SHA51cbc658fcf5877a0b46776e361adb99d36d4551841aacdf7559ac6d46c937d6；nativeaab40a87/worker原03329/独审0fc1425f/61真mock+69ASThash+7真CLI拒绝。新copy绑定4e8与期望live48fc，原ff7 DRAFTTrue/code-parent-null及失败元数据保持；全部runtime函数AST/原资源口径不变，无原地启用旧包。
- root单flag CTSanchor新copy310ed9显式exact0fc审后，实际只静态release eaa3 bytecopy+CTS历史/外锚；actualguard a9946e21核当前owner/context/rawUUID/版本/原deadline，prepare0/1精确registeredbusy拒绝，14非法入口+deadline拒绝，0transport/process/network/Torch/active。原8source/YAML/primary28/index/13账保持；独审另附。该结果不是NVML idle/原生两步/资源PASS。
- CTS未来沿原7036协议，在fresh真实空卡绑定后做M95/CTS固定TRAIN2+原资源；须3distinct/multiround/r>=1与三W input块每step原loss有限非零grad+实际update。缺覆盖INCONCLUSIVE，不换样本/seed/precision/阈值；逐call合法零。native/resource/efficacy均未测，无M214receipt/queue/训练。
- 新唯一M215-BEC implementation，私有8model+原YAML字节冻结，code/source/futureparent均null，不造CTS旁支Git。双跨层joint child+parent→2C/GELU各split u/v，v按true child等权上行；原coarse LN/FFN组合后，两2C→C/GELU向middle/fine回传，原三cfskip/HCG/一次inst回写。rawmeans/FPS/IDs/CSORT与六原model文件逐字保持，coarse空/unsupported bias mask0。
- BEC当前真实stdlib生产AST plan133cases、forward provenance42cases、14拒绝/10643assertions；不是Torch/GELU数值/autograd/原数据/10G。有限CCP/REAG_CASC/HRC/lite_agg源近邻审及最终实现独审留档，不称一般新颖/attention/新覆盖/单因素收益，不恢复M206。
- BEC源码推断新4Linear787968、替代2FFN1051136、净−263168；fine/middle denseMAC各6C² vs8C²，coarse原8C²，linear metadata grouping；全口径FLOPs/CPU开销/时延/显存均未知。未来实际派生共同参数集合，不照抄843；核2U双split、4maps及原coarse loss路径grad/update，当前不入队。

## Closed Or Failed Directions
- 本轮旧9 parked不due，未再读655旧证据正文或旧grant正文、checkpoint body；不改旧scope、失败、修订上限或恢复状态。前336有界声明/授权目录无新动作证据8f5a970b…沿用，不能当新授权。
- 四supervision保持辅助；PCE默认2+额外1已尽/2.861e-6/13.86x，RSTR默认2已尽/R2mean1.027033878e-6>1e-6；禁PCE_R4/RSTR_R3/M201自动恢复。旧RSTR9文件localcommit授权不授额外修订，全部负证据保持。

## Running And Queue
- 采集{stamp}上海：BFC原PID219369/start56265957 GPU0 Train3/50 2980→2987/4686；BCR原PID1215422/start51717921 GPU1 Train17/50 1929→1933/4686。两真native增长/唯一argv/cwd/fd1/8源/YAML77e/UUID核实，proof88fe3025…/独审ec8e73bd…。本轮preflight best .3793/.4955仅运行中指标，不是新终态。
- 当前2running/0ready，2准备储备CTS+源级BEC；M206-CGCA waiting但paused/dispatch_hold/resume_authorizedfalse/noPID，不计ready、不恢复迁卡；历史meta24/best.4952535927295685/noimprove7与checkpointSHAe9b42b26…保持，未读body。
- pinned songcl@192.168.1.115 / dl04-MS-7E06，GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c、GPU1 GPU-7f82edb9-f620-8045-caea-a75232265cd1；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster/runtime server4_conda_4ca73fba.sh，data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints。keys/strict hostkey/先hostname，不用旧IP/密码/sudo；python -B/PYTHONDONTWRITEBYTECODE=1。
- 任何新GPU计算均需fresh实际owner/deadline/资源UUID/idle/assets/三锁；旧lease/context空不是未来许可。原训练未知claim/request/PID只读reconcile，不盲重启/kill/删锁。BFC启动三flock未覆盖整个训练，未知如实保持。

## Open Questions And Risks
- 目标差距.0080不变；BFC/BCR最终收益未知。BEC/CTS仅准备与软件正确性，尚无两步native backward、同输入/common配对、原口径资源或准确率，新颖性未证。
- BFC P90+3.2118%/BCR原GPU1 median+2.55%、P90+9%更慢，不夸称全面效率或跨GPU因果；预测/含observer smoke不等于pureTRAIN峰值。fullbuffers/RNG/FP32/offdiagonal与未行使零边界尚未测。
- CTS新catalog可复用但当前无activebinding；只在原版本/原协议/fresh空卡检验。BEC还需兼容当时实际tested main源版本与native observer，不从旧null推断已测或造旁支假定可ff。

## Last Tick
- 本轮6bdb snapshot2running(BFC/BCR)/0ready、admission_budget2/creation1/reserve1，due仅CTS、旧9不due。先有界双样本观察确认两原训练增长，未再次preflight/monitor或等训练终态。
- 实际完成CTS受审4e8版本静态操作包外锚与当前owner/两registeredbusy无transport检查；新唯一BEC8model+原YAML/生产stdlib实际检查/独审，均不冒充原生资源PASS。
- 1新候选/0准入/0queue/0启动/0新训练终态，旧BTC为前轮归档识别；公共源48fc/index空/历史28status+bytes及运行账保护，M206暂停/旧holds保持。snapshot预算内形成CTS+BEC两项准备，卡忙后续原生需自然空槽。
- root保护快照首版因Git折叠untracked目录拒绝，另有一次inlinePowerShell quoting失败；原失败源码/记录保留，新v2 expanded28与历史bytes精确核，非模型修订/科学失败或共享写。
- 完整本轮证据tick_6bdbcf77；七段memory/notes/真实implementation tick_attempt后canonical六段report与finish，核FINALIZED/released和lock/pending消失；未发生前不预签，释放后不回写。需处理：无新增用户授权项。
'''
        assert len(memory.splitlines())<120 and memory.count('\n## ')==7
        save(memory_path,memory)
        notes={'actions':[
            '本轮actual owner与target一致，snapshot仅CTS due/creation1。两原BFC0/BCR1 native步数3:2980→2987、17:1929→1933，原PID/start/argv/log/8source/YAML77e/UUID与公共48fc/科学BCR11a分开核实并独审；无新终态，snapshot BTC是前336已归档识别。',
            'CTS4e8/parent和期望live48fc新版本绑定包完成61真实mock、69ASThash编译检查及7实际CLI前置拒绝，原worker03329/资源AST/8model/YAML字节保持；原ff7 disabled/null元数据不改。独审0fc142无阻断。',
            '独审后root新oneflag执行副本只落静态release eaa3 bytecopy与CTS历史/外锚。当前actualguard通过owner/context/rawUUID/version/originaldeadline；prepare0/1因实际registered running拒绝，14非法入口与deadline拒绝，0transport/process/network/Torch/active。此为本地软件测试，不是native/idle/资源PASS。',
            '新增唯一M215-BEC私有独立8源+原字节YAML：fine joint边消息分上行/保留两支，中层再次组合，上行均值经原coarse FFN后逐层回传，原三cfskip/HCG/一次inst回写保持。code/futureparent null，无Git/部署/训练。',
            'BEC真实stdlib生产plan133、forward provenance42、invalid14/10643assertions及独立生产源审通过；rawmean/FPS/IDs/CSORT原件保持，coarse unsupported bias mask0。新四Linear与替代fine/middle FFN的source参数净−263168；仅源推断，不填10G或收益PASS。',
            'M206暂停/旧9 parked不due保持，未复查655正文/旧grant/checkpoint body。主HEAD48fc/index空/历史28status+bytes与10运行归档账核保护；未改资源/禁项/seed/data/schedule/原YAML/调度。根快照首版目录折叠与inline quoting失败保留，v2真实核修正，非模型revision。'],
            'decisions':[
            '优先把已有CTS推进到受审可复用静态操作包；两实际运行占卡，仅做本地检查，不抢占训练。真实原生两步/资源仍待自然空槽及fresh身份/UUID/idle/assets/三锁。',
            '按snapshot creation1准备单个跨层角色分工BEC，有限源近邻核区别CCP/REAG/HRC，归属于bipartite messagepassing家族；不声称attention、新颖、覆盖新增或单因素收益。原native控制/common实测及效能缺口如实保留。',
            '本轮1新source-only候选/0准入/0启动，无新用户确认项。CTS+BEC两储备不计ready；M95.5020距.5100仍.0080，继续观察原BFC/BCR，不改旧holds或自动恢复M206。']}
        save(HERE/'report_notes.json',notes)
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        out={'token':TOKEN,'new_candidates':1,'new_admissions':0,'new_launches':0,'new_terminal_experiments':0,
            'CTS_local_check':ref(local_path),'BEC_preparation':ref(prep_path),'BEC_review':ref(bec_review_path),'memory_lines':len(memory.splitlines()),'postflight':'NOT_YET_CALLED'}
        save(HERE/'final_tick_persisted.json',out)
        print(json.dumps(out,ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
