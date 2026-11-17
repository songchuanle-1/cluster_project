"""Root-only routine evidence refresh; no native/tool/source/queue changes."""
from pathlib import Path
from datetime import datetime, timezone
import copy,json,sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
SFC='hierarchy-synchronous-full-neighbor-composition'
ELC='hierarchy-undirected-edge-state-line-graph-composition'
WFC='hierarchy-wedge-factor-incidence-composition'
LFT='hierarchy-nonlinear-lifting-analysis-synthesis'
IDS={SFC,ELC,WFC,LFT}

def add(c,refs):
    u.check_refs(refs)
    for r in refs:
        if r not in c['evidence']:c['evidence'].append(r)

def main():
    guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    import gpu_occupation
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        baseline=u.read(HERE/'protected_assets_before.json');u.primary_protection(baseline);u.lifecycle_protection(baseline)
        path=ROOT/'pipeline/research_work.json';memorypath=ROOT/'pipeline/codex_memory.md'
        before=sha(path);work=u.read(path);assert len(work['candidates'])==153
        byid={c['id']:c for c in work['candidates']}
        others={c['id']:u.digest(c) for c in work['candidates'] if c['id'] not in IDS}
        assert len(others)==149 and others=={k:v for k,v in baseline['candidate_digests'].items() if k not in IDS}
        peerpath=HERE/'routine_observation_independent_review.json';peer=u.read(peerpath)
        assert peer['material_concerns']==[]
        u.check_refs(list(peer['anchors'].values()))
        delta_path=HERE/'resource_context_delta.json';delta=u.read(delta_path);assert delta['owner']==EXPECTED and delta['ownership']=='UNKNOWN';u.check_refs(list(delta['anchors'].values()))
        observations={};now=datetime.now(timezone.utc).isoformat()
        for cid,dirname,name,pid,start in [(SFC,'sfc_phase_progress_observer','sfc_phase_progress_observation.json',3696093,'96568246'),(ELC,'elc_phase_progress_observer','elc_phase_progress_observation.json',3786531,'96685141')]:
            obs_path=HERE/dirname/name;record=u.read(obs_path);obs=record['observation'];c=byid[cid]
            assert record['owner']==EXPECTED and record['returncode']==0 and c['stage']=='training'
            assert obs['identity_before']==obs['identity_after'] and obs['identity_before']['pid']==pid and obs['identity_before']['start_ticks']==start
            assert obs['runtime_commit']==u.SOURCE and obs['signals_sent'] is False and obs['checkpoint_body_read'] is False
            assert obs['strict_native_train_growth'] is True
            a,b=obs['samples'];assert tuple(b['max_native_step'])>tuple(a['max_native_step']) and b['log_size']>a['log_size']
            old=copy.deepcopy(c.get('current_live_observation'))
            if old and old not in c.setdefault('live_observation_history',[]):c['live_observation_history'].append(old)
            c['current_live_observation']=dict(recorded_at=now,observed_at=obs['observed_at'],evidence=u.ref(obs_path),independent_review=u.ref(peerpath),original_pid=pid,original_start_ticks=start,original_admitted_source_commit=c['code_commit'],actual_global_checkout_commit=u.SOURCE,native_step_before=a['max_native_step'],native_step_after=b['max_native_step'],precise_native_validation=record['precise_native_validation'],observed_native_train_growth=obs['strict_native_train_growth'],observed_native_validation_growth=obs['strict_native_validation_growth'],native_validation_step_before=a.get('max_native_validation_step'),native_validation_step_after=b.get('max_native_validation_step'),scope='Routine healthy original training partial only; no final efficacy/champion or process/source/lifecycle change.')
            c['partial_best_miou']=record['precise_native_validation']['best'];add(c,[u.ref(obs_path),u.ref(peerpath),u.ref(HERE/'phase_observers_preparation.json'),u.ref(delta_path)])
            observations[c['experiment_id']]=c['current_live_observation']
        occupation=u.ref(HERE/'source_reserve_gpu_occupation.json');raw=u.ref(HERE/'source_reserve_gpu_occupation_raw.json');validation=u.ref(HERE/'source_reserve_gpu_occupation_validation.json')
        proof=u.read(ROOT/occupation['path']);states=u.read(ROOT/validation['path'])['states']
        assert proof['token']==EXPECTED['token'] and proof['snapshot_sha256']==EXPECTED['context_sha256']
        assert all(s['state']['busy_gpu_ids']==[0,1] and not s['state']['idle_gpu_ids'] for s in states)
        for cid in (WFC,LFT):
            c=byid[cid];assert c['stage']=='validation' and c['queued'] is False
            add(c,[occupation,raw,validation,u.ref(peerpath),u.ref(delta_path)])
            c['occupation_evidence']=occupation;c['last_resource_check_at']=proof['observed_at']
            c['native_status']=c['resource_status']='NOT_RUN_BOTH_ALLOWED_GPUS_OCCUPIED'
        byid[LFT]['next_action']=byid[LFT]['next_action'].replace('main18e/source94','main18e/source5931')
        previous=copy.deepcopy(work.get('tick_attempt'))
        if previous:work.setdefault('tick_attempt_history',[]).append(previous)
        work['tick_attempt']=dict(tick_started_at=EXPECTED['generated_at'],candidate_id=WFC,kind='resource_check',result='blocked',command=proof['command'],observation='Actual pinned hostname, both fixed physicalGPU UUIDs and all compute PIDs observed; canonical validated_state recomputed busy0+1/idle[]. Protected original SFC/ELC continue. Existing two source reserves/tools unchanged; no native TRAIN2/resource profiling or new scientific conclusion.',evidence=[occupation,raw,validation,u.ref(peerpath),u.ref(delta_path)])
        work['updated_at']=now
        work['next_action']='Routine healthy original SFC/ELC still occupy both allowed cards. Preserve existing WFC/LFT reviewed registered static tools and validation reserves; no creation budget or runnable queue. Recheck actual source compatibility/occupation at the next real authorized opening and execute existing native checks, then admit/queue only on actual PASS. No new design/tool revision, held recovery or global policy change.'
        u.save(HERE/'routine_record_intent.json',dict(owner=EXPECTED,work_before_sha256=before,memory_before_sha256=sha(memorypath),other149_digests=others,scope='Only routine original progress and dated resource wait evidence. No tools/code/receipts/queue/launch or historical gate changes.'))
        assert sha(path)==before and {c['id']:u.digest(c) for c in work['candidates'] if c['id'] not in IDS}==others
        u.primary_protection(baseline);u.lifecycle_protection(baseline);u.atomic(path,work)
        sf=observations['M224-SFC'];ef=observations['M225-ELC']
        old=memorypath.read_text(encoding='utf-8')
        names=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick']
        def section(name):return old.split('## '+name+'\n',1)[1].split('\n## ',1)[0].strip()
        active=section('Active Hypotheses').replace('WFC前轮formal','WFC既有formal').replace('前轮单次隔离exact9A','工具准备轮的单次隔离exact9A').replace('前轮activation','既有activation')
        lines=[]
        for line in active.splitlines():
            if '严格原身份/source/YAML/UUID核验，SFC TRAIN' in line:
                line=f"- {sf['observed_at']} 严格原身份/source/YAML/UUID核验，SFC TRAIN{sf['native_step_before']}→{sf['native_step_after']}且log增长；原生validation{len(sf['precise_native_validation']['values'])}次，partial best {sf['precise_native_validation']['best']}/noimprove{sf['precise_native_validation']['no_improve']}；global18e只加原ELC9A，SFC历史code仍C9。"
            elif line.startswith('- 同期ELC'):
                line=f"- 同期ELC TRAIN{ef['native_step_before']}→{ef['native_step_after']}且log增长；原生validation{len(ef['precise_native_validation']['values'])}次，partial best {ef['precise_native_validation']['best']}/noimprove{ef['precise_native_validation']['no_improve']}。两者都是健康在训局部进度，未完成、不更换冠军；本轮独审 {sha(peerpath)[:8]}。"
            lines.append(line)
        risk_text='\n'.join(line for line in section('Open Questions And Risks').splitlines() if not line.startswith('- 当前两运行相位观察器'))
        risk_text+=f"\n- 当前两运行相位观察器源见pipeline/diagnostic_bundles/tick_{EXPECTED['token'][:8]}/下sfc_phase_progress_observer与elc_phase_progress_observer；今后复用需复制到新tick并绑定新owner，不重放旧owner。分别记录实际TRAIN/VAL flags，rc0本身不证明TRAIN增长。仅VAL时按相位记录，不作新launch或native-smoke TRAIN过关。"
        sections={
        'Goal And Phase':f"- 本轮owner {EXPECTED['token']}，generated {EXPECTED['generated_at']}，deadline {EXPECTED['deadline_at']}；真实root thread {EXPECTED['thread_id']}与execution_mode一致。收尾结果以真实receipt为准，不延长租约。\n- 目标 .5100，冠军M95 .5020，gap .0080；baseline .4894。Phase1固定原YAML/data/pretrain/loss/optimizer/precision/seed1999/50epochs/maxiters70/patience10、10G/bans/验证边界，Phase2人工。\n- 最新资源grant6529/standing2e89有效，仅server4 GPU0/1每卡1任务；SERVERS19b375，其余新dispatch禁用，Pipeline-cluster_project仍Disabled，不改调度/授权边界。",
        'Champion And Baseline':"- 冠军不变；SFC/ELC早期partial不替代完整效果/新颖性结论。M222-AOC正常earlystop30/best .5000720620155334/archive b132ffc4；M223-FCB stopped_unknown/archive be33748f，根因/best UNKNOWN，原证据不改、不恢复。\n- 上轮ad0af359已真实FINALIZED/context_committed/released。工具准备轮85772373的LFT隔离source5931及两套静态工具登记属于历史，本轮不重算新成果。34f4e385的两原型/WFC94、a6e82f44的两准入启动和68d6c0e3 INCOMPLETE历史保持。",
        'Active Hypotheses':'\n'.join(lines),
        'Closed Or Failed Directions':section('Closed Or Failed Directions'),
        'Running And Queue':f"- 原SFC GPU1/PID3696093与ELC GPU0/PID3786531持续受保护；本轮严格原生步增。物理查询 {proof['observed_at']} 核实两固定UUID与原两PID，canonical raw parser/validated_state复算busy[0,1]/idle[]，不驱逐、信号、共享、迁移或重派。\n- 总153候选，2training+2validation储备，ready waiting0，唯一waiting M206有用户hold；本轮新候选/模型revision/sourcecommit/工具登记/native/admission/正式launch均0。\n- main/runtime18e保持，WFC94和LFT5931是18e兄弟隔离版本，未来任一真实提升后另一必须另存真实兼容同源版本，不盲ff。当前两个静态工具仅physicalGPU0能力，授权仍0/1；GPU1先空闲须另做实际受审卡适配。",
        'Open Questions And Risks':risk_text+'\n- 本轮NVML在GPU1另见PID293251（上轮未见）；其任务/归属/启动时间UNKNOWN。原SFC真实步增且未见故障证据，不声称卡独占，也未查询/干预额外context。资源仍busy，不新增GPU任务或自动暂停原运行。',
        'Last Tick':"- 本轮是例行健康/资源复查：先observe/dispatch，实际无新终态、无就绪队列、reserve2/creation0。两原训练局部指标随训练推进，未完成、无新的科学结论。WFC/LFT已具备既有静态工具，未重复编译/旧suite/改模型或制造新候选。\n- tick_attempt是真实resource_check/blocked，当前token/context/白名单/原始NVML查询与校验结果同时绑定WFC及LFT；stagevalidation保留，不冒充原生PASS/已准入waiting或用户权限缺失。source字段、两工具及旧冻结包不改。\n- baseline300e35ef保护main/index/28用户文件/34生命周期，其他149候选与原receipt/archive保持。七段memory和六段report依实际结果留档；finish是否通过以真实receipt为准，不释放后补写。\n- 无需用户操作，healthy/inprogress且两卡仍busy，按通知策略静默；后续真实空槽到来时核源码/owner/三锁，使用已有检查工具完成原生TRAIN2/资源，通过后当轮准入入队派发。不恢复M206/旧holds、不改调度或反复索权。"}
        memory='# Codex Research Memory\n\n'+'\n\n'.join('## '+name+'\n'+sections[name] for name in names)+'\n'
        assert len(memory.splitlines())<120
        notes={'actions':[f"本轮{sf['observed_at']}核实原SFC TRAIN{sf['native_step_before']}→{sf['native_step_after']}、部分best {sf['precise_native_validation']['best']}；原ELC TRAIN{ef['native_step_before']}→{ef['native_step_after']}、部分best {ef['precise_native_validation']['best']}。原PID/start/source/YAML/UUID、两日志增长和观测尾部无异常均核，未读checkpoint体。",'实际物理查询 '+proof['observed_at']+' 核实GPU0/1仍由原两训练占用；原始hostname/NVML inventory/compute PID及canonical validated_state结果绑定本轮owner/context和两储备候选，busy[0,1]/idle[]。','预算reserve2/creation0；已备WFC/LFT静态工具保持，未重复旧suite/改实验源码/新候选/原生检查/准入/正式启动。仅更新例行部分进度和资源证据，原冻结包/科学状态保持。'],'decisions':['本轮健康在训/资源等待，未完成、无新科学结论或用户动作；依通知策略静默。冠军M95 .5020/目标 .5100保持，部分指标随原训练推进不用于替换冠军或宣称效力。','现有两储备保validation，native/resources NOT_RUN；下一合法真实空槽先核实际source兼容/授权/owner/三锁，执行既有原生YAML TRAIN2和完整资源检查，通过才准入入队。不开新路线填额度，不重开旧holds或暂停任务，不更改资源/参数/调度。']}
        notes['actions'].append('复用两套已审运行相位观察器，源字节与前轮相同；本轮两原任务实际TRAIN增长且VAL flags为false，不能以rc0或VAL代证TRAIN。未改模型、native-smoke/新launch TRAIN门或既有静态工具。')
        notes['actions'].append('GPU1原始NVML本轮另见PID293251（相较上轮查询新增context）；归属/任务/启动时间UNKNOWN，原SFC仍实际步增。未查询/干预它，不声称只有原两PID或独占；双卡busy、无新增可行动事项结论保持。')
        u.atomic(memorypath,memory,text=True);u.save(HERE/'final_report_notes.json',notes)
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        assert {c['id']:u.digest(c) for c in u.read(path)['candidates'] if c['id'] not in IDS}==others
        u.save(HERE/'routine_record_result.json',dict(owner=EXPECTED,work_after_sha256=sha(path),memory_sha256=sha(memorypath),memory_lines=len(memory.splitlines()),other149_unchanged=True,primary_index_user28_all34_lifecycle_unchanged=True,observations=observations,resource_evidence=[occupation,raw,validation,u.ref(delta_path)],additional_compute_contexts=delta['additional_compute_contexts'],tick_attempt=work['tick_attempt'],new_candidates=0,new_model_revisions=0,native=0,admissions=0,launches=0,notification='ROUTINE_HEALTHY_DONT_NOTIFY'))
        print(json.dumps({'result':u.ref(HERE/'routine_record_result.json'),'memory_lines':len(memory.splitlines()),'routine_healthy':True,'resource_wait':True,'new_action':False}))
    finally:lock.close()

if __name__=='__main__':main()
