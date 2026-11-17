"""Record one actual PES launch and its tested source; no training control."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent;CODE=ROOT/'Cluster'
PES='hierarchy-palindromic-euler-state-composition';AOC='hierarchy-ancestral-order-commutator-composition'
SOURCE='9c42fdc4e9168acec18980d782ee9c163e043bb7'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');a=ap.parse_args()
    if not a.execute_root:print('DEFAULT_NO_RECORD_MUTATION');return
    guard();b=u.read(HERE/'protected_assets_before.json');ff=u.read(HERE/'pes_root_ff_result.json');assert ff['HEAD']==SOURCE and ff['only_nine_tested_additions'] is True
    paths=ff['source_paths'];assert len(paths)==9
    index=Path(u.git(CODE,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else CODE/index
    index_hash=sha(index)
    def protect_source():
        guard();assert u.git(CODE,'rev-parse','HEAD').decode().strip()==SOURCE
        assert u.git(CODE,'status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex']
        assert not u.git(CODE,'diff','--cached','--name-only','-z') and sha(index)==index_hash
        assert all(sha(CODE/n)==h for n,h in b['files'].items()) and all(sha(CODE/n)==h for n,h in paths.items())
    protect_source()
    assert sha(ROOT/'pipeline/admissions/M221-PES.json')=='6fcee3f5bbfb865b9902ff04e0b019c464f8911c600906de07577608a930f2b1'
    assert sha(ROOT/'pipeline/admissions/M220-DCE.json')=='4e2b30199b272f7898172aea88411ee12d9f280732cc4dd821d028a60dd3236f'
    peer=HERE/'pes_launch_independent_review.json';assert sha(peer)=='204b6b2b80d8c4179571c7040032b4653e2cb5330b5ee57cb7c5212420bb93cd' and u.read(peer)['material_concerns']==[]
    progress=HERE/'pes_progress_observer/pes_training_progress_observation.json';assert sha(progress)=='c1f725ebc36141158b0d37a5ce542e6aacfb02fc092ab85f81e1648adbde34d0'
    ob=u.read(progress);assert ob['owner']==EXPECTED and ob['returncode']==0
    samples=ob['observation']['samples'];assert samples[0]['last_native_step']==[1,210] and samples[-1]['last_native_step']==[1,215]
    assert samples[-1]['log_size']>samples[0]['log_size'] and ob['observation']['runtime_commit']==SOURCE
    assert all(ob['precise_native_validation'][k] is None for k in ('values','best','no_improve'))
    parent=HERE/'aoc_parent_ready_local_observation.json';assert sha(parent)=='217d87beef77826d22845f471a37b138de77cc6c0c55d7e696f972d73cf61efe'
    assert u.read(parent)['status']=='ACTUAL_PARENT_PROMOTION_LOCAL_GUARD_PASSED_NOT_GPU_IDLE' and u.read(parent)['transport_calls']==0
    dispatch=u.read(HERE/'pes_dispatch_result.json');assert dispatch['canonical_dispatch_invoked_once'] is True and dispatch['verified_native_progress'] is True
    assert dispatch['task_after']['pid']==2265073 and dispatch['task_after']['launch_verified'] is True
    assert u.read(HERE/'dce_finalize_result.json')['state']=='done_earlystop'
    assert u.read(HERE/'dce_finalize_result.json')['archive_id']=='a5a9de2153724a968a91316b8438701f'
    names=list(dict.fromkeys([*b['protected_ledgers'],'admissions/M221-PES.json','experiments/M221-PES.json']))
    ledgers={n:sha(ROOT/'pipeline'/n) for n in names}
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        protect_source();assert all(sha(ROOT/'pipeline'/n)==h for n,h in ledgers.items())
        workpath=ROOT/'pipeline/research_work.json';before=sha(workpath);w=u.read(workpath);old={c['id']:u.digest(c) for c in w['candidates']};assert len(old)==148
        p=next(c for c in w['candidates'] if c['id']==PES);c=next(c for c in w['candidates'] if c['id']==AOC)
        assert p['stage']=='training' and p['code_commit']==SOURCE and c['stage']=='validation' and c['code_commit']=='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
        q=mon.load_queue(str(ROOT));tasks=[t for rows in q['gpu_queues'].values() for t in rows]
        live=next(t for t in tasks if t.get('id')=='M221-PES');paused=next(t for t in tasks if t.get('id')=='M206-CGCA')
        assert live['status']=='running' and live['pid']==2265073 and live['launch_verification']=='training_progress' and str(live['gpu'])=='0'
        assert paused['status']=='waiting' and paused['dispatch_hold'] and paused.get('pid') is None
        assert mon.load_running(str(ROOT))['server-4']['0']=='M221-PES'
        now=datetime.now(timezone.utc).isoformat()
        p['current_live_observation']={'recorded_at':now,'evidence':u.ref(progress),'independent_review':u.ref(peer),'original_pid':2265073,'original_start_ticks':88396735,'native_step_before':[1,210],'native_step_after':[1,215],'precise_native_validation':copy.deepcopy(ob['precise_native_validation']),'scope':'Actual new original formal PES native progress. Validation values/best/no-improve are None because none printed; technical admission is not efficacy.'}
        p['current_resource_check']={'recorded_at':now,'result':'original_PES_formal_training_confirmed_on_authorized_GPU0','evidence':u.ref(progress),'scope':'Original admitted process/context/source and step growth; no GPU1, second launch or pureTRAIN memory claim.'}
        p['next_action']='Monitor the exact original PES2265073/start88396735/log/source9c on server4 GPU0 through natural completion. Do not replay stale dispatch_phase progress_pending: actual launch_verified/training_progress and strict original step growth are already proved. GPU1 prohibited; no resume/restart or other old task recovery.'
        p['source_status']='EXACT_TESTED_PES_PRESENT_PRIMARY_AND_VERIFIED_REMOTE_RUNTIME'
        for r in [u.ref(progress),u.ref(peer),u.ref(HERE/'pes_original_process_identity.json')]:
            if r not in p['evidence']:p['evidence'].append(r)
        c.setdefault('version_compatibility_history',[]).append(copy.deepcopy(c.get('current_version_compatibility')))
        c['current_version_compatibility']={'recorded_at':now,'current_source_commit':c['code_commit'],'current_parent_commit':SOURCE,'runtime_expected_commit':SOURCE,'current_primary_and_runtime':SOURCE,'status':'ACTUAL_TESTED_PARENT_PROMOTED_LOCAL_GUARD_PASSED_GPU0_OCCUPIED_BY_PES','PES_technical_receipt':u.ref(ROOT/'pipeline/admissions/M221-PES.json'),'local_parent_guard':u.ref(parent),'physical_occupation_scope':u.ref(progress),'scope':'Only source-parent/technical-receipt readiness changed. AOC native/resources remain NOT_RUN. No claim that GPU0 is idle; preserve current PES. Future main changes still require actual compatible source checks.'}
        c['native_status']='NOT_RUN_GPU0_OCCUPIED_BY_ORIGINAL_PES';c['resource_status']='NOT_RUN_GPU0_OCCUPIED_BY_ORIGINAL_PES'
        c['next_action']='PES technical9c parent is now genuinely promoted and current local parent guard passes without transport. Wait for original PES GPU0 task to end naturally; then fresh owner/original deadline/current source9c/runtime/UUID/assets/idle/three-lock checks may run the original AOC0314 paired natural TRAIN2/resources. No AOC native PASS/admission/queue yet, no GPU1 or sibling ff.'
        if u.ref(parent) not in c['evidence']:c['evidence'].append(u.ref(parent))
        w['updated_at']=now;w['last_event_tick']=EXPECTED['generated_at'];w['next_action']=p['next_action']
        smoke=u.read(HERE/'pes_native_smoke.json')
        w['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':PES,'kind':'native_smoke','result':'passed','command':smoke['command'],'observation':'Actual original matched two natural TRAIN steps, finite backward and whole-cell updates plus original paired resources independently reviewed; one actual admission/dispatch and strict formal native growth verified. Efficacy and pureTRAIN memory UNKNOWN.','evidence':[u.ref(HERE/'pes_native_smoke.json')]}
        assert all(u.digest(x)==old[x['id']] for x in w['candidates'] if x['id'] not in (PES,AOC))
        memory=f'''# Codex Research Memory

## Goal And Phase
- 当前14fea205 generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值；Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。
- goal0441/standing2e892/GPU0auth94075/SERVERS2583不变；仅server4物理GPU0/max1，GPU1禁用。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50-maxiters70-patience10/10G口径及bans保持。

## Champion And Baseline
- 项目最佳仍M95 .5020；DCE正常earlystop27/50，27val exactbest.4971300959587097/noimprove10，低M95 .0048699040412903，注册单seed此实现无增益，非全hierarchy假设被否定。
- PES新正式训练尚无验证值/best/noimprove，均None非0；BEC.5001/24、AEF.495597243309021/23、CRE.4961479902267456/30历史正常早停保持。

## Active Hypotheses
- 当前唯一正式训练M221-PES：source/primary/runtime9c42fdc4e9168acec18980d782ee9c163e043bb7，原型0c3e/协议ef7f/原NULL冻结。真实Euler+inverse4E receiver-only persistentcurrentstate、逆游不reset，原3LN/rawskip/HCG/CSORT/单inst保持；novelty/efficacy UNKNOWN。
- 当前tick actual manifestd7ee/lease4a1d，原nativef2fc/op7124/release090一次prepare-stage与四arms均terminal0。两自然TRAIN batches/common835/155907386/hash5c80一致；candidate2loss9.176618576049805/13.907245635986328、wholecell实际原loss梯度与weight/module每步更新；4E/currentstate语义独审2b71。
- PES resources9.758338124G vs M95 9.762532428G，median45.457764994353056 vs33.915601030457765ms（+34.0320%），P9049.52625324949622 vs37.252200150396675（+32.9485%），alloc930981888 vs936763392（−.61718%），原+15%条件false。原unsupported完整保留，未声称更快/纯TRAIN峰值；准确率未知。
- 原disabled promotion1c787/e666 dc3不改；本轮actualpeer绑定active206e/summary2fed/smoke6a9/resources3fd/constraints315，exacttested9A localff+safe remote sync9c；receipt6fcee3f5、onecanonicaldispatch ae160、onePopen/15pinnedcalls，非PID冒充启动。
- AOC0314b932a92a8cc7f67804068ecb1c1f7a5f2e33单父9c；原f7 NULL/ref5c与proof83d/c11保留，模型无修订。native9cf/op e45/release630十active仍NULL无AOC native/profile/queue。父9c与真实PES技术receipt现已满足，root本地guard217d passes/transport0；GPU0被原PES占用，待其自然结束再原AOC paired TRAIN2/resources，不增新门或盲siblingff。

## Closed Or Failed Directions
- DCE原1327826已消失、完整原日志36289362B/hashf3b59/soleexplicit earlystop27/noimp10、无exception；source5c/receipt4e2b/原技术与launch证据保持。canonical archivea5a9de2153724a968a91316b8438701f/resultf1e1，不能重归档/自动重启；首次liveobserver PID断言失败9fd是观察失败非模型失败。
- APF/e759原DataLoader before-forward dtype crash；HPC73ba stopped_unknown/CTS14/BFC overlap及触发样本RNG/上游causeUNKNOWN保持。旧10hold不重开；M206用户暂停/dispatch_hold/noPID，PCE2+extra1/RSTR2已尽/HAP旧授权消费，无GPU0迁移或旧自动恢复。

## Running And Queue
- 唯一原PES PID2265073/start88396735，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pes_20261029_175027.log；UTC09:52:48→51 TRAIN1/50 210→215/4686，strict native/log growth proofc1f725/source9c8+YAML77e/GPU0context保持，尚无val。launch peer204b。
- queue launch_verifiedtrue/training_progress，但dispatch_phase仍progress_pending旧字段；真实已启动且增长，绝不可重放dispatch。M206waiting是user_paused，不算ready；AOC未入队/未测原生，GPU1不用。

## Open Questions And Risks
- PES长链遗忘/串行kernel与最终收益未知；实测慢约34%已诚实保留，非新latency硬门。AOC q丢共有语义/仿射fine项取消/b=c零差风险保留，不增逐call/row/column/bias正性、FP32/Jacobian门；onlywholecell原lossaggregate与真实更新门。
- APF公共loader触发输入未定位，后续检查/训练成功不等于已修复。数据/环境/公共代码与旧失败/授权不动，不挤占其他任务。

## Last Tick
- 本轮DCE正常归档1，PES真实smoke M95/candidate各2步+原resources各1臂（共4arm）通过，真实准入1/新正式启动1并步增；0新候选/0模型修订/0新commit，148ID保持。
- 实际测试版本已main/runtime9c；28用户字节/status保持/indexempty。当前26生命周期文件已记录post_pes_launch_baseline.json（含HEAD9c/新indexhash/PES精确9source/current148digests），未来新tick setup要以此真实新版本接管，不再用5c旧baseline或旧DCE observer；PES新observer2fabd4可复制到新tick嵌套目录复用fresh anchor。
- AOC仅父版本就绪localguard/evidence更新，无native执行；完整六段报告与finish由root完成，实际完成以原token receipt为准，不预签。
'''
        assert len(memory.splitlines())<120
        notes={'actions':['DCE原任务在第27/50轮按原patience10正常早停，exactbest0.4971300959587097低于M95 .5020；完整ownlog/PIDabsence/独审后canonical归档一次a5a9，保留原receipt及全部技术证据，没有信号/重启。','GPU0真实空闲且原三锁可用后，PES original prepare/stage和四arms实际执行terminal0；两自然TRAIN/common初始化真实配对、新路径4E-currentstate及wholecell原loss梯度/更新通过独审。','PES同口径资源9.758338124G、allocated下降约.617%；median/P90分别约+34.032%/+32.949%，诚实记录更慢，无新latency门。原FLOPs<=10G/15%显存条件通过，unsupported完整、pureTRAIN峰值和效果未知。','仅exacttested9A primaryff和safe remote sync9c，经真实receipt6fce准入一次，canonical GPU0派发一次/唯一Popen。原PES2265073/start88396735/log/source9c已实测TRAIN1/210→215，不以PID代替进度。GPU1不用、M206用户暂停保持。','AOC实际父9c/PES技术receipt现在已就绪，root本地guard通过/transport0；这不表示GPU0空闲或AOC原生通过，AOC继续等待原PES自然结束。'],'decisions':['本次“继续推送任务”已落实为M221-PES正式运行GPU0；原数据/seed1999/YAML/50-maxiters70/precision等保持，不修改调度或资源边界。','DCE本注册单seed实现没有超过M95，不宣称整个层级特征研究无效或新冠军；PES尚无验证指标，效果仍未知。','PES已有strict原生增长，queue旧progress_pending字段不能用作重复启动理由。保持原PID/log/receipt/source继续监控；AOC不抢占、不用GPU1、不自动恢复旧任务。','保护28用户字节/indexempty及其他生命周期；版本已真实前进到9c，接管基线/源map据post_pes_launch_baseline，未来fresh tick用PES observer与真实原PID/start/log，不回退5c。无需用户重复授权。']}
        u.save(HERE/'final_records_intent.json',{'owner':EXPECTED,'recorded_at':now,'research_work_sha256':before,'protected_post_launch_ledgers':ledgers,'changed_candidate_ids':[PES,AOC],'scope':'Only actual PES progress and actual AOC parent-readiness references, memory and report notes; no additional queue/source/compute/launch, no postflight PASS claim.'})
        guard();assert sha(workpath)==before;u.atomic(workpath,w);u.atomic(ROOT/'pipeline/codex_memory.md',memory,text=True);u.save(HERE/'report_notes.json',notes)
        protect_source();assert all(sha(ROOT/'pipeline'/n)==h for n,h in ledgers.items())
        baseline={'owner':EXPECTED,'recorded_at':now,'head':SOURCE,'files':b['files'],'status_hex':b['status_hex'],'index_empty':True,'index_sha256':index_hash,'protected_ledgers':ledgers,'candidate_digests':{x['id']:u.digest(x) for x in w['candidates']},'current_candidate_source_paths':paths,'exact_tested_nine_source_paths':paths,'research_work_sha256':sha(workpath),'native_progress':u.ref(progress),'source_ff':u.ref(HERE/'pes_root_ff_result.json')}
        u.save(HERE/'post_pes_launch_baseline.json',baseline)
        u.save(HERE/'final_records_result.json',{'owner':EXPECTED,'status':'ACTUAL_ARCHIVE_ADMISSION_LAUNCH_MEMORY_SAVED_POSTFLIGHT_NOT_YET_RUN','candidate_count':148,'new_candidates':0,'model_revisions':0,'new_commits':0,'terminal_archives':1,'native_arms':4,'admissions':1,'formal_launches':1,'native_progress':u.ref(progress),'AOC_parent_readiness':u.ref(parent),'post_launch_baseline':u.ref(HERE/'post_pes_launch_baseline.json'),'memory_lines':len(memory.splitlines()),'current_primary_runtime_commit':SOURCE,'user28_bytes_and_indexempty_preserved':True,'post_launch_lifecycle_files_unchanged':len(ledgers)})
        print(json.dumps({'status':'Actual PES push recorded; postflight not yet run','PID':2265073,'TRAIN':[1,215],'validation':None,'head':SOURCE,'post_launch_ledger_count':len(ledgers),'baseline':u.ref(HERE/'post_pes_launch_baseline.json')}))
    finally:lock.close()

if __name__=='__main__':main()
