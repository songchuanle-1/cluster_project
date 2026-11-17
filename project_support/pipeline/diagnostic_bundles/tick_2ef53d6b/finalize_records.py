"""Save this tick's source/static preparation and real resource disposition."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
DCE='hierarchy-directed-cavity-edge-composition';PES='hierarchy-palindromic-euler-state-composition';AOC='hierarchy-ancestral-order-commutator-composition'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--occupation');a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_RECORDS_MUTATION');return
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b);u.lifecycle_protection(b)
    latest=HERE/'dce_progress_observer_final/dce_training_progress_observation.json';ob=u.read(latest)
    initial=HERE/'dce_progress_observer/dce_training_progress_observation.json';start=u.read(initial)
    assert sha(initial)=='872ea028c6f5bf6faf2259957e5c3e702542beb35f21ad245272588cc1040bf5'
    assert ob['owner']==EXPECTED and ob['returncode']==0 and ob['observation']['runtime_commit']==u.SOURCE and ob['observation']['signals_sent'] is False
    samples=ob['observation']['samples'];values=ob['precise_native_validation'];firstvals=start['precise_native_validation']['values']
    assert values['values'][:len(firstvals)]==firstvals and samples[-1]['last_native_step']>=start['observation']['samples'][-1]['last_native_step']
    local=HERE/'aoc_local_parent_guard_observation.json';check=u.read(local)
    assert check['owner']==EXPECTED and check['status']=='EXPECTED_UNPROMOTED_PARENT_LOCAL_REFUSAL' and check['transport_calls']==0
    occupation=(ROOT/a.occupation).resolve();assert occupation.is_relative_to((ROOT/'pipeline/checks').resolve())
    proof=u.read(occupation);assert proof['token']==EXPECTED['token'] and proof['snapshot_sha256']==EXPECTED['context_sha256'] and proof['complete'] is True
    assert proof['candidate_ids']==[PES] and proof['scope']['allowed_gpus']==[0]
    assert 0 <= (datetime.now(timezone.utc)-datetime.fromisoformat(proof['observed_at'])).total_seconds()<240
    assert proof['queries']['hostname']['stdout'].strip()=='dl04-MS-7E06' and all(x['rc']==0 for x in proof['queries'].values())
    assert '1327826' in [x.split(',')[-1].strip() for x in proof['queries']['compute']['stdout'].splitlines()]
    held=HERE/'held_boundary_observation.json';assert sha(held)=='30f663ea49a378b1098795d010496a1a5791c1ae5b214a24621876effcdd506c'
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b);u.lifecycle_protection(b)
        path=ROOT/'pipeline/research_work.json';before=sha(path);w=u.read(path);old={c['id']:u.digest(c) for c in w['candidates']};assert len(old)==148
        assert w['tick_attempt']['candidate_id']==PES and w['tick_attempt']['kind']=='resource_check' and w['tick_attempt']['result']=='blocked'
        d=next(c for c in w['candidates'] if c['id']==DCE);p=next(c for c in w['candidates'] if c['id']==PES);c=next(c for c in w['candidates'] if c['id']==AOC)
        assert d['stage']=='training' and d['code_commit']==u.SOURCE and p['stage']=='blocked'
        assert c['stage']=='validation' and c['code_commit']=='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
        assert c['source_parent_commit']=='9c42fdc4e9168acec18980d782ee9c163e043bb7' and c['native_execution_code_commit'] is None and c['queued'] is False
        now=datetime.now(timezone.utc).isoformat();last=samples[-1]['last_native_step'];span_increased=samples[-1]['last_native_step']>samples[0]['last_native_step']
        d['current_live_observation']={'recorded_at':now,'evidence':u.ref(latest),'earlier_native_step_growth':u.ref(initial),'original_pid':1327826,'original_start_ticks':81524190,'native_step_before':samples[0]['last_native_step'],'native_step_after':last,'latest_interval_native_step_increased':span_increased,'latest_interval_log_bytes_increased':samples[-1]['log_size']>samples[0]['log_size'],'precise_native_validation':copy.deepcopy(values),'scope':'Only actual original native logger/process/source observations. Earlier this tick TRAIN9/4067→4074 increased. Incomplete training; current interval growth is recorded literally, not inferred from PID.'}
        p['current_resource_check']={'recorded_at':proof['observed_at'],'result':'Original_DCE_GPU0_compute_process_confirmed_busy','evidence':u.ref(occupation),'original_progress_evidence':u.ref(latest),'scope':'Fresh canonical physicalGPU0 occupation only; PES native smoke and resource profiling remain NOT_RUN.'}
        c['current_local_guard_observation']=u.ref(local)
        for candidate,refs in [(d,[u.ref(latest)]),(p,[u.ref(latest)]),(c,[u.ref(local)])]:
            for r in refs:
                if r not in candidate['evidence']:candidate['evidence'].append(r)
        w['updated_at']=now;w['last_event_tick']=EXPECTED['generated_at']
        assert all(u.digest(x)==old[x['id']] for x in w['candidates'] if x['id'] not in (DCE,PES,AOC))
        stamp=samples[-1]['observed_at'];best=values['best'];count=len(values['values']);native_ref=c['worker_preparation']['preparation'];op_ref=c['execution_adapter']['preparation']
        memory=f'''# Codex Research Memory

## Goal And Phase
- 当前2ef53d6b generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值；Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。
- goal0441/standing2e892/GPU0auth94075/SERVERS2583不变；仅server4物理GPU0/max1，GPU1禁用。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50-maxiters70-patience10/10G口径保持，禁调参/gate/langrouting/大QKV/N²attention/重复inst/旧拒绝改名。

## Champion And Baseline
- 项目最佳仍M95 .5020；DCE原生已打印{count}次val，精确序列{values['values']}，best{best}/noimprove{values['no_improve']}；未完整训练，不是新champion。
- BEC.5001/24、AEF.495597243309021/23、CRE.4961479902267456/30为历史正常早停。

## Active Hypotheses
- DCE M220原1327826/start81524190/source-runtime5c0c211c8ecc9479ecb34dbb8118a95f4b20e391；原4臂/receipt4e2b/原失败证据保持。
- PES M221 source9c42fdc4e9168acec18980d782ee9c163e043bb7单父5c，原型0c3e/协议ef7f/NULL原件冻结。Euler闭游+逆游4E真实receiver-state更新；nativef2fc/op7124/release090未执行，promotion dc3dc5仍disabled/actualraw-peerNULL。
- AOC M222同原f7b85精确9源已实际另存0314b932a92a8cc7f67804068ecb1c1f7a5f2e33单父PES9c；proof83d8/sourcepeerc11c。原f7 NULL/ref5c原件不回填，模型无字节修订；当前主线/runtime仍5c，未ff18A。
- AOC祖先两顺序sharedbinary2层diamond差q，fine q、upper直接finepath等权mean同q，原3LN/rawskip/HCG/CSORT/单inst保持。旧33作者+84独立/27集成核保留，不重跑或当nativePASS。
- 新AOC native9cf931（38软件核、37map/12diag）及op {op_ref['sha256'][:12]}已冻结静态独审；expectedparent/runtime9c，正式DRAFTFalse/10activeNULL。没有activebinding/manifest/lease/transport、Torch/TRAIN/profile。op mutation先验实际本地主线9c与PES技术receipt原smoke+4gates/decisionhash，read-only核对能力保留，无PES训练完成/涨点门。

## Closed Or Failed Directions
- APF/e759 crashed TRAIN2/301/唯一val.27984941005706787，公共DataLoader before-forward scatter索引dtype契约错误，原失败scan/dtype/RNG/上游causeUNKNOWN；CPUtoy不是复现/修复，无自动恢复。
- HPC73ba stopped_unknown TRAIN2/3687/唯一val.2810768485069275，causeUNKNOWN；CTS14/.4890及BFC20/3832 overlap历史保持，不重归档/恢复。
- 本轮旧10hold仅30f663元数据digest比对，边界未变/无新action或授权；M206用户暂停/dispatch_hold/noPID，PCE2+extra1/RSTR2已尽、HAP旧授权消费，不据空槽重开。

## Running And Queue
- 唯一正式训练DCE GPU0：本轮先TRAIN9/4067→4074，最新UTC{stamp} TRAIN{last[0]}/50 {last[1]}/4686；最新3秒步增={span_increased}按实际记录，原identity/source/YAML/GPU0context保持，精确partial验证见上。
- PES仍blocked exclusive_gpu_slot/resumevalidation；当前canonical token2ef proof原DCE计算PID在场，busy[0]/idle[]，无PES原生/资源/准入/新启动，GPU1不用。
- AOC stagevalidation/实际source0314/静态条件工具；当前primary5c的root实际mutation guard已本地拒绝，transport0，无active执行产物。先PES真实技术通过并正式提升9c；若PES不提升或main改父则保留全部原件，另存相同九源的真实兼容版本，禁止跨兄弟或5c→0314盲ff。

## Open Questions And Risks
- DCE训练未完；PES长链遗忘/串行kernel及真实训练性资源未知。AOC q可丢共有语义、T仿射fine a取消/b=c零差；不增逐call/row/column/bias正性、FP32或Jacobian门，wholecell原loss梯度/真实更新未来原生实测。
- APF公共loader触发输入仍未定位，DCE继续不是故障已修复；不改数据/环境/公共代码，不挤占DCE/外部任务。GPU0自然释放后优先PES原paired TRAIN2+完整resources，实过才receipt/安全ff/入队/一步派发/原生步增。

## Last Tick
- 148ID不变；本轮0新候选/0模型修订，新增1真实AOC条件源版本及静态native-op能力，0原生TRAIN/资源实测/准入/启动。未为额度新增M223。
- 旧carrier失败/WIPTrue与首次source审时点误比原件留档，均非模型或假设被否定；实际源码保存before=after workhash与随后DCE/PES进度登记时点链由独审核实。
- 主线/runtime5c、24生命周期账、28用户路径及index保持；完整六段报告/finish由root执行，实际完成以原token receipt为准，不预签。
'''
        assert len(memory.splitlines())<120
        notes={'actions':[f'截至UTC{stamp}，原DCE进程/源码/YAML/GPU0 context保持；最新第{last[0]}/50轮{last[1]}/4686，已打印{count}次验证，partial best={best}。本轮开始时真实TRAIN9/4067→4074递增，最新短区间是否步增按原样记录。','优先推进已有AOC：原f7b85九源码不改，另存真实隔离0314单父PES9c，primary/runtime5c不提升，保留原NULL/ref5c。实际Git对象/字节/单父和24账/28用户/index经独审。','完成AOC native38软件核与条件op静态独审；正式DRAFTFalse但10执行字段NULL，无activebinding/manifest/lease、Torch/native/profile。mutation需要实际parent9c与PES技术receipt，当前primary5c实测本地拒绝、零transport；read-only观察能力保持。','旧10due hold仅元数据digest小核，边界未变，无新授权或人工事项。fresh canonical GPU0占用原DCE计算PID仍在，PES继续等待，无GPU1/停止/恢复/调度变更。'],'decisions':['项目最佳仍M95 .5020，目标.5100；DCE训练未完，不把早期验证作为收益或失败结论。','先PES、后AOC。GPU0自然释放且fresh owner/原deadline/实际source-assets-idle-三锁允许后，PES使用原YAML执行paired两步TRAIN与完整resources；实际通过当轮准入、派发并核步数增长。','AOC0314只是以PES9c为父的条件源版本，不证明PES通过或可从5c直接提升18A。若PES未提升/main变动，保留全部原件并制作相同九源的真实兼容版本；不增PES训练完成或准确率门，不自动恢复旧任务。','本轮0新候选/模型修订/原生检查/准入/启动，已有PES+AOC继续准备，不为额度另造M223；常规操作沿用现有授权，无需用户再次确认。']}
        u.save(HERE/'final_records_intent.json',{'owner':EXPECTED,'recorded_at':now,'research_work_sha256':before,'protected_ledgers':b['protected_ledgers'],'occupation':u.ref(occupation),'scope':'Final original progress, source/static evidence references, memory and notes only. Postflight completion not yet claimed.'})
        guard();assert sha(path)==before;u.atomic(path,w);u.atomic(ROOT/'pipeline/codex_memory.md',memory,text=True);u.save(HERE/'report_notes.json',notes)
        u.primary_protection(b);u.lifecycle_protection(b)
        u.save(HERE/'final_records_result.json',{'owner':EXPECTED,'status':'MEMORY_AND_NOTES_SAVED_POSTFLIGHT_NOT_YET_RUN','candidate_count':148,'new_candidates':0,'source_versions':1,'native_smokes_or_profiles':0,'admissions':0,'launches':0,'source_model_revisions':0,'primary_index28_and24_lifecycle_preserved':True,'memory_lines':len(memory.splitlines()),'occupation':u.ref(occupation),'latest_progress':u.ref(latest),'local_guard':u.ref(local),'native_preparation':native_ref,'operational_preparation':op_ref})
        print(json.dumps({'status':'Honest records saved; postflight not yet run','latest_native_step':last,'validation_count':count,'partial_best':best,'latest_observed_at':stamp}))
    finally:lock.close()

if __name__=='__main__':main()
