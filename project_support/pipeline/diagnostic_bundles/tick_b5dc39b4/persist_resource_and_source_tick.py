"""Persist resource contention and actual BEC isolated source version, no native PASS."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='b5dc39b4780a44c6855520bc22692b65';CTS='hierarchy-parent-cyclic-triadic-state-composition';BEC='hierarchy-cross-level-bipartite-edge-composition'
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
    assert sha(review_path)=='4118fb5675ccbcc1ad55debe9407bb338a184a018cc2ef318504dd3b8d8c74c8'
    assert isinstance(review['material_concerns'],list) and review['material_concerns']
    assert review['original_jobs_verified'] is True and review['resource_block_verified'] is True
    extra_path=HERE/'additional_gpu_context_probe.json';extra=read(extra_path)
    assert sha(extra_path)=='3eb859cd4be49b516f36576df29d50455719096470ca37dc4aeb1c63ae7f0552'
    assert extra['current_project_queue_pid_matches']==[] and extra['signals_sent'] is False and extra['remote_file_writes'] is False
    assert extra['extra_process_metadata']==[{'pid':1565126,'observed':False,'error_type':'PermissionError'}]
    contexts={(line.split(',')[0].strip(),int(line.split(',')[1])) for line in extra['compute_contexts'].splitlines()}
    assert contexts=={('GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',219369),('GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1565126),
        ('GPU-7f82edb9-f620-8045-caea-a75232265cd1',1215422),('GPU-7f82edb9-f620-8045-caea-a75232265cd1',1565126)}
    held_path=HERE/'held_boundary_check.json';held=read(held_path)
    assert held['material_concerns']==[] and held['new_action'] is False and held['user_decision'] is False
    version_path=HERE/'bec_version_execute/isolated_source_version.json';version=read(version_path)
    source_review_path=HERE/'bec_isolated_source_version_review.json';source_review=read(source_review_path)
    assert sha(version_path)=='e2f3439ead898c3f8acdc8d54d929720515aa5783650850ae2c8d20666c30f44'
    assert sha(source_review_path)=='cb7ec9d87a8fabdc32a51ebdbc593557f42afd331a96c3d4cddc3cc7aa7dfd61'
    assert source_review['material_concerns']==[] and source_review['anchors']['source_version']==ref(version_path)
    assert version['candidate_id']==BEC and version['code_commit']=='9b6782f44ca7f2c8ac35baea01dfd070314b5701'
    assert version['parent_commit']=='48fc302c3c02ffef0b241be3593c386b6b65a72e'
    assert len(version['frozen_source_files'])==9 and version['committed_blob_sha256']==version['frozen_source_files']
    assert version['primary_HEAD_index_status_28_protected_bytes_unchanged'] and version['pending_CTS_worktree_unchanged'] and version['frozen_BEC_native_unversioned_and_unchanged']
    assert all(version['protected_ledgers_unchanged'].values()) and version['native_resources_transport_queue_or_launch']=='NOT_RUN'
    assert version['native_draft_execution_binding'] is None and version['remote_operations'] is False
    assert not (HERE/'cts_execution').exists() and not (HERE/'bec_execution').exists()
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();before=read(HERE/'protected_assets_before.json')
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        work=read(ROOT/'pipeline/research_work.json');old=copy.deepcopy(work)
        assert len(work['candidates'])==len(before['candidate_digests'])==141
        c=next(c for c in work['candidates'] if c['id']==CTS)
        bec=next(c for c in work['candidates'] if c['id']==BEC)
        assert c['stage']=='validation' and c['code_commit']=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d' and c['native_execution_code_commit'] is None
        assert c['execution_adapter'].get('actual_current_local_guard')!=ref(local_path)
        assert bec['stage']=='implementation' and bec['code_commit'] is None and bec['source_commit'] is None and bec['future_version_parent'] is None
        assert bec['native_execution_code_commit'] is None
        assert bec['worker_preparation']['source_commit'] is None and bec['worker_preparation']['draft_execution_disabled'] is True
        assert sha(ROOT/bec['source_preparation']['path'])=='2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d'
        assert sha(ROOT/bec['worker_preparation']['preparation']['path'])=='322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff'
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
        bec.setdefault('source_version_history',[]).extend([
            {'recorded_at':read(ROOT/bec['source_preparation']['path'])['recorded_at'],'code_commit':None,'parent_commit':None,
                'source_preparation':copy.deepcopy(bec['source_preparation']),'scope':'Original frozen unversioned declaration retained; never backfilled.'},
            {'recorded_at':version['recorded_at'],'code_commit':version['code_commit'],'parent_commit':version['parent_commit'],
                'source_version':ref(version_path),'independent_review':ref(source_review_path),'scope':'Actual isolated9A single child48fc, sibling of pendingCTS4e8; no main/runtime promotion or native test.'}])
        bec.update(stage='validation',code_commit=version['code_commit'],source_commit=version['code_commit'],source_parent_commit=version['parent_commit'],
            future_version_parent=version['parent_commit'],source_version=ref(version_path),isolated_worktree=version['worktree'],
            version_packaging_status='ACTUAL_ISOLATED_NINE_BLOB_CHILD_OF_TESTED48FC_SIBLING_OF_PENDING_CTS_NO_FF_ASSUMPTION',
            source_status='FROZEN_NINE_BLOBS_SAVED_ISOLATED9B67_PRIMARY_RUNTIME48FC_UNCHANGED',
            implementation_status='SOURCE_VERSION_SAVED_REVIEWED_OLD_DISABLED_NATIVE322C_REQUIRES_NEW_VERSION_BOUND_COPY',
            native_status='NOT_RUN_REQUIRES_NEW_VERSION_BOUND_NATIVE_COPY_AND_GENUINELY_IDLE_RESOURCES')
        bec['version_compatibility']={'actual_parent':version['parent_commit'],'pending_sibling_CTS':'4e80006047d5cb3dcdfb9c1102e02c33f354a07d',
            'relationship':'SIBLINGS_NOT_MUTUAL_ANCESTORS_NO_DIRECT_FF','boundary':'If actual tested main changes, prepare a new compatible source version and real native checks for that exact version. Never relabel old raw evidence.'}
        bec['worker_preparation']['requires_new_version_bound_copy']={'source_commit':version['code_commit'],'source_parent_commit':version['parent_commit'],
            'frozen_native322c_unchanged':True,'old_native_source_parent_and_active_fields_remain_null':True,'native_execution':'NOT_RUN'}
        bec['next_action']='Preserve isolated BEC9b678 source9A single child of actual tested48fc and original2d06/source hashes/YAMLa18/protocol6555. Original native322c remains immutable null-versioned/DRAFTTrue; prepare a new separately reviewed version-bound native/operational copy for9b678 while live main stays48fc. BEC and pendingCTS4e8 are siblings: if main changes first, create a new compatible exact-nine-blob source version then actually test that version, never assume sibling ff or relabel results. GPU work requires fresh actual owner/context/original deadline/whitelist/UUID/liveidle/assets/three locks, with original BFC/BCR and unknown extraPID1565126 protected; no native test/admission until full real paired gates pass. Local version/package work does not require a free GPU or new permission.'
        add(bec,[version_path,source_review_path,HERE/'bec_version_prepare/preparation.json',HERE/'bec_source_version_helper_review.json',HERE/'bec_version_execute/execution_preparation.json'])
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
        work['next_action']=c['next_action']+' Existing BEC source version is now saved; its new version-bound package can be prepared locally, with sibling compatibility explicitly guarded.'
        permitted={CTS,BEC,'hierarchy-parent-butterfly-token-composition','hierarchy-parent-bidirectional-complement-recurrence'}
        assert [x for x in work['candidates'] if x['id'] not in permitted]==[x for x in old['candidates'] if x['id'] not in permitted]
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        with (HERE/'persist_intent.json').open('x',encoding='utf8') as f:
            json.dump({'token':TOKEN,'helper_sha256':sha(Path(__file__)),'research_work_before_sha256':sha(ROOT/'pipeline/research_work.json'),
                'scope':'Once-only resource observation plus existing BEC isolated source-version registration; existing journal or current evidence requires readonly reconciliation, never replay.'},f,indent=2)
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
        lines[i]='- 本轮旧9到期，仅声明candidate内容/证据path-hash签名及授权目录元数据有界复核；未改候选/读655正文/旧grant正文/checkpoint body。旧hold新动作/用户决定均false，原scope/失败/修订上限/M206pause保持，复查不是新授权。'
        i=next(i for i,line in enumerate(lines) if line.startswith('- 既有M215-BEC implementation'))
        graph_text=lines[i][lines[i].index('双跨层'):]
        lines[i]=f'- M215-BEC现validation，实际隔离source{version["code_commit"]}/单父{version["parent_commit"]}，9blob精确等于原2d06；primary/runtime仍48fc。它与pendingCTS4e8为兄弟，不假定相互ff；原2d06及native322c的null版本声明保持，不回填。'+graph_text
        memory='\n'.join(lines)+'\n'
        memory=memory.replace('- 本轮f86d CTS只读','- 前f86d CTS只读').replace('- 本轮f86d BEC禁用','- 前f86d BEC禁用')
        memory=memory.replace('当前snapshot new_terminal仅识别前轮归档，不是本轮新完成，未重复archive。','前6bdb snapshot仅识别前336归档；本轮无新终态，不重复archive。')
        memory=memory.replace('2准备储备CTS+源级BEC','2准备储备CTS+已保存隔离源版本BEC')
        memory=memory.replace('BEC还需兼容当时实际tested main源版本与native observer，不从旧null推断已测或造旁支假定可ff。',
            'BEC已实存9b678/parent48fc源版本，仍需新版本绑定native/operational copy；若tested main改变必须另建兼容版本并按该版本真实检查，不从旧null推断已测或假定兄弟可ff。')
        saved=f'- 本轮实际BEC隔离保存证据{ref(version_path)["path"]} SHA{sha(version_path)}，独审cb7ec9d8…确认32项/实际Git父tree/blob/clean与全部保护。仅新本地9A子提交，无主线ff/部署/native/queue；source母本2d06及旧native322c23文件全部原字节，native_execution_code_commit仍null。\n'
        memory=memory.replace('\n## Closed Or Failed Directions','\n'+saved+'\n## Closed Or Failed Directions')
        added='- 本轮新增资源事实：NVML额外PID1565126同时在GPU0/1使用9594/9804MiB，原BFC19714/BCR19724MiB，总显存29366/32607、29563/32607MiB（约90%）。不在本项目queue；最小/proc归属读取PermissionError，owner/start/用途UNKNOWN。只读probe3eb859cd…保留，无sudo/绕权限/重探、无signals或其他项目文件读取。未知进程受保护，不自动终止或暂停原训练。\n'
        memory=memory.replace('\n## Open Questions And Risks','\n'+added+'\n## Open Questions And Risks')
        memory=memory.split('\n## Last Tick')[0]+f'''
## Last Tick
- 本轮b5dc snapshot2running/0ready、reserve2/creation0，due11含CTS/BEC及旧9，无新terminal/operationalissue。begin已查进展/尝试派发既有合格队列，M206paused不计ready。
- 本轮只读BFC10:1086→1093、BCR21:3551→3556均增长，原PID/start/argv/log/源8/YAML77e/UUID保持；新增未登记PID1565126同时占两卡，归属PermissionError未知，约90%总显存。当前CTSguard5543eb11…两registered卡均beforetransport busy拒绝，0native/transport/active；真实resource_check=blocked，不是机制失败。
- CTS源4e8/原51cbc工具/checker82da+审5d36沿用；BEC原2d06精确9blob已实保存隔离9b678/parent当前已测main48fc并独审，主线28/index/13+4账/CTS4e8/旧native322c均保持。新保存助手30项本地检查与自身测试修正证据保留，不重跑原模型/observer已过tests，不改计算图或新增候选。
- 独审发现root未执行WIP错误前提“唯一context”，已保留旧草稿并更正，原94db raw不重写；追加一次必要最小只读probe3eb验证新增占用，PermissionError后停止身份探查、无权限绕过。独审保留此实质concern，不改空数组伪PASS。
- 1个既有BEC源版本保存/0新候选/0模型实现修订/0准入/0queue/0启动/0新训练终态，141IDs集合、公共HEAD48fc/index空/28保护status+bytes/10运行归档账保持；仅CTS资源观察、BEC源版本与两原观察更新。资源新差异与实际源准备需NOTIFY，不称研究增益或训练失败。
- GPU空闲不是BEC本地版本前提，本轮已推进该合法步骤；9b678与CTS4e8是兄弟且merge-base48fc，未来main改变需另建兼容版本并真实测该版本。下一步新版本绑定native包可本地准备，GPU执行仍需真正空卡及fresh绑定。完整七段memory/blocked tick_attempt/Chinese notes/六段report后原token finish核实际FINALIZED/released；未发生前不预签，释放后不回写。
'''
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        save(memory_path,memory)
        notes={'actions':[
            '本轮actual owner一致，前f86d已FINALIZED/released且lock/pending消失后begin；snapshot2running/0ready、reserve2/creation0，due11含CTS/BEC和旧9，无新terminal或连接/源/派发故障。M206paused不是ready，未另跑monitor。',
            '有界只读真观察：BFC GPU0 Train10 1086→1093，BCR GPU1 Train21 3551→3556，原PID/start/argv/cwd/log/8源/YAML77e/UUID保持；publicruntime48fc/BCR科学11a分开。原始NVML同时显示两卡各有额外PID1565126，不能称唯一context；当前best等实时指标未采。',
            '独审发现未执行WIP中的唯一context前提错误，保留旧草稿与原94db raw。追加一次必要最小只读probe：全UUID/PID显存确认额外1565126在GPU0/1使用9594/9804MiB，总显存约90%；该PID不在本项目queue。最小proc owner/start/script归属查询PermissionError，身份/用途UNKNOWN；停止探查，不sudo/绕权限/重试，不读其他项目文件或发信号。',
            '既有CTS受审catalog通过本轮fresh实际owner/context/原deadline/source/whitelist检查；两registered卡prepare0/1均beforetransport拒绝，14非法入口和deadline拒绝。0process/network/Torch/active，原生与资源未执行；resource_check blocked按原样留证。',
            'CTS原4e8/51cbc与前f86d checker82da/5d36沿用；BEC原2d06冻结八源+原YAMLa18共9blob实际保存到独立本地commit9b678/单父实际已测main48fc。源版本独审32项通过，主线/28/index/13+4账/CTS4e8/旧native322c23文件保持；source_version完整性不代签native。',
            'BEC源保存助手默认禁用草稿30项检查、独审后仅新副本oneflag开启并执行一次；原模型图与原软件正结果不重跑，助手测试自身语法/文字断言更正及reviewer提取器更正均保留，非模型实现修订。BEC与CTS是兄弟源版本，不能相互直接ff；未来main改变需新兼容版本并按实际版本真实测试。',
            '到期旧9仅声明元数据、证据path-hash签名与授权目录listing核验，未读655正文/旧grant正文/checkpoint body；无新授权或需用户处理项，不改旧scope/负结果/修订预算/M206暂停。',
            '1既有候选本地源版本保存/0新候选/0模型修订/0准入/0queue/0启动/0新训练终态；保持两原运行、公共48fc/index空/28保护status+bytes、10运行归档账、141IDs/goal/资源/禁项/data/seed/schedule/YAML/调度。'],
            'decisions':['本轮新增资源差异必须如实通知：保护不明PID1565126和两个原训练，未识别用途前不自动驱逐/暂停/恢复或迁卡。原native资源独占条件未满足，CTS/BEC原生检查继续等待；原训练仍增长且无已观测错误，不记为模型失败。',
                'GPU占用不是本地源版本的逻辑前提，按站立项目权限推进既有BEC隔离9blob保存。已测parent48fc真实核验；兄弟关系如实保留，不合并/假定ff或推进运行主线。旧322c null元数据不可原地启用，下一步另建对应真实版本的受审native copy。']}
        save(HERE/'report_notes.json',notes)
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        save(HERE/'final_tick_persisted.json',{'token':TOKEN,'new_candidates':0,'new_admissions':0,'new_launches':0,'new_terminal_experiments':0,'existing_candidate_source_versions_saved':1,
            'resource_check':'BLOCKED_ORIGINAL_JOBS_PLUS_UNREGISTERED_EXTRA_CONTEXTS','native':'NOT_RUN','current_progress':ref(observation_path),
            'current_CTS_guard':ref(local_path),'additional_context':ref(extra_path),'held_metadata_check':ref(held_path),'BEC_actual_source_version':ref(version_path),'BEC_source_review':ref(source_review_path),'memory_lines':len(memory.splitlines()),'notification':'NOTIFY_RESOURCE_CHANGE_AND_SOURCE_PREPARATION','postflight':'NOT_YET_CALLED'})
        print(json.dumps({'status':'REAL_RESOURCE_CONTENTION_AND_BEC_SOURCE_VERSION_PERSISTED','resource_check':'blocked','new_research_conclusion':False,'notification':'NOTIFY_RESOURCE_CHANGE_AND_SOURCE_PREPARATION','memory_lines':len(memory.splitlines())}))
    finally:lock.close()
if __name__=='__main__':main()
