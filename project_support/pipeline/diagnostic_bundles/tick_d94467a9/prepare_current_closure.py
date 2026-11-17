"""Finalize current evidence/memory/notes under the same real foreground lease."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import sys,json,copy,csv,io,hashlib
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
CID='hierarchy-nonlinear-lifting-analysis-synthesis'
COMMIT='4457a46f9075f61e83340aa0f0af87d5bf4e986c'

def main():
    if sys.argv[1:]!=['--execute-root']:print('DEFAULT_NOP');return
    guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();base=u.read(HERE/'protected_assets_before.json');fresh=u.read(HERE/'lft_before_admission_lifecycle.json')
        q=u.read(ROOT/'pipeline/queue.json');r=u.read(ROOT/'pipeline/running.json');w=u.read(ROOT/'pipeline/research_work.json')
        old=copy.deepcopy(w);target=next(c for c in w['candidates'] if c['id']==CID)
        tasks=q['gpu_queues']['server-4'];lft=next(t for t in tasks if t['id']=='M227-LFT');wfc=next(t for t in tasks if t['id']=='M226-WFC');held=next(t for t in tasks if t['id']=='M206-CGCA')
        assert lft['status']==wfc['status']=='running' and lft['launch_verified'] is wfc['launch_verified'] is True
        assert lft['pid']==2685912 and wfc['pid']==2085005 and str(lft['gpu'])=='1' and str(wfc['gpu'])=='0'
        assert lft['code_commit']==COMMIT and wfc['code_commit']==base['head'] and held['status']=='waiting' and held.get('dispatch_hold') and not held.get('pid')
        code=ROOT/'Cluster'
        assert u.git(code,'rev-parse','HEAD').decode().strip()==COMMIT
        assert u.git(code,'status','--porcelain=v1','--untracked-files=all','-z').hex()==base['status_hex'] and not u.git(code,'diff','--cached','--name-only','-z')
        assert all(sha(code/p)==h for p,h in base['files'].items())
        for ff in [ROOT/'pipeline/diagnostic_bundles/tick_9bb5908b/wfc_root_ff_result.json',HERE/'lft_root_ff_result.json']:
            assert all(sha(code/p)==h for p,h in u.read(ff)['source_paths'].items())
        assert all(sha(ROOT/'pipeline'/p)==h for p,h in fresh['protected_ledgers'].items() if p not in ('queue.json','running.json','experiments.csv'))
        norm=copy.deepcopy(q)
        for rows in norm['gpu_queues'].values():rows[:]=[x for x in rows if x.get('id')!='M227-LFT']
        assert norm==fresh['queue']
        assert [row for row in csv.DictReader(io.StringIO((ROOT/'pipeline/experiments.csv').read_text('utf-8-sig'))) if row.get('id')!='M227-LFT']==fresh['csv_rows']
        assert len(w['candidates'])==155 and all(u.digest(c)==fresh['candidate_digests'][c['id']] for c in w['candidates'] if c['id']!=CID)
        obsfile=HERE/'dual_original_run_observer/original_both_phase_observation.json';assert sha(obsfile)=='c51572580596f28820b7afb6feaec8900e4888d4a29cb357c2b5865cccfa0b22'
        obs=u.read(obsfile);assert obs['returncode']==0 and obs['observation']['runtime_commit']==COMMIT
        entries=obs['observation']['observations'];assert all(x['strict_native_train_growth'] is True for x in entries)
        refs=[u.ref(HERE/n) for n in ['lft_consumer_activation.json','lft_activation_and_standards_independent_review.json','lft_root_ff_result.json','lft_prior_WFC_source_preservation.json','lft_admission_queue_result.json','lft_dispatch_result.json','lft_original_process_binding.json','lft_original_identity_collection.json','dual_original_run_observer_independent_review.json','lft_launch_and_progress_independent_review.json']]+[u.ref(obsfile)]
        assert sha(HERE/'lft_launch_and_progress_independent_review.json')=='fb7a7460d6341b9d6a9c930f0ef27bc613cfaaf0c1174537863ca22f06aa8c42'
        peer=u.read(HERE/'lft_launch_and_progress_independent_review.json');assert peer['material_concerns']==[]
        u.check_refs(refs)
        for ref in refs:
            if ref not in target['evidence']:target['evidence'].append(ref)
        target['next_action']='Monitor original M227-LFT PID2685912/start-bound native log on server4 physicalGPU1, source4457. Both original runs confirmed progressing at12:53Z. Preserve WFC originalPID2085005/source94, M206 user pause, all10 oldholds, frozen data/seed/schedule/resources/bans. Efficacy remains UNKNOWN; never replay original dispatch.'
        w['updated_at']=datetime.now(timezone.utc).isoformat()
        assert all(c==next(x for x in old['candidates'] if x['id']==c['id']) for c in w['candidates'] if c['id']!=CID)
        u.atomic(ROOT/'pipeline/research_work.json',w)
        counts=dict(Counter(c['stage'] for c in w['candidates']))
        state={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'code_HEAD':COMMIT,'running':r,'candidate_stage_counts':counts,'canonical_LFT_original_once':u.ref(HERE/'lft_dispatch_result.json'),'original_dual_progress':u.ref(obsfile),'protected_28_user_files_status_and_empty_index':True,'protected_WFC_original_source9_and_process':True,'protected_all_nontarget_lifecycle_and154_candidates':True,'new_source_only_candidates':2,'new_native_arms':4,'new_technical_admissions':1,'new_verified_formal_runs':1,'formal_training_completed_this_tick':0,'champion_mIoU':0.5020,'goal_mIoU':0.5100,'efficacy_and_novelty':'UNKNOWN','foreground_finish':'NOT_YET_EXECUTED'}
        u.save(HERE/'preclosure_actual_state.json',state)
        memory='''# Codex Research Memory

## Goal And Phase
- 当前owner d94467a927904249b5584aa173433593，generated 2026-10-31T12:12:24.274969Z，deadline13:12:24.274969Z；真实root thread01a159c5-29ab-7a22-ba7f-e79174757253与foreground target一致，不延租约。收尾仅以真实receipt为准。
- Phase1目标mIoU .5100；冠军M95 .5020/baseline .4894，gap .0080。原YAML/data/pretrain/loss/optimizer/precision/seed1999/50epochs/maxiters70/patience10、10G/原conditional15%及bans保持；Phase2人工。
- 仅server4物理GPU0/1各1任务；goal0441/SERVERS19b3/closure2993/standing2e89/GPU1grant6529保持，其他服务器新dispatch禁用，Pipeline-cluster_project仍Disabled。

## Champion And Baseline
- 冠军不换。旧SFC .49663493037223816@20/epoch30与ELC .5015384554862976@21/epoch31均正常早停，archive2816/c437、完整native日志及精确校正018c保留；不重复本轮完成通知。
- generic归档stdout舍入/空log路径局限仍在，终态须核完整native日志及远端SHA，不改全局skill/调度。原CSV换行失败和binary atomic仅目标两行修复证据保留。
- 上轮9bb5908b已FINALIZED/context_committed/released；旧AOC .500072062/archive b132、FCB stopped_unknown/archive be337及PES clip_grad_norm原失败保持，不重开。

## Active Hypotheses
- M226-WFC：无序楔[中心,两端和]共享Linear/GELU→一次incidence mean回节点，原3LN/skip/HCG/单inst；原PID2085005/start105948793/source94/GPU0不变。12:53:28→31Z TRAIN[5,715]→[5,720]、log+1280B，原native4val best .42256200313568115/noimp0；仅早期部分结果。
- M227-LFT：真fine祖先路径的非线性P/U三角分析→原3packedFFN→逆向合成→3层原skip/LN/HCG/单inst。原协议60d0/proto1210与原5931兄弟版历史保留，另存字节相同9A兼容版4457(parent94)，无模型revision。
- 当前LFT四臂在tick_d94467a9/lft_execution：真实两自然TRAINbatch各2步/同common847参数配对；新增whole P/U core聚合finite非零梯度与真实更新核实，原FFN更新不能代签；8map/4mean/8算术/原3FFN与3scatter实际路径。单map/row/column/bias零合法，无新FP32/Jacobian门。
- 原资源20warm100：LFT9.781406796G vs M95 9.762532428G；median88.3758245ms vs87.1036780ms；allocated937816064B vs936763392B，增幅.11237%，原15%条件不触发；unsupported完整保留，无新latency门，pureTRAIN峰/效力/novelty UNKNOWN。独审db71，actualreview34bc/smoke0625/resources7bf1/constraintsb06c。
- source4457 exact9A已ff并安全同步；receipt ad0f，canonical一次GPU1 dispatch0b56；原PID2685912/start见cb92、envdontwrite1、12:53:31→34Z TRAIN[1,84]→[1,90]，尚无val。双原运行证据c515，独审见本轮launchpeer；WFC原source94未重标签。
- M228-NEC：节点h与边e双持久状态按真forest结构直径2/4同步交替组合；与旧node-only/edge-only实现区分。proto7592/manifest38ce/protocol17ba，29项stdlib源检查+9carrier案例，独审8cdc；native/resources未测、效果/novelty未知。
- M229-MIC：真fine路径共享非线性八顶点Möbius混合差分，q按fine直接均值回各mid/coarse；proto346a/manifesta5d2/protocola507，33项stdlib源检查+实际17carrier案例，独审0a67；原作者构造字符串失败及15→17计数澄清另存，未改模型/协议或冒称native PASS。

## Closed Or Failed Directions
- 10旧holds、PCE2+extra1/RSTR2已尽预算、已消费HAP旧grant保持。M206 waiting/user_paused/dispatch_hold/noPID，GPU1授权不恢复它或旧FCB。
- PES clip_grad_norm根因UNKNOWN及partial .4211保留；旧APF/HPC/CTS/BFC negative/unknown不借新路线声称修复、不换名重开。

## Running And Queue
- 当前WFC GPU0与LFT GPU1均原PID原版本正式训练，c515现场TRAIN增长确认；global main/remote4457只在94上新增LFT9，WFC9与28用户文件/status/空cached index及非目标生命周期保持。
- 155候选：47complete/94rejected/10blocked/2training/2implementation。新增NEC/MIC source/code/实际parent均NULL；94仅历史参考parent，未来保存版本须按当时真实运行树兼容处理，不能当兄弟版盲ff。
- 本轮2新源码原型、0模型修订、1相同9A兼容源码保存、4真实诊断arm、1技术准入+1确认新正式训练；0正式训练新终态。M206仍唯一暂停waiting，ready_waiting0。

## Open Questions And Risks
- WFC早期best .4226低于冠军，LFT尚无val；技术准入不能代训练效力。保持耐心/参数/数据，不能据此调参或重启。NEC/MIC只有源可行性，后续须实际原生2步及资源检查。
- 旧LFT/WFC工具绑定18e/94与历史raw均保留；新工具必须绑定实际source/runtime/owner，不重放旧manifest/request。当前dualobserver只接受94或其单父exact9A的4457，并另核WFC9保持，未知原PID/start拒绝。
- 原正式canonical argv保留，实际原PID环境dontwrite1已核，本地/诊断继续python -B。仅key+strictknownhost/hostname dl04访问.115，未读密码、不用旧.137、不推断sudo。
- 本轮FF后置index验证重复2947次只读Git已自然完成，无终止/重放；私有维护说明0a25建议下次受审副本缓存一次同等比较，不改本轮frozen工具。

## Last Tick
- 本轮先查WFC原TRAIN4/252→260/best.40993；GPU1先外部busy，后12:32实际idle才开始LFT；不挤占外部任务。四实际arm全部终态0后独审db71，再根activation f70/标准5394、exact9A ff、receipt/queue与一次canonicalGPU1派发并确认增长。
- 同轮按creation_budget2在私有目录实现NEC/MIC，经源独审后登记implementation，源提交/原生PASS/资源/入队全未伪造；其余153初始候选与生命周期在登记时完整保持。
- 最新12:53双原进度与exactnative指标见c515；报告0–3仍是begin12:12冻结快照，实际处置后状态见动作/决策和preclosure_actual_state。本轮需NOTIFY，无用户待办；report/finish/release以实际命令为准，不在释放后补写。
- 下一轮先查两原运行及ready派发；两卡有空槽再按当轮预算保存NEC/MIC真实兼容版本、用原YAML做native/resources，通过当轮入队。源原型未测不得冒充待跑任务；不强填额度、不恢复旧holds、不改资源/调度。
'''
        assert len(memory.splitlines())<120 and memory.count('\n## ')==7
        u.atomic(ROOT/'pipeline/codex_memory.md',memory,text=True)
        notes={'actions':[
            '实际收尾前现场2026-10-31T12:53:28→34Z：原WFC source94/PID2085005/GPU0 TRAIN5/715→720，原LFT source4457/PID2685912/GPU1 TRAIN1/84→90，双原运行均增长。WFC原native4次val最佳.42256200313568115/noimp0，LFT尚无val；begin12:12表格是历史冻结快照。',
            'LFT另存原9A字节相同兼容source4457(parent94)，原5931/proto1210/协议60d0保留，无模型修订。严格GPU1空闲/UUID/3locks和owner/版本核验后，原YAML真实2自然TRAINbatch/control候选各2步、原loss/backward、新whole P/U core聚合梯度与真实更新、common847参数配对及实际8map/4mean/原3FFN/3scatter通过。',
            '四实际arm终态0后独审db71：原20warm100、LFT whole counted9.781406796G<10G，M95 9.762532428G；allocated937816064B vs936763392B增.11237%不触发原15%条件；median88.3758ms vs87.1037ms仅描述，unsupported完整保留，无新latency/FP32门。pureTRAIN峰、效力及novelty未知。',
            '实际标准34bc/0625/7bf1/b06c及独审后，exact9A已测版本ff到main并安全同步；receipt ad0f+FIFO GPU1实际入队，一次canonical dispatch0b56、再c515现场增长核实。WFC原source94/原PID、源9与28用户文件/status/空index及其余生命周期保持。',
            '按本轮新增预算2实现M228-NEC节点边双状态组合、M229-MIC祖先路径Möbius混合差分；29/33项stdlib源检查与独立源审通过，登记2个implementation储备。实际source/code/parent均NULL，native/resources未测、不入队；NEC9/MIC17 carrier案例不能当作真实训练。',
            '本轮0新正式终态、1兼容源码保存、4真实诊断arm、1新技术准入+1确认正式运行，当前2training+2implementation；旧SFC/ELC终态与精确校正仅保留不重复计本轮成果。旧10holds/M206暂停保持，无外部任务干预。FF重复index只读验证已自然完成，维护建议另存未改本轮工具。'
        ],'decisions':[
            '冠军仍M95 .5020，目标.5100/gap.0080；WFC早期.4226及LFT smoke/新启动都不证明效果。两原训练继续保持原seed/data/schedule/patience，技术准入不改冠军。',
            'NEC/MIC后续先按当轮真实运行树保存兼容独立版本，再在授权空槽以原YAML执行真实最小检查与资源检查；通过当轮准入/入队，原型源码可行性不冒充待跑实验。不耗尽额度、不恢复历史holds或M206，不改服务器/调度/禁用项。',
            '本轮有实质新正式训练与两源储备，应NOTIFY，无需用户处理。七段memory与六段report先留档；是否成功完成收尾以真实finish/postflight/release收据为准。'
        ]}
        u.save(HERE/'final_report_notes.json',notes)
        print(json.dumps({'status':'ACTUAL_EVIDENCE_MEMORY_AND_NOTES_SAVED_FINISH_NOT_YET_RUN','state':u.ref(HERE/'preclosure_actual_state.json'),'notes':u.ref(HERE/'final_report_notes.json'),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md'),'stage_counts':counts},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
