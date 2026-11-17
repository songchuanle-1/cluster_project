"""Current-owner original WFC observation and due NEC physical precondition check."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
import hashlib,json,os,subprocess,sys

ROOT=Path('D:/project/cluster_project'); P=ROOT/'pipeline'; HERE=Path(__file__).resolve().parent
EXPECTED={'token': 'aa802fed2fbd4f43a19795bbcf8e281e', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-04T10:17:15.272959+00:00', 'deadline_at': '2026-11-04T11:17:15.272959+00:00', 'context_sha256': 'ae1b6478daf6ac6ee7f8e54f1777dbbc0c014272229684cdaa99a9476a78cd88', 'pending_sha256': '3215eeac474df47c9b0141a8cd83675c03704bfc49299150a88a8e67dcd83c21'}
CID='hierarchy-coupled-node-edge-state-composition'; ID='M226-WFC'
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def ref(p): return dict(path=Path(p).relative_to(ROOT).as_posix(),sha256=sha(p))
def now(): return datetime.now(timezone.utc).isoformat()
def guard():
    owner=load(P/'headless/.foreground.lockdir/owner.json'); assert {k:owner.get(k) for k in EXPECTED}==EXPECTED
    assert os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
    assert load(P/'execution_mode.json')==dict(mode='foreground',target_thread_id=EXPECTED['thread_id'])
    assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
    assert sha(P/'headless/.tick_context.json')==EXPECTED['context_sha256'] and sha(P/'headless/.tick_context_state.next.json')==EXPECTED['pending_sha256']
def save(p,v,exclusive=False):
    guard(); p=Path(p)
    if exclusive:
        with p.open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
    else:
        temp=p.with_name(p.name+'.aa802fed.tmp')
        with temp.open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
        guard(); os.replace(temp,p)
def git(*args): return subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-c','core.fsmonitor=false','-C',str(ROOT/'Cluster'),*args])
def snapshot():
    old=load(P/'diagnostic_bundles/tick_25fc0b57/protected_assets_before.json')
    ix=Path(git('rev-parse','--git-path','index').decode().strip()); ix=ix if ix.is_absolute() else ROOT/'Cluster'/ix
    w=load(P/'research_work.json')
    return dict(owner=EXPECTED,head=git('rev-parse','HEAD').decode().strip(),status_hex=git('status','--porcelain=v1','--untracked-files=all','-z').hex(),
        index_sha256=sha(ix),index_empty=not git('diff','--cached','--name-only','-z'),
        files={n:sha(ROOT/'Cluster'/n) for n in old['files']},WFC_source_paths={n:sha(ROOT/'Cluster'/n) for n in old['WFC_source_paths']},
        LFT_source_paths={n:sha(ROOT/'Cluster'/n) for n in old['LFT_source_paths']},
        protected_ledgers={n:sha(P/n) for n in old['protected_ledgers']},
        candidate_digests={c['id']:digest(c) for c in w['candidates']},research_work_sha256=sha(P/'research_work.json'),memory_sha256=sha(P/'codex_memory.md'),
        settings={n:sha(ROOT/n) for n in ['SERVERS.yaml','pipeline/goal.json','pipeline/closure_policy.json','pipeline/authorizations/server4_gpu0_20261104.json','pipeline/authorizations/m226_resume_gpu0_20261104.json']})
def protect(b):
    current=snapshot()
    for k in ('head','status_hex','index_sha256','index_empty','files','WFC_source_paths','LFT_source_paths','protected_ledgers','settings'): assert current[k]==b[k],k

REMOTE=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,time
assert datetime.now(timezone.utc)<datetime.fromisoformat(PARAMS['owner']['deadline_at'])
root=Path(PARAMS['root']); proc=Path('/proc')/str(PARAMS['pid'])
assert subprocess.check_output(['git','--no-optional-locks','-C',str(root),'rev-parse','HEAD'],text=True).strip()==PARAMS['commit']
source={}
for name,want in PARAMS['hashes'].items():
    actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
    assert actual==(PARAMS['yaml_sha'] if name.endswith('.yaml') else want),name
    source[name]=actual
assert hashlib.sha256(Path(PARAMS['extension']['path']).read_bytes()).hexdigest()==PARAMS['extension']['sha256']
def identity():
    stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
    args=[a.decode() for a in (proc/'cmdline').read_bytes().split(b'\0') if a]
    assert stat[19]==PARAMS['starttime'] and proc.stat().st_uid==os.getuid() and stat[0] not in ('Z','X')
    assert os.readlink(proc/'cwd')==str(root) and os.readlink(proc/'fd/1')==PARAMS['log']
    assert args==['python','tools/train.py',PARAMS['config'],'--gpu_ids','0','--num_gpus','1','--resume',PARAMS['resume_from']]
    return dict(pid=PARAMS['pid'],starttime=stat[19],argv=args,cwd=str(root),stdout=PARAMS['log'])
def sample():
    p=Path(PARAMS['log']); size=p.stat().st_size
    with p.open('rb') as f:f.seek(max(0,size-260000)); text=f.read().decode(errors='replace')
    assert not any(x in text for x in ('Traceback (most recent call last):','CUDA out of memory','RuntimeError:'))
    train=[(int(a),int(b)) for a,b in re.findall(r'Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+',text)]
    val=[(int(a),int(b)) for a,b in re.findall(r'Val\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+',text)]
    return dict(observed_at=datetime.now(timezone.utc).isoformat(),log_size=size,train=max(train) if train else None,val=max(val) if val else None)
before=identity(); a=sample(); time.sleep(15); b=sample(); after=identity(); assert before==after
prefix='/data/songcl/Project/Cluster_project/Cluster_checkpoints/'+Path(PARAMS['config']).stem+'/'
loggers=[]
for fd in (proc/'fd').iterdir():
    try:
        name=os.readlink(fd)
        if name.startswith(prefix) and name.endswith('.log'): loggers.append(name)
    except OSError:pass
loggers=sorted(set(loggers)); assert len(loggers)==1
with open(loggers[0],encoding='utf-8',errors='replace') as f: metric_lines=[line.strip() for line in f if 'resume start_epoch:' in line or 'mIoU :' in line]
resume=[m for line in metric_lines for m in re.findall(r'resume start_epoch:(\d+),best_miou:([0-9.eE+-]+),epochs_no_improve:(\d+)!',line)]
assert len(resume)==1 and int(resume[0][0])==26 and int(resume[0][2])==5
queries={}
for k,cmd in dict(gpu=['nvidia-smi','-i','0','--query-gpu=index,uuid,utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],compute=['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits']).items():
    r=subprocess.run(cmd,text=True,capture_output=True,timeout=15); assert r.returncode==0
    queries[k]=dict(command=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
row=queries['gpu']['stdout'].strip().split(','); assert row[0].strip()=='0' and row[1].strip()==PARAMS['uuid']
contexts=[(x.split(',')[0].strip(),int(x.split(',')[1])) for x in queries['compute']['stdout'].splitlines() if ',' in x]
assert (PARAMS['uuid'],PARAMS['pid']) in contexts
def grew(key): return a[key] is not None and b[key] is not None and tuple(b[key])>tuple(a[key])
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),hostname=socket.gethostname(),owner=PARAMS['owner'],
    identity_before=before,identity_after=after,source_hashes=source,source_commit=PARAMS['commit'],samples=[a,b],
    train_progress_increased=grew('train'),validation_progress_increased=grew('val'),native_logger=loggers[0],metric_lines=metric_lines,
    restored_meta=dict(start_epoch=int(resume[0][0]),best_miou=float(resume[0][1]),epochs_no_improve=int(resume[0][2])),
    queries=queries,resource_precondition=dict(server='server-4',allowed_gpu_ids=[0],busy_gpu_ids=[0],idle_gpu_ids=[],result='blocked'),
    GPU1='NOT_QUERIED_NOT_AUTHORIZED',new_model_or_backward_executed=False,checkpoint_body_loaded=False,signals_sent=False)))
'''
def main():
    guard(); sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline'); import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT)); assert lock is not None
    try:
        guard(); b=snapshot(); save(HERE/'protected_assets_before.json',b,True)
        q=load(P/'queue.json'); t=next(t for t in q['gpu_queues']['server-4'] if t['id']==ID)
        assert t['status']==t['training_status']=='running' and t['pid']==678134 and t['runtime_starttime']=='138058005'
        k=load(P/'diagnostic_bundles/tick_d94467a9/dual_original_run_observer/constants.json')
        prepared=load(P/'manual_ops/20261104_wfc_gpu0_start/runtime_preparation_and_checkpoint.json')['data']
        params=dict(owner=EXPECTED,pid=t['pid'],starttime=t['runtime_starttime'],root=t['remote_code_root'],config=t['config'],log=t['log'],
            resume_from=t['resume_from'],commit=t['code_commit'],hashes=k['WFC']['hashes'],yaml_sha=k['DEPLOYED_YAML_SHA256'],uuid=k['WFC']['gpu_uuid'],extension=prepared['compiled_extension'])
        run=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input='PARAMS='+repr(params)+'\n'+REMOTE,text=True,encoding='utf-8',capture_output=True,timeout=65)
        result=dict(owner=EXPECTED,recorded_at=now(),returncode=run.returncode,stdout=run.stdout,stderr=run.stderr,command='pinned SSH key/known host; python -B stdin; original WFC identity/source/native progress plus GPU0 physical precondition only')
        if run.returncode==0:
            result['observation']=json.loads(run.stdout); x=result['observation']; vals,best,noimp=mon.parse_native_lineage('\n'.join(x['metric_lines']),resumed=True)
            x['precise_current_native_validation']=dict(values=vals,best=best,no_improve=noimp,has_new_validation=vals is not None,
                restored_best=x['restored_meta']['best_miou'],restored_no_improve=x['restored_meta']['epochs_no_improve'])
        save(HERE/'wfc_original_run_and_resource_observation.json',result,True); assert run.returncode==0,run.stderr[-1200:]
        x=result['observation']; assert x['train_progress_increased'] or x['validation_progress_increased']
        metrics=x['precise_current_native_validation']; assert metrics['best'] is None or metrics['best']<.502,'Material result needs visible followup'
        protect(b); w=load(P/'research_work.json'); c=next(c for c in w['candidates'] if c['id']==CID); assert c['stage']=='validation' and c['native_status']==c['resource_status']=='NOT_RUN'
        entry=ref(HERE/'wfc_original_run_and_resource_observation.json'); c['evidence'].append(entry)
        previous=c.get('native_execution_blocker')
        if previous: c.setdefault('native_execution_blocker_history',[]).append(previous)
        c['native_execution_blocker']=dict(kind='occupied_authorized_gpu',server='server-4',observed_at=x['observed_at'],allowed_gpu_ids=[0],busy_gpu_ids=[0],original_tasks=[ID],evidence=entry,
            scope='Physical precondition only. Current runtime is original WFC94 in new root; old NEC GPU1/runtime4457 draft still needs separate reviewed metadata adaptation. No model/backward/resources entered.')
        c['last_resource_check_at']=x['observed_at']; c['retry_after']=(datetime.fromisoformat(x['observed_at'])+timedelta(hours=1)).isoformat()
        previous=w.get('tick_attempt')
        if previous and previous.get('tick_started_at')!=EXPECTED['generated_at']: w.setdefault('tick_attempt_history',[]).append(previous)
        w['tick_attempt']=dict(tick_started_at=EXPECTED['generated_at'],candidate_id=CID,kind='resource_check',result='blocked',
            command='python -B -X utf8 '+str(Path(__file__).resolve()),observation='Fresh original resumed WFC PID/start/source/native progress and authorized GPU0 physical context verified. Sole allowed card occupied. NEC activation/native check not entered; source/runtime/GPU metadata port remains needed.',evidence=[entry]); w['updated_at']=now()
        assert all(digest(z)==b['candidate_digests'][z['id']] for z in w['candidates'] if z['id']!=CID)
        samples=x['samples']; summary=f"WFC原PID678134/start138058005/source94/GPU0，{samples[0]['observed_at']}→{samples[1]['observed_at']} TRAIN{samples[0]['train']}→{samples[1]['train']}、VAL{samples[0]['val']}→{samples[1]['val']}，log增长{samples[1]['log_size']-samples[0]['log_size']}B；新完整val数{len(metrics['values']) if metrics['values'] is not None else 0}，当前精确best={metrics['best'] if metrics['best'] is not None else metrics['restored_best']}、noimp={metrics['no_improve'] if metrics['no_improve'] is not None else metrics['restored_no_improve']}（含已恢复seed）。"
        memory=(P/'codex_memory.md').read_text(encoding='utf-8'); lines=memory.splitlines()
        lines=[('- 当前owner'+EXPECTED['token']+'，generated'+EXPECTED['generated_at']+'/deadline'+EXPECTED['deadline_at']+'；实际root thread与target一致，不延租约；完成和释放仅以真实receipt为准。' if z.startswith('- 最近研究owner') or z.startswith('- 当前owner') else
            '- M226-WFC：原无序楔机制/原协议保持；'+summary if z.startswith('- M226-WFC：') else z) for z in lines]
        memory='\n'.join(lines)+'\n'; memory=memory.replace('上轮48fe3373实际FINALIZED/PASS/context_committed/released于2026-11-04T06:16:30.878894+00:00','上轮828cd503实际FINALIZED/PASS/context_committed/released于2026-11-04T08:43:25.648328+00:00'); a=memory.index('## Last Tick'); memory=memory[:a]+f'''## Last Tick
- begin{EXPECTED['generated_at']}先查原WFC进度并尝试已有ready派发，无终态/故障/readywaiting；creation/reserve_budget0、NEC/MIC两个储备已准备，不新建候选/复制草案/重跑旧suite。
- 本轮一次真实只读原续训观察：{summary}唯一授权物理GPU0仍由原WFC占用；仅资源前置blocked证据归NEC，不是候选模型/backward/profile失败。
- 新root的原94模型8py/确定性YAML及compiled扩展SHA、PID/start/argv/cwd/stdout与物理UUID核真；不使用旧原2085005或LFT双卡观察器。NEC旧GPU1/旧root/runtime4457草案不能直接重放，GPU0忙时不激活，未来元数据端口须明确local primary4457/source parent4457和remote runtime94的区别。
- 0源码/版本/模型修订/nativearm/准入/新训练/终态；其他154候选、LFT/M206暂停、GPU1禁用、当前38账/用户28/index/两run18本地源保持。辅助代理仅做只读核对，无文件写/remote/第二次测试。
- 仅健康进度和已知资源等待，无新的科学结论或用户动作，DONT_NOTIFY。六段report/七段memory先持久化，finish/release按真实receipt核；不能把当轮收尾当方法有效或启动新实验。
'''
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        notes=dict(actions=[summary,'本轮新增一次原续训/source/物理GPU0观察，NEC真实resource_check被既有WFC占槽阻断，未进入新模型、backward、profile、active binding或诊断三锁。','候选创建与储备预算为0，NEC/MIC已有两包准备；没有为凑额度制造新草案、重复旧suite、借原运行的验证当新候选结果。','0源码提交/修订/准入/新训练/终态；LFT/M206暂停、GPU1禁用、其他154候选和38账/用户28/index/运行18源保持。'],
            decisions=['冠军M95仍.5020，目标.5100/gap.0080；原WFC继续原版本数据种子/50epochs/patience10，不重新恢复、调参或额外早停。','NEC元数据适配必须另存并审查physical0/新root/runtime94，不能改原source parent4457、补签旧NULL草案或重放旧租约。原生模型/资源执行等待当时真实授权独占空卡。','仅健康运行与相同资源等待，无可行动用户事项，DONT_NOTIFY；按真实report/finish/release收尾。'])
        protect(b); save(P/'research_work.json',w); temp=P/'codex_memory.aa802fed.tmp'; temp.write_text(memory,encoding='utf-8',newline='\n'); guard();os.replace(temp,P/'codex_memory.md')
        save(HERE/'final_report_notes.json',notes,True); protect(b)
        save(HERE/'preclosure_actual_state.json',dict(owner=EXPECTED,recorded_at=now(),work_sha256=sha(P/'research_work.json'),memory_sha256=sha(P/'codex_memory.md'),
            evidence=[entry],notes=ref(HERE/'final_report_notes.json'),candidate_stage_counts=dict(Counter(z['stage'] for z in w['candidates'])),
            all154_other_candidates_and_all38_lifecycle_user28_source18_index_preserved=True,notify='DONT_NOTIFY',finish='NOT_YET_RUN'),True)
        print(json.dumps(dict(status='OBSERVED_RESOURCE_BLOCK_PERSISTED_FINISH_PENDING',evidence=entry,summary=summary,notify='DONT_NOTIFY'),ensure_ascii=False))
    finally: lock.close()
if __name__=='__main__': main()
