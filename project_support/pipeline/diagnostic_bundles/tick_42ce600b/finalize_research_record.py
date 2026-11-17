"""Persist actual local/static results and resource block without scientific PASS."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='42ce600bac914e84bceee707167a669b'
CID='hierarchy-parent-spectral-nonlinear-token-coupling'
COMMIT='43dce016c1a1713c2a5dab7061810dc2efde8954'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,value):
    p=Path(p);tmp=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with tmp.open('x',encoding='utf-8') as f:
        if isinstance(value,str):f.write(value)
        else:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)

def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    anchor=read(HERE/'static_adapter_anchor_result.json')
    for key in ['native_preparation','adapter_preparation','static_release','review','independent_review','independent_tests','preparer_static_tests']:
        assert sha(ROOT/anchor[key]['path'])==anchor[key]['sha256']
    review=ROOT/anchor['review']['path'];assert read(review)['material_concerns']==[]
    guard_path=HERE/'psnc_actual_guard_integration.json';guard=read(guard_path)
    assert guard['status']=='ACTUAL_CURRENT_REGISTERED_BUSY_GUARD_REFUSED_BEFORE_TRANSPORT'
    assert guard['transport_calls']==[] and not guard['production_manifest_lease_binding_created']
    observation=read(HERE/'hrc_training_progress_observation.json')
    assert observation['exact_original_process_and_native_progress_increasing']
    a,b=[row['data'] for row in observation['observations']]
    assert a['pid']==b['pid']==2780804 and a['starttime']==b['starttime']=='29604100'
    assert a['progress']==[12,50,3582,4686] and b['progress']==[12,50,3592,4686]
    assert not b['errors'] and b['runtime_HEAD']=='74fcd21df0af9a971792038ffe251af1ffea2604'
    observed_local=datetime.fromisoformat(observation['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    metrics_path=HERE/'hrc_preflight_partial_metrics.json';metrics=read(metrics_path)
    assert metrics['best_mIoU_reported_4dp']==0.4795 and metrics['native_epoch']==12
    assert read(HERE/'continuation_boundary_check.json')['material_concerns']==[]
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        protected={name:sha(ROOT/'pipeline'/name) for name in ['queue.json','running.json','experiments/M208-HRC.json',
            'experiments/M209-PSBR.json','experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']}
        work=read(ROOT/'pipeline/research_work.json');by_id={c['id']:c for c in work['candidates']};c=by_id[CID]
        assert c['code_commit']==COMMIT and c['native_execution_code_commit'] is None
        assert c['execution_adapter']['release']==anchor['static_release'] and c['resume_stage']=='validation'
        assert c['stage']=='blocked' and c['blocker_kind']=='exclusive_gpu_slot'
        now=datetime.now(timezone.utc)
        c['execution_adapter']['actual_local_guard_integration']=ref(guard_path)
        c['execution_adapter']['static_module_release_only']=True
        c['execution_adapter']['external_anchor_verified_at']=now.isoformat()
        c['blocker']='Only authorized GPU0 occupied by original HRC2780804/start29604100, observed12/50 native3582->3592 at'+observed_local+' Shanghai. Actual reviewed operational adapter prepare(0) refuses registered busy card before transport; PSBR74f FIFO remains protected. No native execution slot.'
        c['blocked_at']=now.isoformat();c['retry_after']=(now+timedelta(hours=1)).isoformat()
        c['unblock_condition']='Retain current HRC and PSBR74f FIFO. Once PSBR fresh dispatch is safe, primary source may advance only by safe ff; never modify active remote checkout. With genuinely idle allowedGPU0, fresh actual owner/context/deadline/exact source43/assets checks, two live-idle samples and three exclusive locks, reviewed adapter may create new execution binding and run original-YAML M95/candidate TRAIN2+resources. Static release is not a lease or permission to replay.'
        c['next_action']='No further stub/variant needed: reuse reviewed operational adapter/static module release and source43. Wait for authorized GPU0 and PSBR protected dispatch/version conditions; then prepare fresh actual binding, run original M95/candidate two-TRAIN-step and resource pair, inspect actual raw results, create standard summaries/receipt and enqueue/dispatch only if real gates pass. No GPU1/M206 resume or oldhold reopening.'
        current_evidence=[ref(HERE/'hrc_training_progress_observation.json'),ref(metrics_path),ref(HERE/'continuation_boundary_check.json'),
            anchor['native_preparation'],anchor['adapter_preparation'],anchor['static_release'],anchor['review'],anchor['independent_review'],
            anchor['independent_tests'],anchor['preparer_static_tests'],ref(HERE/'static_adapter_anchor_result.json'),ref(guard_path)]
        for item in current_evidence:
            if item not in c['evidence']:c['evidence'].append(item)
        for item in [ref(HERE/'hrc_training_progress_observation.json'),ref(metrics_path)]:
            by_id['hierarchy-bottom-up-refined-token-composition']['evidence'].append(item)
        by_id['hierarchy-parent-segmented-bidirectional-token-state']['evidence'].append(ref(HERE/'continuation_boundary_check.json'))
        work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked',
            'command':'python -B pipeline/diagnostic_bundles/tick_42ce600b/observe_hrc_training.py',
            'observation':'Only authorizedGPU0 has exact original HRC12/50/native3582->3592; real PSNC adapter local prepare refuses registered busy GPU before any transport/manifest/lease/binding. Same candidate complete operational preparation and static module release independently checked; native/TRAIN/resources and efficacy NOT_RUN/UNKNOWN. Existing PSBR FIFO and active jobs unchanged.',
            'evidence':current_evidence}
        work['updated_at']=now.isoformat();work['next_action']=c['next_action']
        command=['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','other',
            'Finish PSNC guarded native adapter','Anchor reviewed adapter; wait for idle GPU0',
            'HRC唯一GPU0第12/50轮持续递增，PSBR已准入等待。继续同一PSNC，完成原生检查执行编排与离线模拟/独审并由root外锚静态模块release；实际真实项目prepare被占卡登记提前拒绝，0transport/0nativelease/binding。source43与原9文件不变，不新造候选/提交/同步/入队/训练，不占GPU1或恢复M206；真实native与资源待实际空槽。',
            '; '.join(x['path']+' SHA'+x['sha256'] for x in current_evidence)]
        run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',env=os.environ.copy(),timeout=30)
        assert run.returncode==0,run.stderr
        decision=ref(Path(run.stdout.strip().split('-> ',1)[1].strip()));c['evidence'].append(decision)
        save(HERE/'canonical_adapter_decision.json',{'command':command,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'decision':decision})
        save(ROOT/'pipeline/research_work.json',work)
        assert {name:sha(ROOT/'pipeline'/name) for name in protected}==protected
        memory=(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('\n## Last Tick\n',1)[0]
        lines=memory.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('- 当前foreground'):
                lines[i]='- 当前foreground'+TOKEN+'；actual owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致，generated20:07:24.856321UTC/原deadline21:07:24.856321不延长。前轮d6已FINALIZED/released(02:26:41上海)且无headless lock/pending才begin。本轮随后真实report/finish/receipt确认，不预写PASS。'
            elif line.startswith('- HRC/PSBR完整训练效果'):
                lines[i]='- HRC/PSBR最终训练效果仍UNKNOWN；此前真实技术准入保留。PSNC为已有候选/独立source43，本轮补完整检查执行脚本和离线护栏，未真实模型执行，不把数学/静态/模拟检查代签native或资源。'
            elif line.startswith('- 当前2026-10-23 02:10:49'):
                lines[i]='- 当前'+observed_local+'上海真实同HRC PID2780804/start29604100/原argv/cwd/remoteHEAD74f/UUID，native12/50两次3582→3592/4686、仅GPU0原HRC context、logfresh；proof SHA'+sha(HERE/'hrc_training_progress_observation.json')+'。begin04:07监控partial best.4795/noimprove1，非终态/非champion，GPU1未查未用，无signal/新GPU计算。'
            elif line.startswith('- PSNC外置包'):
                lines[i]=line.replace('本轮native工具为disabled草案','旧d6 native工具disabled草案冻结保留，本轮独立完整operational包/static release仅供未来fresh执行')
            elif line.startswith('- PSNC当前blocked/'):
                lines[i]='- PSNC当前blocked/exclusive_gpu_slot/resumevalidation：实现/执行编排已静态准备完整，唯一GPU0忙，PSBR74f freshdispatch仍受保护。source43保持单亲74f/原9blob不改，主74f/index/28status+bytes/既有三账保持；root真实prepare(0)在占卡登记处提前拒绝，0transport/manifest/lease/binding；真实TRAIN2/资源待空GPU0，不跳准入。'
            elif line.startswith('- 前轮dfb诊断stage'):
                lines[i]='- 前轮dfb诊断执行lease已过期不重放。HRC/PSBR按原receipt/current source及资源保护训练/派发；unknownlaunch只读reconcile不盲重试。PSNC旧d6 disabled包不改，新42ce完整脚本/静态模块release可复用，但prepared token只是provenance；未来执行必须freshowner/context/deadline/lease，未创建任何activebinding。'
        memory='\n'.join(lines)+'\n\n## Last Tick\n'
        memory+='- 本轮42ce begin一次monitor/已有派发/goal，design/candidate1/creation1，但现有PSBR+PSNC约2准备足够，不新建变体；1HRCrunning/0claiming/1readyPSBRwaiting，M206另人工paused，10个blocked notdue不复核旧8hold或655证据。无新终态/故障。\n'
        memory+='- 精确HRC12/50两次3582→3592证实原生进展；begin监控partial best.4795/noimprove1，目标champion仍M95.5020/目标.5100差.0080。无空槽给native，未重复monitor/盲launch/处置进程或GPU1。\n'
        memory+='- 同一PSNC完整operational adapter/remote_ops+独立native包准备，复用原worker与原YAML/TRAIN2/资源/双idle/三锁；离线mock检查/独审见'+anchor['adapter_preparation']['path']+' SHA'+anchor['adapter_preparation']['sha256']+' / '+anchor['review']['path']+' SHA'+anchor['review']['sha256']+'。不把mock/native工具准备当真实native PASS。\n'
        memory+='- root物化仅静态modulehash release并外部锚，source43不改、原d6 disabled包不改、无新Gitcommit/sync。真实项目prepare(0)被原GPU0running登记提前拒绝，proof SHA'+sha(guard_path)+'，0transport/remote/GPU/nativelease/binding/收据/queue/训练。真实data/loss/backward/参数inventory/资源/效果仍待执行或UNKNOWN。\n'
        memory+='- 既有PSBR receipt/3summary及readonly admission继续通过、主74f/index/28小字节及PSNC43原9blob保持，continuation审SHA'+sha(HERE/'continuation_boundary_check.json')+'；HRC/M206/HAP原记录/原失败/授权保护不变。当前resource_check blocked与所有本轮证据同归PSNC，候选stageblocked/resumevalidation。\n'
        memory+='- 七段memory/六段report随后按原token真实finish/FINALIZED released及headless lock/pending消失才确认，释放后不回写。下一步只在PSBR版本边界安全且真空GPU0时用freshbinding完成原YAML M95/candidate TRAIN2+原资源，再据实准入入队；GPU1让出/M206暂停，旧hold不问重复确认，调度/资源/目标不改。\n'
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        save(ROOT/'pipeline/codex_memory.md',memory)
        notes={'actions':[
            'actual thread/target一致；canonical SKILL/experimentfirst/foreground及goal/SERVERS/当前memory已核，goalSHA0441/onlyserver4GPU0/max1/GPU1释放/M206paused/WindowsDisabled保持。前d6 FINALIZED released且无headless lock/pending才begin；原20:07:24.856321UTC/deadline21:07:24.856321不改。',
            'begin先monitor/已有队列派发/goal各一次，operationalissues空、新终态0；1running/0claiming/1readyPSBRwaiting，M206paused waiting另计。10旧blocked notdue不重审655/旧8，不重复授权问题或造新候选。',
            observed_local+'上海额外只读精确HRC原PID2780804/start29604100/原argv/cwd/remoteHEAD74f/GPU0 UUID核，native12/50两次3582→3592/4686、无error；仅GPU0原HRC context，未查询GPU1。begin04:07partial best.4795/noimprove1，非终态结果，champion仍M95.5020距目标.0080。',
            '既有PSBR74f/c85ae4fe receipt与3summary/readonly admission有效，仍waiting无hold/PID；主74f/index空/28status与小字节hash保持、PSNC独立43单亲74f且9blob同冻结302。HRC/M206人工pause/HAP自然earlystop原记录不变，无活跃checkout改动。',
            '继续同一PSNC完成完整operational adapter/remote_ops/native包，原worker/原YAML/TRAIN2/资源协议及双idle/3锁不变。离线模拟检查和独审实际结果留档，不声称真实模型路径/backward/效率已测。旧d6 disabled准备与9源hash不改，本轮0新candidate/commit/sync。',
            '独审通过后root仅copy已审static release并外部hash锚定；它仅批准确切工具module/version，不是freshlease/GPU空闲/执行授权证明。candidate resumevalidation而stage仍blocked。静态准备provenance可跨tick复用，实际运行需操作时freshowner/context/deadline/exactsource/assets/allowedGPU0/locks，禁止重放旧binding。',
            'root实际本项目Adapter.prepare(0)注入NoTransport，真实registered GPU0 HRC busy guard提前Refused，transport_calls0/SSH或GPU事件0/torch未导入/production执行dir与manifest/lease/binding均未创建，既有台账和module/staticreleasehash不变；不是实际原生或资源结果。',
            '当前tick_attempt是真resource_check blocked，当前HRC进展/新完整工具及guard证据全部同归PSNC。0新native/资源profile/标准summary/receipt/queue/launch；后续空GPU0且PSBR版本派发边界安全才可真实原YAML四进程pair，按实际结果review/准入/派发，不为本轮检查通过冒称方法有效。',
            '七段memory/六段report后按原token finish，真实返回/FINALIZED released/headless lock+pending消失才确认完成；释放后不回写。GPU1给别人/M206不恢复、不变资源白名单/原失败/修订上限/目标/调度，无需新用户处理事项。'
        ],'decisions':['canonical other决策已保存：完成已有PSNC完整检查编排与静态外锚并验证真实busy拒绝；等待实际GPU0和受保护版本条件，不新建重复候选、不把模拟/静态当科学准入。']}
        save(HERE/'tick_notes.json',notes)
        save(HERE/'research_persistence_result.json',{'recorded_at':now.isoformat(),'token':TOKEN,'candidate_id':CID,'code_commit':COMMIT,
            'native_execution_code_commit':None,'native':'NOT_RUN','resources':'NOT_RUN','decision':decision,
            'actual_local_guard':ref(guard_path),'static_release':anchor['static_release'],'memory_lines':len(memory.splitlines()),
            'new_candidates_commits_sync_receipts_queue_or_launches':0,'protected_registry_unchanged':{name:sha(ROOT/'pipeline'/name)==expected for name,expected in protected.items()}})
        print(json.dumps({'recorded':CID,'native':'NOT_RUN','source_commit':COMMIT,'resume_stage':'validation','stage':'blocked',
            'static_release_only':True,'actual_local_busy_guard':'refused_before_transport','decision':decision,'memory_lines':len(memory.splitlines())},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
