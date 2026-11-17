"""Record unchanged busy-resource waiting; do not repeat frozen preparation."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
TOKEN='f34f60e9728a46d29c554c10cf3b0934'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
    t=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with t.open('x',encoding='utf-8') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(t,p)
owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
obs=read(HERE/'psnc_progress_observation.json');a,b=[x['data'] for x in obs['observations']]
assert sha(HERE/'psnc_progress_observation.json')=='676c154f49fb7c809996ccb635bea67fd1768d016dcc5472145dbf5d5f773ef9'
assert obs['same_exact_registered_process_and_native_TRAIN_growth'] and a['train_progress']==[31,50,1616,4686] and b['train_progress']==[31,50,1625,4686]
assert a['pid']==b['pid']==2502712 and a['start_ticks']==b['start_ticks']=='41082267' and not b['errors']
boundary=read(HERE/'waiting_boundary_check.json');assert boundary['material_concerns']==[]
stamp=datetime.fromisoformat(obs['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
lock=monitor.acquire_lock(str(ROOT));assert lock is not None
try:
    names=['queue.json','running.json','experiments/M210-PSNC.json','experiments/M206-CGCA.json','admissions/M210-PSNC.json']
    before={n:sha(ROOT/'pipeline'/n) for n in names}
    assert read(ROOT/'pipeline/running.json')['server-4']=={'0':'M210-PSNC'}
    work=read(ROOT/'pipeline/research_work.json');now=datetime.now(timezone.utc)
    c=next(c for c in work['candidates'] if c.get('experiment_id')=='M211-BTC')
    assert c['stage']=='blocked' and c['blocker_kind']=='exclusive_gpu_slot' and c['resume_stage']=='validation' and c['native_execution_code_commit'] is None
    evidence=[ref(HERE/'psnc_progress_observation.json'),ref(HERE/'waiting_boundary_check.json')]
    block='Only authorized server4GPU0 runs original PSNC2502712/start41082267, native31/50 steps1616->1625 observed '+stamp+' Shanghai. Existing BTC00e complete reviewed tools reused, no idle slot for native checks; GPU1 released and M206 human-paused.'
    c['blocker']=block;c['last_resource_check_at']=obs['recorded_at'];c['retry_after']=(now+timedelta(hours=1)).isoformat()
    p=next(c for c in work['candidates'] if c.get('experiment_id')=='M210-PSNC');assert p['stage']=='training'
    for candidate in [c,p]:
        for item in evidence:
            if item not in candidate['evidence']:candidate['evidence'].append(item)
    work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':c['id'],'kind':'resource_check','result':'blocked',
        'command':'python -B -X utf8 '+str(HERE/'observe_psnc_progress.py'),'observation':block+' Healthy in progress only. No new scientific result/terminal/failure/permission request, source, native check, resource profile, receipt, queue or launch.', 'evidence':evidence}
    work['updated_at']=now.isoformat();save(ROOT/'pipeline/research_work.json',work)
    assert {n:sha(ROOT/'pipeline'/n) for n in names}==before
    memory=(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('## Last Tick',1)[0].rstrip()
    lines=memory.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('- 最新接管'):
            lines[i]='- 最新接管f34f60e9728a46d29c554c10cf3b0934；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致，generated2026-10-24T14:07:54.301549UTC/原deadline15:07:54.301549UTC不延长。前e118已FINALIZED/released且无ownedlock/pending才begin；本轮真实report/finish结果见receipt，不预签。'
        elif line.startswith('- 当前唯一M210'):
            lines[i]='- 当前唯一M210-PSNC running server4GPU0/PID2502712/start41082267；'+stamp+'上海原argv/cwd/fd1唯一log/HEAD43/GPU0UUID双核，Train31/50 1616→1625/4686，无error/logfresh，GPU0原context。proof本轮psnc_progress_observation.json SHA676c154f49fb7c809996ccb635bea67fd1768d016dcc5472145dbf5d5f773ef9；未查询/使用GPU1。'
    for i,line in enumerate(lines):
        if line.startswith('- 当前8旧hold'):
            lines[i]=line.replace('- 当前8旧hold','- 最近2747轮8旧hold',1)
    memory='\n'.join(lines)+'\n\n## Last Tick\n'
    memory+='- 本轮f34 begin一次monitor/goal/既有派发，design预算2/reserve2/creation2；1running/0readywaiting，0newterminal/operationalissue，0due/10blockednotdue。BTC00e现成完整工具复用，不因compact reserve0再造候选或重复46/10/589检查。\n'
    memory+='- '+stamp+'上海精确原PSNC2502712/start41082267/argv/cwd/fd1/HEAD43/GPU0UUID，native31/50 1616→1625/4686增长、无error；健康进行，正式validation指标本轮未采集，M95仍best.5020距目标.5100差.0080。\n'
    memory+='- 最小waiting边界复核'+ref(HERE/'waiting_boundary_check.json')['path']+' SHA'+sha(HERE/'waiting_boundary_check.json')+'无实质问题：原PSNC/406receipt、BTC00e/native执行null/3小metadata锚、M206暂停、main43/index/status保持；旧28字节hash证据复用，本轮不重hash源码/整包26/14/12/大标准证据。\n'
    memory+='- 本轮真实BTC resource_check blocked同归候选；8旧hold/notdue授权或655正文不重读/重hash/重开，0新candidate/模型改动/native/profile/commit/sync/receipt/queue/launch，不动GPU1/M206/原运行、goal/SERVERS/协议/禁用项/调度。\n'
    memory+='- 只有健康训练/资源等待，无新实质成果/完成/失败/用户决定，DONT_NOTIFY。六段report/七段memory后原token真实finish及FINALIZED/released、lock/pending消失核验；释放后不回写。\n'
    assert memory.count('\n## ')==7 and len(memory.splitlines())<120;save(ROOT/'pipeline/codex_memory.md',memory)
    notes={'actions':['核验actualowner/target、canonical技能/experimentfirst、最新memory和未变goal/SERVERS及WindowsDisabled；前e118 FINALIZED/released、无ownedlock/pending后begin，原deadline不延长。',
        'begin已一次monitor/goal/已有派发，0newterminal/operationalissue、0due/10notdue；PSNC唯一running，M206人工暂停，BTC现成工具等待唯一GPU0。',
        stamp+'上海只读双核原PSNC2502712/start41082267/argv/cwd/fd1原log/HEAD43/GPU0UUID，Train31/50 1616→1625/4686增长且无error；未查或用GPU1、无新计算或进程处置。',
        '一次最小waiting边界核PSNC receiptJSON、BTC00e/native执行null与3小metadata锚、M206暂停和main43/index/status；完整源码/26/14/12map/大标准不重hash，46/10/589测试不重复，旧28字节证据复用。',
        '当前BTC真实resource_check blocked及本轮新证据已保存；旧hold/notdue与655正文/授权正文不复核或重开，无新候选/模型变动/原生/profile/version/sync/receipt/queue/launch。',
        '仅健康进行和资源等待，DONT_NOTIFY；七段memory/六段report后真实finish并查receipt及lock/pending释放，释放后不回写。'],
        'decisions':['延续已授权PSNC原run与BTC既有完整准备，无新增路线/操作决策；无新实质成果/完成/失败/用户事项，静默。']}
    save(HERE/'tick_notes.json',notes)
    save(HERE/'resource_wait_persistence.json',{'recorded_at':now.isoformat(),'token':TOKEN,'evidence':evidence,'notification':'DONT_NOTIFY',
        'new_scientific_result':False,'protected_registries_unchanged':{n:sha(ROOT/'pipeline'/n)==h for n,h in before.items()}})
    print(json.dumps({'recorded':'resource_check_blocked','native_progress':[a['train_progress'],b['train_progress']],'new_candidates':0,'native_checks':'NOT_RUN','notification':'DONT_NOTIFY'}))
finally:lock.close()
