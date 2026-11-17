"""Record a routine current resource refusal and original training observation."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
def main():
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b);u.lifecycle_protection(b)
    live=u.read(HERE/'cre_training_progress_observation.json');ob=live['observation'];samples=ob['samples']
    assert live['owner']==EXPECTED and live['returncode']==0 and ob['identity_after']['pid']==118189 and ob['runtime_commit']==u.SOURCE
    assert samples[-1]['max_native_step']>samples[0]['max_native_step']
    epoch,step=samples[-1]['max_native_step'];best=live['precise_native_validation']['best']
    observed=datetime.fromisoformat(ob['observed_at']);shanghai=observed.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    results=u.read(HERE/'current_resource_guard_result.json');assert results['owner']==EXPECTED and results['transport_calls']==0
    assert {r['candidate_id'] for r in results['results']}=={u.HPC,u.APF}
    held=u.read(HERE/'held_boundary_observation.json');assert held['owner']==EXPECTED and held['unchanged'] is True
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import closure
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b);u.lifecycle_protection(b)
        work=u.read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==145
        assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'])
        now=datetime.now(timezone.utc).isoformat();live_ref=u.ref(HERE/'cre_training_progress_observation.json')
        cre=next(c for c in work['candidates'] if c['id']==u.CRE);assert cre['stage']=='training' and cre['code_commit']==u.SOURCE
        cre.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(cre['latest_native_training_progress'])})
        cre['latest_native_training_progress']={'recorded_at':ob['observed_at'],'pid':118189,'epoch':epoch,'step':step,
            'steps_per_epoch':4686,'observed_steps':samples,'precise_native_validation':live['precise_native_validation'],
            'evidence':live_ref,'scope':'Original source8/YAML/runtime/startPID/cwd/physicalGPU0 UUID and increasing native TRAIN; healthy ongoing training, not final efficacy.'}
        cre['current_resource_check'].update(recorded_at=ob['observed_at'],evidence=live_ref)
        if live_ref not in cre['evidence']:cre['evidence'].append(live_ref)
        for row in results['results']:
            c=next(c for c in work['candidates'] if c['id']==row['candidate_id']);assert c['stage']=='validation'
            check=u.read(ROOT/row['guard']['path']);assert check['owner']==EXPECTED and check['transport_calls']==0
            assert check['actual_call']['result']=='refused' and check['native_or_resources_executed'] is False
            c.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(c.get('resource_check')),
                'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check'))})
            c['resource_check']=row['guard'];c['current_resource_check']={'recorded_at':ob['observed_at'],'kind':'resource_check','result':'blocked',
                'server':'server-4','physical_gpu':0,'evidence':row['guard'],'hardware_evidence':live_ref,
                'scope':'Actual reviewed prepare(0) refused original registered CRE before transport; separately dated physical0 original training growth. Existing source/tool packets unchanged, candidate TRAIN2/resources NOT_RUN, no future idle authorization.'}
            for entry in (row['guard'],live_ref):
                if entry not in c['evidence']:c['evidence'].append(entry)
        if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
        hpc_guard=next(r['guard'] for r in results['results'] if r['candidate_id']==u.HPC)
        work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':u.HPC,'kind':'resource_check','result':'blocked',
            'command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_66c96d43/check_current_resource_guards.py',
            'observation':'Actual existing reviewed HPC6282 prepare(0) refused current registered CRE GPU0 locally, zero transport/active/native work. Exact original CRE118189/runtime d585/source8/YAML/physical0 steps increased. APF own prepare(0) independently refused too. No new software preparation, model revision, candidate or scientific result.',
            'evidence':[hpc_guard,live_ref]}
        hpc=next(c for c in work['candidates'] if c['id']==u.HPC)
        for entry in work['tick_attempt']['evidence']:assert entry in hpc['evidence'];closure.artifact(ROOT,entry)
        if work.get('held_boundary_review'):work.setdefault('held_boundary_review_history',[]).append(copy.deepcopy(work['held_boundary_review']))
        work['held_boundary_review']=u.ref(HERE/'held_boundary_observation.json');work['updated_at']=now;work['last_event_tick']=EXPECTED['generated_at']
        work['next_action']='Continue exact original CRE118189/source-runtime d585 on sole authorized server4GPU0. HPC6282/APFbf6 unchanged reviewed static packets wait for genuinely idle GPU0, fresh actual owner/deadline/current compatible parent/assets/UUID/three locks, then native pairedTRAIN2/resources. No GPU1, new model preparation, reopen or protected recovery needed while reserve full.'
        assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in {u.CRE,u.HPC,u.APF})
        memory=(ROOT/'pipeline/codex_memory.md').read_text('utf8')
        start=memory.index('- 当前');end=memory.index('\n',start)
        memory=memory[:start]+f'- 当前{EXPECTED["token"]}；actual/target {EXPECTED["thread_id"]}一致；generated{EXPECTED["generated_at"]}/deadline{EXPECTED["deadline_at"]}原值不延长。'+memory[end:]
        lines=memory.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('- 上海') and '原CRE TRAIN' in line:
                lines[i]=f'- 上海{shanghai}原CRE TRAIN{epoch}/50 {samples[0]["max_native_step"][1]}→{step}/4686；{len(live["precise_native_validation"]["values"])}次原生验证best={best}，训练尚未完成、无最终收益结论。当前proof tick_66c96d43/cre_training_progress_observation.json。'
            if line.startswith('- 当前唯一M217-CRE'):
                lines[i]=f'- 当前唯一M217-CRE server4 GPU0原PID118189/runtime d585；上海{shanghai} TRAIN{epoch}/50 step{step}/4686/native best{best}。0ready/0claiming；waiting M206用户暂停不可派发。储备HPC6282/APFbf6两条，原生检查待空槽，尚非训练队列。'
            if line.startswith('- HPC原c94f'):lines[i]=line.replace('本轮9文件','fd073f88轮9文件')
            if line.startswith('- HPC本轮兼容'):lines[i]=line.replace('HPC本轮兼容','HPC既有兼容')
            if line.startswith('- APF source '):lines[i]=line.replace('上轮35软件核','01b轮35软件核').replace('本轮新native','fd073f88轮native')
        memory='\n'.join(lines)+'\n';memory=memory[:memory.index('## Last Tick')]+f'''## Last Tick
- canonical begin一次进展/派发/目标检查；无新终态/运维问题，snapshot reserve2/creation0，不新造模型或重测旧软件套件。
- 原CRE PID118189/source8/YAML/runtime d585/GPU0真步数{samples[0]['max_native_step'][1]}→{step}，TRAIN{epoch}/50，原生best{best}，仍健康训练中；未超过champion或达目标。
- 原HPC/APF reviewed prepare(0)各实际因CRE登记占用在transport前拒绝；0transport/0active/0native，既有两静态包/各源码保持不变。最新physical证据另有时间，不是未来空卡许可。
- 10旧held本轮只比小record digest和相关冻包hash，未读旧grants/ckpt/855目标；全部不变，无人类待处理事项。145仅CRE/HPC/APF观察metadata更新，142其他保持。
- 本轮仅例行运行/资源等待核查，无新准备/准入/启动或科研结论；六段report notes留档，随后canonical finish核FINALIZED/contextcommitted/released，不预签收尾结果。正常进度不通知。
'''
        assert len(memory.splitlines())<120 and sum(line.startswith('## ') for line in memory.splitlines())==7
        notes={'actions':[
            f'上海{shanghai}精确核验原M217-CRE PID118189/start/cwd/source8/YAML/runtime d585和physicalGPU0 UUID+computePID；TRAIN{epoch}/50 {samples[0]["max_native_step"][1]}→{step}/4686，{len(live["precise_native_validation"]["values"])}次原生验证best={best}。当前健康继续，尚无最终结果。',
            '复用原HPC6282/APFbf6的既有审查包，各实际prepare(0)均因原CRE登记占用在transport前拒绝；0连接/0active material/0native命令，不重复42/46或HPC软件检查，不新增源版本或模型。',
            '10旧held仅有限record digest/相关冻结包哈希复核均不变；未读取旧grant/检查点或历史大量目标，不重开/恢复/新增审批。',
            '原145候选集合/主线d585/28用户文件/status/index/空暂存/18生命周期账本保持；仅CRE/HPC/APF观察metadata和本轮resource_check实测留档，无新增候选/修订/准入/启动。'],
            'decisions':['资源仍被原训练占用，现有两项储备已满，无本轮新准备或可执行GPU检查；继续等待合法空GPU0，GPU1保持不用。',
                '运行正常、无新终态/故障/目标突破/用户动作，按心跳通知规则保持静默；训练中早期mIoU不代表最终有效性。']}
        json.dumps(work,ensure_ascii=False,allow_nan=False);json.dumps(notes,ensure_ascii=False,allow_nan=False);memory.encode('utf8')
        intent={'owner':EXPECTED,'recorded_at':now,'before_work_sha256':sha(ROOT/'pipeline/research_work.json'),
            'program':u.ref(__file__),'live':live_ref,'guards':u.ref(HERE/'current_resource_guard_result.json'),
            'held':u.ref(HERE/'held_boundary_observation.json'),'scope':'Current bounded routine observation only; no source/training/queue/receipt or protected hold mutation.'}
        guard()
        with (HERE/'observation_record_intent.json').open('x',encoding='utf8') as f:
            json.dump(intent,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        u.atomic(ROOT/'pipeline/research_work.json',work);u.atomic(ROOT/'pipeline/codex_memory.md',memory,text=True)
        u.save(HERE/'report_notes.json',notes)
        u.primary_protection(b);u.lifecycle_protection(b)
        changed=[c['id'] for c in work['candidates'] if u.digest(c)!=b['candidate_digests'][c['id']]];assert set(changed)=={u.CRE,u.HPC,u.APF}
        u.save(HERE/'protected_assets_after.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
            'changed_existing_candidates':changed,'candidate_count':145,'other_142_unchanged':True,
            'primary_head':u.SOURCE,'primary_index_source28_status_empty_staging_and_18_lifecycle_unchanged':True,
            'new_candidates':0,'new_model_revisions':0,'new_native_commands':0,'new_admissions_or_launches':0,
            'memory_lines':len(memory.splitlines()),'current_training':live_ref,'report_notes':u.ref(HERE/'report_notes.json'),
            'notification_decision':'DONT_NOTIFY','finish_status':'NOT_YET_CALLED'})
        print(json.dumps({'epoch':epoch,'step':step,'native_best':best,'new_preparations':0,'new_launches':0,'notification':'DONT_NOTIFY','notes':u.ref(HERE/'report_notes.json')},ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
