"""Register only the independently reviewed external, unversioned preparation."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PREP=HERE/'psnc_prepare';TOKEN='e2742b06404240e398267db352a2b91a'
CID='hierarchy-parent-spectral-nonlinear-token-coupling';EXP='M210-PSNC'
BASE='74fcd21df0af9a971792038ffe251af1ffea2604'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):return {'path':Path(path).relative_to(ROOT).as_posix(),'sha256':sha(path)}
def save(path,data):
    path=Path(path);tmp=path.with_name(path.name+'.'+TOKEN+'.tmp')
    with tmp.open('x',encoding='utf-8') as stream:
        if isinstance(data,str):stream.write(data)
        else:json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n')
        stream.flush();os.fsync(stream.fileno())
    os.replace(tmp,path)

def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    assert sha(PREP/'preparation.json')=='302432f1e2ba136576c4eb8a814a7ab3fb9596272304924b2a9db356074b49de'
    independent=HERE/'psnc_implementation_independent_review.json'
    assert sha(independent)=='526001bd8b5afc089438be21066302887e69269d5c10575b59da7e80e9214133'
    scope=HERE/'spectral_scope_review.json'
    assert sha(scope)=='c2a763c39240cfdaebcf5f05cf88a1e7460d770122744c52152b2e3415625b09'
    assert read(independent)['status']=='INDEPENDENT_STATIC_SOURCE_REVIEW_NO_DEFINITE_IMPLEMENTATION_BUG_NATIVE_UNEXECUTED'
    prep=read(PREP/'preparation.json')
    assert prep['candidate_id']==CID and prep['experiment_id']==EXP and prep['code_commit'] is None
    assert prep['baseline_reference_HEAD']==BASE and prep['prepared_under_parent_token']==TOKEN
    for name,expected in prep['prepared_file_hashes'].items():
        path=(PREP/name).resolve();assert path.is_relative_to(PREP.resolve()) and sha(path)==expected,name
    assert len(prep['source_files'])==9
    for name,expected in prep['source_files'].items():assert sha(PREP/'staged_repository'/name)==expected,name
    assert prep['native_backward']=='NOT_RUN' and prep['resources']=='NOT_RUN'
    assert prep['static_check_count']==23 and prep['stdlib_reference_tests']==17
    progress=read(HERE/'hrc_training_progress_observation.json')
    assert progress['exact_original_process_and_native_progress_increasing']
    a,b=[x['data'] for x in progress['observations']]
    assert a['pid']==b['pid']==2780804 and a['starttime']==b['starttime']=='29604100'
    assert a['progress']==[4,50,1396,4686] and b['progress']==[4,50,1406,4686]
    assert b['gpu0_contexts']=='2780804, 19720'
    observed_at=progress['observations'][-1]['observed_at']
    observed_local=(datetime.fromisoformat(observed_at)+timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    assert subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'rev-parse','HEAD'],text=True).strip()==BASE
    assert not subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'diff','--cached','--name-only'],text=True).strip()
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        work=read(ROOT/'pipeline/research_work.json')
        assert not any(c['id']==CID or c.get('experiment_id')==EXP for c in work['candidates'])
        assert not(ROOT/'pipeline/admissions'/f'{EXP}.json').exists() and not(ROOT/'pipeline/experiments'/f'{EXP}.json').exists()
        view=read(ROOT/'pipeline/headless/.tick_model_view.json')
        assert view['generated_at']==owner['generated_at'] and view['research']['creation_budget']==1
        assert view['research']['reserve_budget']==1 and view['queue']['ready_waiting_count']==1
        protected={name:sha(ROOT/'pipeline'/name) for name in ['queue.json','running.json','experiments/M208-HRC.json','experiments/M209-PSBR.json','experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']}
        q=monitor.load_queue(str(ROOT));tasks={t['id']:t for t in q['gpu_queues']['server-4']}
        assert tasks['M208-HRC']['status']=='running' and tasks['M208-HRC']['pid']==2780804 and tasks['M208-HRC']['launch_verified']
        assert tasks['M209-PSBR']['status']=='waiting' and not tasks['M209-PSBR'].get('dispatch_hold') and 'pid' not in tasks['M209-PSBR']
        assert tasks['M209-PSBR']['code_commit']==BASE and tasks['M206-CGCA']['resume_authorized'] is False
        policy=read(ROOT/'pipeline/closure_policy.json');auth=policy['experiment_first']['authorization']
        assert sha(ROOT/auth['path'])==auth['sha256'] and policy['experiment_first']['enabled']
        command=[
            'C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','next_batch',
            'Prepare independent parent spectral token coupling','Prepare PSNC outside repo; preserve admitted PSBR74f',
            '待跑PSBR1/目标2且本轮准备预算1；选固定DCT分析→原middle非线性FFN→逆合成、保留f(0)的结构图，参数/构造不增，旧RSTR/PCE失败不重开。外置8源+原YAML已完成23静态/17stdlib参考和独审；真实torch/native/resources/效果未知。当前HRC占唯一GPU0，PSBR已有74f收据，故不改Cluster/HEAD/commit/sync，不把base74f当新实现版本；以后先保护PSBR派发再定真实版本/真GPU0检查。',
            '; '.join(item['path']+' SHA'+item['sha256'] for item in [ref(PREP/'preparation.json'),ref(independent),ref(scope),ref(HERE/'hrc_training_progress_observation.json')])]
        decision_run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',env=os.environ.copy(),timeout=30)
        assert decision_run.returncode==0,decision_run.stderr
        decision=Path(decision_run.stdout.strip().split('-> ',1)[1].strip())
        save(HERE/'canonical_psnc_preparation_decision.json',{'command':command,'returncode':decision_run.returncode,'stdout':decision_run.stdout,'stderr':decision_run.stderr,'decision':ref(decision)})
        now=datetime.now(timezone.utc)
        config=next(name for name in prep['source_files'] if name.endswith('.yaml'))
        evidence=[ref(PREP/name) for name in ['preparation.json','implementation_contract.json','implementation.md','static_validation.json','static_validation_attempt1.json','static_validate.py','test_math_reference.py']]
        evidence += [ref(HERE/name) for name in ['spectral_scope_review.json','psnc_implementation_independent_review.json','continuation_boundary_check.json','hrc_training_progress_observation.json','psnc_next_native_protocol.md']]
        evidence += [ref(decision)]
        candidate={
            'id':CID,'experiment_id':EXP,'profile':'experiment_first','created_at':now.isoformat(),
            'stage':'blocked','resume_stage':'implementation','authorization':auth,
            'goal_sha256':sha(ROOT/'pipeline/goal.json'),
            'hypothesis':'Fixed signed orthogonal analysis within original coarse-parent middle-token groups, followed by the original pointwise nonlinear FFN and inverse synthesis, may create useful sibling evidence dependence before unchanged HCG/inst_feats readback. Preserve zero response with b=f(0); efficacy, population bottleneck and novelty are unknown.',
            'matched_control':'Original M95 with identical native YAML/seed1999/pretrain/data/schedule/optimizer and original fine/middle/coarse FFNs. Future identity-Q same-layout and original-layout controls remain distinguished. No actual torch/model/data comparison performed this tick.',
            'formula':'Y=X+Q^T(f(QX)-b)+b, b=f(0), f=original middle FFN after original LN; singleton skips Q and bias subtraction/addition, original outer skip retained.',
            'code_commit':None,'base_code_commit':BASE,
            'config':config,'config_status':'Native YAML prepared only in external staged_repository; intended future repository path. Not installed/deployed.',
            'source_status':'PREPARED_EXTERNAL_UNVERSIONED','source_preparation':ref(PREP/'preparation.json'),
            'prepared_model_sources':prep['source_files'],'prepared_repository_root':(PREP/'staged_repository').relative_to(ROOT).as_posix(),
            'static_status':'23 static checks and17 stdlib reference tests passed; independent static review has no definite implementation bug. Not torch/native/resource evidence.',
            'native_status':'NOT_RUN_waiting_authorized_idle_gpu_and_exact_new_version','resource_status':'NOT_RUN_waiting_authorized_idle_gpu_and_exact_new_version',
            'native_worker_adapter':'NOT_PREPARED','scientific_admission':False,'experiment_first_admission':False,
            'expected_parameter_buffer_delta_source_inference':0,'actual_parameter_inventory':'NOT_RUN','efficacy':'UNKNOWN',
            'blocker_kind':'exclusive_gpu_slot','required_server':'server-4','required_gpu':'0',
            'blocked_at':now.isoformat(),'retry_after':(now+timedelta(hours=1)).isoformat(),
            'blocker':'Only authorized physicalGPU0 has exact ongoing HRC2780804/start29604100/native4/50 increasing1396->1406 with19720MiB context; no native slot. Existing admitted PSBR74f FIFO also requires preserving current localHEAD until its fresh dispatch is safe.',
            'unblock_condition':'Preserve existing PSBR74f dispatch first. Before later scoped promotion, PSBR must have verified launched or all remaining admitted74f launch bindings must be safely reconciled; preserve protected local work and active remote jobs. Then bind this exact new source/YAML to a real new commit, prepare current native worker, and use a fresh truly idle authorizedGPU0/current owner/deadline/assets/exclusive checks for actual TRAIN2 and original resources. GPU1 availability is never authorization.',
            'source_version_boundary':{'current_base_commit':BASE,'new_source_commit':None,'protect_existing_admitted_task':'M209-PSBR',
                'current_Cluster_modified':False,'Git_commit_or_sync':False,'future_exact_tested_version_required':True},
            'next_action':'Do not open another duplicate preparation to fill counts: there is existing admitted PSBR plus this external model. Monitor HRC and retain PSBR FIFO. When version promotion and native resource conditions become safe, promote only these nine files, bind actual tested new commit/native YAML, prepare guarded native controls/worker, run real M95/candidate TRAIN2+original resources and review actual data before standard summaries/receipt/queue. Preserve all original failures and no GPU1/M206 operation.',
            'risks':[
                'Actual cf-dtype cosine basis orthogonality/FP32 transform errors are unmeasured; stdlib double reference tests do not establish native numerical equivalence.',
                'Mixed-group batches useK+1 original FFN work layout; singleton direct rows still share that GEMM. Only all-unmixed batches preserve originalK layout. No FP32 bitwise claim.',
                'Nonzero constant fields need not preserve original FFN response; group size and detached xyz/ID order can affect calibration and rotation behavior.',
                'True support/empty/padding/sentinel isolation and b=f(0) autograd are source-reviewed but not actual torch/native exercised.',
                'DCT operation/sentinel extra cost, real latency/memory/common initialization/TRAIN pairing and efficacy remain unmeasured. OriginalDropout0 is required unchanged.'
            ],'evidence':evidence}
        work['candidates'].append(candidate)
        byexp={c.get('experiment_id'):c for c in work['candidates'] if c.get('experiment_id')}
        for exp,item in [('M208-HRC',ref(HERE/'hrc_training_progress_observation.json')),('M209-PSBR',ref(HERE/'continuation_boundary_check.json'))]:
            if item not in byexp[exp]['evidence']:byexp[exp]['evidence'].append(item)
        work['tick_attempt']={
            'tick_started_at':owner['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked',
            'command':'python -B pipeline/diagnostic_bundles/tick_e2742b06/observe_hrc_training.py',
            'observation':'Exact current HRC PID2780804/start29604100/native4/50 steps1396->1406 on physicalGPU0 verified; onlyGPU0 authorized and occupied19720MiB. PSBR is admitted74f waiting. New PSNC9-source/config external unversioned preparation completed23static+17stdlib checks/independent source review but torch/native/resources NOT_RUN. No Cluster HEAD/queue/receipt/source/launch/GPU1 changes.',
            'evidence':[ref(HERE/'hrc_training_progress_observation.json'),ref(PREP/'preparation.json'),ref(independent)]}
        work['updated_at']=now.isoformat()
        work['next_action']='Monitor exact HRC onGPU0; preserve existing admitted PSBR74f FIFO. One independent external PSNC preparation now exists, unversioned and unexecuted. Preserve HEAD74f until existing admitted dispatch is safe; then only exact scoped new version/native-YAML/current-resource checks can advance PSNC. No M206 restart/GPU1 or oldhold reopening.'
        save(ROOT/'pipeline/research_work.json',work)
        assert {name:sha(ROOT/'pipeline'/name) for name in protected}==protected
        save(HERE/'psnc_registration_result.json',{
            'recorded_at':now.isoformat(),'token':TOKEN,'candidate_id':CID,'experiment_id':EXP,
            'preparation':ref(PREP/'preparation.json'),'independent_review':ref(independent),'scope_review':ref(scope),'decision':ref(decision),
            'new_candidates':1,'creation_budget':1,'native':'NOT_RUN','resources':'NOT_RUN','code_commit':None,
            'Cluster_HEAD':BASE,'source_installed_committed_or_synced':False,
            'existing_queue_running_experiments_admissions_hash_identical':{name:sha(ROOT/'pipeline'/name)==value for name,value in protected.items()},
            'new_receipt_queue_or_training_created':False,'new_GPU_work':False,'GPU1':'NOT_QUERIED_RELEASED_TO_OTHERS'})
        # Preserve prior factual sections; distinguish their native tests from this tick.
        memory=(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8')
        memory=memory.split('\n## Last Tick\n',1)[0].replace('本轮','前轮dfb6440d')
        lines=memory.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('- 当前foreground'):
                lines[i]=f'- 当前foreground{TOKEN}；actual owner01a159c5-29ab-7a22-ba7f-e79174757253与target一致，generated UTC16:04:33.909155/原deadline17:04:33.909155不延长。前轮dfb6440d已FINALIZED/released(14:43:24UTC)且无lock/pending才begin。本轮真实report/finish/receipt与lease释放才确认收尾，不预写PASS。'
            if line.startswith('- HRC/PSBR所有运行效果'):
                lines[i]='- HRC/PSBR完整训练效果仍UNKNOWN；前轮真实技术准入保留。本轮新增一个外置PSNC，尚未真实模型执行，不把数学/静态参考代签native或参数inventory。'
            if line.startswith('- 诊断当前stage/manifest/lease只绑定'):
                lines[i]='- 前轮dfb诊断stage/manifest/lease已收尾过期，不重放/续租。已准入HRC/PSBR按各自receipt/current source及资源保护训练/派发；未知launch保留PID/log/claim，只读reconcile不盲重试/kill。PSNC没有native worker/binding/lease。'
        memory='\n'.join(lines)+'\n'
        insertion=f'''- 本轮{observed_local}上海真实同HRC PID2780804/start29604100/原argv/cwd/remoteHEAD74f/UUID，native4/50两次1396→1406/4686、logfresh.0088s、仅HRC19720MiB context，GPU0整卡19773MiB。proof SHAfb159ac5671fb13248f2783ffc8a4070e8e46208ca0af14dd9708744bd38c1cf；没有新GPU计算/进程处置，GPU1未查未用。
- M210-PSNC stable hierarchy-parent-spectral-nonlinear-token-coupling：原middle f的父组固定DCT-II共轭非线性，Y=X+Qᵀ(f(QX)-f(0))+f(0)，原skip与fine/coarse/raw-CSORT/HCG/单inst保持。true支持ids1[ids0]、原ids2父组、detached原xyz+ID序、逆散原ID；zero sentinel只在原FFN一次工作调用、f0不detach、不入任何ID/readback。
- PSNC外置包tick_e2742b06/psnc_prepare/preparation.json SHA302432f1e2ba136576c4eb8a814a7ab3fb9596272304924b2a9db356074b49de；8源+原YAML，23静态/17stdlib数学检查通过，独立source审526001bd8b5afc089438be21066302887e69269d5c10575b59da7e80e9214133无确定实现bug。code_commit=null/base74f，未装入Cluster/commit/sync/worker/native/resources/receipt/queue；source推断Δparams/buffers0，实际inventory未知。
- PSNC与RSTR/PCE/PSBR定向graph比对scope审c2a763c39240cfdaebcf5f05cf88a1e7460d770122744c52152b2e3415625b09未发现明确等价重开；不背书全史/文献新颖性或收益。非零常量组不保持f、cf-dtype Q误差/GEMM布局/真实边界/autoGrad/成本待实测；原Dropout0不改。纯mode行置换可抵消，符号翻转一般不可抵消，勿作无效negative control。
- PSNC当前blocked/exclusive_gpu_slot/resumeimplementation：唯一GPU0忙，且既有PSBR74f新派发必须保留localHEAD74f。未来先确保PSBR verifiedlaunch或相应74f待派发全部安全处理，再只入新9文件的真实新版本；之后真空GPU0用原YAML/数据/seed/schedule做TRAIN2与原资源才可准入。现有PSBR1+此准备1已覆盖约2待跑准备，不为重复计数再建结构。
'''
        memory=memory.replace('\n## Closed Or Failed Directions\n','\n'+insertion+'\n## Closed Or Failed Directions\n',1)
        memory+='''
## Last Tick
- 本轮e2742b06 begin仅一次monitor/已有派发/goal，budget1/creation1/reserve1、1HRCrunning/0claiming/1readyPSBRwaiting；M206另userhold waiting非ready。compact new_terminal M207-HAP是前轮已处理归档变动，不重复归档/通知；9旧hold notdue不重扫655。
- 精确HRC4/50步1396→1406、只GPU0/原PID/start/argv/HEAD/UUID核成功，现无新native空槽。现成PSBR原c85ae4fe receipt/三个标准hash保持，实际readonly canonical closure.admission PASS，queue/exp仍waiting无PID/hold；continuation审76b2d108592dc9b703eafd8ea66dc0b3be536b51d59a7fd3fd1d76a43fa40e7f，原28status+356497字节小范围hash全同/emptyindex，HRC/M206/HAP原记录保持。
- 按唯一准备预算1完成M210-PSNC外置8源+原YAML/23static+17stdlib参考及source独审；首static runner误用decoder键已修实际model.dec并保留失败记录，未改模型/YAML或跑native。新源/数学参考只支持准备，不宣称Q实dtype数值、真实梯度/loader/资源/效果通过。
- Root外部锚全部preparedmap/9sourcehash后登记PSNC稳定CID，code_commit=null，source_version_boundary明确保护PSBR74fFIFO；新candidate未入训练队列。当前tick_attempt=实际resource_check blocked，证据同归PSNC。0native/0新收据/0queue/0launch/0Gitcommit/0sync/0模型修订；HRC/PSBR/M206既有三账/收据hash保持。
- 七段memory/六段report随后按原token真实finish/receipt FINALIZED+released及lock/pending消失确认，释放后不回写；不创建全局穷尽/冷却、不改调度/白名单/目标/旧失败。因新增真实外置实现与静态/独审进展简报NOTIFY，无新用户处理事项；下一轮优先HRC/PSBR已授权工作和该PSNC具体缺口。
'''
        assert len(memory.splitlines())<120 and memory.count('\n## ')==7
        save(ROOT/'pipeline/codex_memory.md',memory)
        notes={'actions':[
            '仅cluster_project；actual thread/target一致，goalSHA0441/experiment_first/onlyserver4GPU0 max1/GPU1释放/其他server禁用/WindowsDisabled保持。前轮dfb已FINALIZED/released且无lock/pending才begin，current generated16:04:33.909155UTC/原deadline17:04:33.909155不改。',
            'begin先monitor/已有派发/goal一次；1HRCrunning/0claiming/PSBR已准入readywaiting1，M206paused waiting另计非ready。compact HAP new_terminal为前轮手工归档已处理，不重复操作或当作本轮新完成；9notdue holds不复扫655。',
            f'{observed_local}上海只读核HRC原PID2780804/start29604100/原argv/cwd/HEAD74f/GPU0UUID，native4/50两次1396→1406/4686、logfresh.0088s，GPU0仅HRC19720MiB context；无空卡可新native。未查询/用GPU1、未signal/修改既有运行。',
            '现成PSBR74f/c85ae4fe收据及三个标准artifact哈希有效，独立只读canonical closure.admission PASS；current PSBRwaiting无hold无PID、HRC唯一GPU0registeredrunning、M206完整暂停queue保持。localHEAD74f/index空、28protected status及356497小范围字节hash同原；不重复执行以前8个native/resource或旧证据扫描。',
            'snapshot待跑准备缺1且creation/reserve1，选一个可区分图PSNC：原ids2父组真正occupied middle siblings固定DCT→原LN/FFN→逆DCT，零响应f(0)同一次FFN且autograd保留；原skip/fine/coarse/raw-CSORT/HCG/单inst保持，无新参数/门控/QKV/训练超参。定向RSTR/PCE/PSBR比对未发现计算图等价重开，不把有限比对当全史/文献新颖性证据。',
            '已完成独立8源+原YAML外置准备，23静态AST/构造/原路径/原字节检查与17stdlib数学参考通过，source独审无确定bug。初static runner YAML键decoder修为原model.dec，失败记录保留，0模型/YAML改变。数学n1/零/仿射性质不等于FP32或torch/native验证，实际DCT误差/GEMM/梯度/空padding/成本/效果均未知。',
            'Root核冻结prep全部16map/9sourcehash并外锚独审，按唯一预算1登记M210-PSNC；code_commit=null/base74f，只在pipeline外置目录，未装入Cluster/commit/sync。既有PSBR74f待派发期间不推进HEAD；未来先保护PSBR成功派发，再定新确切版本并用真空GPU0进行原生TRAIN2/资源与准入，不将74f冒称包含新实现。',
            '本轮tick_attempt是真resource_check blocked，当前HRC忙证据/新sourceprep/独审均归PSNC。0新native/0资源profile/0新admission receipt/0queue/0launch/0Gitcommit/0sync/0模型修订；原HRC/PSBR/M206/HAP queue/running/experiment/receipt字节保持，原失败和授权边界不改。',
            '七段memory与六段脚本报告留档后按原token finish；真实返回/FINALIZED released/lock+pending消失才确认完成，不预写PASS，不在释放后回写。本轮新增实现/静态准备有实质进展故NOTIFY；无需新用户确认，GPU1留给别人/M206暂停，继续HRC、按FIFO待PSBR，PSNC尚无native worker/版本/原生及资源证据。'
        ],'decisions':[
            'canonical next_batch已记录：以实验优先授权做单一PSNC外置技术准备，保留PSBR74f派发所需HEAD。原训练资源满不抢占；现有PSBR待跑1+新具体准备1，下一步推进这两项，不为计数继续造重复变体或重开旧hold。'
        ]}
        save(HERE/'tick_notes.json',notes)
        print(json.dumps({'registered_external_only':EXP,'source_commit':None,'prepared_source_files':9,'static_checks':23,'stdlib_reference_tests':17,
                          'memory_lines':len(memory.splitlines()),'decision':ref(decision),'registration':ref(HERE/'psnc_registration_result.json'),
                          'native':'NOT_RUN','GPU0':'occupied_by_existing_HRC','receipt_queue_or_launch_created':False},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
