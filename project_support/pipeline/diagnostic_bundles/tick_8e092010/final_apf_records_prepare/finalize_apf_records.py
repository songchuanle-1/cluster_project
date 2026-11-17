"""Final APF research/memory/notes only. Default no writes; no lifecycle/launch API."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,re,sys
TICK=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_8e092010')
sys.path.insert(0,str(TICK))
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
DRAFT_EXECUTION_DISABLED=True
APF='hierarchy-ancestry-path-factor-composition';HPC='hierarchy-tree-resolvent-nonlinear-composition';EXP='M219-APF'
PARENT='6282263d805c1741234f97afc981a05aca2ad6e3'
HPC_FINAL=TICK/'hpc_finalize_result.json';HPC_SHA='7a78d3485b61a6e41035dc4b660f5d80a88f4bbb8ab4d2b1e03b9f1ff7e90bdf'
SECTIONS=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick']
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def exclusive(path,data):
    guard()
    with Path(path).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def atomic(path,data):
    guard();path=Path(path);tmp=path.with_name(path.name+'.8e092010.final.tmp')
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
    for n in ('experiments/M219-APF.json','admissions/M219-APF.json'):
        if (ROOT/'pipeline'/n).exists():names.add(n)
    assert len(original['protected_ledgers'])==20
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
    rows=[];directory=TICK/'apf_execution'
    for mode in ('smoke','resources'):
        for target in ('champion','candidate'):
            request=directory/(mode+'_'+target+'_request.json')
            if not request.exists():continue
            q=u.read(request);path=directory/(mode+'_'+target+'_execution.json');assert path.exists(),'Started request has no terminal envelope; read-only reconcile first'
            e=u.read(path);assert e['certainty']=='terminal' and e['identity']['request_id']==q['request_id'] and e['identity']['candidate_id']==APF and e['identity']['code_commit']==code
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
    status=data['status'];code=data['code_commit'];assert isinstance(code,str) and re.fullmatch(r'[0-9a-f]{40}',code)
    binds=data['bindings'];loaded={k:bound_ref(v) for k,v in binds.items()};assert 'source_version' in loaded
    version=loaded['source_version'];assert version['candidate_id']==APF and version['code_commit']==code and version['parent_commit']==PARENT and version['diff_exact9A'] is True and len(version['frozen_source_files'])==9
    source_manifest=ROOT/'pipeline/diagnostic_bundles/tick_01b53a4e/new_candidate_prepare/source_manifest.json'
    assert sha(source_manifest)=='0ef045c73d89c3c33200f31bb7eeb05667f81e2bf653f77aafb8951c6b6fd8e3' and version['frozen_source_files']==u.read(source_manifest)['source_files']
    assert sha(HPC_FINAL)==HPC_SHA;hpc=u.read(HPC_FINAL)
    assert hpc['owner']==EXPECTED and hpc['archive_id']=='73ba99a73d394a37a41dc431277a3543' and hpc['state']=='stopped_unknown' and hpc['root_cause']=='UNKNOWN'
    assert hpc['epochs']=='2/50' and hpc['last_native_step']==3687 and hpc['exact_logger_best']==0.2810768485069275
    assert sha(ROOT/hpc['exact_full_log']['path'])==hpc['exact_full_log']['sha256']
    rows=settled_requests(code);assert rows,'No actual original APF request evidence'
    queue=u.read(ROOT/'pipeline/queue.json');target=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')==EXP]
    if status=='launched':
        assert len(rows)==4 and all(e['returncode']==0 and e['result']['execution_completed'] is True for _,_,_,e in rows)
        for k in ('review','native_peer','resources','receipt','dispatch','growth'):assert k in loaded,k
        peer=loaded['native_peer'];assert peer['status']=='FOUR_ACTUAL_APF_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED' and peer['candidate_id']==APF and peer['code_commit']==code and peer['material_concerns']==[] and peer['goal_sha256']=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
        assert {(x['execution_path'],x['execution_sha256']) for x in peer['raw_results']}=={(ref['path'],ref['sha256']) for _,_,ref,e in rows}
        review=loaded['review'];assert review['review_status']=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' and review['candidate_id']==APF and review['code_commit']==code
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
        fail=loaded['failure_execution'];assert fail['certainty']=='terminal' and fail['identity']['candidate_id']==APF and fail['identity']['code_commit']==code
        assert any(ref==binds['failure_execution'] for _,_,ref,e in rows)
        assert fail['returncode']!=0 or str((fail.get('result') or {}).get('coverage_status','')).startswith('INCONCLUSIVE')
        assert not target and not (ROOT/'pipeline/admissions/M219-APF.json').exists(),'Partial admission/claim must be reconciled, not relabeled failure'
        head=current_head();assert head in (PARENT,code)
        outcome='Actual APF attempt '+status+'; scope '+str(data.get('failure_scope','UNKNOWN'))+'; no efficacy rejection, root-cause inference or automatic retry.'
    assert current_head()==head
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();original=u.read(TICK/'protected_assets_before.json');work=u.read(ROOT/'pipeline/research_work.json')
        assert len(work['candidates'])==145 and len({c['id'] for c in work['candidates']})==145
        before=fresh_baseline(original,work,head);before['current_candidate_source_paths']=version['frozen_source_files'] if head==code else {}
        assert all(sha(ROOT/'Cluster'/n)==h for n,h in before['current_candidate_source_paths'].items())
        oldmemory=(ROOT/'pipeline/codex_memory.md').read_text('utf8');sections=section_map(oldmemory)
        by={c['id']:c for c in work['candidates']};assert by[HPC]['stage']=='complete' and by[HPC]['training_status']=='stopped_unknown'
        c=by[APF];assert c['code_commit']==code
        if status=='launched':assert c['stage']=='training'
        else:assert c['stage']=='validation'
        now=datetime.now(timezone.utc).isoformat();attempt={'recorded_at':now,'status':status,'code_commit':code,'source_parent_commit':PARENT,'evidence':list(binds.values()),'scope':outcome}
        if c.get('current_attempt_record'):c.setdefault('attempt_record_history',[]).append(copy.deepcopy(c['current_attempt_record']))
        c['current_attempt_record']=attempt
        if status=='launched':
            epoch,step=samples[-1]['max_native_step'];pid=task['pid'];start=ob['identity_after']['start_ticks']
            c.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(c.get('latest_native_training_progress'))})
            c['latest_native_training_progress']={'recorded_at':ob['observed_at'],'pid':pid,'start_ticks':start,'epoch':epoch,'step':step,'steps_per_epoch':4686,'observed_steps':samples,'evidence':binds['growth'],'scope':'Actual exact original PID/source/runtime/GPU0 growth. Validation only as explicitly observed, efficacy UNKNOWN.','precise_native_validation':copy.deepcopy(live.get('precise_native_validation','UNKNOWN_NOT_RECORDED'))}
            c['next_action']='Monitor only original admitted APF PID/log under original patience. Preserve all raw history and HPC stopped_unknown73ba; no automatic HPC restart, GPU1, blind relaunch or model tuning.'
            running_line=f'唯一已验证训练M219-APF GPU0 PID{pid}/start{start}，source/runtime{code}；根{ob["observed_at"]} TRAIN{epoch}/50 {samples[0]["max_native_step"][1]}→{step}/4686。'
        else:
            c.setdefault('native_attempt_history',[]).append(attempt)
            c['next_action']='Preserve exact current failed/inconclusive APF request and stderr/coverage; determine its implementation/runtime/coverage scope before any separately reviewed fresh action. Do not infer whole-mechanism failure, replay, resume HPC or change seed/data/precision.'
            running_line='本记录器没有APF已验证launch；当前原始诊断请求已terminal，失败/覆盖范围待有据定位，不自动重试或恢复HPC。'
        for v in binds.values():
            if v not in c.setdefault('evidence',[]):c['evidence'].append(v)
        work['updated_at']=now;work['last_event_tick']=EXPECTED['generated_at'];work['next_action']=c['next_action']
        hpc_line='HPC/M218已canonical stopped_unknown：原PID187081 absent，最后TRAIN2/50 3687/4686，仅epoch1 val exact.2810768485069275/printed.2811，archive73ba99a73d394a37a41dc431277a3543；无earlystop/exceptionmarker，原因UNKNOWN，不作正常结束/OOM/机制否定/恢复推断。'
        sections['Goal And Phase']=f'- 当前8e092010；generated{EXPECTED["generated_at"]}/deadline{EXPECTED["deadline_at"]}原值。Phase1原层级pointfeature→inst_feats→masks；目标.5100/M95 champion.5020，Phase2人工。\n- goal0441/standing2e892/GPU0auth94075/SERVERS2583；仅server4 physicalGPU0/max1，GPU1禁用；M206用户pause/resumeFalse不变。\n- seed1999/epochs50/patience10/原YAML/data/pretrain/loss/optimizer/precision/≤10G资源口径不变；禁调参/gate/语言routing/大QKV/N²attention/重复inst/旧拒绝改名。'
        sections['Active Hypotheses']='- '+hpc_line+'\n- 原HPC c94f NULL/旧2f7与6282技术准入/receipt/两TRAIN与资源记录完整保留；本次训练中断不抹去技术检查，也不证明效果。\n- APF：真实fine祖先路径joint3C→3C/GELU三split；fine直接、middle/coarse直接按fine路径私有mean，原3LN/rawskip/HCG/CSORT/单inst保留。原04993/61185 NULL母本、旧bf6父d585及静态包不改；当前实际兼容source'+code+'/父6282。\n- APF本轮实际状态：'+outcome+' 九块描述，逐call/row/bias零合法；仅整体factor原loss聚合训练性门，非新数值或Jacobian门。'
        sections['Closed Or Failed Directions']=sections['Closed Or Failed Directions']+('\n- '+hpc_line if hpc['archive_id'] not in sections['Closed Or Failed Directions'] else '')
        sections['Running And Queue']='- '+running_line+'\n- CRE30/50 exact.4961479902267456已历史正常早停；M206与旧hold/quota边界原样，不自动恢复CTS/BFC/HPC。仅GPU0 UUID958e741a，SSH keys/strict pinned dl04；无信号/删锁/盲重放。\n- 145原IDs；本记录器0新候选/0模型修订/0新native或launch，canonical queue/running/CSV/experiment/receipt一字节不改。'
        sections['Open Questions And Risks']='- HPC停止原因UNKNOWN，非完整训练效果；APF效果/泛化/新颖性及pureTRAIN峰值UNKNOWN。技术两TRAIN/资源或早期增长不等于收益。\n- 单个call/row/bias/九块零合法，缺可选边界NOT_EXERCISED；无重抽样、额外backward或新FP32数值门。历史导入问题未据后续通过宣称根因已修。'
        sections['Last Tick']='- 本轮HPC按精确原日志归档stopped_unknown，保留全部旧证据；APF实际分支'+status+'，只按哈希绑定事实记录，不预签report/postflight/finish。\n- 最终记录器仅APF研究对象与memory/notes改变，其他144（含HPC）保持；真实执行时head/index/28用户文件及原20加当前存在目标生命周期账全部保护。'
        memory='# Codex Research Memory\n\n'+'\n\n'.join('## '+title+'\n'+sections[title] for title in SECTIONS)+'\n'
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        notes={'actions':[hpc_line,'APF实际分支'+status+'：'+outcome,running_line],'decisions':['原source/null/protocol/旧负证据不改；0新候选/0模型修订，未由记录器启动/恢复任何任务。','HPC原因UNKNOWN；APF收益UNKNOWN。只实际证据可说明技术准入/launch，不借用旧PASS或推测终态。'],'evidence':{'hpc_terminal':u.ref(HPC_FINAL),'apf_status_input':u.ref(inp),'bindings':binds},'protected_lifecycle_count':len(before['protected_ledgers'])}
        assert all(u.digest(x)==before['candidate_digests'][x['id']] for x in work['candidates'] if x['id']!=APF)
        payloads=[(ROOT/'pipeline/research_work.json',encoded(work)),(ROOT/'pipeline/codex_memory.md',memory.encode('utf8')),(TICK/'report_notes.json',encoded(notes))]
        intent=TICK/'final_apf_records_intent.json';result=TICK/'final_apf_records_result.json';snap=TICK/'final_apf_records_before.json'
        assert not any(x.exists() for x in (intent,result,snap,TICK/'report_notes.json'))
        assert all(not x.with_name(x.name+'.8e092010.final.tmp').exists() for x,_ in payloads)
        protect(before);assert sha(ROOT/'pipeline/research_work.json')==before['research_work_sha256'] and sha(ROOT/'pipeline/codex_memory.md')==before['memory_sha256']
        exclusive(intent,encoded({'owner':EXPECTED,'recorded_at':now,'input':u.ref(inp),'before':before,'old_memory':oldmemory,'scope':'APF research/memory/private notes only; no source or canonical lifecycle writes; partial replay forbidden.'}))
        exclusive(snap,encoded(before))
        for dest,data_bytes in payloads:
            if dest==TICK/'report_notes.json':exclusive(dest,data_bytes)
            else:atomic(dest,data_bytes)
        protect(before);after=u.read(ROOT/'pipeline/research_work.json');assert len(after['candidates'])==145
        assert all(u.digest(x)==before['candidate_digests'][x['id']] for x in after['candidates'] if x['id']!=APF)
        exclusive(result,encoded({'owner':EXPECTED,'recorded_at':now,'actual_branch':status,'source_head_preserved':head,'changed_candidates':[APF],'other144_including_HPC_unchanged':True,'protected_lifecycle_count':len(before['protected_ledgers']),'source28_status_empty_staging_and_actual_index_preserved':True,'notes':u.ref(TICK/'report_notes.json'),'memory_lines':len(memory.splitlines()),'canonical_postflight_report_finish_performed':False}))
        print(json.dumps(u.ref(result)))
    finally:lock.close()
if __name__=='__main__':main()
