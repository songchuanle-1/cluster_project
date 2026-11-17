"""Owned-tick metadata reconciliation after the reviewed R1 static guard.

No transport, queue dispatch, source promotion, or training operation.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, subprocess, sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
TOKEN = 'e2e3d058a5274d2db709c77a328b363f'
CTS = 'hierarchy-parent-cyclic-triadic-state-composition'
BEC = 'hierarchy-cross-level-bipartite-edge-composition'
CODE = '4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')

def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p): return {'path': Path(p).relative_to(ROOT).as_posix(), 'sha256': sha(p)}
def encoded(x): return (json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf8')
def save_new(p, x):
    with Path(p).open('xb') as f: f.write(encoded(x)); f.flush(); os.fsync(f.fileno())
def replace_bytes(p, content):
    temp = p.with_name(p.name+'.'+TOKEN+'.reconcile.tmp')
    with temp.open('xb') as f: f.write(content); f.flush(); os.fsync(f.fileno())
    os.replace(temp, p)

def main():
    guard()
    sys.path.insert(0, str(SKILL)); import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT)); assert lock is not None
    try:
        guard()
        assert not (HERE/'final_reconciliation_intent.json').exists(), 'Reconcile any previous partial operation; never replay'
        before = snapshot()
        original = read(HERE/'protected_assets_before.json')
        assert all(before[k] == original[k] for k in ['head','index_empty','status_hex','files','protected_ledgers'])
        assert (HERE/'protected_assets_after.json').exists(), 'Complete twelve-ledger audit before the single-field reconciliation'
        anchor = read(HERE/'bec_r1_static_anchor_result.json')
        local = read(HERE/'bec_r1_actual_local_guard.json')
        assert anchor['owner']['token'] == TOKEN and anchor['R1_revision_result'] == 'pending'
        assert local['owner']['token'] == TOKEN and local['transport_calls'] == 0 and local['native'] == local['resources'] == 'NOT_RUN'
        assert local['outcomes']['0']['refused'] and local['outcomes']['1']['refused']
        observation_path = HERE/'cts_native_progress_observation.json'
        observation = read(observation_path)
        assert observation['owner_token'] == TOKEN and observation['native_TRAIN_growth'] is True
        samples = observation['observations']; first, last = samples[0], samples[-1]
        assert (last['pid'], last['start_ticks'], last['runtime_HEAD']) == (3505065, '61122472', CODE)
        assert first['train_progress'] == [5,50,1688,4686] and last['train_progress'] == [5,50,1697,4686]
        peer = read(HERE/'cts_native_progress_independent_review.json')
        assert peer['material_concerns'] == []
        ep = ROOT/'pipeline/experiments/M214-CTS.json'; exp = read(ep)
        assert (exp['status'], exp['training_status'], exp['pid'], exp['launch_verified'], exp['code_commit']) == ('running','waiting',3505065,True,CODE)
        new_exp = copy.deepcopy(exp); new_exp['training_status'] = 'running'
        assert {k for k in set(exp)|set(new_exp) if exp.get(k) != new_exp.get(k)} == {'training_status'}
        wp = ROOT/'pipeline/research_work.json'; work = read(wp); updated = copy.deepcopy(work)
        target = next(c for c in updated['candidates'] if c['id'] == CTS)
        bec = next(c for c in updated['candidates'] if c['id'] == BEC)
        assert bec['code_commit'] == '026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563' and len(bec['revision_history']) == 1
        assert bec['revision_history'][0]['result'] == 'pending' and bec['native_execution_code_commit'] is None
        now = datetime.now(timezone.utc).isoformat()
        changed_keys = ['stage','training_status','admission_status','resource_authorization','resource_wait','next_action','known_limits','matched_control','preparation_complete_source_only','operational_preparation_status']
        target.setdefault('training_catalog_history', []).append({'recorded_at':now,'reason':'Reconcile earlier waiting/source-only catalogue with canonical launch and actual native progress; all historical evidence remains unchanged.','previous_fields':{k:copy.deepcopy(target.get(k)) for k in changed_keys}})
        resource = {'path':'pipeline/authorizations/server4_gpu0_only_20261026.json','sha256':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'}
        target.update(stage='training', training_status='running', admission_status='ADMITTED_TRAINING_PROGRESS_VERIFIED', resource_authorization=resource,
            preparation_complete_source_only=False, operational_preparation_status='NATIVE_GATES_PASSED_ORIGINAL_TRAINING_PROGRESS_VERIFIED',
            matched_control='Original M95 native YAML/pretrain/seed1999/epochs50/max_iters70/data/optimizer. Actual matched TRAIN2/common initialization and original resource arms reviewed in tick45eb/a33c; no trained efficacy result yet.',
            next_action='Preserve original M214-CTS PID3505065 on server4 physicalGPU0. Observe native training and validation until canonical terminal handling; no restart, source promotion, GPU1, eviction, or replay of the earlier e245 no-launch helper.')
        target['resource_wait'] = {'server':'server-4','physical_gpu':0,'state':'OWN_ORIGINAL_TRAINING_RUNNING','evidence':ref(observation_path),'observed_at':last['observed_at'],'note':'Historical foreign-PID waiting evidence retained in training_catalog_history. This observation is bounded, not continuous exclusivity.'}
        target['known_limits'] = [
            'Actual original TRAIN2 backward and original paired resource gates passed on source4e8; these do not establish accuracy, novelty, or single-factor causality.',
            'Current original training progress was observed at 08:11:34-08:11:38 UTC, epoch5/50 step1688 to1697/4686. Current best validation metric was not extracted by this observer.',
            'Full-buffer/RNG equality, offdiagonal effects and unexercised singleton/empty/pad boundaries remain unknown; predicted and observer-smoke allocated memory are not pure TRAIN peak memory.',
            'All historical source-only checks, older resource authorizations and no-launch observations remain historical evidence. Only current GPU0 authorization governs future computation.'
        ]
        progress = {'observed_at':last['observed_at'],'pid':3505065,'start_ticks':'61122472','server':'server-4','physical_gpu':0,'train_progress_first':first['train_progress'],'train_progress_last':last['train_progress'],'evidence':ref(observation_path),'independent_review':ref(HERE/'cts_native_progress_independent_review.json'),'scope':'Original training confirmed by increasing native steps; no new launch by this observer.'}
        target['training_progress_observation'] = progress
        for r in [ref(observation_path),ref(HERE/'cts_native_progress_independent_review.json')]:
            if r not in target['evidence']: target['evidence'].append(r)
        for r in [ref(HERE/'bec_r1_static_anchor_result.json'),ref(HERE/'bec_r1_actual_local_guard.json')]:
            if r not in bec['evidence']: bec['evidence'].append(r)
        bec['execution_adapter']['actual_current_local_guard'] = ref(HERE/'bec_r1_actual_local_guard.json')
        bec['current_resource_check'] = {'result':'blocked','evidence':ref(HERE/'bec_r1_actual_local_guard.json'),'reason':'Sole permitted GPU0 has registered original CTS training, independently observed in this tick. GPU1 unauthorized. NoTransport check is software metadata validation, not hardware or native resource PASS.'}
        if work.get('tick_attempt'):
            updated.setdefault('tick_attempt_history', []).append(copy.deepcopy(work['tick_attempt']))
        owner = guard()
        updated['tick_attempt'] = {'tick_started_at':owner['generated_at'],'candidate_id':BEC,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_e2e3d058/bec_r1_anchor_execute/check_bec_r1_current_guard.py --execute-root','observation':'Actual reviewed R1 adapter/current-owner/source guard reached GPU0 registered-CTS-busy refusal; GPU1 refused current explicit GPU0-only authorization. Zero transport/process/network/Torch/active binding. R1 native TRAIN/resources remain NOT_RUN; separate fresh current-tick native CTS progress evidence confirms original GPU0 training.','evidence':[ref(HERE/'bec_r1_actual_local_guard.json')]}
        updated['updated_at'] = now
        updated['next_action'] = 'Continue original CTS on sole server4 GPU0. BEC R1 tools and exact026c source are reviewed and statically bound; after original training releases GPU0, fresh actual idle/UUID/assets/three-lock checks must precede all original M95/R1 TRAIN2 and resource arms. M206 stays paused; no GPU1, old route reopening or BFC restart.'
        unrelated = lambda w: {c['id']:c for c in w['candidates'] if c['id'] not in (CTS,BEC)}
        assert len(updated['candidates']) == 141 and unrelated(updated) == unrelated(work)
        assert bec['revision_history'] == next(c for c in work['candidates'] if c['id']==BEC)['revision_history']
        memory = '''# Codex Research Memory

## Goal And Phase
- 本轮e2e3d058a5274d2db709c77a328b363f；实际会话/target均01a159c5-29ab-7a22-ba7f-e79174757253。generated2026-10-26T08:09:05.798203+00:00，原deadline09:09:05.798203+00:00不变。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020，baseline.4894，gap.0080。Phase1层级分工→inst_feats→query/masks，监督辅助；Phase2需人工确认。
- seed1999/epochs50/max_iters70/原YAML/data/pretrain/optimizer/precision不变。原10G/原fvcore handlers/fullunsupported、bs1/lang1/warm20/repeat100 median/P90；峰值显存+15%需≥+.003mIoU。禁调参、gate/cag/cfe/layerscale、语言路由、大QKV/N²attention、重复inst注入、旧rejected改名与无图改变微调。
- standing authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖普通实现/测试/相关版本/安全同步/准入训练；不授旧hold重开/额外修订/受保护恢复/扩大资源/改调度。
- 最新人类“不用gpu1”已应用：SERVERS SHA2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1，仅server4 physical[0]/max1；授权server4_gpu0_only_20261026.json SHA94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09。旧GPU1实测保留历史合法依据，未来不再使用GPU1；其他allowed[]、调度Disabled保持。

## Champion And Baseline
- M95仍.5020；M205-MDC26/.4872、M207-HAP31/.5002、M208-HRC31/.4901、M209-PSBR23/.4969、M210-PSNC31/.5001、M211-BTC31/.4914、M212-BCR27/.4995均自然早停且未超M95。不调参重跑或整体否定层级方向。
- HAP原epoch19 DataLoader异常根因UNKNOWN，epoch18授权恢复已消费；BTC/BCR原终态与归档证据保留，不重启。既有版本/归档详见原证据，不以记忆覆盖原账。

## Active Hypotheses
- M214-CTS已真实训练；source/primary/runtime4e80006047d5cb3dcdfb9c1102e02c33f354a07d（父48fc），原8源/YAML/receipt5416d5e…保持。入队是e245，实际启动是中断前facc的canonical begin，本轮不冒称新增启动。
- CTS为同父几何cycle上的共享dense3tap dilated circular Conv1D家族：每轮old own/±3^r→共享3C→C/GELU，最小3^k≥n；保留原LN/cfskip/finecoarse/rawmean/FPS/IDs/CSORT/HCG与单inst注入。不是新覆盖/新颖或单因素收益证明。
- 原45eb真实M95/CTS固定TRAIN2+原资源四臂/a33c0fe7…与独审5d2f0716…通过：两loss9.547047615/13.908418655、原共同843张量/156958522参数、三distinct/多轮64/60与三W列原loss非零有限grad+每step更新。原owner/原GPU0证据不重标，不重测。
- CTS原资源9.761811532G vsM959.762532428G，params157155386 vs157484090；同GPU0 median35.8969 vs38.2312ms，P9037.4890 vs42.4553ms；+15%条件未触发。准确率/新颖性/pureTRAIN峰值未知。
- 本轮只读observed2026-10-26T08:11:34.910062至08:11:38.264124Z，原PID3505065/start61122472，TRAIN5/50 step1688→1697/4686；8源/YAML77e/argv/cwd/fd1/UUID0核实。证据7753f123…/独审b7a99c4e…；不声称持续独占或提取过最新验证指标。
- M215-BEC现绑定隔离R1 source026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563（单父4e8），主线/运行源码仍4e8。双跨层joint child+parent→2C/GELU split u/v、v等权上行、coarse原LN/FFN、两2C→C/GELU回传middle/fine；保留六原model文件、rawmean/FPS/IDs/CSORT与单inst回写。
- 原9b678…在45eb的两smoke实际finite成功，但资源candidate rc1/JIT aten::index_fill bool alias断言，原f8fac959…/旧四臂/旧native code9b保持；属于实现失败，不是资源超标或假设反证，不将原生成功继承到R1。
- 已有唯一implementation revision1仍pending；注册3fa782b8…、CPU原3case bool eager/traced精确等价且int1修JIT/原fvcore390ac50a…、单True→1私包2ef488c4…、Git实证617203db…（创建时primary48fc）保持，未新增修订或改原注册。
- R1新op包tick_faccbed6/bec_r1_operational_prepare/preparation.json SHA9a81c28ac80f2f9f00184f67f7bd47841124cb8a18e0a22c554eaceb10957d35，nativeedd2049e…，release模板ee75b293…，worker7e5d原字节/all9runtime函数AST不改。独审tick_e2e3d058/bec_r1_operational_independent_review.json SHA0e3572192e3a0d68e8d4f656cdf3d74d15a8e3f9b1b2b79f2fcf4671f5dcc627仅静态工具准备通过。
- R1只读四结果checker57752ca3…/071202cf…及peer98def957…保持原15科学函数AST，拒旧9b/GPU1/缺四结果；source026c真实native TRAIN与resources均NOT_RUN，native_execution_code_commit=null，10active字段null，不伪造receipt/PASS/queue。
- 本轮root只静态release bytecopy与现有BEC新外锚，完整旧candidate/旧双卡resource_wait/旧版本工具/原四raw留history；actual NoTransport当前owner/source026c/current0 guard：0 registeredCTSbusy、1 unauthorized，零transport/process/network/Torch/active材料。这是软件保护核验，不是硬件空闲或原生资源通过。
- BEC下一步仅在CTS自然终态/原占用释放后，以fresh真实GPU0 idle/UUID/assets/三锁/currentowner绑定跑原M95/R1固定TRAIN2与原资源四臂。不得改样本/seed/阈值，未测不入队，不对运行CTS同步026c。
- M213-BFC原TRAIN20/50 step3832/4686共享DataLoader scatter overlap RuntimeError，已crashed archiveb91b3ba11671451bb28f39dc3cc3f2c7；原source48fc/receipt812454/launch/完整log daf14d06…保留，根因UNKNOWN，不否定机制、不自动resume。
- BFC原last.pth SHA24b3424f0cdc3a6f004bf20ff49b1799e75b92382214b2590d90486192883777，epoch19、best.4992169439792633/noimprove4、1151CPUtensor finite/640optstates/5groups/maxstep89034/scheduler19；CPU证据9b957f10…、计划8379534d…已存。RNG/sampler/失败输入未复现，不能称续3833；需具体兼容源计划与BFC专属人类授权，不借HAP/M206grant。
- BFC原四真臂资源9.775377484G，median42.21815 vs42.31158ms，P9062.91052 vs60.95282ms更慢；预测/observer-smoke不等pureTRAIN峰值。原日志.499仅3dp，与checkpoint精度分开。BCR已早停27/.4995，终态不动。

## Closed Or Failed Directions
- 本轮旧10均未due，未扫655正文/旧grant/checkpoint体、未重开held或做重复全套检查。最近有界复核tick_509e9191/held_boundary_check.json SHA6b87e37d8d7dc31f13540774023a524cfd18db642b556ba458fa191bedc257a7仅历史metadata依据。
- PCE默认2+额外1已尽/2.861e-6/13.86x；RSTR默认2已尽/R2mean1.027033878e-6>1e-6；禁PCE_R4/RSTR_R3/M201自动恢复。旧RSTR9文件localcommit授权不授额外修订，所有负证据保持。
- 原2d06源码prep/null、native322c原23文件/null/DRAFTTrue、旧9b op420/8e/b551均原字节保持；新R1工具是新包，不原地填旧null/启用旧禁用包或改原失败。

## Running And Queue
- 当前1running CTS，仅server4 GPU0；采集上海16:11:34–16:11:38，TRAIN5/50 1688→1697/4686。CTS最佳验证指标本轮未知。queue/running/receipt/source不改；仅exp辅助training_status waiting→running与research catalogue校正并独立留差异证据。
- M206-CGCA仍waiting但paused/dispatch_hold/resume_authorized=false，不计ready；当前0可运行待跑。BEC R1待真正空闲GPU0后实测，BFC恢复尚无完整授权，不挪卡/驱逐/重启。GPU1禁用。
- pinned songcl@192.168.1.115，先验证dl04-MS-7E06；GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c。root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1；conda project_cluster/server4_conda_4ca73fba.sh；data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints。keys/strict hostkey，不用旧IP/密码/sudo。
- 未知claim/request/PID只读reconcile，不盲重启/kill/删锁。白名单与旧lease从不等于未来空卡授权；每次真实GPU计算前重新检查当前资源/UUID/三锁/原deadline。只用python -B与PYTHONDONTWRITEBYTECODE=1。

## Open Questions And Risks
- 目标gap.0080仍未缩小；CTS正在测训练效果，R1尚未原生GPU复测。不得将静态工具、CPU兼容或metadata guard当作实际GPU backward/resources/准确率结果。
- 实际native FP32有限grad/update已在原CTS/BFC相应臂观察；fullbuffer/RNG/offdiagonal、未行使零边界和pureTRAIN峰值仍未知，不笼统说FP32从未测试。
- BFC crash根因/输入未复现，clone修复未验证；不未经BFC专属授权续训。当前primary/runtime4e8不因私有R1准备改变，历史GPU1实测与当前禁用边界严格区分。

## Last Tick
- faccbed6旧轮因上游模型容量中断遗留租约；新heartbeat核原轮结束/本地相关writer0后，用原token canonical abort为INCOMPLETE并释放，然后新begin e2e3。旧06:36/06:38/06:42冻结准备包均在原07:05deadline前生成，保留原owner，无重造/延时旧snapshot。
- 本轮snapshot candidate/admission预算2，creation/reserve预算0、reserve2/target2、pending12；只接续CTS/BEC，0新候选、0新修订、0新Git/receipt/准入/入队/dispatch/训练启动。现CTS启动是前轮canonical行为。
- 接纳已冻结R1工具的独审与静态外锚，真实运行当前NoTransport资源保护核验；tick_attempt=resource_check/blocked，不冒充native科学PASS。CTS独立只读进度核验确认原运行，保留queue残余dispatch_phase不改/不据此重启。
- 主线4e8/28用户文件status+bytes/index空、其他139候选、11账不变；CTS experiment只有辅助training_status一个field改变，原前值/完整前对象/12账基线与精确语义diff另存。六段report与本七段memory收尾，实际finish/receipt为准，释放后不回写。
'''
        assert len(memory.splitlines()) < 120 and memory.count('\n## ') == 7
        notes = {'actions':[
            '核验实际会话/target一致，安全终止已确认中断且无writer的旧facc研究租约后，以新e2e3原始snapshot继续；CTS远端训练全程未被触动。',
            '本轮08:11:34–08:11:38 UTC两次只读实观原CTS PID3505065，TRAIN5/50步数1688→1697/4686；版本4e8、8源/YAML/argv/cwd/fd1/UUID0保持，独立31项复核无实质疑点。原启动发生于前facc canonical begin，本轮新增训练启动0。',
            '复用原deadline前冻结的新BEC R1 exact026c工具包与只读四结果checker；35项静态独审无未决问题，root只做byteexact静态release/现有candidate版本外锚，完整9b原native两smoke成功及JIT资源失败留历史，R1仍pending/原生NOT_RUN。',
            '实际运行当前owner/current0/新R1外锚NoTransport guard：GPU0因登记原CTS忙拒绝，GPU1因明确仅GPU0授权拒绝；0transport/process/network/Torch/active材料。这是软件保护测试，不是硬件或原生资源PASS。',
            '校正CTS research catalogue为training；其experiment只将辅助training_status waiting改running，queue/running/receipt/code未改。主线/28用户文件/index及其他139候选/其他11受保护账保持，精确差异与前对象归档。',
            '0新候选/0新修订/0新Git版本/0新收据准入/0入队/0派发，旧10未due不重查；M206暂停与BFC不恢复、GPU1禁用、调度Disabled保持。'],
            'decisions':[
            'CTS继续原GPU0训练，效果与当前最佳验证指标未知；目标.5100/M95.5020/gap.0080保持。',
            'BEC R1只是已评审、已绑定的待测准备；仅在CTS自然释放GPU0且fresh真实idle/UUID/assets/三锁/currentowner复核后，原协议跑全部M95/R1 TRAIN2和资源臂；不重标旧raw、不改抽样/阈值，不据静态结果入队。',
            '本轮有当前实际资源保护测试但受已证实CTS运行阻塞，按experiment_first保存同候选当前resource_check/blocked证据收尾；不凑满准入额度，不把注册busy当实测空闲。',
            '旧facc INCOMPLETE仅为研究轮中断，不是训练失败；本轮报告不预先宣称postflight通过，实际收尾以canonical结果/FINALIZED released receipt为准。']}
        # Complete serialization and scope checks before any shared write or intent.
        work_bytes, exp_bytes, memory_bytes = encoded(updated), encoded(new_exp), memory.encode('utf8')
        encoded(notes)
        before_refs = {'work_sha256':sha(wp),'experiment_sha256':sha(ep),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
        save_new(HERE/'final_reconciliation_before.json', {'owner':{k:owner[k] for k in ['token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256']},'CTS_experiment_before':exp,'CTS_catalog_before':next(c for c in work['candidates'] if c['id']==CTS),'BEC_catalog_before_final_notes':next(c for c in work['candidates'] if c['id']==BEC),'work_tick_attempt_before':work.get('tick_attempt'),'hashes':before_refs,'protected_before':before})
        save_new(HERE/'final_reconciliation_intent.json', {'recorded_at':now,'owner_token':TOKEN,'scope':'CTS current catalogue, BEC actual local guard evidence/tick_attempt, compact memory; experiment auxiliary training_status only','before':before_refs,'no_remote_source_or_queue_operation':True})
        guard(); assert sha(wp)==before_refs['work_sha256'] and sha(ep)==before_refs['experiment_sha256']
        replace_bytes(wp, work_bytes); replace_bytes(ep, exp_bytes); replace_bytes(ROOT/'pipeline/codex_memory.md', memory_bytes)
        save_new(HERE/'report_notes.json', notes)
        after = snapshot()
        assert all(after[k] == before[k] for k in ['head','index_empty','status_hex','files'])
        changed_ledgers = [k for k in before['protected_ledgers'] if before['protected_ledgers'][k] != after['protected_ledgers'][k]]
        assert changed_ledgers == ['experiments/M214-CTS.json']
        actual_exp = read(ep); assert actual_exp == new_exp
        assert {k for k in set(exp)|set(actual_exp) if exp.get(k)!=actual_exp.get(k)} == {'training_status'}
        actual_work = read(wp); assert actual_work == updated and unrelated(actual_work)==unrelated(work)
        assert (ROOT/'pipeline/codex_memory.md').read_bytes() == memory_bytes
        result = {'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'source_head_28_user_files_status_and_index_unchanged':True,'other139_candidates_unchanged':True,'candidate_count':141,'new_candidates':0,'changed_protected_ledgers':changed_ledgers,'CTS_experiment_semantic_diff':{'training_status':{'before':'waiting','after':'running'}},'other11_protected_ledgers_unchanged':True,'queue_running_receipts_unchanged':True,'CTS_native_progress':progress,'BEC_R1_native_resources':'NOT_RUN','BEC_R1_revision_result':'pending','new_training_launches_by_this_tick':0,'memory_lines':len(memory.splitlines()),'after_snapshot':after,'work_sha256':sha(wp),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md'),'notes':ref(HERE/'report_notes.json'),'material_concerns':[]}
        save_new(HERE/'final_reconciliation_result.json', result)
        print(json.dumps({'status':'CURRENT_CATALOGUE_AND_AUX_FIELD_RECONCILED','result':ref(HERE/'final_reconciliation_result.json'),'memory_lines':len(memory.splitlines())},ensure_ascii=False))
    finally: lock.close()

if __name__ == '__main__': main()
