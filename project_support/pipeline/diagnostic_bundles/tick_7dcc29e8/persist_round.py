"""Persist BTC implementation checks and protected PSNC resource carryover."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
PACKET=HERE/'btc_operational_prepare'; TOKEN='7dcc29e8844245ec87b6d58eee6ec966'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,x,text=False):
    t=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with t.open('x',encoding='utf-8') as f:f.write(x if text else json.dumps(x,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(t,p)
def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    proof=HERE/'btc_actual_local_guard_integration.json';g=read(proof)
    assert g['status']=='ACTUAL_LOCAL_CURRENT_OWNER_GUARD_VALID_BUSY_PREPARE_REFUSED_NO_TRANSPORT'
    assert g['actual_transport_calls']==0 and not g['active_binding_manifest_lease_or_execution_directory_created']
    assert read(PACKET/'offline_tests/full_offline_run1.json')['tests_run']==46
    assert sha(HERE/'btc_operational_final_review.json')=='d6621170da757565ab6ffd41e8dc6459bcd3d36ea6ad41d54e7257b342cb4ece'
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        work=read(ROOT/'pipeline/research_work.json');queue=monitor.load_queue(str(ROOT))
        c=next(c for c in work['candidates'] if c.get('experiment_id')=='M211-BTC')
        p=next(c for c in work['candidates'] if c.get('experiment_id')=='M210-PSNC')
        assert c['stage']=='blocked' and c['blocker_kind']=='exclusive_gpu_slot' and c['native_execution_code_commit'] is None
        assert p['stage']=='training' and next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M210-PSNC')['pid']==2502712
        assert not any(t['id']=='M211-BTC' for ts in queue['gpu_queues'].values() for t in ts)
        assert next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA')['resume_authorized'] is False
        c['execution_adapter']['actual_local_guard_integration']=ref(proof)
        c['implementation_status']='OPERATIONAL_PACKET_REVIEWED_STATIC_ONLY_NATIVE_PENDING'
        for path in [proof,HERE/'btc_static_anchor_result.json',HERE/'btc_native_implementation_review/static_validation.json',PACKET/'offline_tests/full_offline_run1.json',HERE/'btc_independent_review/native_protocol_boundary.json']:
            item=ref(path)
            if item not in c['evidence']:c['evidence'].append(item)
        item=ref(HERE/'psnc_progress_observation.json')
        if item not in p['evidence']:p['evidence'].append(item)
        work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':c['id'],'kind':'implementation_test','result':'passed',
            'command':'python -B -X utf8 '+str(HERE/'check_btc_actual_guard.py'),
            'observation':'BTC frozen-source operational packet passed 46 actual offline orchestration tests and 10 AST/stdlib/stub checks plus independent review. Root actual current-owner guard/external anchors passed; prepare refused registered busy PSNC, GPU1/deadline refused; zero transport/torch/GPU/active binding. Actual native TRAIN2/resources/efficacy remain NOT_RUN; no admission/queue/launch.',
            'evidence':[ref(proof),ref(PACKET/'offline_tests/full_offline_run1.json'),ref(HERE/'btc_native_implementation_review/static_validation.json'),ref(HERE/'btc_operational_final_review.json'),ref(HERE/'btc_static_anchor_result.json')]}
        work['updated_at']=datetime.now(timezone.utc).isoformat();save(ROOT/'pipeline/research_work.json',work)
        memory=(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8').replace('本轮','前轮a4f')
        lines=memory.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('- 最新接管'):
                lines[i]='- 最新接管7dcc29e8844245ec87b6d58eee6ec966；actual CODEX_THREAD_ID/target=01a159c5-29ab-7a22-ba7f-e79174757253一致。generated2026-10-24T00:03:32.596669UTC/原deadline01:03:32.596669UTC不延长；前a4f已FINALIZED/released并无ownedlock/pending才begin。'
            elif line.startswith('- 当前唯一M210'):
                lines[i]='- 当前唯一M210-PSNC running server4GPU0/PID2502712/start41082267；2026-10-24 08:05左右上海原argv/cwd/fd1精确唯一log/HEAD43/GPU0UUID两次核，Train4/50 1352→1361/4686，无error/logfresh。proof本轮psnc_progress_observation.json SHA413b7e52e79d3766baf97eb27b21b1082631652efebb52d8c1cdd11cc085fd77；原dispatch未记startticks，本次只核两次start一致，不伪称原启动时已记录。'
            elif line.startswith('- BTC isolated_versions/'):
                lines[i]='- BTC isolated_versions/btc_2c25f38f与PSNC isolated_versions/psnc_d6b400e3保留clean，primary/runtime43不动。BTC目前blocked/exclusive_gpu_slot/resumevalidation；本轮已补齐专属完整worker/runtime+adapter/remote_ops，仍无native_execution_commit/receipt/queue。'
        memory='\n'.join(lines)+'\n'
        memory=memory.replace('现workers[]/computecontexts空已只读reconcile留证','当时诊断workers[]/computecontexts空已只读reconcile留证')
        added='''- BTC本轮operational packet tick_7dcc29e8/btc_operational_prepare：outer prep9be7386ad317c4286ce697acf6e114f2c7e02e920fb0950ac4b7134f4432918e(26map)，native prep82b7ae52260fdfb79c69e96d20c8e8b5ea501a70bfaaf4e71d3028ad0c9cbe18(14map)、manifest4a28e488…(12diagnostic)。9冻源与Git00e exact、parent43/sourceproof49f85…；所有active字段null，原c36b prep不改。
- BTC worker a39fbffa…/runtime dd2ac226…；实际10项AST/生产stdlib/stub检查通过a6222a4a…，资源函数/7runtime安全函数AST沿用。观察生产builder一次透传及真实GELU输出；未来必须真实n>=3使inside原loss可达、inside/outside/leaf各有限梯度和更新，原cfskip/fine-coarse/rawCSORT/HCG/单inst保持。非torch/autograd实测。
- BTC adapter c83d9e88…/remote97192f56…；实际46离线orchestration/mock tests全PASS(6adc8dbf…)、0真实Popen/socket/torch。首次11子集属于46不另加数，旧589不重跑。最终独审d6621170…43项只读核26/14/12maps、原源码/保护/所有边界，无materialconcern，不是native PASS。
- Root已materialize同字节reviewed static release765beabf…并外锚worker/adapter/prep/release。真实当前owner/context/外锚guard通过；NoTransport实际prepare因registered PSNC忙在probe/目录/lease前拒绝，GPU1/deadline也拒绝，0transport/torch/GPU，见btc_actual_local_guard_integration.json。不是实际idle/assets/native证据。
- BTC完整操作工具准备完成可复用；GPU0仍PSNC占用，未来fresh owner/context/deadline/授权/assets/UUID/真实idle/双观察3锁后才stage+M95/BTC TRAIN2/原resource pair；实际全params/common初始化/FP32/梯度/n>=3/资源/效能一律NOT_RUN或UNKNOWN。静态catalog不授GPU或解除M206暂停。
'''
        memory=memory.replace('\n## Closed Or Failed Directions','\n'+added+'\n## Closed Or Failed Directions')
        memory=memory.split('## Last Tick',1)[0]+'''## Last Tick
- 本轮7dcc begin一次monitor/goal/既有派发，design预算2/reserve2/creation2；唯一PSNC训练。快照new_terminal M209是前a4f已归档/已通知结果，本轮不重复归档、重跑或当新训练完成。
- 实际PSNC第4/50轮1352→1361/4686，同PID/start/argv/cwd/fd1/UUID/HEAD43，无error，GPU1未查未用。当前正式validation指标本轮未采集；M95仍best.5020距.5100差.0080。
- 完成既有BTC00e完整原生执行工具与46离线+10静态/模拟检查、独立整包review、静态catalog/外部锚及真实root NoTransport guard集成；0native/GPU资源实测/新candidate/新sourcecommit/sync/admission/queue/launch。
- 当前实际implementation_test passed同归BTC证据；prepare真实因registered PSNC占唯一GPU0拒绝，无active目录/manifest/lease/transport。保留blocked资源等待，不为通过校验伪造native PASS或权限问题、不为compact reserve0再造候选。
- 8旧hold及655旧证据/授权正文未重读、未重hash或重开；goal0441/SERVERS9a8原hash/standing授权/禁用项/协议/资源和Windows Disabled保持，PSNC/M206不动。
- 本轮NOTIFY：BTC工具从缺失到完整准备/离线验收，不等于已训练；无需新授权。七段memory与六段report在原lease内保存，实际收尾核pipeline/tick_receipts/7dcc29e8844245ec87b6d58eee6ec966.json和lock/pending消失；写此条时尚未finish，不预写PASS或释放后回写。
'''
        assert len(memory.splitlines())<120 and memory.count('\n## ')==7
        save(ROOT/'pipeline/codex_memory.md',memory,text=True)
        notes={'actions':[
            '2026-10-24 08:05左右上海只读双核原PSNC PID2502712/start41082267/argv/cwd/fd1唯一log/HEAD43/GPU0UUID，真实Train4/50 1352→1361/4686增长，无error。GPU1未查未用，无signal/重启/源码变动。',
            '复用既有BTC00e冻结9文件，逐字节匹配原c36b prep及Git00e/parent43；仅在本轮诊断目录准备专属nativeworker/runtime和完整guarded adapter/remote_ops，原模型源/YAML/seed/schedule/data不改。',
            '实际10项AST/生产纯stdlib/observer stub边界检查通过，原resources/7安全函数AST保持；46项离线orchestration/mock测试全PASS、0真实Popen/socket/torch。11早期子集不重复计数，旧589不重跑。',
            '冻结native14prepared/12diagnostic及outer26map，经43项独立只读整包审核无问题；root仅materialize同字节reviewed staticrelease和外部candidate锚，所有active执行字段仍null，无lease/真实GPU检查/receipt/queue。',
            '实际root当前owner/context/pending/外锚guard通过；NoTransport prepare在registeredPSNC占GPU0时于probe/目录/lease之前拒绝，GPU1及deadline不足同样拒绝，0transport与共享文件变化。',
            '前a4f已归档PSBR23/.4969虽再次列为快照new_terminal，此轮不重复归档/当新完成。M206暂停、GPU1让出、28保护/index/main43及原资源/目标/禁用项/调度保持；8旧hold未重读或重开。'],
            'decisions':[
            'BTC已从缺少专属native操作工具推进到完整静态准备并离线验收；实际TRAIN2/参数初始化配对/FP32/autograd/n>=3梯度/资源/效能仍NOT_RUN或UNKNOWN，不生成原生PASS/准入/排队。',
            '未来仅在PSNC自然结束且实际授权GPU0空闲后，以freshowner/deadline/assets/UUID/双idle/三锁运行M95/BTC原TRAIN2及原资源pair；保持原source00e/protocol，挂起旧路线不获恢复/额外修订。',
            '当前PSNC继续原生训练且无错误，本轮正式validation指标未采集；M95仍0.5020距目标0.5100差0.0080。不为了缺口调参、造重复候选或打扰现有训练。',
            '完整BTC执行入口准备完成属于本轮实质变化，NOTIFY；无需用户新增确认。report/finish按原deadline真实收尾，不提前写成功。']}
        save(HERE/'tick_notes.json',notes)
        save(HERE/'round_persistence.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,
            'tick_attempt':work['tick_attempt'],'memory_lines':len(memory.splitlines()),'native_executed':False,'training_launched':False,'finish_yet':False})
        print(json.dumps({'memory_lines':len(memory.splitlines()),'tick_attempt':'actual_implementation_test_passed_native_NOT_RUN','notes_saved':True,'finish_yet':False}))
    finally:lock.close()
if __name__=='__main__':main()
