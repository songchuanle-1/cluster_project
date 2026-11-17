"""Final DCE research/memory/notes only. Default no writes; no lifecycle/launch API."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,re,sys
TICK=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_01d9102a')
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
DRAFT_EXECUTION_DISABLED=False
DCE='hierarchy-directed-cavity-edge-composition';APF='hierarchy-ancestry-path-factor-composition';EXP='M220-DCE'
PARENT='d0e2f95712ed16446907706fbf6a65d34996a9ad'
APF_FINAL=TICK/'apf_finalize_result.json';APF_SHA='f0bb37ce4339c868849b11dbfc1c3be0549764ec4353584873d74076373419a9'
SECTIONS=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick']
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def exclusive(path,data):
    guard()
    with Path(path).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def atomic(path,data):
    guard();path=Path(path);tmp=path.with_name(path.name+'.01d9102a.final.tmp')
    exclusive(tmp,data);guard();os.replace(tmp,path)
def bound_ref(entry):
    assert isinstance(entry,dict) and re.fullmatch(r'[0-9a-f]{64}',str(entry.get('sha256','')))
    path=(ROOT/entry['path']).resolve();assert path.is_relative_to(ROOT.resolve()) and sha(path)==entry['sha256']
    return u.read(path)
def current_head():return u.git(ROOT/'Cluster','rev-parse','HEAD').decode().strip()
def fresh_baseline(original,work,head):
    repo=ROOT/'Cluster';assert current_head()==head and u.git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==original['status_hex']
    assert len(original['files'])==28 and all(sha(repo/n)==h for n,h in original['files'].items())
    assert not u.git(repo,'diff','--cached','--name-only','-z')
    index=Path(u.git(repo,'rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute():index=repo/index
    names=set(original['protected_ledgers'])
    for n in ('experiments/M220-DCE.json','admissions/M220-DCE.json'):
        if (ROOT/'pipeline'/n).exists():names.add(n)
    assert len(original['protected_ledgers'])==22
    return {'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'head':head,'status_hex':original['status_hex'],'files':original['files'],'index_sha256':sha(index),
        'protected_ledgers':{n:sha(ROOT/'pipeline'/n) for n in sorted(names)},'candidate_digests':{c['id']:u.digest(c) for c in work['candidates']},
        'research_work_sha256':sha(ROOT/'pipeline/research_work.json'),'memory_sha256':sha(ROOT/'pipeline/codex_memory.md')}
def protect(b):
    guard();repo=ROOT/'Cluster';assert current_head()==b['head']
    assert u.git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and not u.git(repo,'diff','--cached','--name-only','-z')
    assert all(sha(repo/n)==h for n,h in b['files'].items())
    index=Path(u.git(repo,'rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute():index=repo/index
    assert sha(index)==b['index_sha256'] and all(sha(ROOT/'pipeline'/n)==h for n,h in b['protected_ledgers'].items())
    assert all(sha(repo/n)==h for n,h in b.get('current_candidate_source_paths',{}).items())
def settled_requests(code):
    rows=[];directory=TICK/'dce_execution'
    for mode in ('smoke','resources'):
        for target in ('champion','candidate'):
            request=directory/(mode+'_'+target+'_request.json')
            if not request.exists():continue
            q=u.read(request);path=directory/(mode+'_'+target+'_execution.json');assert path.exists(),'Started request has no terminal envelope; read-only reconcile first'
            e=u.read(path);assert e['certainty']=='terminal' and e['identity']['request_id']==q['request_id'] and e['identity']['candidate_id']==DCE and e['identity']['code_commit']==code
            assert e['identity']['token']==EXPECTED['token'] and e['identity']['physical_gpu']==0
            rows.append((mode,target,u.ref(path),e))
    return rows
def section_map(text):
    parts=text.split('\n## ');assert len(parts)==8
    out={}
    for part in parts[1:]:
        title,body=part.split('\n',1);out[title]=body.strip()
    assert set(out)==set(SECTIONS);return out

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute-root',action='store_true');ap.add_argument('--input-file');ap.add_argument('--input-sha256');args=ap.parse_args()
    if not args.execute_root:print('DEFAULT_READ_ONLY_NO_RECORD_WRITES');return
    assert not DRAFT_EXECUTION_DISABLED,'Review and enable a separate root-only copy'
    guard();assert sys.dont_write_bytecode and os.environ.get('GIT_OPTIONAL_LOCKS')=='0'
    assert re.fullmatch(r'[0-9a-f]{64}',args.input_sha256 or '')
    inp=Path(args.input_file or '').resolve();assert inp.is_relative_to(TICK.resolve()) and sha(inp)==args.input_sha256
    data=u.read(inp);assert data['owner']==EXPECTED and data['status'] in ('launched','failed','inconclusive')
    status=data['status'];code=data['code_commit'];assert code=='5c0c211c8ecc9479ecb34dbb8118a95f4b20e391'
    binds=data['bindings'];loaded={k:bound_ref(v) for k,v in binds.items()};assert 'source_version' in loaded
    version=loaded['source_version'];assert version['candidate_id']==DCE and version['code_commit']==code and version['parent_commit']==PARENT and version['diff_exact9A'] is True and len(version['frozen_source_files'])==9
    source_manifest=ROOT/'pipeline/diagnostic_bundles/tick_01d9102a/new_candidate_prepare/source_manifest.json'
    assert sha(source_manifest)=='747d0ae1382dee602291dff017da259e0a6bd82892b7ca172d16b2eaf6b32cc6' and version['frozen_source_files']==u.read(source_manifest)['source_files']
    assert sha(APF_FINAL)==APF_SHA;prior=u.read(APF_FINAL)
    assert prior['owner']==EXPECTED and prior['archive_id']=='e759341fee174dffb750f28a112aa25c' and prior['state']=='crashed'
    assert prior['root_cause_and_triggering_input']=='UNKNOWN' and prior['observed_exception']=='DataLoader scatter index dtype contract violation'
    assert prior['epochs']=='2/50' and prior['last_native_step']==301 and prior['exact_logger_best']==0.27984941005706787
    assert sha(ROOT/prior['exact_full_log']['path'])==prior['exact_full_log']['sha256']
    rows=settled_requests(code);assert rows,'No actual original DCE request evidence'
    queue=u.read(ROOT/'pipeline/queue.json');target=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')==EXP]
    if status=='launched':
        assert len(rows)==4 and all(e['returncode']==0 and e['result']['execution_completed'] is True for _,_,_,e in rows)
        for k in ('review','native_peer','resources','receipt','dispatch','growth'):assert k in loaded,k
        peer=loaded['native_peer'];assert peer['status']=='FOUR_ACTUAL_DCE_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED' and peer['candidate_id']==DCE and peer['code_commit']==code and peer['material_concerns']==[] and peer['goal_sha256']=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
        assert {(x['execution_path'],x['execution_sha256']) for x in peer['raw_results']}=={(ref['path'],ref['sha256']) for _,_,ref,e in rows}
        review=loaded['review'];assert review['review_status']=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' and review['candidate_id']==DCE and review['code_commit']==code
        assert review['observations']['native_semantics_and_pairing_checked'] is True and review['observations']['resource_protocol_checked'] is True
        receipt=loaded['receipt'];assert receipt['id']==EXP and receipt['code_commit']==code and receipt['profile']=='experiment_first'
        ds=loaded['dispatch'];assert ds['canonical_dispatch_invoked_once'] is True and ds['verified_native_progress'] is True and ds['physical_gpu']==0 and ds['token']==EXPECTED['token']
        task=ds['task_after'];assert task['status']=='running' and task['launch_verified'] is True and task['launch_verification']=='training_progress' and task['code_commit']==code
        assert len(target)==1 and target[0]['pid']==task['pid'] and target[0]['status']=='running'
        live=loaded['growth'];assert live['owner']==EXPECTED and live['returncode']==0
        ob=live['observation'];assert ob['runtime_commit']==code and ob['identity_before']==ob['identity_after'] and ob['identity_after']['pid']==task['pid']
        samples=ob['samples'];assert len(samples)==2 and samples[-1]['max_native_step']>samples[0]['max_native_step'] and all(s.get('tail_exception_seen') is False for s in samples)
        assert 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in str(ob) and str(task['pid']) in str(ob['GPU0_contexts'])
        if 'launch_peer' in loaded:assert loaded['launch_peer']['material_concerns']==[] and loaded['launch_peer']['code_commit']==code
        head=code;outcome='Actual four-arm technical admission and single canonical launch verified; efficacy UNKNOWN.'
    else:
        assert 'failure_execution' in loaded and isinstance(data.get('observation'),str) and data['observation'].strip()
        fail=loaded['failure_execution'];assert fail['certainty']=='terminal' and fail['identity']['candidate_id']==DCE and fail['identity']['code_commit']==code
        assert any(ref==binds['failure_execution'] for _,_,ref,e in rows)
        assert fail['returncode']!=0 or str((fail.get('result') or {}).get('coverage_status','')).startswith('INCONCLUSIVE')
        assert not target and not (ROOT/'pipeline/admissions/M220-DCE.json').exists(),'Partial admission/claim must be reconciled, not relabeled failure'
        head=current_head();assert head in (PARENT,code)
        outcome='Actual DCE attempt '+status+'; scope '+str(data.get('failure_scope','UNKNOWN'))+'; no efficacy rejection, root-cause inference or automatic retry.'
    assert current_head()==head
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();original=u.read(TICK/'protected_assets_before.json');work=u.read(ROOT/'pipeline/research_work.json')
        assert len(work['candidates'])==146 and len({c['id'] for c in work['candidates']})==146
        before=fresh_baseline(original,work,head);before['current_candidate_source_paths']=version['frozen_source_files'] if head==code else {}
        assert all(sha(ROOT/'Cluster'/n)==h for n,h in before['current_candidate_source_paths'].items())
        oldmemory=(ROOT/'pipeline/codex_memory.md').read_text('utf8');sections=section_map(oldmemory)
        by={c['id']:c for c in work['candidates']};assert by[APF]['stage']=='complete' and by[APF]['training_status']=='crashed'
        c=by[DCE];assert c['code_commit']==code
        if status=='launched':assert c['stage']=='training'
        else:assert c['stage']=='validation'
        now=datetime.now(timezone.utc).isoformat();attempt={'recorded_at':now,'status':status,'code_commit':code,'source_parent_commit':PARENT,'evidence':list(binds.values()),'scope':outcome}
        if c.get('current_attempt_record'):c.setdefault('attempt_record_history',[]).append(copy.deepcopy(c['current_attempt_record']))
        c['current_attempt_record']=attempt
        if status=='launched':
            epoch,step=samples[-1]['max_native_step'];pid=task['pid'];start=ob['identity_after']['start_ticks']
            c.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(c.get('latest_native_training_progress'))})
            c['latest_native_training_progress']={'recorded_at':ob['observed_at'],'pid':pid,'start_ticks':start,'epoch':epoch,'step':step,'steps_per_epoch':4686,'observed_steps':samples,'evidence':binds['growth'],'scope':'Actual exact original PID/source/runtime/GPU0 growth. Validation only as explicitly observed, efficacy UNKNOWN.','precise_native_validation':copy.deepcopy(live.get('precise_native_validation','UNKNOWN_NOT_RECORDED'))}
            c['next_action']='Monitor only original admitted DCE PID/log under original patience. Preserve all raw history and APF crashed e759 plus old HPC stopped_unknown73ba; no automatic APF/HPC restart, GPU1, blind relaunch or model tuning.'
            running_line=f'唯一已验证训练M220-DCE GPU0 PID{pid}/start{start}，source/runtime{code}；根{ob["observed_at"]} TRAIN{epoch}/50 {samples[0]["max_native_step"][1]}→{step}/4686。'
        else:
            c.setdefault('native_attempt_history',[]).append(attempt)
            fail_mode=next(mode for mode,target,ref,e in rows if ref==binds['failure_execution'])
            command=fail.get('command');assert isinstance(command,list) and command and all(isinstance(x,str) for x in command),'Actual raw worker command missing'
            actual_error=fail.get('result') or {}
            observation=json.dumps({'returncode':fail['returncode'],'error_type':actual_error.get('error_type'),'error':actual_error.get('error'),'coverage_status':actual_error.get('coverage_status'),'stderr_sha256':fail.get('stderr_sha256'),'root_observation':data['observation']},ensure_ascii=False,allow_nan=False)
            if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
            work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':DCE,'kind':'native_smoke' if fail_mode=='smoke' else 'resource_check','result':'failed' if status=='failed' else 'blocked','command':command,'observation':observation,'evidence':[binds['failure_execution']]}
            if fail_mode=='smoke':c['native_status']='ACTUAL_NATIVE_SMOKE_FAILED' if status=='failed' else 'ACTUAL_NATIVE_SMOKE_INCONCLUSIVE'
            else:c['resource_status']='ACTUAL_RESOURCES_FAILED' if status=='failed' else 'ACTUAL_RESOURCES_INCONCLUSIVE'
            if fail_mode=='resources' and any(mode=='smoke' for mode,target,ref,e in rows) and c.get('native_status','').startswith('NOT_RUN'):
                c['native_status']='ACTUAL_SMOKE_REQUESTS_EXECUTED_PENDING_SEMANTIC_PAIR_REVIEW'
            if fail_mode=='smoke' and any(mode=='resources' for mode,target,ref,e in rows) and c.get('resource_status','').startswith('NOT_RUN'):
                c['resource_status']='ACTUAL_RESOURCE_REQUESTS_EXECUTED_PENDING_PAIR_REVIEW'
            c['native_execution_code_commit']=code
            c['next_action']='Preserve exact current failed/inconclusive DCE request and stderr/coverage; determine its implementation/runtime/coverage scope before any separately reviewed fresh action. Do not infer whole-mechanism failure, replay, resume APF/HPC or change seed/data/precision.'
            running_line='本记录器没有DCE已验证launch；当前原始诊断请求已terminal，失败/覆盖范围待有据定位，不自动重试或恢复HPC。'
        for v in binds.values():
            if v not in c.setdefault('evidence',[]):c['evidence'].append(v)
        work['updated_at']=now;work['last_event_tick']=EXPECTED['generated_at'];work['next_action']=c['next_action']
        prior_line='APF/M219 canonical crashed/e759341fee174dffb750f28a112aa25c；原TRAIN2/50 step301、best exact.27984941005706787。已知DataLoader before-forward scatter index dtype contract violation，触发dtype/scan/RNG/upstream cause UNKNOWN；非HPC73ba stopped_unknown，不作OOM/机制否定/自动恢复推断。'
        sections['Goal And Phase']=f'- 当前01d9102a；generated{EXPECTED["generated_at"]}/deadline{EXPECTED["deadline_at"]}原值。Phase1层级pointfeature→inst_feats→masks；目标.5100/M95 champion.5020，Phase2人工。\n- goal0441/standing2e892/GPU0auth94075/SERVERS2583；仅server4 physicalGPU0/max1，GPU1禁用；M206pause/resumeFalse不变。\n- seed1999/epochs50/patience10/原YAML/data/pretrain/loss/optimizer/precision/≤10G不改；禁调参/gate/语言routing/大QKV/N²attention/重复inst/旧拒绝改名。'
        sections['Active Hypotheses']='- '+prior_line+'\n- 原APF04993 NULL/bf6/d0e兼容源/61185协议、技术准入和原crash证据保持；HPC6282技术检查与73ba stopped_unknown旧终态不动。\n- M220-DCE：原真fine-middle-coarse森林上directed cavity；fine_up=z_f，midup聚合fine、rootdown排receiver midup、middown平均1条rootdown+其他fine，三个readout；原3LN/rawskip/CSORT/HCG/单inst保留。bank-token分支删除不等于物理点自信息排除；同属cavity/messagepassing家族，novelty/收益UNKNOWN。\n- 原44e75 NULL/proto4b3c冻结；实际source'+code+'/父d0e2，本轮实际状态'+outcome+' 全新module aggregate训练性，individualmap/edge/row/bias零合法。'
        sections['Champion And Baseline']='- M95 champion.5020，目标.5100，gap.0080；本轮尚无新champion。\n- BEC.5001/24、AEF.495597243309021/23及CRE.4961479902267456/30均为历史正常早停，非本轮新结果。'
        sections['Closed Or Failed Directions']='- '+prior_line+'\n- 历史HPC73ba stopped_unknown：TRAIN2/3687，唯一val.2810768485069275；原因UNKNOWN，保留4技术门与收据，不自动恢复。\n- M206用户暂停、旧10parked边界不变；PCE2+extra1/RSTR2预算已尽，HAP授权已消费，不据空槽重开。\n- 历史CTS stopped_unknown14/.4890、BFC DataLoader overlap crash20/3832的上游原因仍UNKNOWN，恢复边界保留。'
        sections['Running And Queue']='- '+running_line+'\n- APF已crashed，HPC73ba stopped_unknown均不自动恢复；M206及旧hold/quota边界不动。仅GPU0 UUID958e741a，keys/strictpinned dl04；无信号/删锁/盲重放。\n- 当前146IDs；本记录器0新候选/0模型修订/0native或launch，canonicalqueue/running/CSV/experiment/receipt一字节不改。'
        sections['Open Questions And Risks']='- DCE效果/泛化/新颖性/pureTRAIN峰值UNKNOWN；两TRAIN/资源或早期增长非效果证明。\n- APF DataLoader契约错误已知，但真实触发输入/scan/RNG/上游cause UNKNOWN。HPC停止原因仍UNKNOWN，不混淆二者，不自动修依赖/数据或重启。\n- DCE各map/edge/row/bias零合法，缺可选degree/pad边界NOT_EXERCISED；无重抽样/额外backward/新FP32门。'
        sections['Last Tick']='- 本轮精确归档APF crash/e759并保留原证据，DCE实际分支'+status+'；只按真实哈希记录，不预签report/postflight/finish。\n- 最终仅DCE研究对象和memory/notes改变，其他145（含APF/HPC）保持；执行时实际HEAD/index/28用户字节及原22加目标存在账动态保护。'
        memory='# Codex Research Memory\n\n'+'\n\n'.join('## '+title+'\n'+sections[title] for title in SECTIONS)+'\n'
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        notes={'actions':[prior_line,'DCE实际分支'+status+'：'+outcome,running_line],'decisions':['原source/null/protocol/旧负证据不改；0新候选/0模型修订，未由记录器启动/恢复任何任务。','HPC停止原因UNKNOWN；APF触发causeUNKNOWN；DCE收益UNKNOWN。只实际证据可说明技术准入/launch，不借用旧PASS或推测终态。'],'evidence':{'apf_terminal':u.ref(APF_FINAL),'dce_status_input':u.ref(inp),'bindings':binds},'protected_lifecycle_count':len(before['protected_ledgers'])}
        assert all(u.digest(x)==before['candidate_digests'][x['id']] for x in work['candidates'] if x['id']!=DCE)
        payloads=[(ROOT/'pipeline/research_work.json',encoded(work)),(ROOT/'pipeline/codex_memory.md',memory.encode('utf8')),(TICK/'report_notes.json',encoded(notes))]
        intent=TICK/'final_dce_records_intent.json';result=TICK/'final_dce_records_result.json';snap=TICK/'final_dce_records_before.json'
        assert not any(x.exists() for x in (intent,result,snap,TICK/'report_notes.json'))
        assert all(not x.with_name(x.name+'.01d9102a.final.tmp').exists() for x,_ in payloads)
        protect(before);assert sha(ROOT/'pipeline/research_work.json')==before['research_work_sha256'] and sha(ROOT/'pipeline/codex_memory.md')==before['memory_sha256']
        exclusive(intent,encoded({'owner':EXPECTED,'recorded_at':now,'input':u.ref(inp),'before':before,'old_memory':oldmemory,'scope':'DCE research/memory/private notes only; no source or canonical lifecycle writes; partial replay forbidden.'}))
        exclusive(snap,encoded(before))
        for dest,data_bytes in payloads:
            if dest==TICK/'report_notes.json':exclusive(dest,data_bytes)
            else:atomic(dest,data_bytes)
        protect(before);after=u.read(ROOT/'pipeline/research_work.json');assert len(after['candidates'])==146
        assert all(u.digest(x)==before['candidate_digests'][x['id']] for x in after['candidates'] if x['id']!=DCE)
        exclusive(result,encoded({'owner':EXPECTED,'recorded_at':now,'actual_branch':status,'source_head_preserved':head,'changed_candidates':[DCE],'other145_including_APF_unchanged':True,'protected_lifecycle_count':len(before['protected_ledgers']),'source28_status_empty_staging_and_actual_index_preserved':True,'notes':u.ref(TICK/'report_notes.json'),'memory_lines':len(memory.splitlines()),'canonical_postflight_report_finish_performed':False}))
        print(json.dumps(u.ref(result)))
    finally:lock.close()
if __name__=='__main__':main()
