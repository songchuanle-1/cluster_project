"""Persist existing BEC native-tool preparation; never manufacture native results."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='521a6f59f2a74a69b41144aa6a8b6153';BEC='hierarchy-cross-level-bipartite-edge-composition';CTS='hierarchy-parent-cyclic-triadic-state-composition'
COMMIT='9b6782f44ca7f2c8ac35baea01dfd070314b5701';PARENT='48fc302c3c02ffef0b241be3593c386b6b65a72e'
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
    owner=guard();assert not any((HERE/n).exists() for n in ['final_persist_intent.json','final_tick_persisted.json','codex_memory_before_finalization.md'])
    snapshot=read(ROOT/'pipeline/headless/.tick_model_view.json')
    assert snapshot['experiment_first']['enabled'] and snapshot['research']['creation_budget']==snapshot['research']['reserve_budget']==0
    assert snapshot['queue']['running_count']==2 and snapshot['queue']['ready_waiting_count']==0 and snapshot['changes']['new_terminal_ids']==[]
    op_path=HERE/'bec_operational_prepare/preparation.json';op=read(op_path)
    assert sha(op_path)=='420022f59bfcf0a9fcbdcced42003adfb8dc30f58ef74a6e59b6cef1070b3c6e'
    assert op['code_commit']==COMMIT and op['source_parent_commit']==op['runtime_expected_commit']==PARENT
    for name,h in op['prepared_file_hashes'].items():
        p=(op_path.parent/name).resolve();assert p.is_relative_to(op_path.parent.resolve()) and sha(p)==h
    checker_path=HERE/'bec_execution_review_prepare/preparation.json';checker=read(checker_path)
    checker_review_path=HERE/'bec_checker_final_review.json';checker_review=read(checker_review_path)
    assert checker_review['material_concerns']==[] and checker_review['anchors']['preparation']==ref(checker_path)
    assert checker['candidate_id']==BEC and checker['code_commit']==COMMIT and checker['runtime_expected_commit']==PARENT
    assert sha(checker_path)=='5f739a385ffb8032b31b95e170f9380bbd3962df5b04fc2b923eb5d3af34956f'
    assert checker['native']==checker['resources']=='NOT_RUN' and checker['actual_four_result_review']=='NOT_RUN_NO_ACTUAL_RESULTS'
    assert checker['standard_PASS_receipt_queue_written'] is False and checker['active_manifest_lease_binding_created'] is False
    assert checker['validation_summary']['software_logical_checks']==8 and checker['validation_summary']['software_negative_refusals']==98
    for name,h in checker['prepared_file_hashes'].items():
        p=(checker_path.parent/name).resolve();assert p.is_relative_to(checker_path.parent.resolve()) and sha(p)==h
    anchor_path=HERE/'bec_static_anchor_result.json';anchor=read(anchor_path)
    assert anchor['code_commit']==COMMIT and not anchor['active_binding_manifest_lease_created'] and anchor['native_resources_transport_queue_launch']=='NOT_RUN'
    anchor_review_path=HERE/'bec_static_anchor_and_guard_review.json';anchor_review=read(anchor_review_path)
    assert sha(anchor_review_path)=='d7751b7d53bb27050f2a596808ab6acd71be55d54aad3fb1232e4a8d4ee591c3' and anchor_review['bookkeeping_blockers']==[]
    bec_guard_path=HERE/'bec_actual_local_guard_integration.json';bg=read(bec_guard_path)
    assert sha(bec_guard_path)=='24c8719aa56a1e5cc22bb4f94a8d30f5d68bd20deb7862a7421a979869969488'
    assert bg['current_owner_token']==TOKEN and bg['code_commit']==COMMIT and bg['actual_transport_calls']==0 and not bg['active_binding_manifest_lease_or_execution_directory_created']
    assert bg['native_execution']==bg['resources']=='NOT_RUN'
    cts_guard_path=HERE/'cts_actual_local_guard_integration.json';cg=read(cts_guard_path)
    assert sha(cts_guard_path)=='57a7bd01792731619fc0a9660bec955b1615c70568cb926bd16d64fa138dc8f8'
    assert cg['actual_transport_calls']==0 and not cg['active_binding_manifest_lease_or_execution_directory_created']
    observation_path=HERE/'active_runs_progress_observation.json';observation=read(observation_path)
    assert sha(observation_path)=='7f364ffa0c29d5ab463b69b6d2284a5c67b36815236474eb341c91290c782b24'
    assert all(x['native_TRAIN_growth'] for x in observation['summary'])
    progress_review_path=HERE/'progress_and_guard_independent_review.json';progress_review=read(progress_review_path)
    assert progress_review['new_action'] is False and progress_review['user_decision'] is False
    assert len(progress_review['material_concerns'])==1 and progress_review['material_concerns'][0]['new_issue'] is False
    assert progress_review['material_concerns'][0]['pid']==1565126
    assert not (HERE/'bec_execution').exists() and not (HERE/'cts_execution').exists()
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();before=read(HERE/'protected_assets_before.json')
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        work=read(ROOT/'pipeline/research_work.json');old=copy.deepcopy(work)
        assert len(work['candidates'])==len(before['candidate_digests'])==141
        bec=next(c for c in work['candidates'] if c['id']==BEC);cts=next(c for c in work['candidates'] if c['id']==CTS)
        assert bec['stage']=='validation' and bec['code_commit']==COMMIT and bec['source_parent_commit']==PARENT and bec['native_execution_code_commit'] is None
        assert bec['execution_adapter']['preparation']==ref(op_path)
        assert bec['execution_adapter'].get('actual_current_local_guard')!=ref(bec_guard_path)
        assert bec['worker_preparation']['preparation']['sha256']=='8e2d957ea537dfd3d14dde4d32bbc6135f8b1d4b9a3788d1d01417b9a5aa5d1d'
        assert bec['execution_preparation_history'][-1]['worker_preparation']['preparation']['sha256']=='322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff'
        bec['execution_adapter'].update(actual_current_local_guard=ref(bec_guard_path),actual_static_anchor=ref(anchor_path),actual_anchor_guard_review=ref(anchor_review_path),
            prepared_readonly_result_checker=ref(checker_path),prepared_result_checker_independent_review=ref(checker_review_path),actual_native_four_result_review_executed=False)
        bec['result_checker_status']='PREPARED_REVIEWED_SOFTWARE_ONLY_NO_ACTUAL_NATIVE_FOUR_RESULTS'
        bec['implementation_status']='VERSIONED_SOURCE_NATIVE_OPERATIONAL_CATALOG_AND_REAL_RESULT_CHECKER_PREPARED_REVIEWED_NO_NATIVE_RUN'
        bec['native_status']='NOT_RUN_BOTH_REGISTERED_GPUS_BUSY_WITH_PERSISTENT_UNREGISTERED_CONTEXT'
        bec['native_smoke_status']=bec['resource_status']=bec['resource_profile_status']='NOT_RUN'
        bec['admission_status']='NOT_EVALUATED';bec['efficacy']='UNKNOWN'
        bec['next_action']='Preserve exact BEC9b678/parent48fc and reviewed420022/8e2d static catalog plus original6555 actual-result checker. Actual current local guard passes but both registered cards are busy, with persistent unknownPID1565126 also present; preserve all jobs. For real native use require fresh actual owner/context/original deadline/current raw whitelist/physicalUUID/trueidle with all contexts absent/assets/three locks and a new execution binding. Run original paired M95/BEC first2 unmodified TRAIN batches and resource pair; derive actual common names excluding FFN0/1 and BEC subtree, measure5module/12blocks original-loss gradients and updates with legal per-call0, and original HCG/singleinst. Only actual verified raw results may be admitted/queued. If actual main changes from48fc first, prepare a compatible source version and new bound copy and actually test that version; BEC9b andCTS4e8 are siblings, never assume direct ff or relabel old raw. Original322c and2d06 remain frozen/null declarations.'
        wait={'allowed_server':'server-4','allowed_physical_gpus':[0,1],'observed_at':observation['observations'][-1]['observed_at'],
            'observed_tasks':{'0':{'id':'M213-BFC','pid':219369,'start_ticks':'56265957'},'1':{'id':'M212-BCR','pid':1215422,'start_ticks':'51717921'}},
            'additional_unregistered_gpu_pid':1565126,'additional_gpu_memory_MiB':{'0':10776,'1':10464},
            'additional_process_identity':'UNKNOWN_FROM_PRIOR_PERMISSION_ERROR_NOT_REQUERIED',
            'evidence':[ref(observation_path),ref(cts_guard_path),ref(bec_guard_path)],
            'scope':'Registered and physical busy. Same extraPID still visible; no new ownership inquiry, idle/lease or scientific resource result. Prepared reserves are retained.'}
        bec['resource_wait']=copy.deepcopy(wait)
        cts.setdefault('resource_wait_history',[]).append(copy.deepcopy(cts.get('resource_wait',{})));cts['resource_wait']=copy.deepcopy(wait)
        cts['execution_adapter']['actual_current_local_guard']=ref(cts_guard_path)
        add(cts,[observation_path,cts_guard_path,progress_review_path])
        add(bec,[checker_path,checker_review_path,checker_path.parent/'software_validation_final.json',checker_path.parent/'static_validation_final.json',
            bec_guard_path,anchor_path,anchor_review_path,observation_path,progress_review_path])
        for eid in ['M213-BFC','M212-BCR']:
            c=next(c for c in work['candidates'] if c.get('experiment_id')==eid)
            add(c,[observation_path,progress_review_path])
            c['latest_runtime_observation']={'evidence':ref(observation_path),'independent_review':ref(progress_review_path),'shared_runtime_commit':PARENT,
                'admitted_source_unchanged':c['code_commit'],'additional_gpu_pid':1565126,'additional_process_identity':'UNKNOWN_NO_REQUERY',
                'scope':'Original PID/start/argv/log/source8/YAML/UUID and actual TRAIN growth; extra context remains, no exclusivity claim or process operation.'}
        work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':BEC,'kind':'implementation_test','result':'passed',
            'command':"python -B -X utf8 'D:/project/cluster_project/pipeline/diagnostic_bundles/tick_521a6f59/check_bec_actual_guard.py'",
            'observation':'New BEC9b678/parent-live48fc source-bound static catalog was independently reviewed and externally anchored. Actual current owner/context/whitelist/source/deadline guard passed;prepare0/1 refused registered running before transport,14invalid/deadline refused,0process/network/Torch/active. New read-only four-result checker has actual local synthetic software validation and independent review, not actual native review. No data backward/resource GPU experiment or admission/queue/launch occurred.',
            'evidence':[ref(bec_guard_path),ref(anchor_path),ref(anchor_review_path),ref(checker_path),ref(checker_review_path)]}
        work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']=cts['next_action']+' BEC source-bound native catalog and result checker are now also prepared; execute real paired gates only after genuine current resources and bindings pass.'
        permitted={CTS,BEC,'hierarchy-parent-butterfly-token-composition','hierarchy-parent-bidirectional-complement-recurrence'}
        assert [c for c in work['candidates'] if c['id'] not in permitted]==[c for c in old['candidates'] if c['id'] not in permitted]
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        with (HERE/'final_persist_intent.json').open('x',encoding='utf8') as f:
            json.dump({'token':TOKEN,'helper_sha256':sha(Path(__file__)),'research_work_before_sha256':sha(ROOT/'pipeline/research_work.json'),
                'scope':'Once-only existing-candidate preparation/observation metadata. Partial intent or same new refs require readonly reconciliation, never replay.'},f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        save(ROOT/'pipeline/research_work.json',work)
        p=ROOT/'pipeline/codex_memory.md';memory=p.read_text('utf8')
        with (HERE/'codex_memory_before_finalization.md').open('xb') as f:f.write(p.read_bytes())
        lines=memory.splitlines();i=next(i for i,x in enumerate(lines) if x.startswith('- 最新接管'))
        lines[i]=f'- 最新接管{TOKEN}；actual owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner["generated_at"]}/原deadline{owner["deadline_at"]}不延长。前b5dc FINALIZED/released且lock/pending消失后begin，本轮finish以实际receipt为准，不预签。'
        stamp=datetime.fromisoformat(observation['observations'][-1]['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
        i=next(i for i,x in enumerate(lines) if x.startswith('- 采集'))
        lines[i]=f'- 采集{stamp}上海：BFC原219369/start56265957 GPU0 Train13/50 1537→1544；BCR原1215422/start51717921 GPU1 Train23/50 3459→3464，分母各4686。源8/YAML77e/argv-cwd-fd1/UUID与public48fc/科学BCR11a保持，proof7f364ffa…/独审b0f46cde…。每卡仍有1565126，不称独占；当前best未测。'
        i=next(i for i,x in enumerate(lines) if x.startswith('- 本轮旧9到期'))
        lines[i]='- 本轮旧9不due，未重查655正文/旧grant正文/checkpoint body或旧套件；沿前b5dc有界metadata报告365333bf…无新授权/动作结论，scope/失败/修订上限/M206pause保持。'
        i=next(i for i,x in enumerate(lines) if x.startswith('- 本轮新增资源事实'))
        lines[i]='- 前b5dc已通知未知PID1565126额外占两卡，归属PermissionError未知；本轮仍见此PID，额外10776/10464MiB，总used30556/30223MiB。仅用量波动，未再探身份/读其他项目/发信号，保持全部进程；资源concern持续但new_issue/action/user_decision均false，不重复催问。'
        memory='\n'.join(lines)+'\n'
        memory=memory.replace('- 本轮实际BEC隔离保存证据','- 前b5dc实际BEC隔离保存证据')
        memory=memory.replace('BEC已实存9b678/parent48fc源版本，仍需新版本绑定native/operational copy；',
            'BEC已实存9b678/parent48fc，本轮对应版本native/operational静态包和四结果checker已完成并受审外锚；')
        new=f'- 本轮521 BEC新版本绑定op420022/原生pre8e2d（source9b67、parent/live48fc，worker7e及6555原字节）已61mock/71ASThash/7CLI拒绝并独审c8ee1830。root只静态release b551字节copy与新外锚，旧322c全23文件/null/DRAFTTrue及原history保留；新10active仍null，无native执行绑定。\n'
        new+=f'- 本轮BEC实际localguard24c8719a…验证current owner/context/rawUUID/version/原deadline和新catalog，2卡registeredbusy beforetransport、14invalid/deadline、0process/network/Torch/active；实际anchor独审另附。新四原结果checker{ref(checker_path)["path"]} SHA{sha(checker_path)}及独审已具备，5module/12block/common实际名/原资源门不改，软件fixture不代签原生。\n'
        memory=memory.replace('\n## Closed Or Failed Directions','\n'+new+'\n## Closed Or Failed Directions')
        memory=memory.split('\n## Last Tick')[0]+f'''
## Last Tick
- 本轮521 snapshot2running/0ready、已备储备2、reserve_budget0/creation_budget0、due仅CTS/BEC，旧9不due；begin查进展/尝试已有合格派发，M206paused不是ready，无新终态/operationalissue。
- 两原TRAIN13:1537→1544及23:3459→3464，源/版本/身份保持；额外1565126持续，未再读其身份，原PermissionError事实沿用。current CTSguard57a7与BEC24c8两registeredbusy拒绝，0transport/active，非GPU idle或native PASS。
- 既有BEC9b67新版本绑定op420022/native8e2d/runtime37543063/原worker7e及真实四结果checker完成软件检查/独审；root外锚静态catalog+b551，actual局部guard过。原2d06/322c null冻结不改，新10active null/无manifestlease/native/receipt/queue。
- 0新候选/0源Git提交/0模型修订/0准入/0queue/0启动/0训练终态；141IDs、公共HEAD48fc/index空/28status+bytes及10运行归档账保持，仅现有4候选准备/观察变化。源9b与CTS4e8仍兄弟，main变须新兼容版本+该版本真测，无ff/旧raw重标。
- 下一步为授权卡真正idle且fresh owner/UUID/assets/三锁/绑定后真实M95/CTS或M95/BEC固定TRAIN2+资源；实测通过才收据/入队/原生步数核验。此轮软件准备不是训练效果结论，持久resource问题无新增确认项。
- 完整七段memory/真实implementation tick_attempt/Chinese notes/六段report后原token finish核实际FINALIZED/released及lock/pending消失；不预签，释放后不回写。通知仅本轮新工具准备成果，不重复资源旧问题催问。
'''
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        save(p,memory)
        notes={'actions':[
            'actual owner与target一致，前b5dc已FINALIZED/released/锁状态消失后begin；snapshot2running/0ready、已备储备2、reserve_budget0/creation_budget0、due仅CTS/BEC，旧9不due。无新terminal/connection/source问题，不重复monitor或旧hold/tests。',
            '本轮有界只读确认BFC GPU0第13/50轮1537→1544、BCR GPU1第23/50轮3459→3464；原PID/start/argv/cwd/log/8source/YAML77e/UUID保持，public48fc与BCR科学11a分开。1565126额外context持续，仅显存用量波动；未再探身份或发信号，当前best未测。',
            '既有BEC真实source9b678/parent48fc，对应新version-bound operational/native包420022/8e2d完成61mocks、71AST/hash/schema、7CLI前置拒绝及独审；原worker7e/source2d/YAMLa18/协议6555/原runtime函数和resource AST保持。旧322c null/DRAFTTrue全23文件不改，新10active仍null。',
            'root只将受审静态release_template b551原字节物化并登记BEC外锚/history；当前实际BEC guard24c8通过owner/context/whitelist/source/原deadline，prepare0/1均registeredbusy beforetransport，14invalid+deadline拒绝、0process/network/Torch/active。保护主48fc/index/28/10账，未source同步/ff/GPU执行。',
            '新BEC四原结果checker完成实际本地软件验证与独审，按原6555核2TRAIN/common动态名字、5module/12aggregate块、原skip/HCG/单inst、原资源和完整unsupported。仅SYNTHETIC软件schema/缺结果拒绝证明，没有真实四raw、native损失/反传、资源数值或标准PASS/receipt。',
            '0新候选/0Git提交/0模型实现修订/0准入/0queue/0启动/0新训练终态；两原训练/M206pause/141IDs/旧9/goal/资源/bans/data/seed/schedule/YAML/调度保持。未知资源问题沿用，不重复索权或催问。'],
            'decisions':[
            '按当前准备目标已满不扩变体，优先完成既有BEC精确source9b版本的测试入口和真实结果审核工具。本地软件与静态外锚不构成原生、资源或效果PASS；新GPU计算继续等待真正空槽及fresh完整门。',
            'BEC9b678与CTS4e8为48fc兄弟，若实际main先变化，需重新保存兼容版本和新绑定工具并真实检查该版本，不能假定兄弟ff/改原null或旧raw标签。已有项目授权继续覆盖常规后续步骤，当前无新增用户确认。']}
        save(HERE/'report_notes.json',notes)
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        save(HERE/'final_tick_persisted.json',{'token':TOKEN,'new_candidates':0,'new_admissions':0,'new_launches':0,'new_terminal_experiments':0,
            'BEC_version_bound_tools':ref(op_path),'BEC_result_checker':ref(checker_path),'BEC_actual_local_guard':ref(bec_guard_path),
            'memory_lines':len(memory.splitlines()),'native_resources':'NOT_RUN','postflight':'NOT_YET_CALLED'})
        print(json.dumps({'status':'EXISTING_BEC_PREPARATION_COMPLETE_REVIEWED_NATIVE_NOT_RUN','memory_lines':len(memory.splitlines()),'new_candidates':0}))
    finally:lock.close()
if __name__=='__main__':main()
