"""Expired-tick cleanup records only; no research or executable-helper replay."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, shutil, subprocess, sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
TOKEN='e2e3d058a5274d2db709c77a328b363f'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf8') as f: json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')

def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ.get('CODEX_THREAD_ID')==read(ROOT/'pipeline/execution_mode.json')['target_thread_id']
    assert datetime.now(timezone.utc)>datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    sys.path.insert(0,str(SKILL)); import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT)); assert lock is not None
    try:
        assert read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')['token']==TOKEN
        missing=['bec_r1_anchor_intent.json','bec_r1_static_anchor_result.json','bec_r1_actual_local_guard.json','protected_assets_after.json','final_reconciliation_intent.json','final_reconciliation_result.json']
        assert all(not (HERE/n).exists() for n in missing)
        assert not (ROOT/'pipeline/diagnostic_bundles/tick_faccbed6/bec_r1_operational_prepare/adapter_release.json').exists()
        baseline=read(HERE/'protected_assets_before.json')
        ledger_hashes={n:sha(ROOT/'pipeline'/n) for n in baseline['protected_ledgers']}
        assert ledger_hashes==baseline['protected_ledgers']
        wp=ROOT/'pipeline/research_work.json'; w=read(wp)
        assert {c['id']:digest(c) for c in w['candidates']}==baseline['candidate_digests']
        code=ROOT/'Cluster'
        def git(*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(code),*args],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
        assert git('rev-parse','HEAD').decode().strip()==baseline['head']
        assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==baseline['status_hex']
        assert not git('diff','--cached','--name-only')
        assert all(sha(code/rel)==value for rel,value in baseline['files'].items())
        exp=read(ROOT/'pipeline/experiments/M214-CTS.json')
        assert exp['status']=='running' and exp['training_status']=='waiting' and exp['pid']==3505065 and exp['launch_verified'] is True
        memory='''# Codex Research Memory

## Goal And Phase
- 本轮e2e3d058a5274d2db709c77a328b363f，实际会话/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-26T08:09:05.798203+00:00，原deadline09:09:05.798203+00:00。上游模型容量中断，09:11恢复时已过期；未延长/重造snapshot，当前仅收尾记录并canonical abort，不能标COMPLETE。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020/baseline.4894/gap.0080。Phase1层级分工→inst_feats→query/masks，监督辅助，Phase2需人工确认。
- seed1999/epochs50/max_iters70/原YAML/data/pretrain/optimizer/precision不变。原10G/原fvcore handlers/fullunsupported、bs1/lang1/warm20/repeat100 median/P90；峰值显存+15%需≥+.003mIoU。禁止调参、gate/cag/cfe/layerscale、语言路由、大QKV/N²attention、重复inst注入、旧rejected改名/无图改变微调。
- standing authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖普通项目实验操作，不授旧hold重开/额外修订/受保护恢复/扩大资源/改调度。
- 最新人类“不用gpu1”：SERVERS SHA2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1仅server4 physical[0]/max1；授权server4_gpu0_only_20261026.json SHA94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09。旧GPU1实测仅历史依据，未来禁用GPU1；其他allowed[]、调度Disabled保持。

## Champion And Baseline
- M95仍.5020；M205-MDC26/.4872、M207-HAP31/.5002、M208-HRC31/.4901、M209-PSBR23/.4969、M210-PSNC31/.5001、M211-BTC31/.4914、M212-BCR27/.4995均自然早停未超M95。不调参重跑或整体否定层级路线。
- HAP原DataLoader异常根因UNKNOWN，epoch18恢复授权已消费；BTC/BCR原版本/归档/完整日志保持，不再启动。BCR archive5d060afca23d43deb4ae63525c00ff3d，完整log f14c962f…。

## Active Hypotheses
- CTS M214已经真实训练；source/primary/runtime4e80006047d5cb3dcdfb9c1102e02c33f354a07d（父48fc），原8源/YAML及admission5416d5e…不改。e245已准入waiting，实际启动是前facc canonical begin，本轮新增启动0。
- CTS同父几何cycle上共享dense3tap dilated circular Conv1D家族：old own/±3^r→3C→C/GELU，最小3^k≥n，保留原LN/cfskip/finecoarse/rawmean/FPS/IDs/CSORT/HCG/单inst注入。不是新覆盖、新颖或单因素收益证明。
- 原45eb真实M95/CTS TRAIN2+原资源四臂a33c0fe7…/独审5d2f0716…通过，loss9.547047615/13.908418655、共同843张量/156958522参数、实际3distinct、多轮64/60、三W列原loss有限非零grad/每step更新。原owner与GPU0结果保持，不重标重测。
- CTS原资源9.761811532G vsM959.762532428G，params157155386 vs157484090，同GPU0 median35.8969 vs38.2312ms/P9037.4890 vs42.4553ms，+15%条件未触发；训练效果/新颖性/pureTRAIN峰值未知。
- 本轮08:11:34.910062–08:11:38.264124Z只读实观原PID3505065/start61122472，TRAIN5/50 step1688→1697/4686；实际8源/YAML77e/argv/cwd/fd1/UUID0一致。证据tick_e2e3d058/cts_native_progress_observation.json SHA7753f123df69abccbab98398bc166546abf53a3775be6f3518c8a783172dfde8，独审b7a99c4e…；不声称持续独占或当前验证指标。
- BEC M215当前共享candidate仍code9b6782f44ca7f2c8ac35baea01dfd070314b5701/stage validation；当前隔离R1真实source026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563（单父4e8）尚未绑定到catalog。主线/运行源保持4e8，不能把私有新源当已部署。
- BEC双跨层joint child+parent→2C/GELU split u/v、v等权上行，经原coarse LN/FFN再两2C→C/GELU回传middle/fine；六原model文件、rawmean/FPS/IDs/CSORT/单inst保持。原9b两smoke实际finite成功，但candidate资源rc1/JIT aten::index_fill bool alias断言，f8fac959…/原四raw/旧native9b不改，属于实现失败非资源超标或假设反证。
- 唯一implementation revision1仍pending。prereg3fa782b8…、CPU390ac50a…：bool/int1 eager mask精确相同，bool JIT原错重现，int1 trace/eager相同且原fvcore通过；仅CPU兼容，不是R1全模型GPU通过。单True→1私包2ef488c4…/Git实证617203db…（创建时primary48fc）保留。
- R1新op tick_faccbed6/bec_r1_operational_prepare/preparation.json SHA9a81c28ac80f2f9f00184f67f7bd47841124cb8a18e0a22c554eaceb10957d35/nativeedd2049e…/release模板ee75b293…，原worker7e5d字节及9runtime函数AST保持。新独审tick_e2e3d058/bec_r1_operational_independent_review.json SHA0e3572192e3a0d68e8d4f656cdf3d74d15a8e3f9b1b2b79f2fcf4671f5dcc627仅静态准备，无未决阻断。
- R1新只读四结果checker57752ca3…/071202cf…与peer98def957…保持原15科学函数AST，拒旧9b/GPU1/缺四结果；新source026c真实native TRAIN/resources均NOT_RUN，不继承9b原结果、不造receipt/queue。
- 本轮新root helper准备包tick_e2e3d058/bec_r1_anchor_prepare/preparation.json SHA546046e969856630fc4a9e614fe3c7c9018b631c4c022c834badf49b1cbdf365；anchor1ca37890…/guard10d07982…/源审910044a1…，默认禁用，只完成准备/独审，未制作执行copy、未静态release/外锚、未actual NoTransport。
- 过期后禁止运行上述旧owner helper。下一新heartbeat先核新实际owner/deadline/context/current0/CTS进度，按同scope新copy重绑，再只做reviewed staticanchor→actual NoTransport→保护audit；不能把准备的guard预测写成已测试。若GPU0真释放，再fresh idle/UUID/assets/三锁后原M95/R1固定TRAIN2+资源四臂，不调样本/seed/阈值，不对运行CTS同步026c。
- BFC M213原TRAIN20/50 step3832/4686共享DataLoader scatter overlap RuntimeError，crashed archiveb91b3ba11671451bb28f39dc3cc3f2c7，source48fc/receipt812454/launch/完整log daf14d06…保留；根因UNKNOWN，不否定机制、不自动resume。
- BFC last.pth SHA24b3424f0cdc3a6f004bf20ff49b1799e75b92382214b2590d90486192883777，epoch19/best.4992169439792633/noimprove4/1151CPUtensor finite/640optstates/5groups/maxstep89034/scheduler19；证据9b957f10…/计划8379534d…已存。RNG/sampler/失败输入未复现，不能称续3833；需具体兼容源计划+BFC专属人类授权，不借HAP/M206grant。

## Closed Or Failed Directions
- 本轮旧10未due，未扫655正文/旧grant/checkpoint体，未重开held或重复全套检查。最近bounded metadata复核tick_509e9191/held_boundary_check.json SHA6b87e37d8d7dc31f13540774023a524cfd18db642b556ba458fa191bedc257a7仅历史依据。
- PCE默认2+额外1已尽/2.861e-6/13.86x；RSTR默认2已尽/R2mean1.027033878e-6>1e-6；禁PCE_R4/RSTR_R3/M201自动恢复。旧RSTR9文件localcommit授权不授额外修订，负证据全保留。
- 原2d06 prep/null、native322c原23文件/null/DRAFTTrue、旧9b op420/8e/b551均原字节；新R1为新包，不填旧null或启用旧禁用包。BFC资源P90+3.2118%/BCR原GPU1较慢不夸全面效率，预测/observer不等pureTRAIN峰值。

## Running And Queue
- 当前canonical CTS running/launch_verified=true/PID3505065，仅server4 GPU0；最近采集上海2026-10-26 16:11:34–16:11:38，第5/50轮1688→1697/4686。其最新验证指标未知。queue/running/receipt/code未改；research catalogue仍旧deployment/waiting、experiment辅助training_status仍waiting是尚未校正的残余，不能据此重启。
- M206-CGCA仍waiting但paused/dispatch_hold/resume_authorized=false，不计ready；当前0可运行待跑。BEC R1待原CTS释放/真空卡；BFC无完整恢复授权，不挪卡/驱逐/重启，GPU1禁用。
- pinned songcl@192.168.1.115，先验证dl04-MS-7E06；GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c。root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster/server4_conda_4ca73fba.sh，data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints；keys/strict hostkey，不用旧IP/密码/sudo。
- 未知claim/request/PID只读reconcile，不盲重启/kill/删锁；白名单/旧lease不是未来空卡许可。每次GPU计算重新核当前资源/UUID/三锁/原deadline；python -B与PYTHONDONTWRITEBYTECODE=1。

## Open Questions And Risks
- CTS训练效果仍待结果，R1尚未GPU原生复测。静态工具/CPU兼容/软件guard均不能代签GPU backward/resources/准确率；本轮连actual NoTransport也未执行。
- 原CTS/BFC相应native臂已观测有限grad/update；fullbuffer/RNG/offdiagonal、未行使零边界/pureTRAIN峰值未知。BFC根因/输入未复现，clone修复未验证，未经专属授权不续训。
- 本轮prepared complete_current_tick.py未执行；final_bookkeeping_review c04f352f…指出其一条CPU记忆措辞需澄清。该源已被hash绑定，后续保留旧源并新copy修文，不能运行过期版本或直接声称安全完成。

## Last Tick
- facc旧轮先核结束/相关writer0，用原token canonical abort/released后新begin e2e3；旧06:36/06:38/06:42冻结工具在原07:05deadline前生成，保留原owner/字节，无旧snapshot延时。
- e2e3新snapshot candidate/admission预算2、creation/reserve预算0、reserve2/target2、pending12；只接续CTS/BEC。实际完成CTS只读进度与独审、BEC R1工具/新静态helper源审；0新候选/修订/Git/准入/入队/派发/训练启动。
- 上游模型capacity中断导致恢复时09:11>09:09真实deadline，故未执行staticanchor/NoTransport/辅助账校正/正式postflight；不虚构tick_attempt或科学PASS。所有141候选/12受保护账/主线4e8/28用户文件status+bytes/index空与本轮before一致。
- 仅在过期收尾阶段保存本七段事实交接/六段report/INCOMPLETE原因，然后canonical abort原token并核释放；最终状态以实际receipt为准，释放后不回写。
'''
        assert len(memory.splitlines())<120 and memory.count('\n## ')==7
        notes={'actions':[
            '本轮实际完成CTS原进程只读核验：08:11:34–08:11:38 UTC，PID3505065/start61122472，TRAIN5/50步数1688→1697/4686，source4e8/8源/YAML/UUID0保持；独立31项复核无实质问题。训练启动是前facc canonical begin，本轮新启动0。',
            'BEC R1新版本026c的op/native/checker静态复核完成；新root静态锚定/NoTransport helper546046与源审910044准备完且默认禁用。原9b两smoke成功/JIT资源失败保留，R1新native与资源仍NOT_RUN。',
            '上游模型可用容量中断，恢复时09:11 UTC已超过原09:09:05.798203 deadline，未延时或重造snapshot；没有执行staticanchor、actual NoTransport、release、辅助账校正或任何GPU测试。',
            '收尾只读核实141候选和12受保护账、primary4e8、28用户文件status+bytes、index空均等于before；仅更新七段事实handoff和本六段报告。0新候选/修订/Git/准入/入队/派发/训练启动，GPU1未查询/使用，M206暂停。'],
            'decisions':[
            '本轮不能标COMPLETE：没有完成当前实际候选测试/准入，且真实deadline已过。保存准备与部分进展后canonical abort原e2e3 token，明确INCOMPLETE并核release；不能补造resource_check/blocked。',
            '下一新heartbeat先核新owner/deadline/context及CTS进度；重绑同scope helper后完成已有R1静态anchor和实际保护核验，原GPU0被CTS占用时不得做nativeGPU测试或同步026c。',
            'CTS当前训练效果/最新验证指标未知，M95.5020/目标.5100/gap.0080保持。保护原训练，不以catalog旧waiting或queue残余phase作为重启理由；无需新增人类操作授权。']}
        # Cleanup only: preserve the old memory and prevalidate both complete documents.
        memory_path=ROOT/'pipeline/codex_memory.md'; old_memory_sha=sha(memory_path)
        json.dumps(notes,ensure_ascii=False,allow_nan=False)
        assert not (HERE/'interrupted_handoff_result.json').exists()
        shutil.copyfile(memory_path,HERE/'codex_memory_before_interruption.md')
        save(HERE/'interrupted_report_notes.json',notes)
        temp=memory_path.with_name('codex_memory.md.'+TOKEN+'.cleanup.tmp')
        with temp.open('x',encoding='utf8') as f:f.write(memory)
        assert read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')['token']==TOKEN
        os.replace(temp,memory_path)
        assert ledger_hashes=={n:sha(ROOT/'pipeline'/n) for n in ledger_hashes}
        assert read(wp)==w
        save(HERE/'interrupted_handoff_result.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':TOKEN,'deadline_unchanged':owner['deadline_at'],'scope':'Expired-tick truthful handoff/report cleanup only; no research continuation','prepared_anchor_and_guard_not_executed':True,'production_release_absent':True,'all141_candidates_unchanged':True,'all12_protected_ledgers_unchanged':True,'source_head_28_user_files_and_index_unchanged':True,'memory_before_sha256':old_memory_sha,'memory_after_sha256':sha(memory_path),'memory_lines':len(memory.splitlines()),'native_R1_resources':'NOT_RUN','round_outcome':'INCOMPLETE_ABORT_REQUIRED'})
        print(json.dumps({'status':'TRUTHFUL_INTERRUPTION_HANDOFF_RECORDED_ABORT_REQUIRED','memory_lines':len(memory.splitlines()),'result_sha256':sha(HERE/'interrupted_handoff_result.json')},ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
