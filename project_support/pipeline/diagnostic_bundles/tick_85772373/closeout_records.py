"""Root-only factual progress/tool/resource records, seven-section memory and report notes."""
from pathlib import Path
from datetime import datetime, timezone
import copy,json,sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
SFC='hierarchy-synchronous-full-neighbor-composition'
ELC='hierarchy-undirected-edge-state-line-graph-composition'
WFC='hierarchy-wedge-factor-incidence-composition'
LFT='hierarchy-nonlinear-lifting-analysis-synthesis'
IDS={SFC,ELC,WFC,LFT}

def add(candidate,refs):
    u.check_refs(refs)
    for entry in refs:
        if entry not in candidate['evidence']:candidate['evidence'].append(entry)

def main():
    guard();assert sys.dont_write_bytecode
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    import gpu_occupation
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        baseline=u.read(HERE/'protected_assets_before.json')
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        workpath=ROOT/'pipeline/research_work.json';memorypath=ROOT/'pipeline/codex_memory.md'
        before=sha(workpath);work=u.read(workpath);assert len(work['candidates'])==153
        others={c['id']:u.digest(c) for c in work['candidates'] if c['id'] not in IDS}
        assert len(others)==149 and others=={k:v for k,v in baseline['candidate_digests'].items() if k not in IDS}
        byid={c['id']:c for c in work['candidates']}
        peerpath=HERE/'dual_current_progress_independent_review.json';peer=u.read(peerpath)
        assert peer['owner']==EXPECTED and peer['material_concerns']==[]
        u.check_refs(list(peer['anchors'].values()))
        now=datetime.now(timezone.utc).isoformat();observations={}
        for cid,dirname,filename,pid,start in [(SFC,'sfc_additive_progress_observer','sfc_additive_training_progress_observation.json',3696093,'96568246'),(ELC,'elc_progress_observer','elc_training_progress_observation.json',3786531,'96685141')]:
            path=HERE/dirname/filename;record=u.read(path);obs=record['observation'];c=byid[cid]
            assert record['owner']==EXPECTED and record['returncode']==0 and c['stage']=='training'
            assert obs['identity_before']==obs['identity_after']
            assert obs['identity_before']['pid']==pid and obs['identity_before']['start_ticks']==start
            assert obs['runtime_commit']==u.SOURCE and obs['signals_sent'] is False and obs['checkpoint_body_read'] is False
            a,b=obs['samples'];assert tuple(b['max_native_step'])>tuple(a['max_native_step']) and b['log_size']>a['log_size']
            assert c['code_commit']==('c9be548699cd66bf68badff9ae6198a03eafa142' if cid==SFC else u.SOURCE)
            previous=copy.deepcopy(c.get('current_live_observation'))
            if previous and previous not in c.setdefault('live_observation_history',[]):c['live_observation_history'].append(previous)
            current=dict(recorded_at=now,observed_at=obs['observed_at'],evidence=u.ref(path),independent_review=u.ref(peerpath),original_pid=pid,original_start_ticks=start,original_admitted_source_commit=c['code_commit'],actual_global_checkout_commit=obs['runtime_commit'],native_step_before=a['max_native_step'],native_step_after=b['max_native_step'],precise_native_validation=record['precise_native_validation'],scope='Exact original process/partial validation only. No final efficacy, champion change, resume, source or lifecycle change.')
            c['current_live_observation']=current;c['partial_best_miou']=record['precise_native_validation']['best'];c['global_checkout_commit']=u.SOURCE
            add(c,[u.ref(path),u.ref(peerpath)]);observations[c['experiment_id']]=current
        context=u.read(ROOT/'pipeline/headless/.tick_context.json')
        server=next(s for s in context['queue']['servers'] if s['name']=='server-4');queue=mon.load_queue(str(ROOT))
        occupation=u.ref(HERE/'source_reserve_gpu_occupation.json');raw=u.ref(HERE/'source_reserve_gpu_occupation_raw.json')
        occupied_at=u.read(HERE/'source_reserve_gpu_occupation.json')['observed_at']
        tools={}
        for cid,label in [(WFC,'wfc'),(LFT,'lft')]:
            c=byid[cid];assert c['stage']=='validation' and c['queued'] is False
            registrationpath=HERE/(label+'_tool_registration_result.json');registration=u.read(registrationpath)
            assert registration['owner']==EXPECTED and registration['integration_status']=='LOCAL_REGISTERED_GUARD_INTEGRATION_PASSED_NATIVE_NOT_RUN'
            integration=u.read(HERE/(label+'_registered_guard_integration.json'))
            assert integration['active_binding_created'] is False and integration['remote_transport'] is False
            assert integration['local_registered_slot']=='REFUSED_BUSY'
            activationpath=ROOT/c['native_tool_preparation']['path'];activation=u.read(activationpath)
            assert activation['code_commit']==c['code_commit'] and activation['operational_ready'] is False
            assert activation['native']==activation['resources']=='NOT_RUN'
            assert c['source_parent_commit']==u.SOURCE
            for folder,prep in [(activationpath.parent,activation),(ROOT/Path(c['execution_adapter']['preparation']['path']).parent,u.read(ROOT/c['execution_adapter']['preparation']['path']))]:
                for name,value in prep['prepared_file_hashes'].items():assert sha(folder/name)==value,name
            assert not (HERE/(label+'_execution')).exists()
            refs=[occupation,raw,u.ref(HERE/'source_reserve_gpu_occupation_validation.json'),u.ref(registrationpath),u.ref(HERE/(label+'_registered_guard_integration.json')),c['native_tool_preparation'],c['native_tool_preparation_review'],c['execution_adapter']['preparation'],c['execution_adapter']['release']]
            for key in ('original_draft_preparation','original_draft_independent_review'):
                if key in activation:refs.append(activation[key])
            add(c,refs);c['occupation_evidence']=occupation;c['last_resource_check_at']=occupied_at
            state=gpu_occupation.validated_state(ROOT,context,c,server,queue)
            assert state['busy_gpu_ids']==[0,1] and not state['idle_gpu_ids']
            c['native_status']=c['resource_status']='NOT_RUN_BOTH_ALLOWED_GPUS_OCCUPIED'
            c['updated_at']=now
            tools[c['experiment_id']]=dict(code_commit=c['code_commit'],native_preparation=c['native_tool_preparation'],execution_adapter=c['execution_adapter'],local_registered_guard_passed=True,local_slot_refused_busy=True,active_binding_created=False,native='NOT_RUN',resources='NOT_RUN')
        draftpath=HERE/'lft_native_prepare/preparation.json';draft=u.read(draftpath)
        assert draft['draft_execution_disabled'] and draft['actual_static_check_count']==30
        assert draft['native']==draft['resources']=='NOT_RUN'
        for name,value in draft['prepared_file_hashes'].items():assert sha(draftpath.parent/name)==value,name
        testrefs=[u.ref(draftpath),draft['static_validation'],draft['initial_software_failure'],u.ref(HERE/'lft_native_preparation_independent_review.json'),u.ref(HERE/'lft_registered_guard_integration.json')]
        add(byid[LFT],testrefs)
        prior=copy.deepcopy(work.get('tick_attempt'))
        if prior:work.setdefault('tick_attempt_history',[]).append(prior)
        work['tick_attempt']=dict(tick_started_at=EXPECTED['generated_at'],candidate_id=LFT,kind='implementation_test',result='passed',command=draft['static_check_command'],observation='Thirty actual local software/opaque-callback checks passed after correcting only a missing checker.clone interface; initial failure retained, worker/model/protocol unchanged. LFT real-source-bound static activation/op and actual registered local owner/receipt/source guard integration passed; selected localGPU0 correctly refused busy. No Tensor/autograd/native TRAIN2, common native pairing or resource profiling executed.',evidence=testrefs)
        work['updated_at']=now
        work['next_action']='Monitor original SFC GPU1 and ELC GPU0 first. Both existing source reserves now have reviewed registered static physicalGPU0 native capabilities; neither has an active binding, native/resource PASS, receipt or ready queue entry. At a genuine allowed opening, recheck actual intended main/source compatibility, bind fresh owner/lease/three locks and execute original paired TRAIN2/resources, then admit/queue/dispatch only after real technical PASS. If GPU1 opens first, prepare a separately reviewed actual physical-card selection; never blind sibling ff or resume M206/old holds.'
        assert {c['id']:u.digest(c) for c in work['candidates'] if c['id'] not in IDS}==others
        u.save(HERE/'closeout_record_intent.json',dict(owner=EXPECTED,recorded_at=now,work_before_sha256=before,memory_before_sha256=sha(memorypath),other149_digests=others,scope='Only current original progress and2 existing source/tool/resource records; seven-section memory and final report notes. No lifecycle/source/activebinding/native/receipt/queue/launch.'))
        u.primary_protection(baseline);u.lifecycle_protection(baseline);assert sha(workpath)==before
        u.atomic(workpath,work)
        memory=f'''# Codex Research Memory

## Goal And Phase
- 本轮 owner {EXPECTED['token']}，generated {EXPECTED['generated_at']}，deadline {EXPECTED['deadline_at']}；真实root thread {EXPECTED['thread_id']} 与execution_mode一致。report/finish以该token真实receipt为准，不预签收尾，不延长租约。
- 目标 .5100，冠军M95 .5020，gap .0080；baseline .4894，Phase1 pointfeature→inst_feats→masks，Phase2人工。原YAML/data/pretrain/loss/optimizer/precision/seed1999/50epochs/maxiters70/patience10、10G和所有bans保持。
- 最新GPU1 grant6529和standing2e89有效，仅server4 GPU0/1、每卡1任务；SERVERS19b375，其余新dispatch禁用，Pipeline-cluster_project仍Disabled。不跨项目、不改调度或重复索权。

## Champion And Baseline
- 冠军不变。SFC/ELC早期partial验证不能替代完整效果或新颖性结论。M222-AOC正常earlystop30/best .5000720620155334/archive b132ffc4；M223-FCB首个已观测TRAIN前消失，根因/best UNKNOWN、stopped_unknown/archive be33748f；原证据保持，不恢复。
- 上轮34f4e385已真实FINALIZED/context_committed/released；其新增WFC/LFT2源码原型和WFC隔离94属于历史，本轮不重算新候选。更早a6e82f44的8诊断臂/两准入两启动、68d6c0e3 INCOMPLETE历史不补签。

## Active Hypotheses
- M224-SFC：原三层forest节点全邻居mean→共享cell/GELU，OLDstate同步组件直径D轮→原3skip/HCG/CSORT/单inst。原sourceC9/receipt d77a、GPU1原PID3696093/start96568246保持。
- 12:11:04→07Z严格原身份/source/YAML/UUID核验，TRAIN[5,4620]→[5,4626]且log增长；原生validation4次，partial best .4253402352333069/noimprove0。本轮source8与deployedYAML77e保持；global18e只加原ELC9A，不能重标SFC历史code。
- M225-ELC：原边持久状态initialize→OTHER-incident OLDedge mean/cell同步treeD−1轮→incidentmean→原skip/HCG/单inst。原source18e/receipt386e、GPU0原PID3786531/start96685141保持。
- 同期ELC TRAIN[5,1670]→[5,1675]且log增长；原生validation4次，partial best .4419926106929779/noimprove0。两观察由dual_current_progress_independent_review 53c7绑定，均是部分训练结果，效果/稳定性未知。
- M226-WFC：真实不同邻居无序对三元因子[中心,两端和]→共享Linear/GELU→等权incidence回节点，原3LN/3skip/HCG/CSORT/单inst。旧原型6595/协议cc9a/隔离source94(parent18e)/proof7699保持，degree²成本与端点和alias未知。
- WFC本轮formal静态activation07a0/op30d3、独审9684，exact静态release bf2a与candidate外锚已真实注册，本地实际guard校验owner/技术receipt/HEAD/source通过且正确拒绝busyGPU0。没有active manifest/lease/远端请求或原生结果；旧af6d DRAFT原件不改。
- M227-LFT：四共享P/U非线性分析→两detail+coarse→原3FFN各一次packed2D→反序合成→原skip，保原3FFN+3LNcommon。原型1210/协议60d07保持；本轮单次隔离exact9A source5931(parent18e)/proof9203，原型NULL元数据不改，main/runtime未提升。
- LFT草案a87的30新软件检查和独审5fe8通过，首次checker缺clone失败完整保留；仅测试载体接口修正，worker/model/protocol不改，不算模型revision/native失败。本轮activation01f7/opaae0/独审7d17、exactrelease8340与外锚已注册，本地实际guard通过并拒绝busyGPU0。

## Closed Or Failed Directions
- PES TRAIN5/529 clip_grad_norm参数枚举ValueError根因UNKNOWN，归档/partial .4211保持；APF/HPC/CTS/BFC旧negative/unknown不重开、不借SFC/ELC声称修复。
- 旧10holds、已尽PCE2+extra1/RSTR2、已消费HAP旧grant均保持；M206 waiting/user_paused/noPID/dispatch_hold。GPU1授权不自动恢复旧任务、FCB或改变参数/门槛。

## Running And Queue
- 原SFC GPU1和ELC GPU0继续受保护；本轮严格native步增仅证明观察时活跃。最新物理占用 {occupied_at}，固定两UUID及原两PID均在，canonical raw parser复算busy[0,1]/idle[]；不驱逐、共享、迁移、信号或重派。
- 153总候选，2training+2validation源码储备，ready waiting0；唯一waiting M206有用户hold。本轮新增候选0/revision0，1个LFT本地隔离sourcecommit、2套静态工具登记、本地guard集成2；native诊断0/admission0/新正式launch0。
- 主线/远端runtime18e保持；WFC94与LFT5931是同父18e的兄弟隔离版本。任一真实提升后另一工具因HEAD/runtime前置会拒绝，届时保原9源不变另存真实兼容版本；禁止兄弟盲ff或覆盖原源/原receipt。

## Open Questions And Risks
- WFC/LFT真实Torch/CUDA/autograd/自然TRAIN2/common配对/全模型FLOPs/原100次timing/显存均NOT_RUN；CPU软件、静态release及本地guard不代签native/resource/效力/新颖性PASS。两原型保validation，不是已准入waiting。
- 两套新工具当前只能选physicalGPU0，live授权仍0/1；若GPU1先空闲，另冻结实际物理卡操作适配，不改模型/协议或扩大资源。未来fresh owner/deadline/context、实际空闲/双观察、三锁、真实source/assets均须通过；不复用旧绑定或盲重放。
- 仅whole新core原loss聚合finite/nonzero梯度及真实整体更新为新训练性门；单map/node/row/column/bias零合法。LFT旧FFN更新不能代替新P/Ucore；不加FP32守恒/可逆/Jacobian/强制覆盖/latency门，wholemodel预算/原15%显存条件不改。

## Last Tick
- 本轮先observe/dispatch，再按reserve2/creation0续做两既有ID，未新开路线。完成LFT源码保存、真实本地软件检查/保留测试载体失败、两套静态activation/op独审和root登记/真实本地guard；因两原训练占卡，原生检查等待合法真实空槽。
- baseline8bf6保护main18e/index/28用户文件/34生命周期；其他149候选及所有原receipt/archive保持。当前近端事实/工具注册/占用/软件测试已绑定候选；六段report随后由canonical脚本生成，finish结论以真实receipt为准，不在释放后补写。
- 下轮先看原SFC/ELC和卡占用；如GPU0真实空闲且main兼容，可用已注册defaultNOP launcher显式prepare/stage/run四原检查臂，按实际结果评审，通过才当轮准入/队列/派发。GPU1先空闲则同轮先做必要受审卡适配；不恢复M206/旧holds，不为每个常规操作重复索权。
'''
        assert len(memory.splitlines())<120
        notes={'actions':['12:11:04→07Z核实两原训练严格步增：SFC[5,4620]→[5,4626]、partial best .4253402352333069；ELC[5,1670]→[5,1675]、partial best .4419926106929779。原PID/start/source/YAML/UUID不变，无异常，独审53c7；不是最终训练结果。','本轮creation预算0，续做WFC/LFT两现有validation储备，未新造候选。LFT冻结9源单次保存为5931(parent18e)本地隔离版本，原型1210的NULL元数据不改，main/runtime仍18e。','LFT原生草案30项实际CPU/opaque/AST检查及独审通过；首个checker缺clone失败和原source/worker/proto hash完整保留，仅测试载体接口修复，不算模型修订或原生失败。','WFC与LFT两套独立静态activation/op/默认NOP launcher经外审后，root各真实创建exact静态release并登记外锚；实际本地guard核过当前owner/授权/ELC技术receipt/HEAD/source，均正确拒绝busyGPU0，NoTransport禁止所有远端调用。没有active manifest/lease/request/native或资源测量结果。','最新物理查询 '+occupied_at+' 核实固定GPU0/1均由原两PID占用；raw log绑定本轮token/context/白名单，canonical validated_state对两候选均复算busy[0,1]/idle[]。本轮native0、admission0、queue0、新正式launch0。'], 'decisions':['冠军M95 .5020、目标 .5100/gap .0080保持。两早期partial指标不用于宣称效力、替换冠军或科学拒绝；WFC/LFT未训练、效力/新颖性未知。','静态工具准备及本地guard通过只说明目前可安全接续检查的局部能力；真实自然TRAIN2/动态common配对/whole新core原loss聚合梯度与真实更新/原资源完整口径仍需空卡执行，不加数值、可逆性、强制覆盖或latency门。','两工具当前选physicalGPU0，授权边界仍GPU0/1每卡1任务。GPU1先空闲时另冻结受审卡适配；WFC94/LFT5931是同父兄弟，任一提升后另一必须按真实main保存兼容同源版本，不盲ff。','原SFC/ELC不停止或重派，M206用户pause与旧holds/科学负结果保持，不改调度/参数/资源边界、不新增逐变体审批。本轮按实际记录report/finish，不预签postflight。']}
        u.atomic(memorypath,memory,text=True);u.save(HERE/'final_report_notes.json',notes)
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        assert {c['id']:u.digest(c) for c in u.read(workpath)['candidates'] if c['id'] not in IDS}==others
        u.save(HERE/'closeout_record_result.json',dict(owner=EXPECTED,recorded_at=datetime.now(timezone.utc).isoformat(),work_sha256=sha(workpath),memory_sha256=sha(memorypath),memory_lines=len(memory.splitlines()),other149_unchanged=True,primary_index_user28_all34_lifecycle_unchanged=True,candidate_count=153,new_candidates=0,new_model_revisions=0,new_isolated_source_commits=1,static_tool_registrations=2,native_diagnostic_arms=0,new_admissions=0,new_formal_launches=0,observations=observations,tools=tools,physical_observation=occupation,tick_attempt=work['tick_attempt'],notes=u.ref(HERE/'final_report_notes.json')))
        print(json.dumps(dict(result=u.ref(HERE/'closeout_record_result.json'),memory_lines=len(memory.splitlines()),source_reserves=2,ready_waiting=0,native=0,admissions=0,launches=0)))
    finally:lock.close()

if __name__=='__main__':main()
