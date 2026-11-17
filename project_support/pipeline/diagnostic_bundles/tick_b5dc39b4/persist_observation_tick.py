"""Persist actual resource contention without scientific PASS or any process action."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='b5dc39b4780a44c6855520bc22692b65';CTS='hierarchy-parent-cyclic-triadic-state-composition'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x):
    temporary=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with temporary.open('x',encoding='utf8') as f:
        if isinstance(x,str):f.write(x)
        else:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
        f.flush();os.fsync(f.fileno())
    os.replace(temporary,p)
def add(c,paths):
    for p in paths:
        item=ref(p)
        if item not in c.setdefault('evidence',[]):c['evidence'].append(item)
def main():
    owner=guard()
    assert not any((HERE/n).exists() for n in ['persist_intent.json','final_tick_persisted.json','codex_memory_before_finalization.md'])
    snapshot=read(ROOT/'pipeline/headless/.tick_model_view.json')
    assert snapshot['experiment_first']['enabled'] and snapshot['research']['creation_budget']==snapshot['research']['reserve_budget']==0
    assert snapshot['queue']['running_count']==2 and snapshot['queue']['ready_waiting_count']==0 and snapshot['changes']['new_terminal_ids']==[]
    observation_path=HERE/'active_runs_progress_observation.json';observation=read(observation_path)
    local_path=HERE/'cts_actual_local_guard_integration.json';local=read(local_path)
    assert sha(observation_path)=='94db2bf8bcab2c3870d7a9d5fb91c32056da93ce4006685e8261304ede22ac62'
    assert sha(local_path)=='5543eb11dd7ae41d92799784f737564ee97a4d2433f2360bf0e6a1ee3a0df0ee'
    assert all(x['native_TRAIN_growth'] for x in observation['summary'])
    assert local['actual_transport_calls']==0 and local['active_binding_manifest_lease_or_execution_directory_created'] is False
    assert local['native_execution']==local['resources']=='NOT_RUN' and local['current_owner_token']==TOKEN
    review_path=HERE/'progress_and_readiness_review.json';review=read(review_path)
    assert isinstance(review['material_concerns'],list) and review['material_concerns']
    extra_path=HERE/'additional_gpu_context_probe.json';extra=read(extra_path)
    assert sha(extra_path)=='3eb859cd4be49b516f36576df29d50455719096470ca37dc4aeb1c63ae7f0552'
    assert extra['current_project_queue_pid_matches']==[] and extra['signals_sent'] is False and extra['remote_file_writes'] is False
    assert extra['extra_process_metadata']==[{'pid':1565126,'observed':False,'error_type':'PermissionError'}]
    contexts={(line.split(',')[0].strip(),int(line.split(',')[1])) for line in extra['compute_contexts'].splitlines()}
    assert contexts=={('GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',219369),('GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1565126),
        ('GPU-7f82edb9-f620-8045-caea-a75232265cd1',1215422),('GPU-7f82edb9-f620-8045-caea-a75232265cd1',1565126)}
    held_path=HERE/'held_boundary_check.json';held=read(held_path)
    assert held['material_concerns']==[] and held['new_action'] is False and held['user_decision'] is False
    assert not (HERE/'cts_execution').exists() and not (HERE/'bec_execution').exists()
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();before=read(HERE/'protected_assets_before.json')
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        work=read(ROOT/'pipeline/research_work.json');old=copy.deepcopy(work)
        assert len(work['candidates'])==len(before['candidate_digests'])==141
        c=next(c for c in work['candidates'] if c['id']==CTS)
        assert c['stage']=='validation' and c['code_commit']=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d' and c['native_execution_code_commit'] is None
        assert c['execution_adapter'].get('actual_current_local_guard')!=ref(local_path)
        c['execution_adapter']['actual_current_local_guard']=ref(local_path)
        c['execution_adapter']['latest_readonly_resource_review']=ref(review_path)
        c['native_status']='NOT_RUN_ORIGINAL_JOBS_PLUS_UNREGISTERED_EXTRA_GPU_CONTEXTS'
        c.setdefault('resource_wait_history',[]).append(copy.deepcopy(c.get('resource_wait',{})))
        c['resource_wait']={'allowed_server':'server-4','allowed_physical_gpus':[0,1],
            'observed_at':observation['observations'][-1]['observed_at'],
            'observed_tasks':{'0':{'id':'M213-BFC','pid':219369,'start_ticks':'56265957'},'1':{'id':'M212-BCR','pid':1215422,'start_ticks':'51717921'}},
            'evidence':[ref(observation_path),ref(local_path),ref(extra_path)],
            'additional_unregistered_gpu_pid':1565126,'additional_gpu_memory_MiB':{'0':9594,'1':9804},
            'additional_process_identity':'UNKNOWN_PERMISSION_ERROR_NO_ESCALATION',
            'scope':'Original native TRAIN growth and exact UUID preserved. Both devices also contain extraPID1565126 outside current queue; identity UNKNOWN because minimal proc metadata was permission-denied. Preserve all processes. Blocked resource check grants no idle/native lease and changes no scientific gates.'}
        add(c,[observation_path,local_path,review_path,extra_path])
        for eid in ['M213-BFC','M212-BCR']:
            running=next(x for x in work['candidates'] if x.get('experiment_id')==eid)
            add(running,[observation_path,review_path,extra_path])
            running['latest_runtime_observation']={'evidence':ref(observation_path),'independent_review':ref(review_path),
                'shared_runtime_commit':'48fc302c3c02ffef0b241be3593c386b6b65a72e','admitted_source_unchanged':running['code_commit'],
                'additional_gpu_pid':1565126,'additional_process_identity':'UNKNOWN_PERMISSION_ERROR_NOT_IN_CURRENT_PROJECT_QUEUE',
                'scope':'Read-only original process/source/log/UUID and real TRAIN growth. Each card additionally containsPID1565126; original task is not exclusive. No restart/migration/signal or operation on any job.'}
        work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CTS,'kind':'resource_check','result':'blocked',
            'command':"python -B -X utf8 'D:/project/cluster_project/pipeline/diagnostic_bundles/tick_b5dc39b4/check_cts_actual_guard.py'",
            'observation':'Existing CTS catalog passes current guards, but both selected cards refuse as registered running before transport. Actual source/log/process samples confirm original BFC0/BCR1 TRAIN growth. New resource change: extraPID1565126 appears on both GPUs using9594/9804MiB, absent current project queue; minimal proc identity lookup was PermissionError, no privilege escalation or retry. Both cards around90percent total memory occupied. No uniqueness/exclusivity claim or idle slot; no native/model/resource experiment, active artifacts/admission/launch/process signal.',
            'evidence':[ref(local_path),ref(observation_path),ref(review_path),ref(extra_path)]}
        work['updated_at']=datetime.now(timezone.utc).isoformat()
        permitted={CTS,'hierarchy-parent-butterfly-token-composition','hierarchy-parent-bidirectional-complement-recurrence'}
        assert [x for x in work['candidates'] if x['id'] not in permitted]==[x for x in old['candidates'] if x['id'] not in permitted]
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        with (HERE/'persist_intent.json').open('x',encoding='utf8') as f:
            json.dump({'token':TOKEN,'helper_sha256':sha(Path(__file__)),'research_work_before_sha256':sha(ROOT/'pipeline/research_work.json'),
                'scope':'Once-only resource observation bookkeeping; existing journal or current evidence requires readonly reconciliation, never replay.'},f,indent=2)
            f.write('\n');f.flush();os.fsync(f.fileno())
        save(ROOT/'pipeline/research_work.json',work)
        memory_path=ROOT/'pipeline/codex_memory.md';memory=memory_path.read_text('utf8')
        with (HERE/'codex_memory_before_finalization.md').open('xb') as f:f.write(memory_path.read_bytes())
        lines=memory.splitlines();i=next(i for i,line in enumerate(lines) if line.startswith('- 最新接管'))
        lines[i]=f'- 最新接管{TOKEN}；实际owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner["generated_at"]}/原deadline{owner["deadline_at"]}不延长。前f86d FINALIZED/released且lock/pending消失后begin；本轮report/finish以实际receipt为准，不预签。'
        stamp=datetime.fromisoformat(observation['observations'][-1]['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
        i=next(i for i,line in enumerate(lines) if line.startswith('- 采集'))
        lines[i]=f'- 采集{stamp}上海：BFC原PID219369/start56265957 GPU0 Train10/50 1086→1093/4686；BCR原PID1215422/start51717921 GPU1 Train21/50 3551→3556/4686。两原TRAIN增长/8源/YAML77e/argv-cwd-fd1/UUID保持，proof94db2bf8…；各卡另有PID1565126，不可称唯一context或独占。当前best等指标未测，不用cursor/缓存代签。'
        i=next(i for i,line in enumerate(lines) if line.startswith('- 本轮旧9 parked不due'))
        lines[i]='- 本轮旧9到期，仅声明candidate内容/证据path-hash签名及授权目录元数据有界复核；未改候选/读655正文/旧grant正文/checkpoint body。新动作/用户决定均false，原scope/失败/修订上限/M206pause保持，复查不是新授权。'
        memory='\n'.join(lines)+'\n'
        memory=memory.replace('- 本轮f86d CTS只读','- 前f86d CTS只读').replace('- 本轮f86d BEC禁用','- 前f86d BEC禁用')
        memory=memory.replace('当前snapshot new_terminal仅识别前轮归档，不是本轮新完成，未重复archive。','前6bdb snapshot仅识别前336归档；本轮无新终态，不重复archive。')
        added='- 本轮新增资源事实：NVML额外PID1565126同时在GPU0/1使用9594/9804MiB，原BFC19714/BCR19724MiB，总显存29366/32607、29563/32607MiB（约90%）。不在本项目queue；最小/proc归属读取PermissionError，owner/start/用途UNKNOWN。只读probe3eb859cd…保留，无sudo/绕权限/重探、无signals或其他项目文件读取。未知进程受保护，不自动终止或暂停原训练。\n'
        memory=memory.replace('\n## Open Questions And Risks','\n'+added+'\n## Open Questions And Risks')
        memory=memory.split('\n## Last Tick')[0]+f'''
## Last Tick
- 本轮b5dc snapshot2running/0ready、reserve2/creation0，due11含CTS/BEC及旧9，无新terminal/operationalissue。begin已查进展/尝试派发既有合格队列，M206paused不计ready。
- 本轮只读BFC10:1086→1093、BCR21:3551→3556均增长，原PID/start/argv/log/源8/YAML77e/UUID保持；新增未登记PID1565126同时占两卡，归属PermissionError未知，约90%总显存。当前CTSguard5543eb11…两registered卡均beforetransport busy拒绝，0native/transport/active；真实resource_check=blocked，不是机制失败。
- CTS源4e8/原51cbc工具/checker82da+审5d36，BEC原2d06+disabled322c/审ecf0均沿用，不重跑已过软件检查、不造重复工具或额外模型候选。旧9声明元数据到期复核无新许可/变化，不重开旧路或恢复M206。
- 独审发现root未执行WIP错误前提“唯一context”，已保留旧草稿并更正，原94db raw不重写；追加一次必要最小只读probe3eb验证新增占用，PermissionError后停止身份探查、无权限绕过。独审保留此实质concern，不改空数组伪PASS。
- 0新候选/0实现修订/0准入/0queue/0启动/0新训练终态，141IDs集合、公共HEAD48fc/index空/28保护status+bytes/10运行归档账保持；仅CTS资源观察与两原在训观察指针更新。资源出现实质新差异需NOTIFY，不称研究增益或训练失败。
- 资源自然空槽后继续现有CTS原M95对照TRAIN2/资源；BEC保留版本兼容整理待执行项，不称缺用户授权。完整七段memory/真实blocked tick_attempt/Chinese notes及六段report，canonical finish核实际FINALIZED/released和lock/pending消失；未发生前不预签，释放后不回写。
'''
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        save(memory_path,memory)
        notes={'actions':[
            '本轮actual owner一致，前f86d已FINALIZED/released且lock/pending消失后begin；snapshot2running/0ready、reserve2/creation0，due11含CTS/BEC和旧9，无新terminal或连接/源/派发故障。M206paused不是ready，未另跑monitor。',
            '有界只读真观察：BFC GPU0 Train10 1086→1093，BCR GPU1 Train21 3551→3556，原PID/start/argv/cwd/log/8源/YAML77e/UUID保持；publicruntime48fc/BCR科学11a分开。原始NVML同时显示两卡各有额外PID1565126，不能称唯一context；当前best等实时指标未采。',
            '独审发现未执行WIP中的唯一context前提错误，保留旧草稿与原94db raw。追加一次必要最小只读probe：全UUID/PID显存确认额外1565126在GPU0/1使用9594/9804MiB，总显存约90%；该PID不在本项目queue。最小proc owner/start/script归属查询PermissionError，身份/用途UNKNOWN；停止探查，不sudo/绕权限/重试，不读其他项目文件或发信号。',
            '既有CTS受审catalog通过本轮fresh实际owner/context/原deadline/source/whitelist检查；两registered卡prepare0/1均beforetransport拒绝，14非法入口和deadline拒绝。0process/network/Torch/active，原生与资源未执行；resource_check blocked按原样留证。',
            'CTS原4e8/51cbc与前f86d checker82da/5d36，BEC原2d06与disabled322c/ecf0沿用，本轮无新工具/实现、无新机制结论；未重跑已过软件tests，未为了填额度新增模型或把静态准备写成native PASS。',
            '到期旧9仅声明元数据、证据path-hash签名与授权目录listing核验，未读655正文/旧grant正文/checkpoint body；无新授权或需用户处理项，不改旧scope/负结果/修订预算/M206暂停。',
            '0新候选/0修订/0准入/0queue/0启动/0新训练终态；保持两原运行、公共48fc/index空/28保护status+bytes、10运行归档账、141IDs/goal/资源/禁项/data/seed/schedule/YAML/调度。'],
            'decisions':['本轮新增资源差异必须如实通知：保护不明PID1565126和两个原训练，未识别用途前不自动驱逐/暂停/恢复或迁卡。原native资源独占条件未满足，CTS/BEC原生检查继续等待；原训练仍增长且无已观测错误，不记为模型失败。']}
        save(HERE/'report_notes.json',notes)
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        save(HERE/'final_tick_persisted.json',{'token':TOKEN,'new_candidates':0,'new_admissions':0,'new_launches':0,'new_terminal_experiments':0,
            'resource_check':'BLOCKED_ORIGINAL_JOBS_PLUS_UNREGISTERED_EXTRA_CONTEXTS','native':'NOT_RUN','current_progress':ref(observation_path),
            'current_CTS_guard':ref(local_path),'additional_context':ref(extra_path),'held_metadata_check':ref(held_path),'memory_lines':len(memory.splitlines()),'notification':'NOTIFY_RESOURCE_CHANGE','postflight':'NOT_YET_CALLED'})
        print(json.dumps({'status':'REAL_RESOURCE_CONTENTION_PERSISTED','resource_check':'blocked','new_research_conclusion':False,'notification':'NOTIFY_RESOURCE_CHANGE','memory_lines':len(memory.splitlines())}))
    finally:lock.close()
if __name__=='__main__':main()
