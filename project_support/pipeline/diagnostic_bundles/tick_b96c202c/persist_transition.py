"""Persist verified completion/launch and the actual remaining GPU0 wait."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

R=Path('D:/project/cluster_project');D=Path(__file__).resolve().parent
T='b96c202c871a4a1889d47e1fdc75e16e';CID='hierarchy-parent-spectral-nonlinear-token-coupling'
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
prev=read(R/'pipeline/tick_receipts/2a00f6ae699f448e946a45c3ec25251f.json')
assert prev['status']=='FINALIZED' and prev['lease_release']=='released'
obs=read(D/'hrc_terminal_psbr_live_observation.json')
assert sha(D/'hrc_terminal_psbr_live_observation.json')=='32b5b6ae795c531138789b597e28d8b5d1e2fcec6a68325112983c53cd9b8f73'
assert obs['PSBR_exact_native_progress_increasing'] and obs['HRC_natural_earlystop_confirmed']
a,b=[x['data'] for x in obs['observations']]
assert a['PSBR']['progress']==[1,50,207,4686] and b['PSBR']['progress']==[1,50,215,4686]
assert a['PSBR']['starttime']==b['PSBR']['starttime']=='35234267'
assert read(D/'psbr_local_launch_boundary_review.json')['material_concerns']==[]
assert read(D/'hrc_archive_psbr_final_review.json')['material_concerns']==[]
archive=read(D/'hrc_terminal_archive.json');logproof=read(D/'hrc_native_earlystop_log_evidence.json')
assert archive['running_mapping_unchanged'] and logproof['local_remote_sha256_match']
stamp=datetime.fromisoformat(obs['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as pm
lock=pm.acquire_lock(str(R));assert lock is not None
try:
    names=['queue.json','running.json','experiments/M208-HRC.json','experiments/M209-PSBR.json','experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']
    before={n:sha(R/'pipeline'/n) for n in names}
    q=read(R/'pipeline/queue.json')['gpu_queues']['server-4']
    assert not any(x['id']=='M208-HRC' for x in q)
    p=next(x for x in q if x['id']=='M209-PSBR');assert p['status']=='running' and p['pid']==2372658 and p['launch_verified'] is True
    assert read(R/'pipeline/running.json')['server-4']=={'0':'M209-PSBR'}
    w=read(R/'pipeline/research_work.json');c=next(x for x in w['candidates'] if x['id']==CID)
    assert c['stage']=='blocked' and c['resume_stage']=='validation' and c['code_commit']=='43dce016c1a1713c2a5dab7061810dc2efde8954' and c['native_execution_code_commit'] is None
    ev=[ref(D/'hrc_terminal_psbr_live_observation.json'),ref(D/'hrc_archive_psbr_final_review.json')]
    for item in ev:
        if item not in c['evidence']:c['evidence'].append(item)
    now=datetime.now(timezone.utc);c['last_resource_check_at']=now.isoformat();c['retry_after']=(now+timedelta(hours=1)).isoformat()
    c['blocker']='Only authorized GPU0 occupied by freshly canonically launched PSBR2372658/start35234267, original native1/50 steps207->215 observed '+stamp+' Shanghai. HRC exact natural earlystop31/best.4901 archived. Existing complete PSNC43 preparation reused; no native slot and no active checkout modification.'
    h=next(x for x in w['candidates'] if x.get('experiment_id')=='M208-HRC');p=next(x for x in w['candidates'] if x.get('experiment_id')=='M209-PSBR')
    assert h['stage']=='complete' and h['training_status']=='done_earlystop' and p['stage']=='training'
    for c2 in [h,p]:
        for file in ['hrc_terminal_archive.json','psbr_local_launch_boundary_review.json','hrc_archive_psbr_final_review.json']:
            item=ref(D/file)
            if item not in c2['evidence']:c2['evidence'].append(item)
    w['tick_attempt']={'tick_started_at':o['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked','command':'python -B pipeline/diagnostic_bundles/tick_b96c202c/observe_transition.py','observation':c['blocker']+' No new admission/candidate/commit/sync/native PSNC execution. Current snapshot reserve_budget=0/creation_budget=0 respected.','evidence':ev}
    w['updated_at']=now.isoformat();save(R/'pipeline/research_work.json',w)
    assert {n:sha(R/'pipeline'/n) for n in names}==before
    mem=(R/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('\n## Last Tick\n',1)[0];lines=mem.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('- 当前foreground'):
            lines[i]='- 当前foreground'+T+'；actual owner/target一致，generated06:10:33.735496UTC/原deadline07:10:33.735496不延长。前2a00已FINALIZED/released且headless lock/pending消失才begin；本轮随后真实report/finish确认，不预写PASS。'
        elif line.startswith('- M208-HRC stable'):
            lines[i]='- M208-HRC stable hierarchy-bottom-up-refined-token-composition，tested/queued/live commit74fcd21df0af9a971792038ffe251af1ffea2604；本轮原PID2780804消失/原log自然earlystop31/50、10次未提升、best.4901(终态4位)，canonical精确归档为complete/done_earlystop。原3FFN各一次，refined fine经原fixed-child mean进入middle再进入coarse；rawbanks/FPS/IDs/CSORT/HCG/单inst不变。此实现低M95.5020差.0119，不自动重跑或泛化整假设失败。'
        elif line.startswith('- M209-PSBR stable'):
            lines[i]='- M209-PSBR stable hierarchy-parent-segmented-bidirectional-token-state，commit74f；本轮begin按原receipt/YAML自动首次launch GPU0 PID2372658/start35234267/log后缀20261023_141002.log，并额外两次核原生1/50 207→215/4686增长。stage training/running，最终效果UNKNOWN。原middle FFN替换为父组/原xyz+ID排序Wx/Wh双向tanh零边界状态及Wo逆散原ID，fine/coarse/raw-CSORT/HCG/单inst保持。'
        elif line.startswith('- HRC/PSBR最终训练效果'):
            lines[i]='- HRC本实现最终best.4901未超过M95；PSBR最终训练效果仍UNKNOWN，既有真实技术准入保持。PSNC独立source43及51项离线检查/独审完整包复用，当前仍未native/资源检查或准入；本轮不重复准备/模拟测试，creation/reserve预算均0。'
        elif line.startswith('- 当前2026-10-23 '):
            lines[i]='- 当前'+stamp+'上海两次精确观察：HRC原PID已无且原log明确31/50 earlystop/.4901；PSBR原PID2372658/start35234267/argv/cwd/remoteHEAD74f/GPU0UUID相符，native1/50 207→215增长、无error/logfresh，GPU0 context为PSBR。proof SHA'+sha(D/'hrc_terminal_psbr_live_observation.json')+'。GPU1未查未用，无signal或额外计算。'
        elif line.startswith('- PSNC当前blocked/'):
            lines[i]='- PSNC当前blocked/exclusive_gpu_slot/resumevalidation：已有完整source43/工具/静态release保持。PSBR已安全以74f真实首次启动，当前占唯一GPU0；不改活跃remote checkout，待未来真实空槽用freshbinding执行原YAML TRAIN2+资源。主HEAD仍74f，此轮不commit/sync，不新增候选或准入。'
        elif line.startswith('- current queue：'):
            lines[i]='- current queue：仅M209-PSBR running GPU0/launch_verifiedtrue，running映射唯一M209；M208-HRC自然done_earlystop后canonical移出queue/running，完整原log+archive保持；M206 waiting但paused_by_user/dispatch_hold/resumefalse，不计readywaiting，GPU1释放；HAP历史done_earlystop及prior_runs保持。'
        elif line.startswith('- 新HRC原argv'):
            lines[i]=line.replace('- 新HRC原argv','- 历史HRC原argv')
    mem='\n'.join(lines)+'\n\n## Last Tick\n'
    mem+='- 本轮b96c由用户问实验触发：先只读发现HRC自然早停，再canonical begin一次monitor/goal/已有派发。snapshot design/candidate1/reserve0/creation0，无新operationalissue；preflight旧HRC登记running/deathwatch1与真实已终止区别完整留存，不重复monitor。\n'
    mem+='- HRC原PID2780804自然退出、原log31/50/10未提升/best.4901；完整log '+str(logproof['bytes'])+'字节，本地/远端SHA'+logproof['sha256']+'相同，精确finalize_task(done_earlystop)，归档proof SHA'+sha(D/'hrc_terminal_archive.json')+'；未signal/deathwatch递增/重启。M95仍.5020，目标.5100差.0080。\n'
    mem+='- begin已canonical首次launch PSBR2372658；'+stamp+'上海额外原生1/50 207→215增长/start35234267/原argv/cwd/74f/UUID均核，stage training/running。M206队列和PSBR映射归档前后保持，GPU1未查询使用。PSBR尚无已观测验证指标，最终效果UNKNOWN。\n'
    mem+='- 两份最小独审 '+ref(D/'psbr_local_launch_boundary_review.json')['path']+' SHA'+sha(D/'psbr_local_launch_boundary_review.json')+' 与 '+ref(D/'hrc_archive_psbr_final_review.json')['path']+' SHA'+sha(D/'hrc_archive_psbr_final_review.json')+' 无实质问题；原c85receipt/74f/原YAML/index空及GPU0-only/M206暂停保持。\n'
    mem+='- PSNC当前resource_check blocked证据同归该候选，阻塞更新为活跃PSBR；source43/完整既存operational准备未重跑、native_execution仍null。0新candidate/native/profile/receipt/queue/commit/sync，无可新增准备预算，不凑变体；旧8hold/655证据/授权正文不复查或重开。\n'
    mem+='- 实质变化为HRC完成和PSBR确认训练，用户主动询问故正常中文简报；非心跳通知决策。下一步监控PSBR原run，GPU0空闲时以freshowner/lease推进PSNC真实TRAIN2与原资源，通过才准入，不动运行中源码。\n'
    mem+='- 七段memory/六段report后按原token真实finish/receipt FINALIZED released及headless lock/pending消失才确认；释放后不回写。不改目标/资源/禁用/调度、不给M206恢复或旧失败额外修订。\n'
    assert mem.count('\n## ')==7 and len(mem.splitlines())<120;save(R/'pipeline/codex_memory.md',mem)
    notes={'actions':[
        '用户主动询问实验。先只读实时发现HRC原PID已退出/原log31轮自然早停，随后核actual owner/target、最新memory/goal/SERVERS及授权，onlyserver4GPU0/max1/GPU1释放/M206暂停/WindowsDisabled保持；原deadline不延长。',
        'canonical begin仅一次monitor/goal及已有派发，自动首次启动PSBR。快照旧HRC登记running/deathwatch1不作为活进程；本轮用精确原log和PID事实归档，无signal/额外deathwatch或重启。',
        '完整HRC原log本地/远端SHA一致，真实31/50早停、10次未提升、best0.4901(终态4位)，canonical finalize_task写done_earlystop并移出旧queue，原commit/receipt/history保留。低于M95.5020差.0119，目标差.0199，只是该实现无提升。',
        stamp+'上海PSBR原PID2372658/start35234267/原argv/cwd/HEAD74f/UUID相符，两次真实训练1/50 207→215/4686、无error且GPU0 context匹配，确认训练。两份本地/最终独审无实质问题，归档不覆盖PSBR/M206映射。',
        'PSNC完整source43/静态工具包保持未执行；本轮实际GPU0已被PSBR占用，新的resource_check blocked及证据归该候选。reserve/creation0不再生成候选或工具；0新原生验证/资源profile/准入/commit/sync，不动活跃checkout，不重查655旧证据或重开旧hold。',
        '按当前事实更新七段memory，完整六段报告留档，原token真实finish后核receipt与释放；不把收尾PASS当科学成功。当前best仍M95.5020/目标.5100差.0080；PSBR效果待训，PSNC待真实空GPU0再freshbinding检查。'
    ],'decisions':['保留HRC本实现无收益终态，沿既有FIFO继续已获准PSBR原YAML训练；不调参重跑、不扩大资源。','PSNC待唯一授权GPU0真实空闲后复用现成准备执行原生检查；不改正在运行的remote checkout或GPU1/M206暂停。']}
    save(D/'tick_notes.json',notes)
    save(D/'transition_persistence.json',{'recorded_at':now.isoformat(),'token':T,'resource_check_evidence':ev,'HRC_complete':True,'PSBR_verified_training':True,'PSNC_native':'NOT_RUN','new_candidates':0,'new_admissions':0,'protected_registry_unchanged_during_persistence':{n:sha(R/'pipeline'/n)==v for n,v in before.items()}})
    print(json.dumps({'persisted':True,'HRC':'done_earlystop_31_best0.4901','PSBR':'verified_training_1/50','PSNC':'waiting_gpu0_native_unrun','new_candidates':0,'new_admissions':0},ensure_ascii=False))
finally:lock.close()
