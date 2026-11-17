"""Truthful closure of AEF terminal plus two failed independent baseline controls."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,subprocess,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
AEF='hierarchy-parent-antisymmetric-edge-flux';CRE='hierarchy-cross-root-directed-edge-broadcast';HPC='hierarchy-tree-resolvent-nonlinear-composition'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,v):
    guard()
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def atomic(p,v,text=False):
    guard();tmp=Path(str(p)+'.0f02aaa2.final.tmp');assert not tmp.exists()
    with tmp.open('x',encoding='utf8') as f:f.write(v if text else json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    guard();os.replace(tmp,p)
def protect(b):
    git=lambda *a:subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
    assert git('rev-parse','HEAD').decode().strip()==b['head']=='56b2a96dc48cc8a88f0f7105527ef448113b1060'
    assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and not git('diff','--cached','--name-only','-z')
    assert all(sha(ROOT/'Cluster'/n)==h for n,h in b['files'].items())
    allowed={'queue.json','running.json','experiments.csv','experiments/M216-AEF.json'}
    assert all(sha(ROOT/'pipeline'/n)==h for n,h in b['protected_ledgers'].items() if n not in allowed)
    return {n:sha(ROOT/'pipeline'/n) for n in b['protected_ledgers']}
def main():
    guard();b=read(HERE/'protected_assets_before.json');postarchive=protect(b)
    reviewp=HERE/'native_import_failures_independent_review.json';assert sha(reviewp)=='0528056cdbb3049306e9a17dfcab2d14b557475b587340f73906afbd9f523d61'
    review=read(reviewp);assert review['status']=='CRE_AND_HPC_FIRST_CONTROL_IMPORT_FAILURES_INDEPENDENTLY_REVIEWED_NO_ADMISSION'
    probe=HERE/'final_gpu0_observation.json';assert sha(probe)=='456a8a7fd833468c1a58e04c344a7880df0b4aaa46846cc2870d29afdb2e3058'
    assert read(probe)['owner']==EXPECTED and read(probe)['physical_observation']['idle'] is True
    rawpaths={CRE:HERE/'cre_execution/smoke_champion_execution.json',HPC:HERE/'hpc_execution/smoke_champion_execution.json'}
    for cid,p in rawpaths.items():
        raw=read(p);r=raw['result'];assert raw['identity']['candidate_id']==cid and raw['identity']['token']==EXPECTED['token']
        assert raw['certainty']=='terminal' and raw['returncode']==1 and r['execution_completed'] is False
        assert r['optimizer_steps']==r['native_loss_forwards']==r['native_criterion_backwards']==0
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import closure
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();assert protect(b)==postarchive
        work=read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==144
        assert all(digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in {AEF,CRE})
        ae=next(c for c in work['candidates'] if c['id']==AEF);cre=next(c for c in work['candidates'] if c['id']==CRE);hpc=next(c for c in work['candidates'] if c['id']==HPC)
        assert ae['stage']=='complete' and ae['terminal_archive_id']=='ad76de1eebbd43f7be720a8b17fca1cb'
        assert cre['stage']==hpc['stage']=='validation' and cre['code_commit']=='d58576b396cfb54577652be972f3ffaffda508c9' and hpc['code_commit']=='2f7eff19ca59cc4586e13ca81a547a18ea7e313d'
        exp=read(ROOT/'pipeline/experiments/M216-AEF.json');assert exp['status']==exp['training_status']=='done_earlystop'
        assert exp['final_best']=='0.4956' and exp['epochs_final']=='23/50'
        queue=read(ROOT/'pipeline/queue.json');assert not any(t.get('id')=='M216-AEF' for rows in queue['gpu_queues'].values() for t in rows)
        now=datetime.now(timezone.utc).isoformat();save(HERE/'tick_records_final_intent.json',{'recorded_at':now,'owner':EXPECTED,'research_before_sha256':sha(ROOT/'pipeline/research_work.json'),'scope':'Record two actual independently failed baseline imports; no model revision, admission or launch.'})
        extra=['cre_import_diagnostic_r2/cpu_import_probe_result.json','cre_import_diagnostic_r3/cpu_import_probe_result.json','lark_only_control_result.json','lark_only_control_r1_result.json']
        for c,short in [(cre,'cre'),(hpc,'hpc')]:
            raw=read(rawpaths[c['id']]);r=raw['result']
            c.setdefault('native_check_history',[]).append({'recorded_at':now,'prior_current_native_check':copy.deepcopy(c.get('current_native_check'))})
            c['current_native_check']={'recorded_at':now,'kind':'native_smoke','result':'failed','target':'champion','code_commit':c['code_commit'],'optimizer_steps':0,'native_loss_forwards':0,'native_criterion_backwards':0,'request_id':raw['identity']['request_id'],'evidence':ref(rawpaths[c['id']]),'error_type':r['error_type'],'error':r['error'],'failure_scope':'original_M95_dependency_import_before_model_construction','root_cause':'UNKNOWN','candidate_model_graph_executed':False,'remaining_three_arms':'NOT_RUN','model_revision_created':False,'scope':'This candidate independently attempted its original M95 control. Import failed before model construction, so it is no candidate mechanism or resource-budget refutation.'}
            c.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(c.get('resource_check')),'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check'))})
            c['resource_check']=ref(probe);c['current_resource_check']={'recorded_at':read(probe)['recorded_at'],'kind':'physical_occupation_only','result':'physically_idle_at_observation','server':'server-4','physical_gpu':0,'evidence':ref(probe),'scope':'No worker/context and all three locks available at observed time. This is not a FLOPs/latency/native PASS or future launch permission. Import failure is the current readiness gap.'}
            names=[short+'_execution/execution_binding.json',short+'_execution/native_manifest.json',short+'_execution/execution_lease.json',short+'_execution/stage_execution.json',short+'_execution/smoke_champion_execution.json',short+'_initial_smoke_trace.json',short+'_original_request_reconcile_cli.log','native_import_failures_independent_review.json','final_gpu0_observation.json']
            if c['id']==CRE:names+=extra
            for name in names:
                e=ref(HERE/name)
                if e not in c['evidence']:c['evidence'].append(e)
            c['next_action']='Preserve this independent first-control terminal failure, raw/reconcile/trace and exact original source. Root cause of original M95 spconv/pccm/Lark import is UNKNOWN; collect a bounded reproducible same-environment dependency diagnosis before any reviewed compatibility repair or new native request. No replay, model tuning, extra revision, library/cache change or gate PASS is implied. Candidate and resources remain NOT_RUN; require original paired native TRAIN2 and same-budget resources before admission under fresh owner/original deadline/physical0 UUID/idle/three locks.'
        if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
        work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':HPC,'kind':'native_smoke','result':'failed','command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_f395f943/hpc_operational_prepare/adapter.py run --mode smoke --target champion','observation':'HPC independently ran its own original M95 control; terminal rc1 AttributeError in spconv/pccm/Lark before model construction, zero loss/backward/optimizer. Exact request reconciled and workers absent. CRE separately failed original control with TypeError; no raw relabelling. Three remaining arms per candidate NOT_RUN. Root cause unknown, no tested candidate model or admission.','evidence':[ref(rawpaths[HPC]),ref(HERE/'hpc_initial_smoke_trace.json'),ref(reviewp)]}
        work['shared_import_diagnosis']={'recorded_at':now,'root_cause':'UNKNOWN','two_independent_control_import_failures':True,'precise_dependencies':'Original M95 import spconv→pccm→Lark; CRE stdlib regex TypeError, HPC Lark transformer AttributeError.','evidence':ref(reviewp),'CPU_limits':'Standalone regex and original grammar constructor without native user transformer passed; original full-import equivalence unproved. Three CPU collector fence obstacles and one collector failure retained. R2/R3 loaded/source code equal in their own processes, not evidence about original failed workers or a fix.','model_or_dependency_or_global_cache_modified':False,'global_research_pause':False}
        work['last_event_tick']=EXPECTED['generated_at'];work['updated_at']=now;work['next_action']='AEF canonical/research complete23/50, precise best .4955972433 below M95 .5020. Preserve both independently failed CRE/HPC original-M95 control requests. Next bounded task is reproducible dependency import diagnosis; candidate graphs and resources still NOT_RUN, no new training qualified. GPU1 forbidden, all old holds/resumes and source9/config/seed/schedule unchanged.'
        atomic(ROOT/'pipeline/research_work.json',work)
        for c in [ae,cre,hpc]:
            for e in c['evidence']:closure.artifact(ROOT,e)
        assert protect(b)==postarchive
        sections={};name=None
        for line in (ROOT/'pipeline/codex_memory.md').read_text('utf8').splitlines():
            if line.startswith('## '):name=line[3:];sections[name]=[]
            elif name is not None:sections[name].append(line)
        sections['Goal And Phase'][0]='- 当前0f02aaa25b1a4f6e9d27cf8da33b8ca1；actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-27T16:10:56.900706Z/deadline17:10:56.900706Z原值保持不延长。'
        sections['Champion And Baseline'].append('- M216-AEF本轮确认原生正常earlystop23/50，23次native logger精确best.495597243309021，canonical/earlystop打印.4956；低M95 .0064027567。仅该次实现未超过champion，不否定整个机制，不调参重跑。')
        active=[]
        for s in sections['Active Hypotheses']:
            if s.startswith('- 当前c7a4 CRE guard'):continue
            if s.startswith('- M216-AEF原source'):s=s.replace('- M216-AEF原source','- M216-AEF本轮已正常归档，原source')
            s=s.replace('未promotion/sync/native/准入','未promotion/sync/候选图执行/准入').replace('主线/runtime仍56，未promote/sync/native','主线/runtime仍56，未promote/sync/候选图执行')
            active.append(s)
        active.append('- 本轮CREd585与HPC2f7各自prepare/stage成功，各自首M95 control原生worker终态rc1/0loss/0backward/0optimizer；CRE TypeError list callable在sre_compile，HPC AttributeError Transformer_NonRecursive nochildren在Lark，均原M95→spconv/pccm/Lark import、模型构造前。request f11717294d4f4e82b66daa065b58c2ee/cb0abedec37c4d5586814d8d45965f7f分别reconcile，无worker；各余3臂NOT_RUN，未重放。')
        active.append('- 两control失败独审0528056c确认根因UNKNOWN，不签四臂/资源/修复/科学否定。原8源+YAML各9文件/source版本/worker/runtime/门/修订计数保持，native model graph未测。两现有储备继续validation，故障是原生导入就绪，不是GPU忙。')
        active.append('- CPU诊断保留：regex独立PASS；r0挡devnull、r1出现原import异常且collector自身异常、r2挡tmp、r3挡matplotlib目录；r2/r3本进程loaded/source四项相同，不推断原worker或stalepyc。纯Lark原grammar省略AttrArgTransformer的构造PASS17386cf3，只限该条件；完整pccm/native未证明。无依赖/stdlib/全局缓存改动，无无限探针或修复声称。')
        sections['Active Hypotheses']=active
        sections['Closed Or Failed Directions']=[s for s in sections['Closed Or Failed Directions'] if not s.startswith('- 旧10 holds')]
        sections['Closed Or Failed Directions'].append('- 旧10 holds本轮NOTdue，原冻结边界保持；其他141候选保持原值。AEF archive ad76de1eebbd43f7be720a8b17fca1cb，全logSHA0294c92037e9f708ca79ddcc88d6686203147cd9e4800b89a0d8c4d15e71407d，canonical与辅助training_status/research complete已对齐。初observer因刚结束proc缺失失败及exactend证据均保留。')
        sections['Running And Queue'][0]='- 当前0训练/0claiming/0ready；唯一waiting M206仍用户暂停且不可派发。AEF正常23/50终态已归档，不再登记运行。CRE/HPC各独立首M95 control导入失败、0训练步，候选图/资源仍未测，0新准入/排队/正式训练。'
        sections['Running And Queue'].append('- 上海00:38:35最新GPU0只读probe：41MiB/util0/无compute context/三锁available，runtime56/UUID正确。此时间点空闲不授未来启动；GPU1未查询/禁用，不挤占别人。')
        sections['Open Questions And Risks']=[s for s in sections['Open Questions And Risks'] if not s.startswith('- AEF正式训练效果未知')]
        sections['Open Questions And Risks'].append('- 当前精确根因UNKNOWN，不能凭两条导入trace就安装/降级依赖、删缓存、改stdlib或候选图。下一步需有范围的同环境导入复现/代码与包来源定位，再决定兼容修复并重新原生验证；不要把CPU collector的fence障碍当原环境故障。')
        sections['Last Tick']=['- begin一次canonical监控/目标/既有派发；AEF随后正常23/50早停，exactlog/PID/source/YAML/idle证据后canonical归档及research/辅助状态对齐，无archive重放。','- 两独立既有候选各新prepare/stage与首M95 control真实执行，均模型构造前import失败、0loss/backward/optimizer；分别精确reconcile/trace保存，三余臂各未跑，无新正式训练。未把一条失败重标另一候选。','- 多个CPU采集器障碍与独立regex/grammar对照如实留档；没有确定修复，根因UNKNOWN。无源/model/worker/依赖/缓存修改、无准入或新模型修订。','- 主线56/28用户文件/status/index保持；begin16账仅AEF合法归档4条改变，其余12保持，辅助校准只改AEFexp字段；M206/旧10授权及其他项目/调度不动。','- tick_attempt=HPC真实native_smoke/failed，CRE失败也绑原证据。最新GPU0空闲而原生就绪受阻，非资源忙或待新授权。随后report/finish核释放，不预签收尾。']
        names=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick'];lines=['# Codex Research Memory','']
        for n in names:lines.extend(['## '+n]+[s for s in sections[n] if s]+[''])
        assert len(lines)<120;atomic(ROOT/'pipeline/codex_memory.md','\n'.join(lines),text=True)
        notes={'actions':['上海00:12:33核原AEF PID消失、精确earlystop23/50标记/noimprove10且无异常尾标、source8/YAML/runtime56不变；完整原log本远大小/SHA0294c920一致，canonical archive ad76后research complete/辅助training_status对齐。23次native logger best0.495597243309021，打印/canonical0.4956，未读checkpoint指标冒充精确值。','本轮CREd585与HPC2f7分别现有包prepare/stage通过并真实执行独立首M95 control；各终态rc1，均0loss/0backward/0optimizer，模型构造前导入失败。CRE regex TypeError、HPC Lark transformer AttributeError，原request分别reconcile，无worker。各剩余三臂NOT_RUN，无推广或准入。','有范围CPU诊断保留全部负结果/采集障碍；独立regex及省略用户transformer的原grammar构造通过，其条件不等完整原import。R2/R3的loaded/source代码相同只限本进程，不证明原worker或修复。独审0528056c确认两原生失败与根因UNKNOWN；未改依赖/stdlib/全局缓存或原模型图。','上海00:38:35 GPU0 fresh probe idle41MiB/util0/无context/三锁available、runtime56/UUID匹配；GPU1未查/禁用。当前无新训练，障碍是原生导入就绪。主线28/status/index及非AEF12生命周期账保持；0新候选/模型修订/源码提交/同步/准入/正式训练。'],
               'decisions':['AEF本次实现best0.495597低M95 0.5020约0.006403，已正常结束；不调参重跑、不将该结果扩张为整个机制的证伪。目标0.5100/项目最佳0.5020/gap0.0080仍未改变。','CRE和HPC各自独立尝试，挂起一条未阻断另一条。两候选图均未执行、资源均未测试，不能签PASS/入队/启动，也不把CPU软件对照当原生通过或缺授权。','当前根因UNKNOWN；下一步先做有范围的同环境依赖导入复现与包/加载代码定位，获得证据后才能提出具体兼容修复、原生重测及同轮准入。保持原失败及源码/原YAML/data/seed1999/50-70/禁用项；不盲重放、删缓存、改shared环境或扩大资源。','本轮存在实质终态和原生检查失败，应通知当前无新训练及具体阻塞；无需新的常规操作授权。M206继续暂停，BFC/M201恢复与PCE/RSTR预算边界保持，不改其他项目或调度。']}
        save(HERE/'report_notes.json',notes)
        after={c['id']:digest(c) for c in work['candidates']};changed=[k for k,h in b['candidate_digests'].items() if after[k]!=h];assert set(changed)=={AEF,CRE,HPC}
        save(HERE/'protected_assets_after.json',{'recorded_at':now,'primary_HEAD':b['head'],'source28_status_index_preserved':True,'begin16_ledgers_changed_only_AEF_canonical_four':['queue.json','running.json','experiments.csv','experiments/M216-AEF.json'],'other12_begin_ledgers_preserved':True,'postarchive_ledgers_preserved_during_final_records':True,'candidate_count':144,'changed_candidates':changed,'other141_candidates_preserved':True,'new_candidates':0,'new_model_revisions':0,'new_source_commits_or_sync':0,'native_workers_started':2,'independent_native_control_failures':2,'candidate_forwards_or_new_training':0,'new_admissions':0,'root_cause':'UNKNOWN'})
        print(json.dumps({'AEF':'done_earlystop23/50','AEF_precise_best':0.495597243309021,'native_control_attempts':2,'candidate_steps':0,'new_training':0,'memory_lines':len(lines),'notes':ref(HERE/'report_notes.json')},ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
