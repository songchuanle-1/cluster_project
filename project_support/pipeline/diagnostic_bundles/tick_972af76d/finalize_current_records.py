"""Persist a bounded, truthful resource-wait tick; preserve all training assets."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, subprocess, sys
from anchor import ROOT, EXPECTED, guard, sha
HERE=Path(__file__).resolve().parent
AEF='hierarchy-parent-antisymmetric-edge-flux'
CRE='hierarchy-cross-root-directed-edge-broadcast'
HPC='hierarchy-tree-resolvent-nonlinear-composition'

def read(p): return json.loads(Path(p).read_text('utf8'))
def ref(p): return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def digest(c): return hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,v):
    guard()
    with Path(p).open('x',encoding='utf8') as f: json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def atomic(p,v,text=False):
    guard(); tmp=Path(str(p)+'.972af76d.tmp')
    with tmp.open('x',encoding='utf8') as f:
        f.write(v if text else json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    guard();os.replace(tmp,p)
def protect(before):
    git=lambda *a:subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
    assert git('rev-parse','HEAD').decode().strip()==before['head']
    assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==before['status_hex']
    assert not git('diff','--cached','--name-only','-z')
    assert all(sha(ROOT/'Cluster'/n)==h for n,h in before['files'].items())
    assert all(sha(ROOT/'pipeline'/n)==h for n,h in before['protected_ledgers'].items())

def main():
    guard();before=read(HERE/'protected_assets_before.json');protect(before)
    livep=HERE/'aef_training_progress_observation.json'
    assert sha(livep)=='e113257eb9daeb838d71d6790a131e2bb096f8bee975a4a717d54bfa7775a19a'
    live=read(livep); assert live['returncode']==0 and live['owner']==EXPECTED
    ob=live['observation']; samples=ob['samples'];assert samples[-1]['max_native_step']>samples[0]['max_native_step']
    guards={CRE:HERE/'cre_actual_current_guard.json',HPC:HERE/'hpc_actual_current_guard.json'}
    assert sha(guards[CRE])=='0027960367a8aaff4d7ea7138f1816c39def917d8bb7cdfcefefb2f9d6538e42'
    assert sha(guards[HPC])=='f891bb7e53f97cb74417db33f622053438c6b59321892f5bba31f17220c9dbbe'
    for p in guards.values():
        g=read(p);assert g['owner']==EXPECTED and g['transport_calls']==0 and not g['active_binding_manifest_lease_created'] and not g['native_or_resources_executed']
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    import closure
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();protect(before);work=read(ROOT/'pipeline/research_work.json')
        assert len(work['candidates'])==144 and all(digest(c)==before['candidate_digests'][c['id']] for c in work['candidates'])
        now=datetime.now(timezone.utc).isoformat()
        old_hold=work['held_boundary_review'];closure.artifact(ROOT,old_hold)
        old=read(ROOT/old_hold['path']);prior={c['id']:c for c in old['held_records']}
        held=[c for c in work['candidates'] if c['stage']=='blocked'];assert len(held)==10 and set(prior)=={c['id'] for c in held}
        records=[]
        for c in held:
            h=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
            assert h==prior[c['id']]['current_record_sha256'],c['id']
            records.append({'id':c['id'],'stage':c['stage'],'blocker_kind':c.get('blocker_kind'),'failure_scope':c.get('failure_scope'),'current_record_sha256':h,'same_entire_canonical_record_as_prior':True,'decision':'UNCHANGED_HOLD_NOT_REOPENED'})
        save(HERE/'held_boundary_check.json',{'recorded_at':now,'owner':EXPECTED,'status':'BOUNDED_TEN_UNCHANGED_HOLD_METADATA_COMPARISON','baseline':old_hold,'held_records':records,'goal_sha256':sha(ROOT/'pipeline/goal.json'),'SERVERS_sha256':sha(ROOT/'SERVERS.yaml'),'new_human_authorization':False,'historical_evidence_targets_read':False,'native_or_recovery_execution':False,'scope':'Ten complete record digests unchanged; current owner goal/mainline/resource constraints retain existing scope, pause, revision and numeric-control holds. No new scientific conclusion or reopen permission.'})
        ae=next(c for c in work['candidates'] if c['id']==AEF)
        cre=next(c for c in work['candidates'] if c['id']==CRE)
        hpc=next(c for c in work['candidates'] if c['id']==HPC)
        assert ae['stage']=='training' and cre['stage']==hpc['stage']=='validation'
        assert cre['code_commit']=='d58576b396cfb54577652be972f3ffaffda508c9' and hpc['code_commit']=='2f7eff19ca59cc4586e13ca81a547a18ea7e313d'
        ae.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(ae.get('latest_native_training_progress'))})
        ae['latest_native_training_progress']={'recorded_at':ob['observed_at'],'epoch':samples[-1]['max_native_step'][0],'step':samples[-1]['max_native_step'][1],'steps_per_epoch':4686,'observed_steps':samples,'precise_native_validation':live['precise_native_validation'],'evidence':ref(livep),'scope':'Partial original ongoing training only; same PID759301/runtime-source56/eight model files/deployed YAML/GPU0 UUID and compute PID. No checkpoint read or signal.'}
        if ref(livep) not in ae['evidence']:ae['evidence'].append(ref(livep))
        for c in [cre,hpc]:
            g=read(guards[c['id']])
            c.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(c.get('resource_check')),'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check'))})
            c['resource_check']=ref(guards[c['id']])
            c['current_resource_check']={'kind':'resource_check','result':'blocked','server':'server-4','physical_gpu':0,'recorded_at':g['recorded_at'],'evidence':ref(guards[c['id']]),'hardware_evidence':ref(livep),'scope':'Actual current reviewed adapter prepare refused registered original AEF0 before transport; physical readback has its own timestamp. Zero native/resource computation or future idle permission.'}
            for p in [guards[c['id']],livep]:
                if ref(p) not in c['evidence']:c['evidence'].append(ref(p))
        work.setdefault('held_boundary_review_history',[]).append(copy.deepcopy(old_hold))
        work['held_boundary_review']=ref(HERE/'held_boundary_check.json')
        if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
        work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CRE,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_972af76d/check_cre_current_guard.py','observation':'Actual existing reviewed CRE adapter prepare0 refused because original AEF is registered running; prepare1 refused locally under current GPU0-only authorization. No transport, active binding, manifest, lease or native/resources. Separate exact original process/log/source/NVML0 proof shows real TRAIN12/50 step1137 to1145. Two already prepared reserves remain waiting for authorized free GPU0.','evidence':[ref(guards[CRE]),ref(livep)]}
        work['last_event_tick']=EXPECTED['generated_at'];work['updated_at']=now
        atomic(ROOT/'pipeline/research_work.json',work)
        for c in [ae,cre,hpc]:
            for e in c['evidence']:closure.artifact(ROOT,e)
        protect(before)
        sections={};name=None
        for line in (ROOT/'pipeline/codex_memory.md').read_text('utf8').splitlines():
            if line.startswith('## '): name=line[3:];sections[name]=[]
            elif name is not None: sections[name].append(line)
        sections['Goal And Phase'][0]='- 当前972af76d45f74f6bb62167ad9a902616；actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-27T10:06:40.840335Z/deadline11:06:40.840335Z原值保持不延长。'
        active=[]
        for s in sections['Active Hypotheses']:
            if s.startswith('- 当前CRE实际guard '):
                s='- 当前972a CRE guard00279603/HPC guardf891bb7e：实际prepare0因原AEF registered占用拒绝，prepare1本地拒绝；0transport/active/lease/manifest/native。独立物理证据上海18:07:33确认原AEF GPU0，不把拒绝当未来空卡许可。'
            s=s.replace('本轮实际隔离source2f7','既有实际隔离source2f7').replace('当前guard92f1d0d5','既有guard92f1d0d5')
            active.append(s)
        sections['Active Hypotheses']=active
        sections['Closed Or Failed Directions']=[s for s in sections['Closed Or Failed Directions'] if not s.startswith('- 旧10 holds')]
        sections['Closed Or Failed Directions'].append('- 旧10 holds本轮到期做小字段及完整record digest复查，10条与7e492595原记录全部相同，不读855历史目标、不重开、不加授权或改候选。144既有候选仅AEF/CRE/HPC新物理/资源证据，其他141保持。')
        sections['Running And Queue'][0]='- 唯一确认训练M216-AEF server4 GPU0原PID759301/source-runtime56；上海18:07:33 TRAIN12/50 1137→1145/4686。11次精确native validation partial best.48705002665519714/no_improve1，非终态/收益结论；M95.5020/目标.5100保持。0ready；M206继续暂停。CRE/HPC已有受审源+静态工具，均未native准入。'
        sections['Last Tick']=[
            '- begin已执行一次canonical监控/目标检查/既有派发；无新终态、无可派发现成任务。仅GPU0/max1，Windows调度Disabled，actual/target一致。',
            '- 原AEF同PID/start/cwd/source8/YAML/runtime56/physical0 UUID+computePID复核，上海18:07:33 TRAIN12/50 1137→1145，11次验证部分best.48705002665519714/no_improve1。只读自己的日志/进程/NVML0，无checkpoint body/信号/新计算。',
            '- 复用CREd585与HPC2f7既有受审工具，实际prepare0当前登记占用拒绝、prepare1本地拒绝，均0transport/active/manifest/lease/native。保留两储备/0创建预算，不复制新准备、重复旧软件测试或改模型。',
            '- 10旧held完整record digest与7e原值相同，小字段独立复核为同scope/human/numeric holds；不展开历史证据/旧授权，不恢复M206/BFC/M201，不追加PCE/RSTR修订。',
            '- tick_attempt=CRE真实resource_check/blocked。0新候选/模型修订/源码提交/同步/准入/入队/启动；主线28/status/index/16生命周期账保留。仅例行状态与资源等待，无新研究结论，无需用户动作；root接着report/finish核释放，不预签完成。']
        names=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick']
        lines=['# Codex Research Memory','']
        for n in names:lines.extend(['## '+n]+[s for s in sections[n] if s]+[''])
        assert len(lines)<120;atomic(ROOT/'pipeline/codex_memory.md','\n'.join(lines),text=True)
        notes={'actions':[
            '上海18:07:33复核原M216-AEF：同原PID/启动时刻/cwd/source8/deployed YAML/runtime56及物理GPU0 UUID、computePID，TRAIN12/50步1137→1145/4686。11次native验证partial best0.48705002665519714/no_improve1；无checkpoint读取、信号或额外GPU计算。',
            '复用CREd585/HPC2f7受审源与现有工具，实际本轮prepare0分别因原AEF登记占用拒绝，prepare1本地拒绝；0transport/active binding/manifest/lease/native/resources。真实当前资源尝试已绑定候选；拒绝不是原生通过或未来空卡许可。',
            '两条储备均已准备且本轮creation_budget=0，不重复造工具/重跑旧软件用例/增加模型。10旧held到期复查，小字段及完整record digest仍与既有7e记录相同；未读其历史证据目标或旧授权，原失败/恢复及修订边界保持。',
            '当前主线56、28用户工作区文件/status/index及16生命周期账完整保持；本轮0新候选、0模型修订、0提交/同步/准入/排队/启动。'],
            'decisions':[
            'AEF仍在正常原训练中，当前0.48705仅部分最佳。M95仍0.5020，目标0.5100，差0.0080；本轮没有新研究结论或训练终态，不调参、不提前停原任务。',
            '保留现有CRE优先及HPC替代：待GPU0真正空闲，fresh owner/原deadline/资产/UUID/三锁全部通过后执行原生两步TRAIN及同口径资源测试，通过再同轮准入/派发。主线改变须兼容包装实际测试，不跨兄弟ff或重标旧结果。',
            '遵守最新不用GPU1；M206用户暂停、BFC专属恢复授权、M201禁自动恢复、PCE/RSTR已用修订预算与其他禁用项不变。不改其他项目或调度。无需用户处理，例行健康进展保持静默。']}
        save(HERE/'report_notes.json',notes)
        after={c['id']:digest(c) for c in work['candidates']}
        changed=[k for k,h in before['candidate_digests'].items() if after[k]!=h]
        assert set(changed)=={AEF,CRE,HPC} and set(after)==set(before['candidate_digests'])
        save(HERE/'protected_assets_after.json',{'recorded_at':now,'primary_HEAD':before['head'],'primary_source28_status_index_unchanged':True,'lifecycle16_unchanged':True,'candidate_count':144,'new_candidates':[],'changed_candidates':changed,'other141_candidates_unchanged':True,'model_or_native_changes':False,'native_GPU_admission_queue_launch':'NOT_RUN'})
        print(json.dumps({'AEF_progress':samples[-1]['max_native_step'],'partial_best':live['precise_native_validation']['best'],'reserves':'CRE/HPC unchanged source; native/resources NOT_RUN','new_candidates':0,'held10_unchanged':True,'memory_lines':len(lines),'notes':ref(HERE/'report_notes.json')},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
