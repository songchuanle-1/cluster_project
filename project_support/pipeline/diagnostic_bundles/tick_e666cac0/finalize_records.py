"""Persist honest bounded outcomes before canonical report/postflight."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
DCE='hierarchy-directed-cavity-edge-composition';PES='hierarchy-palindromic-euler-state-composition'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--promotion-peer-sha256');ap.add_argument('--occupation');a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_RECORDS_MUTATION');return
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b);u.lifecycle_protection(b)
    obs=HERE/'dce_progress_observer_final/dce_training_progress_observation.json';assert sha(obs)=='6b45ea3d9bb6fac06fd9ff18dcfb6dba8c695592759b67912cd4651633b633b2'
    ob=u.read(obs);assert ob['owner']==EXPECTED and ob['returncode']==0 and ob['observation']['runtime_commit']==u.SOURCE and ob['observation']['signals_sent'] is False
    samples=ob['observation']['samples'];assert samples[-1]['last_native_step']==[6,4686] and samples[-1]['log_size']>samples[0]['log_size']
    values=ob['precise_native_validation'];assert len(values['values'])==5 and values['best']==0.44330915808677673
    promo=HERE/'pes_promotion_prepare/preparation.json';assert sha(promo)=='dc3dc5898937ef21ddd2b8eaedece6bbcaa4cd33cb6aa5622203fca7a2a6e761'
    pr=u.read(promo);assert pr['prepared_for_owner']==EXPECTED and pr['draft_execution_disabled'] is True
    assert all(pr[k] is None for k in ('actual_independent_review','actual_four_result_review','actual_raw_results'))
    for n,h in pr['prepared_file_hashes'].items():
        f=(promo.parent/n).resolve();assert f.is_relative_to(promo.parent) and sha(f)==h,n
    peer=HERE/'pes_promotion_static_independent_review.json';assert sha(peer)==a.promotion_peer_sha256
    review=u.read(peer);assert review['candidate_id']==PES and review['material_concerns']==[]
    assert u.ref(promo) in review['anchors'].values()
    occupation=(ROOT/a.occupation).resolve();assert occupation.is_relative_to((ROOT/'pipeline/checks').resolve())
    proof=u.read(occupation);assert proof['token']==EXPECTED['token'] and proof['snapshot_sha256']==EXPECTED['context_sha256'] and proof['complete'] is True
    assert proof['candidate_ids']==[PES] and proof['scope']['allowed_gpus']==[0]
    assert 0 <= (datetime.now(timezone.utc)-datetime.fromisoformat(proof['observed_at'])).total_seconds()<240
    queries=proof['queries'];assert queries['hostname']['stdout'].strip()=='dl04-MS-7E06'
    assert '1327826' in [x.split(',')[-1].strip() for x in queries['compute']['stdout'].splitlines()]
    assert all(q['rc']==0 for q in queries.values())
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b);u.lifecycle_protection(b)
        path=ROOT/'pipeline/research_work.json';before=sha(path);w=u.read(path);old={c['id']:u.digest(c) for c in w['candidates']};assert len(old)==148
        assert w['tick_attempt']['candidate_id']==PES and w['tick_attempt']['kind']=='resource_check' and w['tick_attempt']['result']=='blocked'
        now=datetime.now(timezone.utc).isoformat();d=next(c for c in w['candidates'] if c['id']==DCE);p=next(c for c in w['candidates'] if c['id']==PES)
        assert d['stage']=='training' and d['code_commit']==u.SOURCE and p['stage']=='blocked'
        d['current_live_observation']={'recorded_at':now,'evidence':u.ref(obs),'earlier_native_step_growth':u.ref(HERE/'dce_progress_observer/dce_training_progress_observation.json'),'original_pid':1327826,'original_start_ticks':81524190,'native_step_before':samples[0]['last_native_step'],'native_step_after':samples[-1]['last_native_step'],'latest_interval_native_step_increased':False,'latest_interval_log_bytes_increased':True,'precise_native_validation':copy.deepcopy(values),'scope':'Latest own native TRAIN step is epoch6/4686; only five validation values have been printed. Earlier this tick TRAIN6/3177→3184 actually increased. Incomplete training, no stop/end or new efficacy claim.'}
        p['promotion_preparation']={'status':'DISABLED_STATIC_SOFTWARE_REVIEWED_NOT_ACTUAL_ADMISSION','preparation':u.ref(promo),'independent_review':u.ref(peer),'actual_raw_results_or_peer_bound':False,'source_version_or_native_or_queue_changed':False,'scope':'Future compatible root copy must bind actual four results and independent actual review under a fresh owner/original deadline. Frozen disabled skeleton is not executable admission or launch evidence.'}
        p['current_resource_check']={'recorded_at':proof['observed_at'],'result':'Original_DCE_GPU0_compute_process_confirmed_busy','evidence':u.ref(occupation),'original_progress_evidence':u.ref(obs),'scope':'Fresh canonical physicalGPU0 occupation only. PES native smoke and resource profiling remain NOT_RUN.'}
        for c,refs in [(d,[u.ref(obs)]),(p,[u.ref(obs),u.ref(promo),u.ref(peer)])]:
            for r in refs:
                if r not in c['evidence']:c['evidence'].append(r)
        w['updated_at']=now;w['last_event_tick']=EXPECTED['generated_at']
        assert all(u.digest(c)==old[c['id']] for c in w['candidates'] if c['id'] not in (DCE,PES))
        memory=f'''# Codex Research Memory

## Goal And Phase
- 当前e666cac0，generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值；Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。
- goal0441/standing2e892/GPU0auth94075/SERVERS2583不变；仅server4物理GPU0/max1，GPU1禁用。原YAML/data/pretrain/loss/optimizer/precision/seed1999/50epochs-maxiters70-patience10/10G口径保持，禁调参/gate/langrouting/大QKV/N²attention/重复inst/旧拒绝改名。

## Champion And Baseline
- 项目最佳仍M95 .5020；DCE原生已打印前5val .3001469075679779/.38952401280403137/.41283756494522095/.4377216398715973/.44330915808677673，best.44330915808677673/noimprove0；未完整训练，不是新champion。
- BEC.5001/24、AEF.495597243309021/23、CRE.4961479902267456/30为历史正常早停。

## Active Hypotheses
- DCE M220原进程1327826/start81524190/source-runtime5c0c211c8ecc9479ecb34dbb8118a95f4b20e391；directed-cavity真三层森林，原4臂/receipt4e2b与原始证据保持。
- PES M221 source9c42fdc4e9168acec18980d782ee9c163e043bb7单父5c，原型0c3e/协议ef7f/NULL原件冻结。Euler闭游+逆游4E真实receiver-state更新，逆游继续state；非逆映射/置换不变/保持早期信息保证。
- PES nativef2fc/op7124/staticrelease090dfa未变、未执行；本轮disabled promotion dc3dc5及静态独审仅未来4实际结果绑定骨架，raw/review/peer仍NULL/DRAFTTrue，无activebinding/manifest/lease或队列。
- AOC M222新增原型f7b85/manifest3a966/协议a04185：共享binary T的两个祖先次序2层diamond差q；fine q，upper直接真实finepath等权mean同q，原3LN/3rawskip/HCG/CSORT/单inst保持。33作者+84独立软件核及27集成核通过，均非Torch/autograd/native/资源PASS。
- AOC code/source/actual-parent仍NULL，只有参考5c；stage implementation。先推进PES，届时以实际兼容currentmain版本化并冻结native工具，禁盲siblingff。APF同祖先输入家族但非同DAG，创新/效力UNKNOWN。

## Closed Or Failed Directions
- APF/e759 crashed TRAIN2/301，唯一val.27984941005706787，公共DataLoader before-forward scatter索引dtype契约错误；原失败scan/dtype/RNG/上游causeUNKNOWN，CPUtoy不是复现/修复；无自动恢复。
- HPC73ba stopped_unknown TRAIN2/3687/唯一val.2810768485069275，causeUNKNOWN。CTS14/.4890 stopped_unknown、BFC20/3832 DataLoader overlap历史保持；不重归档/恢复。
- 旧10冻结边界及PCE2+extra1/RSTR2耗尽不变；M206用户暂停/dispatch_hold/noPID；HAP旧授权已消费，不据空槽重开或要求重复授权。

## Running And Queue
- 唯一正式训练DCE GPU0：本轮先TRAIN6/3177→3184；UTC18:24:07→10最新TRAIN6/4686两次相同但log字节增长，原identity/source/YAML/GPU0context保持；仅前5val已打印，未声称第6次验证结果。
- PES仍blocked exclusive_gpu_slot/resumevalidation；本轮canonical physicalGPU0 proof绑定当前e666 owner/context，原DCE PID在场/busy[0]/idle[]。无PES原生/资源/准入/训练启动，GPU1不用。
- 总148ID；本轮新1AOC软件储备/0模型修订/0原生检查/0准入/0启动。PES+AOC处于不同准备阶段，不把M206暂停或未测原型算就绪队列。

## Open Questions And Risks
- DCE训练早期，PES长链遗忘/串行kernel与真实Torch训练性/资源未知。AOC q可能丢共有语义，T仿射时fine a取消/b=c时q0；属表达性质，不加逐call/row/column/bias正性、FP32或Jacobian门。wholecell原loss梯度/真实更新仍须未来原生实测。
- APF公共loader触发输入未定位，DCE继续不等于已修复；不改数据/环境/公共源码，不挤占DCE/外部任务。资源空后优先PES原paired TRAIN2+完整resources，实过才receipt/安全ff/入队/一步派发/原生步增。

## Last Tick
- 当前观测abc944/6b45；PES promotion dc3dc5保持disabled，AOC sourcepeer28ce与原NULL保存；真实资源占用非resource profilePASS。
- 主线/runtime5c、24生命周期账、28用户路径及index保持。完整六段报告与finish由root执行，实际收尾以原token receipt为准，不预签完成。
'''
        assert len(memory.splitlines())<120
        notes={'actions':['截至上海10月29日02:24，原DCE进程/源码/部署YAML和GPU0 context保持；本轮早先第6轮3177→3184，最新第6轮4686训练步已到末端，仅五次验证已打印，best0.44330915808677673。','优先补齐PES通过原生检查后的disabled promotion静态工具；9项小软件核与独立静态审查完成，实际四结果/实际peer仍NULL，未原生、未准入、未改训练队列。','新增M222-AOC精确8模型源+原YAML原型：两个祖先顺序的共享非线性组合取差，再沿原真实fine路径上收集；33作者软件核、84独立软件核及27集成核通过，Torch/native/autograd/resources尚未运行，code/source/actual-parentNULL。','本轮fresh canonical GPU0占用实际看到原DCE计算PID；PES原生检查继续等待。未使用GPU1，未停止/恢复任何既有任务，主线/24账/28用户字节和index保持。'],'decisions':['项目最佳仍M95 0.5020，目标0.5100；DCE尚未完整训练，不比较早期指标宣称收益或机制被否定。','先推进已有PES，GPU0自然释放且fresh owner/原deadline/实际source-assets-idle-三锁复核允许后，在原生YAML上执行paired两步TRAIN与原resources；实过当轮准入派发并核原生步增长。','AOC属于祖先组合家族内的不同计算图，效果/新颖性未知；仿射fine项取消、相同祖先零差和共有信息丢失为真实风险，不新增数值门或重采样。原型版本化/原生工具留待PES结果与届时兼容主线确定；不为额度继续造候选。','本轮无新训练完成、无新准入或启动，不改资源/禁用项/调度，不自动恢复APF/HPC/M206或旧耗尽路线；无需用户另行授权。']}
        u.save(HERE/'final_records_intent.json',{'owner':EXPECTED,'recorded_at':now,'research_work_sha256':before,'protected_ledgers':b['protected_ledgers'],'scope':'DCE final read-only progress, disabled PES preparation evidence, seven-section memory and report notes only. No lifecycle/source/index/training changes; finish result not claimed.'})
        guard();assert sha(path)==before;u.atomic(path,w);u.atomic(ROOT/'pipeline/codex_memory.md',memory,text=True);u.save(HERE/'report_notes.json',notes)
        u.primary_protection(b);u.lifecycle_protection(b)
        u.save(HERE/'final_records_result.json',{'owner':EXPECTED,'status':'MEMORY_AND_NOTES_SAVED_POSTFLIGHT_NOT_YET_RUN','candidate_count':148,'new_candidates':1,'native_smokes_or_profiles':0,'admissions':0,'launches':0,'source_model_revisions':0,'primary_index28_and24_lifecycle_preserved':True,'memory_lines':len(memory.splitlines()),'occupation':u.ref(occupation),'latest_progress':u.ref(obs),'pes_promotion':u.ref(promo),'pes_promotion_review':u.ref(peer)})
        print('Honest final evidence/memory/notes saved; postflight not yet run.')
    finally:lock.close()

if __name__=='__main__':main()
