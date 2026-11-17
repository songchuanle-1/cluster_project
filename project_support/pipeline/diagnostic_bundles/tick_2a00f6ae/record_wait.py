"""Persist only the current real busy-card observation and readable tick notes."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys
R=Path('D:/project/cluster_project');D=Path(__file__).resolve().parent
T='2a00f6ae699f448e946a45c3ec25251f';CID='hierarchy-parent-spectral-nonlinear-token-coupling'
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
obs=read(D/'hrc_training_progress_observation.json');a,b=[x['data'] for x in obs['observations']]
assert obs['exact_original_process_and_native_progress_increasing'] and a['progress']==[29,50,2151,4686] and b['progress']==[29,50,2160,4686]
assert a['pid']==b['pid']==2780804 and a['starttime']==b['starttime']=='29604100' and not b['errors']
boundary=read(D/'waiting_boundary_check.json');assert boundary['material_concerns']==[]
assert sha(D/'waiting_boundary_check.json')=='cc433a432263e8ebde0f6cf241f1ea41572392198c6a722a4b3c5783055e1fc8'
held=read(D/'held_boundary_check.json');assert held['material_concerns']==[]
assert sha(D/'held_boundary_check.json')=='74115dae2b6689b92ce338d6568d7186b84f71be6a475fa2bab29f26c66c39ef'
assert sha(D/'hrc_training_progress_observation.json')=='bf2b4e7461269cf6d85739e1230ceedcc1b645123ff6699cbe75d5970c2aa2db'
m=boundary['HRC_partial_metrics'];assert m['epoch']==29
stamp=datetime.fromisoformat(obs['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as pm
lock=pm.acquire_lock(str(R));assert lock is not None
try:
    names=['queue.json','running.json','experiments/M208-HRC.json','experiments/M209-PSBR.json','experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']
    before={n:sha(R/'pipeline'/n) for n in names};w=read(R/'pipeline/research_work.json');c=next(x for x in w['candidates'] if x['id']==CID)
    assert c['stage']=='blocked' and c['resume_stage']=='validation' and c['code_commit']=='43dce016c1a1713c2a5dab7061810dc2efde8954' and c['native_execution_code_commit'] is None
    ev=[ref(D/'hrc_training_progress_observation.json'),ref(D/'waiting_boundary_check.json')]
    for item in ev:
        if item not in c['evidence']:c['evidence'].append(item)
    now=datetime.now(timezone.utc);c['last_resource_check_at']=now.isoformat();c['retry_after']=(now+timedelta(hours=1)).isoformat()
    c['blocker']='Only authorizedGPU0 occupied by original HRC2780804/start29604100, native29/50 steps2151->2160 observed '+stamp+' Shanghai. Existing PSBR74f FIFO protected; existing complete PSNC43 preparation reused, no new native slot.'
    h=next(x for x in w['candidates'] if x.get('experiment_id')=='M208-HRC')
    for item in ev:
        if item not in h['evidence']:h['evidence'].append(item)
    w['tick_attempt']={'tick_started_at':o['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked','command':'python -B pipeline/diagnostic_bundles/tick_2a00f6ae/observe_hrc_training.py','observation':c['blocker']+' No actionable state change; no new candidate/native/resource profile/receipt/queue/commit/sync.','evidence':ev}
    w['historical_hold_boundary_review']=ref(D/'held_boundary_check.json')
    w['updated_at']=now.isoformat();save(R/'pipeline/research_work.json',w)
    assert {n:sha(R/'pipeline'/n) for n in names}==before
    mem=(R/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('\n## Last Tick\n',1)[0];lines=mem.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('- 当前foreground'):
            lines[i]='- 当前foreground'+T+'；actual owner/target一致，generated04:05:44.390066UTC/原deadline05:05:44.390066不延长。前d035已FINALIZED/released(10:15:11上海)且headless lock/pending消失才begin；本轮随后真实report/finish确认，不预写PASS。'
        elif line.startswith('- 当前2026-10-23 '):
            lines[i]='- 当前'+stamp+'上海原HRC PID2780804/start29604100/原argv/cwd/remoteHEAD74f/GPU0UUID，native29/50两次2151→2160/4686、无error/logfresh/GPU0原context；proof SHA'+sha(D/'hrc_training_progress_observation.json')+'。beginpartial best'+str(m['best_mIoU_4dp'])+'/noimprove'+str(m['no_improve'])+'，非终态/非champion。GPU1未查未用，无signal/新计算。'
        elif line.startswith('- 8旧hold前轮'):
            lines[i]='- 当前8旧hold到期有界核完整canonical元数据/声明引用清单签名与13授权path-size-mtime，同d8基准；proof '+ref(D/'held_boundary_check.json')['path']+' SHA'+sha(D/'held_boundary_check.json')+'。655旧证据正文读取/重hash/exists-stat均0、grant正文重读0；无新scope/reopen/extra revision授权或用户事项，原失败/1e-6/修订上限保持。'
        elif line.startswith('- PSNC当前blocked/'):
            lines[i]='- PSNC当前blocked/exclusive_gpu_slot/resumevalidation：已有完整source43/检查工具/静态release保持，不重跑42ce guard或51mock。当前HRC29/50占唯一GPU0，PSBR74f freshdispatch/primaryHEAD继续保护；空GPU0且版本条件安全后freshbinding真实TRAIN2+资源，未准入，不凑候选。'
    mem='\n'.join(lines)+'\n\n## Last Tick\n'
    mem+='- 本轮2a00 begin一次monitor/已有派发/goal，design/candidate1/creation1；1HRCrunning/0claiming/1readyPSBRwaiting，M206人工暂停另计，无新终态/operationalissue。PSBR+PSNC两项现成准备足够，不凑新变体。\n'
    mem+='- '+stamp+'上海精确原HRC29/50步2151→2160增长，beginpartial best'+str(m['best_mIoU_4dp'])+'/noimprove'+str(m['no_improve'])+'，仍训练未完成、champion仍M95.5020/目标.5100差.0080。GPU0忙，0新native/profile/进程处置，GPU1未查未用。\n'
    mem+='- 一次小范围waiting边界复核见'+ref(D/'waiting_boundary_check.json')['path']+' SHA'+sha(D/'waiting_boundary_check.json')+'：PSBR仍waiting74f/nohold/PIDnull/c85receiptJSON同、主74f/index空、PSNC43/native执行null及3小metadata/release锚吻合、M206暂停；未重hash标准artifact正文/完整packet/9源，不重复51mock/guard或源码审。\n'
    mem+='- 8旧hold到期仅核元数据/引用清单签名/13授权path-size-mtime；655证据正文/hash/stat与grant正文均未读，M206到期仍暂停，PSNC资源忙notdue，不重开/增修订/重复问权限。当前resource_check blocked新证据同归PSNC，0新candidate/commit/sync/receipt/queue/launch/运行材料。\n'
    mem+='- 仅健康训练和等待资源复查，无新科学结论/完成/失败/需用户处理；DONT_NOTIFY。延续既有FIFO/准备，无新操作决策故不写重复decision，不造新工具/全局穷尽/冷却，不改调度/目标/资源/失败。\n'
    mem+='- 七段memory/六段report后按原token真实finish/receipt FINALIZED released及headless lock/pending消失才确认，释放后不回写；下一步仍是现成工具在PSBR版本边界安全/真实GPU0空槽后freshbinding原YAML TRAIN2与原资源。\n'
    assert mem.count('\n## ')==7 and len(mem.splitlines())<120;save(R/'pipeline/codex_memory.md',mem)
    notes={'actions':['实际会话/target一致，canonical SKILL/experimentfirst/foreground/最新memory及goal/SERVERS核验，goalSHA0441、onlyserver4GPU0/max1/GPU1释放/M206暂停/WindowsDisabled保持。前d035收据FINALIZED released且无headless lock/pending才begin，原generated04:05:44.390066/deadline05:05:44.390066UTC不改。','begin已monitor/已有派发/goal各一次，无新终态/operationalissue。已有PSBRreadywaiting+PSNC完整具体准备，不因预算1再造候选或重造工具；8旧hold到期仅有界核元数据/授权清单，不复查655正文或grant正文；M206保持暂停。',stamp+'上海额外只读精确原HRC29/50 native2151→2160/4686、PID/start/argv/cwd/HEAD74f/UUID及GPU0context核实，native持续进展/无error。beginpartial best'+str(m['best_mIoU_4dp'])+'/noimprove'+str(m['no_improve'])+'，非终态效果或新champion，无空槽给PSNC。','一次最小waiting边界核：PSBR74f waiting/nohold/PIDnull且c85receiptJSON同、主74f/index空，PSNCsource43/native执行null/3小metadata锚保持；M206人工pause保持。未重hash标准artifact正文/完整包/9source、未重复51mock或guard、未新增scientific PASS。','当前tick_attempt是真resource_check blocked且当前证据同归PSNC；0新候选/native/profile/标准summary/receipt/queue/launch/commit/sync/运行材料，既有queue/running/experiments/admissions字节保持。仅健康训练/资源等待，无可行动事项或需用户决定，DONT_NOTIFY。','七段memory/脚本六段report后按原token真实finish与receipt/lock释放核验，释放后不回写。不写重复decision、不造全局穷尽/冷却、不改资源/禁用项/目标/调度，不动GPU1/M206或既有运行。'],'decisions':['延续既有授权、FIFO和PSNC已完成准备；当前无新路线/操作决策与可行动变化，静默。']}
    save(D/'tick_notes.json',notes);save(D/'waiting_tick_persistence.json',{'recorded_at':now.isoformat(),'token':T,'evidence':ev,'notification':'DONT_NOTIFY','new_scientific_result':False,'protected_registry_unchanged':{n:sha(R/'pipeline'/n)==v for n,v in before.items()}})
    print(json.dumps({'recorded':'resource_check_blocked','native':'NOT_RUN','HRC_epoch':m['epoch'],'partial_best':m['best_mIoU_4dp'],'notification':'DONT_NOTIFY'},ensure_ascii=False))
finally:lock.close()
