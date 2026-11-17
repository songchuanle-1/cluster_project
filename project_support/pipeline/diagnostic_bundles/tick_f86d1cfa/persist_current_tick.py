"""Record preparation for two existing candidates; no source, GPU or queue action."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys,copy
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
CTS='hierarchy-parent-cyclic-triadic-state-composition';BEC='hierarchy-cross-level-bipartite-edge-composition'
TOKEN='f86d1cfaf966476db888f6ba553b74d1'
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
def packet(path,review_path,cid):
    prep=read(path);review=read(review_path)
    assert prep['candidate_id']==cid and review['material_concerns']==[]
    assert ref(path) in review['anchors'].values()
    for name,h in prep['prepared_file_hashes'].items():
        p=(path.parent/name).resolve()
        assert p.is_relative_to(path.parent.resolve()) and sha(p)==h
    return prep,review
def main():
    owner=guard();snapshot=read(ROOT/'pipeline/headless/.tick_model_view.json')
    assert not any((HERE/n).exists() for n in ['persist_intent.json','final_tick_persisted.json','codex_memory_before_finalization.md'])
    assert snapshot['experiment_first']['enabled'] and snapshot['research']['creation_budget']==snapshot['research']['reserve_budget']==0
    cts_path=HERE/'cts_execution_review_prepare/preparation.json';cts_review=HERE/'cts_checker_final_review.json'
    bec_path=HERE/'bec_native_prepare/preparation.json';bec_review=HERE/'bec_native_preparation_final_review.json'
    cp,cr=packet(cts_path,cts_review,CTS);bp,br=packet(bec_path,bec_review,BEC)
    # Review requires explicitly unexecuted real native/model/resource operations.
    assert sha(cts_path)=='82da6073da4044c7f666ca70519b3b3ee796e3ad536698180a581823d51e9beb'
    assert cp['actual_semantic_review']=='NOT_RUN' and cp['actual_native_raw_results']=='NOT_PRESENT'
    assert cp['native_TRAIN2']==cp['resources']=='NOT_RUN'
    assert sha(bec_path)=='322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff'
    assert bp['source_commit'] is None and bp['future_version_parent'] is None
    assert bp['native']==bp['resources']=='NOT_RUN'
    assert bp['draft_execution_disabled'] is True
    assert bp['code_commit'] is None and bp['source_parent_commit'] is None
    assert len(bp['manifest_execution_fields'])==10 and all(x is None for x in bp['manifest_execution_fields'].values())
    assert bp['actual_static_checks_passed']==60 and bp['observer_software_counts']['actual_checks_passed']==36
    assert bp['source_preparation']['sha256']=='2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d'
    current_guard=HERE/'cts_actual_local_guard_integration.json'
    g=read(current_guard)
    assert sha(current_guard)=='37a8114424d00c4d59340b9f4419b5b7148165675318f545fd4db563192ea395'
    assert g['current_owner_token']==TOKEN and g['actual_transport_calls']==0 and not g['active_binding_manifest_lease_or_execution_directory_created']
    assert g['native_execution']==g['resources']=='NOT_RUN'
    proof_path=HERE/'active_runs_progress_observation.json';proof=read(proof_path)
    assert sha(proof_path)=='a04cf150867990114027748a893cda01ffd7883427491c882252cd659f4a2cde'
    assert all(x['native_TRAIN_growth'] for x in proof['summary'])
    observation_review=HERE/'progress_and_guard_independent_review.json';assert read(observation_review)['material_concerns']==[]
    assert not (HERE/'cts_execution').exists() and not (HERE/'bec_execution').exists()
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();before=read(HERE/'protected_assets_before.json')
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        work=read(ROOT/'pipeline/research_work.json');old=copy.deepcopy(work)
        assert len(work['candidates'])==len(before['candidate_digests'])==141
        cts=next(c for c in work['candidates'] if c['id']==CTS)
        bec=next(c for c in work['candidates'] if c['id']==BEC)
        assert cts['code_commit']=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d' and cts['stage']=='validation'
        assert bec['stage']=='implementation' and bec['code_commit'] is None and bec['source_commit'] is None and bec['future_version_parent'] is None
        assert cts['native_execution_code_commit'] is bec['native_execution_code_commit'] is None
        assert cts['execution_adapter'].get('prepared_readonly_result_checker')!=ref(cts_path)
        assert bec.get('worker_preparation',{}).get('preparation')!=ref(bec_path)
        cts['execution_adapter'].update(actual_current_local_guard=ref(current_guard),
            prepared_readonly_result_checker=ref(cts_path),prepared_result_checker_independent_review=ref(cts_review),
            actual_native_four_result_review_executed=False)
        cts['result_checker_status']='PREPARED_INDEPENDENTLY_REVIEWED_SOFTWARE_ONLY_REAL_NATIVE_RESULTS_NOT_AVAILABLE'
        cts['next_action']='Preserve frozen CTS4e8/sourcebfab/operational51cbc/worker03329/protocol7036 and existing catalog. Original BFC0/BCR1 are protected and current local prepare0/1 refuses before transport. After one naturally ends, require current exact owner/context/original deadline/allowedUUID/liveidle/assets/three locks, stage the selected one card and execute actual original M95/CTS TRAIN2 plus resource pair. Only actual complete raw four-arm results may be evaluated by reviewed checker; local fixtures cannot grant admission, source promotion, queue or native PASS. Keep M206 paused and all oldholds/data/seed/schedule/bans unchanged.'
        cts.setdefault('resource_wait_history',[]).append(copy.deepcopy(cts.get('resource_wait',{})))
        cts['resource_wait']={'allowed_server':'server-4','allowed_physical_gpus':[0,1],
            'observed_at':proof['observations'][-1]['observed_at'],'observed_tasks':{'0':{'id':'M213-BFC','pid':219369,'start_ticks':'56265957'},'1':{'id':'M212-BCR','pid':1215422,'start_ticks':'51717921'}},
            'evidence':[ref(proof_path),ref(current_guard)],'scope':'Current original native progress plus registered busy; not a live idle grant or parked exclusive_gpu_slot hold.'}
        add(cts,[cts_path,cts_review,current_guard,proof_path,observation_review,
            cts_path.parent/'software_validation_final.json',cts_path.parent/'final_validation.json'])
        bec['worker_preparation']={'status':'PREPARED_DISABLED_UNVERSIONED_INDEPENDENTLY_REVIEWED_NATIVE_NOT_RUN',
            'preparation':ref(bec_path),'worker':ref(bec_path.parent/'worker.py'),'runtime':ref(bec_path.parent/'native_runtime.py'),
            'manifest_template':ref(bec_path.parent/'manifest_template.json'),'independent_review':ref(bec_review),
            'source_commit':None,'future_version_parent':None,'native_backward_executed':False,'resource_profile_executed':False,
            'native_backward_passed':False,'resources_passed':False,'active_native_manifest_or_execution_lease_created':False,
            'draft_execution_disabled':True}
        bec['implementation_status']='FROZEN_PRIVATE_MODEL_AND_DISABLED_NATIVE_OBSERVER_SOFTWARE_PREPARATION_REVIEWED_NO_ACTUAL_NATIVE'
        bec['next_action']='Keep frozen source2d0606/eightmodel/YAMLa18/protocol6555 and new disabled native preparation unchanged with code/source/futureparent and ten active fields null. Select a then actual-tested-main-compatible isolated source version without assuming pendingCTS sibling can ff, then prepare a new independently reviewed version-bound native copy. Use fresh exact owner/deadline/context/UUID/whitelist/liveidle/assets/three locks on authorized server4 physical0or1 for original fixed two TRAIN batches and paired M95 resources. Derive actual common names excluding FFN0/1 and new BEC subtree, observe both U/V split branches, four Linear plus original coarseFFN gradients/updates and actual HCG/singleinst path. Per-call zeros legal; no data/seed/precision/threshold/schedule change, forced boundary resampling, M206 resume or admission from local software checks.'
        add(bec,[bec_path,bec_review,proof_path,observation_review,
            bec_path.parent/'static_validation.json',bec_path.parent/'observer_fixture_run1.json'])
        for eid in ['M213-BFC','M212-BCR']:
            c=next(c for c in work['candidates'] if c.get('experiment_id')==eid)
            add(c,[proof_path,observation_review])
            c['latest_runtime_observation']={'evidence':ref(proof_path),'independent_review':ref(observation_review),
                'shared_runtime_commit':'48fc302c3c02ffef0b241be3593c386b6b65a72e','admitted_source_unchanged':c['code_commit'],
                'scope':'Original PID/start/argv/log/model8/YAML/UUID and two real TRAIN steps; no operation on either job.'}
        work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CTS,'kind':'implementation_test','result':'passed',
            'command':"python -B -X utf8 'D:/project/cluster_project/pipeline/diagnostic_bundles/tick_f86d1cfa/cts_execution_review_prepare/test_checker.py'",
            'observation':'Actual CTS checker software run passed8 logical cases and84 negative refusals, with in-memory SYNTHETIC metadata fixtures and actual CLI missing-result refusal. No actual native four-result review was performed. Separately current existing catalog passed fresh owner/context/raw whitelist/source/deadline guards and both registered cards refused before transport;14 invalid entries/deadline refused. BEC disabled observer software preparation also has independent review. No true Torch backwards/resources/admission/launch.',
            'evidence':[ref(cts_path.parent/'software_validation_final.json'),ref(cts_path.parent/'final_validation.json'),ref(cts_path),ref(cts_review),ref(current_guard),ref(observation_review)]}
        work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']=cts['next_action']+' Then advance existing unversioned BEC using compatible actually tested main.'
        permitted={CTS,BEC,'hierarchy-parent-butterfly-token-composition','hierarchy-parent-bidirectional-complement-recurrence'}
        assert [x for x in work['candidates'] if x['id'] not in permitted]==[x for x in old['candidates'] if x['id'] not in permitted]
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        with (HERE/'persist_intent.json').open('x',encoding='utf8') as f:
            json.dump({'token':TOKEN,'helper_sha256':sha(Path(__file__)),'research_work_before_sha256':sha(ROOT/'pipeline/research_work.json'),
                'CTS_checker':ref(cts_path),'BEC_disabled_native':ref(bec_path),'scope':'Once-only current-tick bookkeeping. Existing intent or new candidate refs require readonly partial-state reconciliation, never replay.'},f,indent=2)
            f.write('\n');f.flush();os.fsync(f.fileno())
        save(ROOT/'pipeline/research_work.json',work)
        p=ROOT/'pipeline/codex_memory.md';memory=p.read_text('utf8')
        with (HERE/'codex_memory_before_finalization.md').open('xb') as f:f.write(p.read_bytes())
        lines=memory.splitlines()
        i=next(i for i,x in enumerate(lines) if x.startswith('- 最新接管'))
        lines[i]=f'- 最新接管{TOKEN}；实际owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated{owner["generated_at"]}/原deadline{owner["deadline_at"]}不延长。前6bdb FINALIZED/released且lock/pending消失后begin；本轮report/finish以实际receipt为准，不预签。'
        stamp=datetime.fromisoformat(proof['observations'][-1]['observed_at']).astimezone(timezone(timedelta(hours=8))).isoformat()
        i=next(i for i,x in enumerate(lines) if x.startswith('- 采集'))
        lines[i]=f'- 采集{stamp}上海：BFC原PID219369/start56265957 GPU0 Train6/50 4352→4360/4686；BCR原PID1215422/start51717921 GPU1 Train19/50 2731→2737/4686。两原TRAIN增长/唯一argv/cwd/fd1/8源/YAML77e/UUID核实，proofa04cf150…/独审eec37a37…。本轮preflight实时指标UNKNOWN，不用cursor或前轮best代签当前best。'
        memory='\n'.join(lines)+'\n'
        memory=memory.replace('- 本轮新CTS版本绑定operational packet','- 前6b CTS版本绑定operational packet')
        memory=memory.replace('- root单flag CTSanchor新copy','- 前6b root单flag CTSanchor新copy')
        memory=memory.replace('- 新唯一M215-BEC implementation','- 既有M215-BEC implementation')
        memory=memory.replace('缺覆盖INCONCLUSIVE，不换样本/seed/precision/阈值；逐call合法零。',
            '缺覆盖INCONCLUSIVE，不换样本/seed/precision/阈值；内部mix call/row合法零，whole-helper input/output沿03329既有非零后验。')
        extra=f'- 本轮f86d CTS只读四臂结果checker已冻结并独审：{ref(cts_path)["path"]} SHA{sha(cts_path)}；只本地软件正确性/缺失拒绝测试，actual_native_results_reviewed=false。当前catalog freshguard37a81144…核20:07原owner/context/deadline与两registeredbusy、0transport/active，不是原生资源PASS。\n'
        extra+=f'- 本轮f86d BEC禁用/无版本native工具冻结并独审：{ref(bec_path)["path"]} SHA{sha(bec_path)}；复用原M95 setup/TRAIN2/criterion/optimizer/原resources整函数AST，只读观测原production split/mean/coarse/down/单inst路径。原2d06/6555不改，source/parent/10active null、DRAFTTrue；实际native/resources/原common/batch配对未知，不能原地填旧包或用软件fixture代签。\n'
        memory=memory.replace('\n## Closed Or Failed Directions', '\n'+extra+'\n## Closed Or Failed Directions')
        memory=memory.split('\n## Last Tick')[0]+f'''
## Last Tick
- 本轮f86d snapshot2running/0ready、candidate_budget2、reserve_target/count2、creation/reserve0，due仅CTS与BEC，旧9不due。begin先查/尝试已有合格队列，M206paused不是ready；无新终态或运行故障。
- root有界两原native观察BFC6:4352→4360、BCR19:2731→2737，current CTS37a8实际localguard/2busy/14invalid/deadline全部正确且无transport；23项独审eec37a37…通过，未再次preflight或反复poll GPU。
- 两分工推进既有候选：CTS四原真实结果语义checker与本地软件测试/独审；BEC原2d06对应disabled/unversioned native observer/manifest/template/本地软件测试/独审。不是新模型候选或真实TRAIN/resource实验，未改原freeze或放松门槛。
- 0新候选/0准入/0queue/0启动/0训练终态；保护公共HEAD48fc/index空/历史28status+bytes/10运行归档账，四个允许候选仅更新准备/观察证据，141IDs集合保持，M206与旧9保持。
- 完整证据tick_f86d1cfa；真实implementation tick_attempt、七段memory和Chinese notes后canonical六段report/finish，核实际FINALIZED/released及lock/pending消失，释放后不回写。当前无新增用户确认，后续原生仍需自然空卡和fresh绑定。
'''
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        save(p,memory)
        notes={'actions':[
            '实际会话与target匹配，前6bdb已FINALIZED/released/锁状态消失后begin；snapshot2running/0ready、creation/reserve0，due仅CTS+BEC，旧9不due，无新终态/连接源故障。未改调度或重复preflight。',
            '本轮有界双样本确认BFC GPU0第6/50轮4352→4360、BCR GPU1第19/50轮2731→2737；原PID/start/argv/cwd/log/8源/YAML77e/UUID/唯一context保持。公共runtime48fc和BCR科学11a分开核实，独审23项通过；当前best等实时指标UNKNOWN。',
            '现有CTS静态catalog以本轮fresh owner/context/rawUUID/原deadline实际通过localguard，两registered卡prepare0/1均在transport前拒绝；14非法入口与deadline拒绝、0process/network/Torch/active。原51cbc/03329/7036/4e8与公共48fc均保持，非native或资源PASS。',
            '准备CTS原M95/CTS四臂真实结果语义checker并完成实际本地软件检查/独审，针对03329原native schema核2TRAIN原loss/backward/optimizer、输入/common配对、3distinct/multiround/r1与3W块聚合grad/update、原资源口径与fullunsupported；未提供任何真实CTS raw结果，未造标准PASS/receipt。',
            '为既有BEC原2d0606/6555准备禁用/无版本native observer、runtime、manifest/template，完整保留原resource函数AST与原数据/criterion/optimizer。实际本地生产AST/list-set载体与回调、合法零边界及disabled/null拒绝检查、独审完成；未Torch backward/GPU/SSH/Git/active。',
            '0新模型候选/0准入/0queue/0启动/0训练终态，保护两原运行、M206pause、旧9与固定goal/资源/bans/data/seed/schedule/YAML。BFC48fc主线/index/28status+bytes、10运行归档账核保持，141候选IDs未增删。'],
            'decisions':[
            '准备名额已满，不再扩展变体；优先填已有CTS真实结果检查与BEC未来原生观测缺口，卡忙期间仅做本地软件准备，不抢占或恢复既有实验。',
            '所有软件fixture/AST/边界测试只证明工具准备，实际原TRAIN2、配对、梯度更新、同口径资源和收益仍未测。CTS使用已有源4e8；BEC code/source/未来parent均null，未来选择兼容实际tested main的版本再另建受审绑定copy，不回写历史null。',
            '后续自然空出授权卡且fresh owner/deadline/UUID/liveidle/assets/三锁通过，再跑CTS原M95对照与真实检查；实际通过才准入并尝试派发。M95完成最佳.5020距目标.5100仍.0080，M206继续暂停，无新增用户授权项。']}
        save(HERE/'report_notes.json',notes)
        guard();assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())
        save(HERE/'final_tick_persisted.json',{'token':TOKEN,'new_candidates':0,'new_admissions':0,'new_launches':0,'new_terminal_experiments':0,
            'CTS_checker':ref(cts_path),'BEC_disabled_native_preparation':ref(bec_path),'current_progress':ref(proof_path),'current_CTS_local_guard':ref(current_guard),
            'memory_lines':len(memory.splitlines()),'postflight':'NOT_YET_CALLED'})
        print(json.dumps({'status':'EXISTING_TWO_RESERVES_SOFTWARE_PREPARATION_PERSISTED_NATIVE_NOT_RUN','memory_lines':len(memory.splitlines()),'new_candidates':0,'native':'NOT_RUN'}))
    finally:lock.close()
if __name__=='__main__':main()
