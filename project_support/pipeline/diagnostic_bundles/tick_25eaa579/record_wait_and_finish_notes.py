"""Record a routine healthy run and actual current resource wait, no new design."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
DCE='hierarchy-directed-cavity-edge-composition';PES='hierarchy-palindromic-euler-state-composition'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--peer-sha256');ap.add_argument('--occupation');a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_RECORD_MUTATION');return
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b);u.lifecycle_protection(b)
    obs=HERE/'dce_progress_observer/dce_training_progress_observation.json';assert sha(obs)=='79b674ccecb5fe31933e4523c41499c28df92a5179f9694518d39515f1948ef5'
    ob=u.read(obs);assert ob['owner']==EXPECTED and ob['returncode']==0 and ob['observation']['runtime_commit']==u.SOURCE and ob['observation']['signals_sent'] is False
    samples=ob['observation']['samples'];values=ob['precise_native_validation'];assert samples[-1]['last_native_step']>samples[0]['last_native_step']
    assert len(values['values'])==26 and values['best']==0.4971300959587097 and values['no_improve']==9
    peer=HERE/'current_wait_independent_review.json';assert sha(peer)==a.peer_sha256
    review=u.read(peer);assert review['material_concerns']==[]
    occupation=(ROOT/a.occupation).resolve();assert occupation.is_relative_to((ROOT/'pipeline/checks').resolve())
    proof=u.read(occupation);assert proof['token']==EXPECTED['token'] and proof['snapshot_sha256']==EXPECTED['context_sha256'] and proof['complete'] is True
    assert proof['candidate_ids']==[PES] and proof['scope']['allowed_gpus']==[0]
    assert 0 <= (datetime.now(timezone.utc)-datetime.fromisoformat(proof['observed_at'])).total_seconds()<240
    assert proof['queries']['hostname']['stdout'].strip()=='dl04-MS-7E06' and all(x['rc']==0 for x in proof['queries'].values())
    assert '1327826' in [x.split(',')[-1].strip() for x in proof['queries']['compute']['stdout'].splitlines()]
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b);u.lifecycle_protection(b)
        path=ROOT/'pipeline/research_work.json';before=sha(path);w=u.read(path);old={c['id']:u.digest(c) for c in w['candidates']};assert len(old)==148
        assert w['tick_attempt']['candidate_id']==PES and w['tick_attempt']['kind']=='resource_check' and w['tick_attempt']['result']=='blocked'
        d=next(c for c in w['candidates'] if c['id']==DCE);p=next(c for c in w['candidates'] if c['id']==PES)
        assert d['stage']=='training' and d['code_commit']==u.SOURCE and p['stage']=='blocked'
        now=datetime.now(timezone.utc).isoformat();stamp=samples[-1]['observed_at'];last=samples[-1]['last_native_step']
        d['current_live_observation']={'recorded_at':now,'evidence':u.ref(obs),'independent_review':u.ref(peer),'original_pid':1327826,'original_start_ticks':81524190,'native_step_before':samples[0]['last_native_step'],'native_step_after':last,'precise_native_validation':copy.deepcopy(values),'scope':'Routine healthy original native training progress; incomplete training, no new champion, completion, failure, native diagnostic or launch.'}
        p['current_resource_check']={'recorded_at':proof['observed_at'],'result':'Original_DCE_GPU0_compute_process_confirmed_busy','evidence':u.ref(occupation),'original_progress_evidence':u.ref(obs),'scope':'Fresh canonical physicalGPU0 occupation only; no native smoke or model resource profile PASS.'}
        for c in (d,p):
            for r in (u.ref(obs),u.ref(peer)):
                if r not in c['evidence']:c['evidence'].append(r)
        w['updated_at']=now;w['last_event_tick']=EXPECTED['generated_at']
        assert all(u.digest(c)==old[c['id']] for c in w['candidates'] if c['id'] not in (DCE,PES))
        memory=(ROOT/'pipeline/codex_memory.md').read_text('utf8');parts=memory.split('\n## ');sections={}
        for part in parts[1:]:name,body=part.split('\n',1);sections[name]=body
        assert len(sections)==7
        goal=sections['Goal And Phase'].strip().splitlines();assert len(goal)==2
        goal[0]=f'- 当前25eaa579 generated{EXPECTED["generated_at"]}/deadline{EXPECTED["deadline_at"]}原值；Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。'
        sections['Goal And Phase']='\n'.join(goal)+'\n\n'
        champion=sections['Champion And Baseline'].strip().splitlines();champion[0]=f'- 项目最佳仍M95 .5020；DCE已打印26次原生val，精确序列{values["values"]}，best{values["best"]}/noimprove9；训练未完成，非新champion。';sections['Champion And Baseline']='\n'.join(champion)+'\n\n'
        sections['Active Hypotheses']=sections['Active Hypotheses'].replace('新AOC native9cf931','AOC已备native9cf931')
        sections['Closed Or Failed Directions']=sections['Closed Or Failed Directions'].replace('旧10hold本轮current_wait独审仅元数据digest比对','旧10hold在ec5轮current_wait仅元数据digest比对')
        sections['Running And Queue']=f'''- 唯一正式训练DCE GPU0：UTC{stamp} TRAIN27/50 2584→2589/4686，原PID1327826/start81524190/source-runtime5c、部署YAML与GPU0context保持；前26val/partialbest/noimprove见上，正常推进。
- PES source9c仍blocked exclusive_gpu_slot/resumevalidation；当前token25e canonical physicalGPU0 proof原DCE计算PID在场，busy[0]/idle[]，无PES原生/资源profile/准入/新启动，GPU1不用。
- AOC0314/native9cf/op e45与条件父9c关系保持；当前主线仍5c、PES技术receipt未产生，上轮root已实测本地拒绝/transport0，本轮不重复同一guard或旧软件suite。先PES，后兼容AOC；若父未提升或main变动保留原件另做实际兼容版本，禁盲ff。

'''
        sections['Last Tick']='''- 本轮仅原DCE只读运行和fresh GPU0占用核对，148ID不变；0新候选/0模型修订/0源版本/0原生TRAIN或资源profile/0准入/0启动。已有PES+AOC等待条件未变，不为额度新增M223或复制无信息增益工具。
- 当前真实resource_check blocked绑定PES与本轮owner/context；这不是资源profile PASS。旧carrier/WIPTrue/时点审计原件全部保留，未重测或改历史边界。
- 主线/runtime5c、24生命周期账、28用户路径/index保持。完整六段报告/finish由root执行；实际完成以原token receipt为准，不预签。正常运行/无人工事项，通知静默。
'''
        memory=parts[0]+''.join('\n## '+name+'\n'+sections[name] for name in sections);assert len(memory.splitlines())<120
        notes={'actions':[f'UTC{stamp}原DCE健康运行，第27/50轮2584→2589/4686；原PID/start/source/runtime/YAML/GPU0 context保持，26次原生验证best0.4971300959587097/noimprove9，训练未完整结束。','当前PES及AOC源/静态工具与条件父版本边界未变：PES等待GPU0，AOC尚需PES技术通过并正式提升兼容父。未重复旧38/16/33/84或本地parent guard，也未新造候选/包。','fresh canonical physicalGPU0占用实际含原DCE计算PID，busy[0]/idle[]；本轮resource_check blocked真实绑定PES/current owner/context，无GPU1、native、资源profile、入队或新启动。'],'decisions':['原DCE继续自然训练，只有实际结束后才考虑GPU0上的下一实验，不干预既有任务。项目冠军仍M95 .5020，目标.5100；partial DCE不是新champion或新机制有效结论。','先PES后AOC；资源及条件未满足时保留已有准备，不为额度扩张M223/新版本/工具副本，不增加审批或科学门。0新候选、修订、源版本、原生检查、准入和启动。','旧暂停/耗尽/失败证据与GPU1禁用、资源/禁用项/调度保持。当前仅健康进行中且无人工事项，按heartbeat规则静默，不把一次常规检查当成实质成果通知。']}
        u.save(HERE/'final_records_intent.json',{'owner':EXPECTED,'recorded_at':now,'research_work_sha256':before,'scope':'Routine original progress/resource-wait references, seven-section memory and report notes only; no completion/native or efficacy claim.'})
        guard();assert sha(path)==before;u.atomic(path,w);u.atomic(ROOT/'pipeline/codex_memory.md',memory,text=True);u.save(HERE/'report_notes.json',notes)
        u.primary_protection(b);u.lifecycle_protection(b)
        u.save(HERE/'final_records_result.json',{'owner':EXPECTED,'status':'ROUTINE_WAIT_RECORDED_POSTFLIGHT_NOT_YET_RUN','candidate_count':148,'new_candidates':0,'model_revisions':0,'source_versions':0,'native_smokes_or_profiles':0,'admissions':0,'launches':0,'primary_index28_and24_lifecycle_preserved':True,'memory_lines':len(memory.splitlines()),'occupation':u.ref(occupation),'current_progress':u.ref(obs),'independent_review':u.ref(peer)})
        print('Routine healthy progress and actual GPU0 wait recorded; no substantive new result or user action.')
    finally:lock.close()

if __name__=='__main__':main()
