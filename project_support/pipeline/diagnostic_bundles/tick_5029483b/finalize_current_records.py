"""Record current physical progress and actual resource refusals, without model changes."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,subprocess,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
AEF='hierarchy-parent-antisymmetric-edge-flux'
CRE='hierarchy-cross-root-directed-edge-broadcast'
HPC='hierarchy-tree-resolvent-nonlinear-composition'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def digest(c):return hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,v):
    guard()
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def atomic(p,v,text=False):
    guard();tmp=Path(str(p)+'.5029483b.tmp')
    with tmp.open('x',encoding='utf8') as f:
        f.write(v if text else json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    guard();os.replace(tmp,p)
def protect(before):
    git=lambda *a:subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(ROOT/'Cluster'),*a])
    assert git('rev-parse','HEAD').decode().strip()==before['head']
    assert git('status','--porcelain=v1','--untracked-files=all','-z').hex()==before['status_hex']
    assert not git('diff','--cached','--name-only','-z')
    for n,h in before['files'].items():assert sha(ROOT/'Cluster'/n)==h,n
    for n,h in before['protected_ledgers'].items():assert sha(ROOT/'pipeline'/n)==h,n
def main():
    guard();before=read(HERE/'protected_assets_before.json');protect(before)
    livep=HERE/'aef_training_progress_observation.json'
    assert sha(livep)=='3059317cfb21c4bf15d2549fdaf9298d7b2dd4aa9925fd0e0396c4c4b3bd1df8'
    live=read(livep);assert live['owner']==EXPECTED and live['returncode']==0
    ob=live['observation'];samples=ob['samples'];assert samples[-1]['max_native_step']>samples[0]['max_native_step']
    guards={CRE:HERE/'cre_actual_current_guard.json',HPC:HERE/'hpc_actual_current_guard.json'}
    assert sha(guards[CRE])=='4f636dc5bbee3dca607cb3cc63af073c631403f7c2c6d02c5ac53dba54048afe'
    assert sha(guards[HPC])=='1112eb60f1d3461bc6a2b93461d4cabcd4e44e05458b943d11890d4de38d0a2b'
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
        ae=next(c for c in work['candidates'] if c['id']==AEF)
        cre=next(c for c in work['candidates'] if c['id']==CRE)
        hpc=next(c for c in work['candidates'] if c['id']==HPC)
        assert ae['stage']=='training' and cre['stage']==hpc['stage']=='validation'
        assert cre['code_commit']=='d58576b396cfb54577652be972f3ffaffda508c9' and hpc['code_commit']=='2f7eff19ca59cc4586e13ca81a547a18ea7e313d'
        ae.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(ae.get('latest_native_training_progress'))})
        ae['latest_native_training_progress']={'recorded_at':ob['observed_at'],'epoch':samples[-1]['max_native_step'][0],'step':samples[-1]['max_native_step'][1],'steps_per_epoch':4686,'observed_steps':samples,'precise_native_validation':live['precise_native_validation'],'evidence':ref(livep),'scope':'Partial original ongoing training only; exact original PID759301/start/cwd/eight model files/deployed YAML/runtime56/physicalGPU0 UUID+computePID. No checkpoint body read or signal.'}
        if ref(livep) not in ae['evidence']:ae['evidence'].append(ref(livep))
        for c in [cre,hpc]:
            g=read(guards[c['id']])
            c.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(c.get('resource_check')),'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check'))})
            c['resource_check']=ref(guards[c['id']])
            c['current_resource_check']={'kind':'resource_check','result':'blocked','server':'server-4','physical_gpu':0,'recorded_at':g['recorded_at'],'evidence':ref(guards[c['id']]),'hardware_evidence':ref(livep),'scope':'Actual existing reviewed adapter prepare refused locally because original AEF0 is registered; separate physical proof is independently dated. No transport, native/resources or future idle permission.'}
            for p in [guards[c['id']],livep]:
                if ref(p) not in c['evidence']:c['evidence'].append(ref(p))
        if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
        work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CRE,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_5029483b/check_cre_current_guard.py','observation':'Actual reviewed CRE adapter prepare0 refused current registered original AEF; prepare1 refused locally under GPU0-only authorization. Zero transport, active binding, manifest, lease or native/resources. Separately observed original physical GPU0 TRAIN16/50 step1646 to1655. Both existing prepared reserves wait for actual free authorized GPU0.','evidence':[ref(guards[CRE]),ref(livep)]}
        work['last_event_tick']=EXPECTED['generated_at'];work['updated_at']=now
        atomic(ROOT/'pipeline/research_work.json',work)
        for c in [ae,cre,hpc]:
            for e in c['evidence']:closure.artifact(ROOT,e)
        protect(before)
        sections={};name=None
        for line in (ROOT/'pipeline/codex_memory.md').read_text('utf8').splitlines():
            if line.startswith('## '):name=line[3:];sections[name]=[]
            elif name is not None:sections[name].append(line)
        sections['Goal And Phase'][0]='- 当前5029483b036443b895dd0b4f8853127d；actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-27T12:06:28.502058Z/deadline13:06:28.502058Z原值保持不延长。'
        sections['Active Hypotheses']=[('- 当前5029 CRE guard4f636dc5/HPC guard1112eb60：实际prepare0因原AEF registered占用拒绝，prepare1本地拒绝；0transport/active/lease/manifest/native。独立物理证据上海20:07:20确认原AEF GPU0，不把拒绝当未来空卡许可。' if s.startswith('- 当前972a CRE guard') else s) for s in sections['Active Hypotheses']]
        sections['Closed Or Failed Directions']=[s for s in sections['Closed Or Failed Directions'] if not s.startswith('- 旧10 holds')]
        sections['Closed Or Failed Directions'].append('- 旧10 holds本轮NOTdue，继续原冻结边界；前轮972a小字段/完整record digest已确认10条与既有记录相同，本轮不重读历史目标/旧授权。144既有候选仅AEF/CRE/HPC更新，其余141原字节保持。')
        sections['Running And Queue'][0]='- 唯一确认训练M216-AEF server4 GPU0原PID759301/source-runtime56；上海20:07:20 TRAIN16/50 1646→1655/4686。15次精确native validation partial best.495597243309021/no_improve2，非终态/收益结论；M95.5020/目标.5100保持。0ready；M206继续暂停。CRE/HPC已有受审源+工具，均未native准入。'
        sections['Last Tick']=[
            '- begin已执行一次canonical监控/目标检查/既有派发，无新终态或可派发就绪任务。资源仍server4 GPU0/max1，GPU1禁用，Windows调度Disabled，实际所属会话匹配。',
            '- 上海20:07:20原AEF同PID/start/cwd/source8/YAML/runtime56/GPU0 UUID+computePID复核，TRAIN16/50 1646→1655。15次native验证部分best.495597243309021/no_improve2；无checkpoint body/信号/新GPU计算。',
            '- 两既有储备CREd585/HPC2f7版本和工具保留；prepare0实际当前登记占用拒绝、prepare1本地拒绝，0transport/active/lease/manifest/native/resources。创建预算0，不重复准备或测试旧软件。',
            '- 10旧heldNOTdue，不重读旧证据/授权或更改冻结边界。无M206/BFC/M201恢复、PCE/RSTR额外修订。两储备小范围独立只读核对15声明SHA均匹配、active空、无新可行动问题，未做native。',
            '- tick_attempt=CRE真实resource_check/blocked。0新候选/模型修订/提交/同步/准入/排队/启动；主线28/status/index/16生命周期账保持。仅例行状态及资源等待，无需用户处理；随后实际report/finish核释放，不预签完成。']
        names=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick'];lines=['# Codex Research Memory','']
        for n in names:lines.extend(['## '+n]+[s for s in sections[n] if s]+[''])
        assert len(lines)<120;atomic(ROOT/'pipeline/codex_memory.md','\n'.join(lines),text=True)
        notes={'actions':[
            '上海20:07:20复核原M216-AEF同原PID/启动时刻/cwd/source8/部署YAML/runtime56/物理GPU0 UUID及computePID，TRAIN16/50步1646→1655/4686；15次原生验证partial best0.495597243309021/no_improve2。仅原训练的部分结果，无checkpoint body读取或信号。',
            '复用既有CREd585/HPC2f7受审工具，实际本轮prepare0分别因原AEF登记占用拒绝、prepare1本地拒绝；0transport/active binding/manifest/lease/native/resources，真实当前resource_check已绑定候选。独立物理证据有单独采集时间，不表示未来空卡许可。',
            '两条已有储备及creation_budget=0保持，不重复新建模型/工具或旧软件测试。独立只读小范围核对两储备15声明SHA全部匹配、active字段仍空、没有新的可行动问题；此为完整性核对，非原生通过或训练效果。10旧held本轮NOTdue，未重读旧历史目标/授权。',
            '主线56、28用户工作区文件/status/index及16生命周期账保留；0新候选/修订/提交/同步/准入/排队/启动。'],
            'decisions':[
            'AEF原训练继续，0.49560是部分最佳，不能当终态或新机制收益。M95仍0.5020，目标0.5100，差0.0080。本轮没有新的研究结论，不调参或提前终止原运行。',
            '等授权GPU0真正空闲，复核fresh owner/原deadline/资产/UUID/三锁后，优先CRE执行原native YAML两步TRAIN及同口径资源检查，通过再同轮准入/派发；HPC作为既有替代。主线变化须兼容版本实际测试，不能跨兄弟ff或重标raw。',
            '保留GPU1禁用、M206暂停、BFC专属恢复授权及其他历史失败/修订/禁用边界，不动其他项目或调度。当前无需用户动作，健康例行进展保持静默。']}
        save(HERE/'report_notes.json',notes)
        after={c['id']:digest(c) for c in work['candidates']};changed=[k for k,h in before['candidate_digests'].items() if after[k]!=h]
        assert set(changed)=={AEF,CRE,HPC} and set(after)==set(before['candidate_digests'])
        save(HERE/'protected_assets_after.json',{'recorded_at':now,'primary_HEAD':before['head'],'primary_source28_status_index_unchanged':True,'lifecycle16_unchanged':True,'candidate_count':144,'changed_candidates':changed,'other141_candidates_unchanged':True,'new_candidates':[],'model_or_native_changes':False,'native_GPU_admission_queue_launch':'NOT_RUN'})
        print(json.dumps({'AEF_progress':samples[-1]['max_native_step'],'partial_best':live['precise_native_validation']['best'],'new_candidates':0,'reserve_native_resources':'NOT_RUN','memory_lines':len(lines),'notes':ref(HERE/'report_notes.json')},ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
