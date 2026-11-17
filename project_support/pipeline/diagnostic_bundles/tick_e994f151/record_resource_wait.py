"""Persist a real busy-GPU observation without repeating frozen preparation."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

R=Path('D:/project/cluster_project');D=Path(__file__).resolve().parent
T='e994f1515652416a8a742ff1ec029934'
IDS={'hierarchy-parent-spectral-nonlinear-token-coupling':'43dce016c1a1713c2a5dab7061810dc2efde8954','hierarchy-parent-binary-tree-complement-composition':'00e2b18c6b8d568a64edb496e6979d766440883c'}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def save(p,v):
    q=p.with_name(p.name+'.'+T+'.tmp')
    with q.open('x',encoding='utf-8') as f:
        f.write(v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(q,p)

o=read(R/'pipeline/headless/.foreground.lockdir/owner.json')
assert o['token']==T and o['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert datetime.now(timezone.utc)<datetime.fromisoformat(o['deadline_at'])
assert sha(R/'pipeline/headless/.tick_context.json')==o['context_sha256'] and sha(R/'pipeline/headless/.tick_context_state.next.json')==o['pending_sha256']
obs=read(D/'psbr_phase_observation.json');a,b=[x['data'] for x in obs['observations']]
assert sha(D/'psbr_phase_observation.json')=='d107d522f513d0a1ff1c5de514d96079b0fae93be67afd8c59f221b55f31c3af'
assert obs['exact_original_process_and_native_progress_increasing'] is False and a['progress']==b['progress']==[13,50,4686,4686]
phase=read(D/'validation_phase_resolution.json');assert phase['exact_original_process_native_validation_increasing'] and phase['validation_progress']==[[13,50,345,363],[13,50,355,363]]
assert a['pid']==b['pid']==2372658 and a['starttime']==b['starttime']=='35234267' and not b['errors']
boundary=read(D/'waiting_boundary_check.json');assert boundary['material_concerns']==[]
m=boundary['PSBR_partial_metrics'];assert m['epoch']==13 and m['best_mIoU_4dp']==0.4881 and m['no_improve']==2
stamp=datetime.fromisoformat(obs['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as pm
lock=pm.acquire_lock(str(R));assert lock is not None
try:
    names=['queue.json','running.json','experiments/M208-HRC.json','experiments/M209-PSBR.json','experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']
    before={n:sha(R/'pipeline'/n) for n in names}
    assert read(R/'pipeline/running.json')['server-4']=={'0':'M209-PSBR'}
    w=read(R/'pipeline/research_work.json');now=datetime.now(timezone.utc)
    ev=[ref(D/'psbr_phase_observation.json'),ref(D/'waiting_boundary_check.json'),ref(D/'validation_phase_resolution.json')]
    blocker='Only authorized GPU0 occupied by original PSBR2372658/start35234267, TRAIN13/50 complete4686/4686, live VAL13/50 steps345->355/363 observed '+stamp+' Shanghai. Existing PSNC43 and BTC00e preparations reused; no new native slot. GPU1 released and M206 paused.'
    for cid,commit in IDS.items():
        c=next(x for x in w['candidates'] if x['id']==cid)
        assert c['stage']=='blocked' and c['resume_stage']=='validation' and c['code_commit']==commit and c['native_execution_code_commit'] is None and c['blocker_kind']=='exclusive_gpu_slot'
        for item in ev:
            if item not in c['evidence']:c['evidence'].append(item)
        c['blocker']=blocker;c['last_resource_check_at']=now.isoformat();c['retry_after']=(now+timedelta(hours=1)).isoformat()
    live=next(x for x in w['candidates'] if x.get('experiment_id')=='M209-PSBR');assert live['stage']=='training'
    for item in ev:
        if item not in live['evidence']:live['evidence'].append(item)
    w['tick_attempt']={'tick_started_at':o['generated_at'],'candidate_id':next(iter(IDS)),'kind':'resource_check','result':'blocked','command':'python -B pipeline/diagnostic_bundles/tick_e994f151/observe_psbr_training.py','observation':blocker+' Healthy in-progress only; no new terminal, failure, required decision, candidate, test, version, receipt, queue or launch.','evidence':ev}
    w['updated_at']=now.isoformat();save(R/'pipeline/research_work.json',w)
    assert {n:sha(R/'pipeline'/n) for n in names}==before
    mem=(R/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('\n## Last Tick\n',1)[0];lines=mem.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('- 当前foreground'):
            lines[i]='- 当前foreground'+T+'；actual owner/target一致，generated14:10:43.668319UTC/原deadline15:10:43.668319不延长。前2335已FINALIZED/released(20:12:52上海)且headless lock/pending消失才begin；本轮随后真实report/finish确认，不预写PASS。'
        elif line.startswith('- 当前2026-10-23 '):
            lines[i]='- 当前'+stamp+'上海精确原PSBR PID2372658/start35234267/argv/cwd/remoteHEAD74f/GPU0UUID，TRAIN13/50最后4686/4686不变、当前VAL13/50两次345→355/363递增，无error/logfresh/GPU0原context；proof SHA'+sha(D/'psbr_phase_observation.json')+'。beginpartial best.4881/noimprove2/10，非终态/非champion。GPU1未查未用，无signal或额外计算。'
        elif line.startswith('- HRC已知本实现best'):
            lines[i]=line.replace('本轮新增BTC00e','此前2c25新增BTC00e')
        elif line.startswith('- PSNC当前blocked/'):
            lines[i]='- PSNC当前blocked/exclusive_gpu_slot/resumevalidation，BTC同；既存source43完整工具/static release、BTC00e冻结source/独立worktree不重做。PSBR13/50验证占唯一GPU0，两具体准备按PSNC→BTC顺序等真实空槽/freshbinding TRAIN2+原资源。主/remoteHEAD仍74f，不凑compact排除blocked后的reserve0再造候选。'
    mem='\n'.join(lines)+'\n\n## Last Tick\n'
    mem+='- 本轮e994 begin一次monitor/已有派发/goal，design/candidate2/reserve2/creation2；PSBR唯一running、0readywaiting，M206暂停另计，0新终态/operationalissue。现成PSNC+BTC两具体准备足够，不重复准备/造候选，compact reserve0不等于没有既备source。\n'
    mem+='- '+stamp+'上海精确原PSBR TRAIN13/50 4686/4686、VAL13/50 345→355/363递增，beginpartial best.4881/noimprove2/10；健康训练非新科学结果/终态。champion仍M95.5020/目标.5100差.0080。GPU0忙，无额外GPU计算/进程处置，GPU1未查未用。\n'
    mem+='- 最小waiting边界复核 '+ref(D/'waiting_boundary_check.json')['path']+' SHA'+sha(D/'waiting_boundary_check.json')+' 无实质问题；PSBR原2372658/launchverified/c85receiptJSON与main74f/index空、PSNC43/native执行null/3小metadata、BTC00e/native执行null/prep与版本小JSON、M206人工暂停及HRC已归档均保持。未重hash大标准/源码/完整packet，未重复51mock/589tests。\n'
    mem+='- 11blocked全部notdue，不复核旧8hold/655正文/授权正文或修订、重开。当前真实resource_check blocked同归PSNC/BTC，0新candidate/native/profile/commit/sync/receipt/queue/launch，不动现有运行、目标、资源、禁用项、调度。\n'
    mem+='- 当前确为原生验证phase推进，不声称Train步增长。初始3秒及15秒Train-only两样本无变化触发观察脚本断言，未写结果；后有界phase证据明确VAL13/50 345→355且logfresh/无error，已解释为观察覆盖限制，无训练故障/重启/阈值或源码变更。\n'
    mem+='- 仅健康训练/资源等待，无可行动变化/完成/失败/需用户处理，DONT_NOTIFY。延续既有FIFO/准备，无新路线/操作决策故不写重复decision；七段memory/六段report后原token真实finish+receipt FINALIZED released/lock pending消失再确认，释放后不回写。\n'
    assert mem.count('\n## ')==7 and len(mem.splitlines())<120;save(R/'pipeline/codex_memory.md',mem)
    notes={'actions':['本轮actual owner/target一致，canonical SKILL/experimentfirst/foreground规则、最新memory授权及未变goal/SERVERS、WindowsDisabled核验；前2335 FINALIZED released且无lock/pending才begin，原deadline不延长。','begin一次monitor/已有派发/goal，无新terminal/operationalissue，PSBR唯一running/0readywaiting；现成PSNC43完整工具和BTC00e冻结source两具体准备足够，不因compact排除blocked后reserve0重复造候选。',stamp+'上海只读精确原PSBR2372658/start35234267/原argv/cwd/HEAD74f/UUID，TRAIN13/50 4686/4686、VAL13/50 345→355/363递增、无error；beginpartial best.4881/noimprove2/10，仅健康训练非最终效果或champion。GPU0忙，无新计算/进程处置；GPU1未查未用。','一次最小waiting边界核：PSBR receiptJSON/74f/index空，PSNC source43/native执行null与3小metadata，BTC source00e/native执行null与prep/版本小JSON，M206暂停与HRC归档保持。未读标准大正文/9源码/完整packet，不重复51mock/589静态测试。','11blocked全部notdue，不复核旧8hold/655旧证据/授权正文，不重开或加修订。当前tick_attempt为PSNC真实resource_check blocked且新证据同归PSNC/BTC；0新candidate/native/profile/version/receipt/queue/launch/sync，原运行台账字节保持。','七段memory/完整六段report后原token真实finish及receipt/lock释放核验，释放后不回写。无实质可行动变化/新完成/失败/用户决定，DONT_NOTIFY；不改目标/资源/禁用/调度或GPU1/M206状态。'],'decisions':['延续已授权PSBR原run和PSNC→BTC现成准备；当前只有健康进行及资源等待，无新路线/操作决策，静默。']}
    notes['actions'].insert(3,'原始Train-only观察3秒和15秒比较均无Train计数变化，断言后未落结果；另行保留有界phase两样本，明确原生VAL13/50 345→355/363推进、Train最后4686/4686保持、logfresh/无error。validation_phase_resolution绑定原始字节，不伪写Train增长/PASS，不把观察覆盖限制当训练故障，无signal/重启或原代码阈值变更。')
    save(D/'tick_notes.json',notes)
    save(D/'resource_wait_persistence.json',{'recorded_at':now.isoformat(),'token':T,'evidence':ev,'notification':'DONT_NOTIFY','new_scientific_result':False,'protected_registry_unchanged':{n:sha(R/'pipeline'/n)==v for n,v in before.items()}})
    print(json.dumps({'recorded':'resource_check_blocked','PSBR_epoch':m['epoch'],'partial_best':m['best_mIoU_4dp'],'native_checks':'NOT_RUN','new_candidates':0,'notification':'DONT_NOTIFY'},ensure_ascii=False))
finally:lock.close()
