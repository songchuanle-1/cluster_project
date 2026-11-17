"""Persist this foreground tick's actual evidence and concise handoff."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import sys

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
TOKEN = '37695e94da4a485c8979d474d3f33b39'
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.37695e94.tmp')
    assert not temporary.exists()
    with temporary.open('x', encoding='utf-8', newline='\n') as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def main():
    owner = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN and owner['thread_id'] == os.environ.get('CODEX_THREAD_ID')
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json') == owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256']
    guard = read(HERE/'hrc_forward_actual_guard_integration.json')
    assert guard['token'] == TOKEN and guard['remote_transport_calls'] == 0
    assert guard['results']['GPU0_current_owner_candidate_policy_whitelist_guard'] == 'PASS_LOCAL_ONLY'
    assert guard['results']['prepare_GPU0']['reason'] == 'Selected GPU has registered running task'
    assert guard['results']['prepare_GPU1']['reason'] == 'Selected GPU is not currently allowed'
    decision = ROOT/'pipeline/decisions/20261022-202458_other.md'
    assert decision.is_file()
    paths = [
        HERE/'continuation_boundary_check.json', HERE/'hrc_commit_lineage.json',
        HERE/'hrc_dispatch_binding_audit.json', HERE/'hrc_forward_binding_independent_review.json',
        HERE/'hrc_forward_independent_fixture_run.json', HERE/'hrc_forward_binding_activation.json',
        HERE/'hrc_forward_actual_guard_integration.json', HERE/'activate_hrc_forward_binding.py',
        HERE/'check_hrc_forward_actual_guards.py', HERE/'canonical_decision_record.json', decision,
    ]
    references = [ref(path) for path in paths]
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None, 'Canonical project lock busy'
    try:
        work = read(ROOT/'pipeline/research_work.json')
        candidate = next(c for c in work['candidates'] if c['id'] == 'hierarchy-bottom-up-refined-token-composition')
        assert candidate['code_commit'] == '74fcd21df0af9a971792038ffe251af1ffea2604'
        assert candidate['scientific_admission'] is False and candidate['stage'] == 'blocked'
        assert len(candidate['version_binding_history']) == 1
        for item in references:
            if item not in candidate['evidence']:
                candidate['evidence'].append(item)
        candidate['execution_adapter']['actual_local_guard_integration'] = ref(HERE/'hrc_forward_actual_guard_integration.json')
        candidate['execution_adapter']['external_anchor_verified_at'] = datetime.now(timezone.utc).isoformat()
        attempt = work['tick_attempt']
        assert attempt['tick_started_at'] == owner['generated_at'] and attempt['kind'] == 'resource_check' and attempt['result'] == 'blocked'
        for name in ['hrc_forward_binding_independent_review.json', 'hrc_forward_binding_activation.json', 'hrc_forward_actual_guard_integration.json']:
            item = ref(HERE/name)
            if item not in attempt['evidence']:
                attempt['evidence'].append(item)
        attempt['non_gpu_continuation'] = 'Detected and repaired real future fresh-dispatch HEAD mismatch using independently reviewed same-source74f preparation. New actual31 offline fixtures and21 independent static checks passed; actual local owner/candidate guard passes, occupiedGPU0 and forbiddenGPU1 refuse before transport. No native/resource/pairing/admission PASS, no source/sync/queue/launch.'
        work['updated_at'] = datetime.now(timezone.utc).isoformat()
        write(ROOT/'pipeline/research_work.json', work)
        memory = '''# Codex Research Memory

## Goal And Phase
- 当前foreground37695e94da4a485c8979d474d3f33b39；actual owner01a159c5-29ab-7a22-ba7f-e79174757253与execution_mode target一致。generated UTC12:08:33.052148/原deadline13:08:33.052148，未延长。前轮9079已FINALIZED/released且lock/pending消失才begin；本轮完成以真实report/finish/receipt/锁释放为准，不提前写PASS。
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100、championM95.5020/gap.0080、baseline.4894。Phase1 hierarchy→inst_feats→query/masks，supervision辅助；Phase2需确认。
- 原生seed1999/epochs50/maxiters70/default10G与bs1/lang1/warm20/repeat100资源口径保持。禁调参/gate/语言routing/大QKV/pointN²/重复注入/新残差系/纯缩放/历史rejected改名重开；静态/mock非native准入。
- standing experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖常规实现/检查/版本/安全同步/准入训练；不覆盖资源扩张/旧hold重开/额外修订/人工暂停恢复。
- 最新人类“GPU1可以先暂停训练了 给别人腾出来一张卡”：仅server4物理GPU0/max1；grant server4_gpu0_only_20261022_gpu1_pause_105409.json SHA1871f8c9777c548acfda87b9e91b72c2d5fc94ac78920430c52bdceea1cbd51e。GPU1无计算权限，M206不迁移/恢复，server3/server6无allowed，Windows Pipeline-cluster_project仍Disabled，不改调度。

## Champion And Baseline
- 本轮begin缓存HAP native28/50/Best.5002/noimprove6/10，近期.4898/.4900/.4938/.4920/.4934；仍低M95.5020及目标.5100。中途平台期不等于终态/机制反证，不调patience/训练协议或人工早停。
- M205-MDC已canonical done_earlystop，epoch26/noimprove10/best.4872，较M95低.0148、baseline低.0022；只保留该实现负结果，不泛化层级机制失败。
- 原HAP在epoch19/50 step3665/4686 DataLoader worker1 AttributeError后canonical crashed归档；原log SHA794be0ab616954c28ec8b120f57309c6443f7ba87133c983e2f506887ad84a59，原history/receipt保留至prior_runs，非earlystop或完整期科学结果。
- HAP历史标准资源9.762944066G vsM95 9.762532428G，median46.254797vs43.596659ms/P9064.774761vs60.729895ms、参数157484090；unsupported pinv/index_add原样披露，计数非完整成本。
- M206-CGCA仍人工暂停：full snapshot meta24/best.4952535927295685/noimprove7，SHAe9b42b2632762dae5ca49d80b3272889809b1ffe3ec30dd377690af8cb2e8e9d；暂停不是失败，HAP授权不覆盖M206。

## Active Hypotheses
- M207-HAP stable hierarchy-affine-coarse-to-fine-prolongation，commitf51823bbddf0f8095a9a5813bf1f8169e3d7edb0；原3FFN后coarse→middle→fine仿射延拓，0新参数，rawbanks/FPS/IDs/CSORT/HCG/末次inst路径保持。历史真实TRAIN2/backward/资源已准入，完整期效益未知。
- 人类直接回复“授权 HAP 在 GPU0 续训”已执行：grant pipeline/authorizations/m207_resume_gpu0_20261022_hap_resume_151948.json SHA21799cd7854fd9e7b2346b7464822b2682e9cebbf5bfc16926544cb8224f13a5，purpose cluster_native_resume绑定M207/f518/原YAML/物理0/固定epoch18 fullstate；不再问、不覆盖M206/GPU1/冷启动/参数改变。
- HAP原生resume固定 /data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261022_hap_crash_5c46f46a/20261022_002007/last.pth，SHA28ad9df5784c0287cc085df81faa10e0efe251cb417126034db1ad24d7e11966；meta18/best.4975287616252899/noimprove0、model/optimizer642states5groups/scheduler/allCPU核全，start_epoch19。无完整RNG/worker精确minibatch恢复，19轮部分重做。
- M208-HRC stable hierarchy-bottom-up-refined-token-composition，当前执行绑定74fcd21df0af9a971792038ffe251af1ffea2604；原实现提交9e543af623acd7fa9bd4a3f81ce79c932e98774a完整保留version_binding_history。h0FFN→原fixed mean_ids1→h1FFN→mean_ids2→h2FFN，3原FFN各一次，内部empty child bias按原等权保留，raw-CSORT/HCG不变。
- HRC实际发现canonical fresh dispatch要求task.code_commit==localHEAD，旧9e包会被当前74f拒绝。9e→74f仅新增PSBR9文件，HRC8源/YAML/worker原字节。新包只更新commit/FROZEN/path/hash元数据，全部guard/方法AST/资源/RNG不变；这是同源版本绑定，不是模型修订/新候选或旧证据重标。
- HRC新冻结外锚以candidate.worker_preparation/execution_adapter为准：tick_37695e94/hrc_native_prepare_head74f/preparation.json SHA87ef65ab7ac065688879bc0587a26ef1704d001a8190086ba55b2d005f6ae8e1，worker37782c1ae1ea9cb2f7bb77d59c7b8aff926438fbac827106f94d8c8fa396ef01；adapterprep SHA f2ed5b65c0d673ec1ef38ed67fc52905aac9e6a1c1cdfd8b0145ac0978e8395a，release7aa68337a4aa653e4bc55d0fff2c4e0a1fa84ac3fda7d968732ddd1bf93c1b23。
- HRC新包实际31离线fixture全过；独审另实际31全过及21静态链/全文/AST检查，review SHAde73d3e10b7e204e1935f54ca9203533c515fe4437867de4029feca0bea48b66；root外锚登记后actual guard通过owner/candidate，prepare0因HAP注册忙拒绝、prepare1因未授权拒绝，transport0/无binding/manifest/lease。native/resources/pairing均NOT_RUN。
- M209-PSBR stable hierarchy-parent-segmented-bidirectional-token-state，commit同74f；middle真support ids1[ids0]、ids2父组内detached原xyz+ID排序，共享Wx/无biasWh双向tanh每组零态，Wo拼接逆散原ID替换wholemiddle residualFFN，fine/coarse/raw-CSORT/HCG/单inst保持。
- PSBR冻结包未改：tick_8fafa3d4/psbr_native_prepare/preparation.json SHA1e1de105f34ce4f6f87fe862bf35ee2c7c0bf26bf7404b0550559534a0e7472e，worker05ab6ac1f72f804bf9799e6b6a95127057d330d13302686740cb1acb94343385；adapterprep9d6c98a4c406d052c5ae1d420053103b0ec08bf71fb0ce5c32de88dd49b5bb4b/releaseb17d424e493bcd49e1858bc6fc4b897d6fab5970a25240cea143e826f40e20d7。
- HRC/PSBR blocked/exclusive_gpu_slot/resumevalidation，唯一授权GPU0由HAP占用；真空卡优先HRC后PSBR，不为额度造结构或重开hold，不把准备/31mock当native准入。

## Closed Or Failed Directions
- 8旧hold保持：4supervision scope、2measurement实现/未定hold、PCE/RSTR数值失败及修订上限；本轮旧8均notdue，无新reopen/scope/extra revision授权，不重扫655证据。前次全body校验与新metadata核界限保留。
- PCE默认2+额外1耗尽/2.861e-6失败及13.86x延迟；RSTR默认2耗尽/R2 mean1.027033878e-6>1e-6，旧passed或独立9.536743e-7不清最终失败，禁PCE R4/RSTR R3。36b59daa九文件本地提交授权不是新修订，M201不自动恢复。
- 不重开pair-edge/moment/改MDC邻域或旧CCP/REAG失败路线。HRC/PSBR历史有限核对不是全历史/文献新颖性或收益证明。
- HAP原DataLoader crash底因实施/环境UNKNOWN，当前继续训练不证明根因已修复；不标整机制rejected，不改加载器/环境凑通过。

## Running And Queue
- M207当前三账running/GPU0/PID1063355/start27048767/launch_verifiedtrue；fullresume起始真实71→81进度proof manual_ops/20261022_hap_resume_151948/native_resume_progress.json SHA0cc547c0b43c0fd6775d5bdb8248ba629b82e29518671adb0c4882ed5edcda20。原crash至prior_runs/manual prior_crashed_experiment.json保留。
- 本轮UTC12:09:19/上海20:09:19 exact原PID/start/原YAML+固定18 --resume argv/cwd、hostname与GPU0UUID匹配；native28/50两次1830→1839/4686，logfresh.336s，整卡19853MiB/util39、仅HAP context19800MiB。proof tick_37695e94/hap_progress_observation.json SHA46fbedfdc2d0c6fe2bf09fa286ff4597af0bc65bd238d65063545cc62ec0742e；GPU1未查询/使用，无信号/驱逐/环境源码操作。
- M206 waiting/paused_by_user/dispatch_hold/resumefalse与manual before task逐字段相同，无新授权；本轮只附boundary与4小时retry。旧HAP grant不覆盖M206/GPU1。HRC/PSBR均未准入、无receipt/queue/launch。
- pinned server4 192.168.1.115/dl04-MS-7E06，root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster；SSH keys/strict hostkey，不用旧.137/密码/sudo。原manual source核remote exactHEADf518/assets不变，本轮未重做远端全source核，也未sync。
- localHEAD74f(parent9e)/index空/原28dirty-untracked字节及status由本轮独审实核保持。禁reset/clean/stash/force/autoCommit；新两包在pipeline外置目录，旧两包全部prepared maps/字节保持，不触运行HAP源码。
- M206固定snapshot /data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261022_gpu1_pause_105409/20261021_232736/last.pth；CPU核proof manual_ops/20261022_gpu1_pause_105409/checkpoint_evidence.json SHA8df6674ca8487a97c81363ddef22f215fee94eab4a1d89b5e077db53f39849b6。admitted898ff63与remote f518区别保留，未来专属human grant/source/fullstate核不可借用。

## Open Questions And Risks
- 原crash scannetv2.py430 np.where(boolTensor)→installed _tensor.py1226 self.numpy()报Tensor缺has_torch_function_unary；实际已通过global-helper guard，不能说global不存在。失败样本/原长期worker状态/根因UNKNOWN。
- 04:21:23UTC同conda CPU torch2.8.0+cu128/np1.26.4，fresh1000迭代及4persistentworkers两轮2000合成样本通过，未native失败样本/长期状态复现；不证明修复，不改worker/persistent/np.where/环境。
- HAP数值风险max|Gplus|1308527.125、GGplus幂等误差.114782333保持；finite非条件良好/精确投影/50轮稳定/效果证明，禁ridge/精度/阈值调整。
- HRC internalempty bias传播/重复pool细节丢失未知；原TRAIN2 mean1e-6/coarse→fine-mid依赖probe未跑，必须隔离原hooks/.grad/opt/sched/RNG并finally恢复，smoke峰值含probe非pureTRAIN，pureTRAIN UNKNOWN支持项。
- PSBR仅fork_rng(devices=[])隔离新构造CPU RNG，无manual_seed；实际common初始化/两TRAINbatch指纹/WxWhWo有限梯度更新/非singleton Wh待实测，tanh/轴偏置/串行延迟风险未知，参数delta−262912非资源PASS。offdiagonal/resetstateprobe未实现未测，不新造门槛。
- 两adapter当前只产生raw四结果，无标准smoke/resources语义配对formatter/receipt/queue。真GPU0空闲后先核candidate精确new prep/release/source外锚，再fresh owner/context/pending/goal/当前allowed[0]/原deadline/UUID/双idle/3flocks；旧token/provenance不作新执行lease。
- 未来HRC74f必须实际重新跑原生及资源并据实生成74f标准汇总/receipt；不重标旧9e结果。canonical fresh dispatch仍要求localHEAD==taskcommit，安全同步仅HAP原checkout不再被运行使用时ff-only；本轮不放宽版本guard。
- 超时只读核原stage/request/PID/startticks/argv/result，不重放/kill/删现场/续deadline；跨tick只读不授权旧mutation。普通waiting不占槽，running/claiming/launch-uncertain保守占槽。

## Last Tick
- 本轮37695e94 begin先monitor/已有派发/goal一次：1running HAP/0claiming，M206 waiting用户hold非ready，0新终态/operational issue。唯一due M206只核授权边界无新grant；其他10blocked notdue，旧8/655不重扫。
- UTC12:09真实同HAP28/50 steps1830→1839，资源检查blocked已入HRC/PSBR/current generated_at tick_attempt、1小时retry。独立24项continuation boundary SHA4d114b6db941e1941519959345fe081e8e2118e55106ab806eb5d77c534e7043在HRC迁移前证明原边界，新迁移由下列新报告独立覆盖。
- 新发现旧HRC9e与fresh派发当前HEAD74f不一致；审计2ce6d3c100537c2eb6bb52ef5b93c8c35193fc4ac8c0085418b003e92742109a，root lineage67fd6c758b03f41991b0793af76862808cdb1546eae90949b34b50ddaaa3b3c1。新同源74f包完成/冻结，21独立静态+31独立实际离线全过，旧全部history/maps和28源码保持。
- root新绑定登记SHAf7fd4ffb7350c2254d86dc402750e5acbdc394182a79292e7c1ba775a3392552，完整原9e worker/adapter存在version_binding_history；actual local guard SHAddf0d25004a2c22868418df3234e2975cb65cd10cb12fe62eef5e0031384e881拒绝GPU0registered busy/GPU1notallowed，transport0/无执行binding/manifest/lease。
- canonical decision pipeline/decisions/20261022-202458_other.md已记录本轮forward-binding选择；只更新元数据，0新模型/0模型修订/0Gitcommit/0sync/0候选native/0准入/0queue/0launch/0新终态。HAP继续/GPU1释放/M206暂停/其余ban与Disabled不动，无新增用户确认事项。
- 六段report及finish仍以真实返回/receipt/锁释放确认；释放后不回写。本轮通知只针对已修复的实质后续派发阻断，不把健康在训轮当通知。下一轮先monitor，HRC74f先于PSBR等待实际授权空GPU0，获取真TRAIN2+资源证据后同轮准入派发；无全局穷尽或冷却声明。
'''
        assert len(memory.splitlines()) < 120
        assert memory.count('\n## ') == 7
        write(ROOT/'pipeline/codex_memory.md', memory)
        notes = {
            'actions': [
                '仅cluster_project；actual owner/target一致，前轮9079已FINALIZED/released且无lock/pending才begin。本轮generated UTC12:08:33.052148/原deadline13:08:33.052148不延长。goal/禁用项/原YAML/seed/资源预算/WindowsDisabled不改。',
                'begin仅一次monitor/已有派发/goal：1HAP running、0claiming，M206 waiting用户hold非ready，0新终态或operational issue。唯一due M206实际核无新授权、原pause队列逐字段保持，附当轮边界/4小时retry；旧8hold notdue不重扫655证据。',
                '20:09:19上海 pinned server4/hostname/UUID与HAP PID1063355/start27048767/原fullresume argv/cwd一致，native28/50两次1830→1839/4686，logfresh.336s，GPU0仅HAP19800MiB context。GPU1未查未用，无信号/驱逐/重启/迁移/源码同步；HRC/PSBR resource_check确实blocked并归档。',
                'HAP begin中途Best.5002/noimprove6/10仍低M95.5020/目标.5100，不调参或人工提前终止。原DataLoader根因UNKNOWN，当前健康不证明修复；HAP21799授权已生效不重复问、不借给M206。',
                '实际审出HRC旧9e包与localHEAD74f冲突，canonical fresh dispatch必拒绝。9e→74f仅PSBR9新增，HRC8源/YAML/worker在两commit/current/旧新stage字节完全同；新建外置native/adapter74f包，仅commit/FROZEN/path/hash元数据变化，原函数AST/guard/资源/RNG保持，旧包/旧raw/28dirty不改。',
                '新包实际31离线fixture全通过；另一审阅者独立21静态链/限定全文/AST及31实际fixture全过（0失败/错误/跳过）。root先核独审和精确prep/release/source外锚，更新HRC code_commit/活动prep refs，完整旧9e worker/adapter及旧证据保存version_binding_history；不是模型修订或新结构。',
                'root实际当前owner/context/pending/goal/whitelist/HRC74f candidate guard通过；prepare0在已注册HAP占用处拒绝、prepare1在未授权处拒绝，transport0；无SSH/torch/GPU计算/执行binding/manifest/lease/stage。HAP/M206 queue/running/exp原字节保持，native/resources/pairing NOT_RUN，未生成PASS/receipt/队列。',
                '本轮0新模型/0模型修订/0Gitcommit/0sync/0候选native/0准入/0queue/0launch/0新终态，完成真实后续派发版本阻断修复。新包/独审/激活/guard/决策完整hash已入HRC与memory；按原foreground六段report、finish真实返回/receipt/锁释放验证，不预写PASS。',
                '有实质版本准备进展故简报NOTIFY，无需人类新决定。HRC74f、PSBR均继续等GPU0自然空闲；届时fresh当前外锚/owner/deadline/UUID/idle/locks后跑真TRAIN2双smoke与原资源pair，审实际结果及标准汇总再准入/canonical派发。GPU1给别人，M206无新grant不恢复，不改调度或建立全局穷尽/冷却。',
            ],
            'decisions': [
                'canonical other决策20261022-202458：同HRC源前向绑定当前HEAD74f，保留旧9e全证据与版史；实际新原生/资源仍待GPU0空闲，不以旧结果重标或放宽fresh dispatch版本检查。无需新审批，使用既有experiment_first常规项目操作授权。'
            ]
        }
        write(HERE/'tick_notes.json', notes)
        summary = {'updated_at': datetime.now(timezone.utc).isoformat(), 'token': TOKEN,
                   'memory_lines': len(memory.splitlines()), 'evidence': references,
                   'native_smoke': 'NOT_RUN', 'resources': 'NOT_RUN', 'report_finish': 'PENDING_ACTUAL_CANONICAL_CALLS'}
        write(HERE/'tick_evidence_persistence.json', summary)
        print(json.dumps({'persisted': True, 'memory_lines': summary['memory_lines'], 'decision': ref(decision)}, ensure_ascii=False))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
