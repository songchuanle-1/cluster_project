"""Bounded progress/resource observation; reuse guarded persistence utilities only."""
from pathlib import Path
from datetime import datetime,timezone
import copy,importlib.util,json,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
prior=ROOT/'pipeline/diagnostic_bundles/tick_5029483b/finalize_current_records.py'
spec=importlib.util.spec_from_file_location('prior_guarded_persistence_utilities',prior)
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
AEF=u.AEF;CRE=u.CRE;HPC=u.HPC
def main():
    guard();before=u.read(HERE/'protected_assets_before.json');u.protect(before)
    livep=HERE/'aef_training_progress_observation.json';assert sha(livep)=='a821e8856957d05f886db8a35967835758d28c851773f6bcd032d716be773057'
    live=u.read(livep);assert live['owner']==EXPECTED and live['returncode']==0
    ob=live['observation'];samples=ob['samples'];assert samples[-1]['max_native_step']>samples[0]['max_native_step']
    guards={CRE:HERE/'cre_actual_current_guard.json',HPC:HERE/'hpc_actual_current_guard.json'}
    assert sha(guards[CRE])=='6ac7acb83ba16867f9273d6345a7df57be9abdd2b980e756464d40f41e24d7e4'
    assert sha(guards[HPC])=='8034624f3cb0aed05dd6c30207b773c4f200f6a029da52afb0f4330730d5e20e'
    for p in guards.values():
        g=u.read(p);assert g['owner']==EXPECTED and g['transport_calls']==0 and not g['active_binding_manifest_lease_created'] and not g['native_or_resources_executed']
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    import closure
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.protect(before);work=u.read(ROOT/'pipeline/research_work.json')
        assert len(work['candidates'])==144 and all(u.digest(c)==before['candidate_digests'][c['id']] for c in work['candidates'])
        now=datetime.now(timezone.utc).isoformat()
        old_hold=copy.deepcopy(work['held_boundary_review']);closure.artifact(ROOT,old_hold)
        old=u.read(ROOT/old_hold['path']);previous={c['id']:c for c in old['held_records']}
        held=[c for c in work['candidates'] if c['stage']=='blocked'];assert len(held)==10 and set(previous)=={c['id'] for c in held}
        import hashlib
        records=[]
        for c in held:
            h=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
            assert h==previous[c['id']]['current_record_sha256'],c['id']
            records.append({'id':c['id'],'stage':c['stage'],'blocker_kind':c.get('blocker_kind'),'failure_scope':c.get('failure_scope'),'current_record_sha256':h,'same_entire_canonical_record_as_prior':True,'decision':'UNCHANGED_HOLD_NOT_REOPENED'})
        u.save(HERE/'held_boundary_check.json',{'recorded_at':now,'owner':EXPECTED,'status':'BOUNDED_TEN_UNCHANGED_HOLD_METADATA_COMPARISON','baseline':old_hold,'held_records':records,'goal_sha256':sha(ROOT/'pipeline/goal.json'),'SERVERS_sha256':sha(ROOT/'SERVERS.yaml'),'new_human_authorization':False,'historical_evidence_targets_read':False,'native_or_recovery_execution':False,'scope':'Due metadata and record-digest comparison only. Original scope/pause/numeric/revision and recovery restrictions retained; no new executable permission.'})
        ae=next(c for c in work['candidates'] if c['id']==AEF);cre=next(c for c in work['candidates'] if c['id']==CRE);hpc=next(c for c in work['candidates'] if c['id']==HPC)
        assert ae['stage']=='training' and cre['stage']==hpc['stage']=='validation'
        assert cre['code_commit']=='d58576b396cfb54577652be972f3ffaffda508c9' and hpc['code_commit']=='2f7eff19ca59cc4586e13ca81a547a18ea7e313d'
        ae.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(ae.get('latest_native_training_progress'))})
        ae['latest_native_training_progress']={'recorded_at':ob['observed_at'],'epoch':samples[-1]['max_native_step'][0],'step':samples[-1]['max_native_step'][1],'steps_per_epoch':4686,'observed_steps':samples,'precise_native_validation':live['precise_native_validation'],'evidence':u.ref(livep),'scope':'Original ongoing partial training only; same PID759301/start/cwd/source8/deployed YAML/runtime56/GPU0 UUID and compute PID. No checkpoint body or signal.'}
        if u.ref(livep) not in ae['evidence']:ae['evidence'].append(u.ref(livep))
        for c in [cre,hpc]:
            g=u.read(guards[c['id']]);c.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(c.get('resource_check')),'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check'))})
            c['resource_check']=u.ref(guards[c['id']]);c['current_resource_check']={'kind':'resource_check','result':'blocked','server':'server-4','physical_gpu':0,'recorded_at':g['recorded_at'],'evidence':u.ref(guards[c['id']]),'hardware_evidence':u.ref(livep),'scope':'Actual current reviewed adapter prepare refused local registered AEF0; separate physical proof has its own timestamp. Zero transport/native/resources; no future idle permission.'}
            for p in [guards[c['id']],livep]:
                if u.ref(p) not in c['evidence']:c['evidence'].append(u.ref(p))
        work.setdefault('held_boundary_review_history',[]).append(old_hold);work['held_boundary_review']=u.ref(HERE/'held_boundary_check.json')
        if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
        work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CRE,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_c7a49040/check_cre_current_guard.py','observation':'Actual existing CRE adapter prepare0 refused original AEF registered occupation; prepare1 refused locally. Zero transport/active/manifest/lease/native/resources. Separate exact original GPU0 TRAIN20/50 step2530 to2538 proves original ongoing physical occupation. Both existing reserves wait for authorized free GPU0.','evidence':[u.ref(guards[CRE]),u.ref(livep)]}
        work['last_event_tick']=EXPECTED['generated_at'];work['updated_at']=now;u.atomic(ROOT/'pipeline/research_work.json',work)
        for c in [ae,cre,hpc]:
            for e in c['evidence']:closure.artifact(ROOT,e)
        u.protect(before)
        sections={};name=None
        for line in (ROOT/'pipeline/codex_memory.md').read_text('utf8').splitlines():
            if line.startswith('## '):name=line[3:];sections[name]=[]
            elif name is not None:sections[name].append(line)
        sections['Goal And Phase'][0]='- 当前c7a49040d08340c5bad8fa59e7dd5594；actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-27T14:07:30.656174Z/deadline15:07:30.656174Z原值保持不延长。'
        sections['Active Hypotheses']=[('- 当前c7a4 CRE guard6ac7acb8/HPC guard8034624f：实际prepare0因原AEF registered占用拒绝，prepare1本地拒绝；0transport/active/lease/manifest/native。独立物理证据上海22:08:08确认原AEF GPU0，不把拒绝当未来空卡许可。' if s.startswith('- 当前5029 CRE guard') else s) for s in sections['Active Hypotheses']]
        sections['Closed Or Failed Directions']=[s for s in sections['Closed Or Failed Directions'] if not s.startswith('- 旧10 holds')]
        sections['Closed Or Failed Directions'].append('- 旧10 holds本轮due，小字段及完整record digest与前972a记录全部相同，保留原scope/暂停/数值/修订/恢复授权边界，不读855历史证据目标或旧授权正文。144既有候选仅AEF/CRE/HPC更新，其他141保持。')
        sections['Running And Queue'][0]='- 唯一确认训练M216-AEF server4 GPU0原PID759301/source-runtime56；上海22:08:08 TRAIN20/50 2530→2538/4686。19次精确native validation partial best.495597243309021/no_improve6，非终态/收益结论；M95.5020/目标.5100保持。0ready；M206继续暂停。CRE/HPC均有受审源/工具，仍未native准入。'
        sections['Last Tick']=[
            '- begin一次canonical监控/目标检查/既有派发，无新终态、无可派发就绪项；actual/target一致，Windows调度Disabled，仍仅server4 GPU0/max1。',
            '- 上海22:08:08原AEF同PID/start/cwd/source8/YAML/runtime56/物理0 UUID+computePID，TRAIN20/50 2530→2538；19次native验证部分best.495597243309021/no_improve6。无checkpoint body/信号/额外GPU计算，原训练继续。',
            '- 复用CREd585/HPC2f7既有工具，prepare0实际登记占用拒绝/prepare1本地拒绝；0transport/active/manifest/lease/native/resources。两现成储备已满、creation0，未造新包或重复旧软件测试。',
            '- due10旧held小字段与完整record digest相同；独立只读核对原边界，无新许可/用户动作。不恢复M206/BFC/M201，不增加PCE/RSTR修订，不展开旧历史目标/授权/checkpoint。',
            '- tick_attempt=CRE真实resource_check/blocked；0新候选/修订/提交/同步/准入/入队/启动，主线28/status/index/16账保持。只有例行进度/资源等待，无新研究结论；随后实际report/finish核释放，不预签完成。']
        names=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick'];lines=['# Codex Research Memory','']
        for n in names:lines.extend(['## '+n]+[s for s in sections[n] if s]+[''])
        assert len(lines)<120;u.atomic(ROOT/'pipeline/codex_memory.md','\n'.join(lines),text=True)
        notes={'actions':['上海22:08:08原M216-AEF同原PID/启动时刻/cwd/source8/部署YAML/runtime56及physicalGPU0 UUID+computePID复核，TRAIN20/50步2530→2538/4686。19次native验证partial best0.495597243309021/no_improve6。无checkpoint body读取、信号或额外GPU计算。','本轮实际调用既有CREd585/HPC2f7 adapter.prepare：GPU0因原AEF登记占用拒绝、GPU1在本地拒绝；均0transport/active binding/manifest/lease/native/resources。当前resource_check已绑定候选，独立物理证据采集时间明确，不是原生PASS或未来空卡许可。','10旧held到期小字段与完整record digest复核均与既有972a冻结记录相同，保持原scope/暂停/数值/修订/恢复授权边界；未读855历史目标或旧授权正文，不重复旧实验。','两已有储备/creation_budget0保持；主线56、28用户文件/status/index及16生命周期账完整保持。本轮0新候选/修订/提交/同步/准入/入队/启动。'],
               'decisions':['AEF仍是原正常训练，0.49560仅部分最佳，no_improve6未到当前10次早停线；本轮没有终态或新机制收益结论，不调参或提前停原任务。M95仍0.5020，目标0.5100，差0.0080。','GPU0真正空闲后，fresh owner/原deadline/资产/UUID/三锁通过，先执行现有CRE原生YAML两步TRAIN与同口径资源检查，通过后同轮准入/派发；HPC保留替代。任何主线变化须兼容包装并真测，不跨兄弟ff或重标raw。','继续禁用GPU1，M206暂停及BFC/M201恢复限制、PCE/RSTR预算与其他禁用项不变。不动其他项目、运行任务或调度。当前无用户动作，仅健康进展与资源等待，保持静默。']}
        u.save(HERE/'report_notes.json',notes)
        after={c['id']:u.digest(c) for c in work['candidates']};changed=[k for k,h in before['candidate_digests'].items() if after[k]!=h]
        assert set(changed)=={AEF,CRE,HPC} and set(after)==set(before['candidate_digests'])
        u.save(HERE/'protected_assets_after.json',{'recorded_at':now,'primary_HEAD':before['head'],'primary_source28_status_index_unchanged':True,'lifecycle16_unchanged':True,'candidate_count':144,'changed_candidates':changed,'other141_candidates_unchanged':True,'new_candidates':[],'native_GPU_admission_queue_launch':'NOT_RUN','model_or_native_changes':False})
        print(json.dumps({'AEF_progress':samples[-1]['max_native_step'],'partial_best':live['precise_native_validation']['best'],'no_improve':live['precise_native_validation']['no_improve'],'held10_unchanged':True,'reserve_native_resources':'NOT_RUN','memory_lines':len(lines),'notes':u.ref(HERE/'report_notes.json')},ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
