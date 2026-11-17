"""Record actual busy GPU0 and reuse the complete unchanged BCR preparation."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,os,sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
TOKEN='3ef7cd268db648efa99cf9b67f30127e'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
    q=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with q.open('x',encoding='utf-8') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(q,p)
owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
obs=read(HERE/'btc_progress_observation.json');a,b=[x['data'] for x in obs['observations']]
assert sha(HERE/'btc_progress_observation.json')=='bfd5940b5c64f0a9769dbc891162abfaf62ea3271628d3a1adfd7444ba3f59a9'
assert obs['same_exact_registered_process_and_native_TRAIN_growth'] and a['train_progress']==[12,50,1461,4686] and b['train_progress']==[12,50,1468,4686]
assert a['pid']==b['pid']==2784474 and a['start_ticks']==b['start_ticks']=='47557208' and not a['errors'] and not b['errors']
assert read(HERE/'waiting_boundary_check.json')['material_concerns']==[]
stamp=datetime.fromisoformat(obs['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor
lock=monitor.acquire_lock(str(ROOT));assert lock is not None
try:
    names=['queue.json','running.json','experiments/M211-BTC.json','experiments/M210-PSNC.json','experiments/M206-CGCA.json','admissions/M211-BTC.json','admissions/M210-PSNC.json']
    before={n:sha(ROOT/'pipeline'/n) for n in names}
    assert monitor.load_running(str(ROOT))['server-4']=={'0':'M211-BTC'}
    work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c.get('experiment_id')=='M212-BCR');live=next(c for c in work['candidates'] if c.get('experiment_id')=='M211-BTC')
    assert c['stage']=='blocked' and c['resume_stage']=='validation' and c['blocker_kind']=='exclusive_gpu_slot' and c['code_commit']=='11a811618179ab1ddc0cee299194667413b7fdb9' and c['native_execution_code_commit'] is None and live['stage']=='training'
    assert c['operational_preparation_status']=='COMPLETE_STATIC_GUARDED_PACKET_NATIVE_NOT_RUN'
    evidence=[ref(HERE/'btc_progress_observation.json'),ref(HERE/'waiting_boundary_check.json')]
    block='Only authorized server4GPU0 runs original BTC2784474/start47557208, native12/50 1461->1468/4686 observed '+stamp+' Shanghai. Existing BCR11a complete reviewed tools reused; no idle slot for its native checks. GPU1 released and M206 human-paused.'
    c['blocker']=block;c['last_resource_check_at']=obs['recorded_at'];c['retry_after']=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    for candidate in [c,live]:
        for item in evidence:
            if item not in candidate['evidence']:candidate['evidence'].append(item)
    work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':c['id'],'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+str(HERE/'observe_btc_progress.py'),'observation':block+' Healthy in progress only. No new scientific result/terminal/failure/permission request, source, native check, resource profile, receipt, queue or launch.','evidence':evidence}
    work['updated_at']=datetime.now(timezone.utc).isoformat();save(ROOT/'pipeline/research_work.json',work)
    assert {n:sha(ROOT/'pipeline'/n) for n in names}==before
    memory=(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('\n## Last Tick\n',1)[0].replace('本轮','前57ec轮').replace('- 新准备M212-BCR','- 已准备M212-BCR').rstrip()
    lines=memory.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('- 最新接管'):
            lines[i]='- 最新接管'+TOKEN+'；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致；generated'+owner['generated_at']+'/原deadline'+owner['deadline_at']+'不延长。前57ec已FINALIZED/released且lock/pending消失才begin；本轮真实finish结果见receipt，不预签。'
        elif line.startswith('- 当前唯一M211-BTC'):
            lines[i]='- 当前唯一M211-BTC server4 GPU0/PID2784474/start47557208；'+stamp+'上海原argv/cwd/fd1唯一log/HEAD00e/UUID0双核，native12/50 1461→1468/4686增长且无error，GPU0为原进程context。proof pipeline/diagnostic_bundles/tick_3ef7cd26/btc_progress_observation.json SHAbfd5940b5c64f0a9769dbc891162abfaf62ea3271628d3a1adfd7444ba3f59a9；GPU1未查询/使用。'
        elif line.startswith('- M212-BCR仅完整静态准备'):
            lines[i]='- M212-BCR完整静态工具/版本11a准备已齐，blocked等待原生GPU检查，未入队；本轮0due旧holds不重读655正文/授权正文、不重hash或重开。'
    memory='\n'.join(lines)+'\n\n## Last Tick\n'
    memory+='- 本轮3ef begin一次monitor/goal/已有派发，design预算2/reserve2/creation2；1running/0ready/0newterminal/0operationalissue，0due/10blockednotdue。完整BCR11a工具复用，不因compact reserve0重复准备或再造占位候选。\n'
    memory+='- '+stamp+'上海原BTC2784474/start47557208/argv/cwd/fd1/HEAD00e/UUID0双核，Train12/50 1461→1468/4686增长，无error/logfresh；健康运行，正式validation指标本轮未采集。\n'
    memory+='- 一次最小12项等待边界复核'+ref(HERE/'waiting_boundary_check.json')['path']+' SHA'+sha(HERE/'waiting_boundary_check.json')+'无concern：BTC receipt9375/原PID、BCR11a/native null/3小outer12dc-nativea7ba-release4a66锚、M206pause/main00e/index/status28保持；28bytes复用41eb实际版本证据。\n'
    memory+='- 本轮真实resource_check blocked及两份新证据归属BCR/BTC；不遍历17/28/14/12maps/4raw/大标准/旧hold/授权，不重跑1334/24/49或native，不改源码/提交/收据/queue/launch/资源/调度。BCR全部原生与资源仍NOT_RUN，效果UNKNOWN。\n'
    memory+='- 只有健康训练和相同资源等待，无新成果/完成/失败/用户决定，DONT_NOTIFY。六段report/七段memory后原token真实finish并核FINALIZED/released及lock/pending消失，释放后不回写。\n'
    assert memory.count('\n## ')==7 and len(memory.splitlines())<120;save(ROOT/'pipeline/codex_memory.md',memory)
    notes={'actions':['核验actual owner/target、canonical前台规则/experiment-first、最新memory/未变goal-SERVERS及WindowsDisabled；前57ec FINALIZED/released、无lock/pending后一次begin，原deadline不延长。','begin一次monitor/goal/已有派发：1running/0ready，0newterminal/operationalissue，0due/10blockednotdue。当前BTC占用唯一授权GPU0，现成BCR完整准备无原生测试空槽。',stamp+'上海只读双核原BTC2784474/start47557208/原argv-cwd-fd1-log/HEAD00e/UUID0，Train12/50 1461→1468/4686增长且无error/logfresh，GPU1未查未用。','一次最小12项等待边界核BTC receipt/原PID、BCR11a/native null与3小metadata锚、M206pause、main00e/index/status28；28bytes仅复用41eb版本前后证据，不重hash整包/source/raw/大标准，不重复1334/24/49或旧hold/授权复核。','BCR实际resource_check blocked及当前证据已保存；0新candidate/源码/commit/native/profile/receipt/queue/launch，不动GPU1/M206/BTC原run、goal/SERVERS/协议/禁用项/调度。','仅健康训练与同资源等待，静默DONT_NOTIFY；七段memory/六段report后真实finish并核receipt与lock/pending释放，释放后不回写。'],'decisions':['复用完整BCR11a准备，等待原BTC自然完成后的真正空GPU0，保留全部原生/资源UNKNOWNs；无新研究或操作决策，无用户待处理事项。']}
    save(HERE/'tick_notes.json',notes)
    save(HERE/'resource_wait_persistence.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'evidence':evidence,'notification':'DONT_NOTIFY','new_scientific_result':False,'protected_registries_unchanged':{n:sha(ROOT/'pipeline'/n)==h for n,h in before.items()}})
    print(json.dumps({'recorded':'resource_check_blocked','native_progress':[a['train_progress'],b['train_progress']],'new_candidates':0,'native_checks':'NOT_RUN','notification':'DONT_NOTIFY'}))
finally:lock.close()
