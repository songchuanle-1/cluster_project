"""Persist current observations and reviewed software preparation, never launch."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import copy,json,os,sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
def main():
    guard();b=u.read(HERE/'protected_assets_before.json');u.primary_protection(b);u.lifecycle_protection(b)
    registered=u.read(HERE/'preparation_registration_result.json');assert registered['owner']==EXPECTED
    assert set(registered['changed_existing_candidates'])=={u.HPC,u.APF}
    resource=u.read(HERE/'current_resource_guard_result.json');assert resource['owner']==EXPECTED and resource['transport_calls']==0
    assert {r['candidate_id'] for r in resource['results']}=={u.HPC,u.APF}
    live_path=HERE/'cre_training_progress_observation_final.json';live=u.read(live_path)
    assert live['owner']==EXPECTED and live['returncode']==0
    ob=live['observation'];samples=ob['samples'];assert samples[-1]['max_native_step']>samples[0]['max_native_step']
    assert ob['identity_before']['pid']==ob['identity_after']['pid']==118189 and ob['runtime_commit']==u.SOURCE
    epoch,step=samples[-1]['max_native_step'];best=live['precise_native_validation']['best']
    observed=datetime.fromisoformat(ob['observed_at']);assert (datetime.now(timezone.utc)-observed).total_seconds()<240
    shanghai=observed.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    catalogue=u.read(HERE/'packet_catalogue.json');assert catalogue['owner']==EXPECTED
    by_id={entry['id']:entry for entry in catalogue['candidates']}
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import closure
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();u.primary_protection(b);u.lifecycle_protection(b)
        work=u.read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==145
        assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in {u.HPC,u.APF})
        now=datetime.now(timezone.utc).isoformat()
        cre=next(c for c in work['candidates'] if c['id']==u.CRE);assert cre['stage']=='training' and cre['code_commit']==u.SOURCE
        cre.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(cre.get('latest_native_training_progress'))})
        cre['latest_native_training_progress']={
            'recorded_at':ob['observed_at'],'pid':118189,'epoch':epoch,'step':step,'steps_per_epoch':4686,
            'observed_steps':samples,'precise_native_validation':live['precise_native_validation'],
            'evidence':u.ref(live_path),'scope':'Exact original PID/start/cwd/source8/YAML/runtime d585/physicalGPU0 UUID+computePID. Native steps increased; early validation only, training incomplete.'}
        cre['current_resource_check']={'recorded_at':ob['observed_at'],'kind':'original_training_occupation',
            'result':'running_original_verified_training','physical_gpu':0,'evidence':u.ref(live_path),
            'scope':'Current original admitted CRE continues; no resource benchmark repeated.'}
        if u.ref(live_path) not in cre['evidence']:cre['evidence'].append(u.ref(live_path))
        for row in resource['results']:
            c=next(c for c in work['candidates'] if c['id']==row['candidate_id'])
            assert c['stage']=='validation' and c['code_commit']==by_id[c['id']]['code_commit']
            u.check_refs([row['guard']]);check=u.read(ROOT/row['guard']['path'])
            assert check['owner']==EXPECTED and check['transport_calls']==0 and check['native_or_resources_executed'] is False
            c.setdefault('resource_check_history',[]).append({'recorded_at':now,
                'prior_resource_check':copy.deepcopy(c.get('resource_check')),'prior_current_resource_check':copy.deepcopy(c.get('current_resource_check'))})
            c['resource_check']=row['guard']
            c['current_resource_check']={'recorded_at':ob['observed_at'],'kind':'resource_check','result':'blocked',
                'server':'server-4','physical_gpu':0,'evidence':row['guard'],'hardware_evidence':u.ref(live_path),
                'scope':'Actual current reviewed prepare(0) refused registered original CRE before transport; separately fresh exact physical0 occupation/progress verified. Native/resource benchmark NOT_RUN, no future idle permission.'}
            for item in [row['guard'],u.ref(live_path)]:
                if item not in c['evidence']:c['evidence'].append(item)
        if work.get('tick_attempt'):work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
        hpc_guard=next(row['guard'] for row in resource['results'] if row['candidate_id']==u.HPC)
        work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':u.HPC,
            'kind':'resource_check','result':'blocked',
            'command':'python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_fd073f88/check_current_resource_guards.py',
            'observation':'Actual current reviewed compatible HPC prepare(0) reached current owner/source/version/catalogue guards and refused registered original M217-CRE occupation locally, zero transport/active material/native commands. Exact original PID118189, runtime/source d585 and physicalGPU0 native progress independently observed. HPC same9 compatible source and HPC/APF static tool checks passed; actual candidate TRAIN2/resources remain NOT_RUN.',
            'evidence':[hpc_guard,u.ref(live_path)]}
        hpc=next(c for c in work['candidates'] if c['id']==u.HPC)
        for e in work['tick_attempt']['evidence']:assert e in hpc['evidence'];closure.artifact(ROOT,e)
        work['updated_at']=now;work['last_event_tick']=EXPECTED['generated_at']
        work['next_action']='Continue original CRE118189 on server4GPU0 and monitor native validation. Existing HPC6282/APFbf6 have reviewed static native/op packets; only after truly idle authorizedGPU0/fresh owner/current actual compatible parent/assets/UUID/three locks execute paired naturalTRAIN2 and original resources, then receipt/queue/verified launch. No GPU1, interrupted CRE, reused PASS or new candidate needed while reserve full.'
        assert {c['id'] for c in work['candidates']}==set(b['candidate_digests'])
        assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in {u.CRE,u.HPC,u.APF})
        json.dumps(work,ensure_ascii=False,allow_nan=False)
        catalogue_refs={cid:{k:entry[k] for k in ('code_commit','source_version','native_preparation','native_review','operational_preparation','operational_review')} for cid,entry in by_id.items()}
        notes={'actions':[
            f'上海{shanghai}只读核验原CRE/M217 PID118189/source8/YAML/runtime d585及GPU0 UUID+computePID，TRAIN{epoch}/50 {samples[0]["max_native_step"][1]}→{step}/4686，已观测{len(live["precise_native_validation"]["values"])}次原生验证，best={best}；仍早期且未完成，M95 champion .5020/目标.5100保持。',
            'HPC/M218只将原c94f的8模型源+原YAML共9文件以原字节保存为6282263d单亲d585兼容版本，18项只读Git独审确认exact9A/9blob/clean；旧2f7/父56、NULL母本、0f原control失败全保留，无模型修订、主线ff或部署。',
            'HPC原native/op工具仅做版本/路径/外锚声明兼容包装；APF/M219 bf6新增真实祖先路径因子专属native观察与op工具，42 native软件核和46 op软件核及独立静态审查通过；原资源函数/数据/seed/精度/优化器/门保持。均未执行Torch/真实TRAIN2/资源，不据此签准确率或新颖性PASS。',
            '两个已有候选登记新准备包后，各实际Adapter.prepare(0)均因CRE登记占用在transport前拒绝：0连接、0active binding/manifest/lease、0 native命令。原GPU0训练继续，GPU1禁用；本轮0新候选/0模型修订/0准入/0新增启动，旧10挂起和其余142候选保持。'],
            'decisions':[
            '本轮creation_budget=0/reserve_budget=0，推进已有HPC/APF，未扩展候选。HPC兼容源保存与APF工具检查是准备进展，实际技术准入必须等合法空GPU0执行原两步自然TRAIN及资源对照。',
            f'优先继续CRE原训练，当前原生验证best={best}处于早期，不推断最终结果。当前champion仍.5020、目标.5100，差.0080；不调参或重跑旧终态。',
            '未来主线/runtime若改变，先对实际父版本做显式兼容核验，禁止跨兄弟ff、重标旧raw或盲重放。PCE/RSTR额度、M206暂停和BFC专属恢复授权边界保持；无新增用户确认事项。']}
        memory=f'''# Codex Research Memory

## Goal And Phase
- 当前fd073f8866984dad9b4df76203a22866；actual/target {EXPECTED['thread_id']}一致；generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值不延长。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020，baseline.4894/gap.0080。Phase1层级分工→inst_feats→query/masks，监督辅助；Phase2人工。
- standing experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖普通实现/保存/检查/既有安全同步/准入/训练，不授旧拒绝重开、额外修订、受保护恢复、扩资源或改调度。
- 最新人类不用gpu1：仅server4 physicalGPU0/max1；SERVERS2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1；GPU0授权94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09。其他allowed[]；Windows Pipeline-cluster_project Disabled。
- seed1999/epochs50/max_iters70/原YAML/data/pretrain/optimizer/precision不变；原fvcore handlers/fullunsupported/≤10G，bs1lang1/warm20repeat100 median/P90；峰值+15%需≥+.003mIoU。
- 禁调参、gate/cag/cfe/layerscale、语言路由、大QKV/N²attention、重复inst/3-4-6层、无图数值微调、旧rejected改名。

## Champion And Baseline
- M95仍.5020/目标未达。MDC.4872/HAP.5002/HRC.4901/PSBR.4969/PSNC.5001/BTC.4914/BCR.4995均历史自然早停，不调参重跑。
- BEC/M215正常earlystop24/50打印best.5001；AEF/M216正常earlystop23/50原生23值精确best.495597243309021（打印.4956）。均未超过M95，只判断该次实现，不否定整个层级机制。

## Active Hypotheses
- 唯一正式训练M217-CRE stableID hierarchy-cross-root-directed-edge-broadcast，原source/primary/runtime d58576b396cfb54577652be972f3ffaffda508c9/唯一父56b2；receipt0ab8d1bd7e518322c25ae36bb80344fb62f90c150e5ca09bd856cb53d0a6320b，canonical原PID118189/launchverified training_progress。不要因dispatch_phase progress_pending重放。
- CRE固定原不同root receiver/sender联合U/GELU定向vector消息→private equalmean，再D0/D1联合fine/middle与祖先root消息，替代3FFN；原3LN/rawskip/rawbanks/CSORT/HCG/单inst保持。效果/新颖性UNKNOWN。
- CRE上轮01b实际四臂原两自然TRAIN/原criterion backward+optimizer和路径门通过/common835项155907386参数/hash5c80…是观测非固定门；独审83b61637。9.639849036G vsM95 9.762532428G，156301370参数（−1182720），median+1.9395%/P90+3.6650%，预测/observer-smoke显存下降；pureTRAIN峰值UNKNOWN。
- 上海{shanghai}原CRE TRAIN{epoch}/50 {samples[0]['max_native_step'][1]}→{step}/4686，原生验证values={live['precise_native_validation']['values']}，best={best}。仅早期指标，非最终收益；当前proof tick_fd073f88/cre_training_progress_observation_final.json。
- M218-HPC stableID hierarchy-tree-resolvent-nonlinear-composition：原fine→middle→coarse真支持森林A=I+L，S=A^-1；raw+[S F(S LN(raw))]，F仍原3FFN；固定两层Schur上行/回代，无denseinverse/新参数/gate。unsupported/pad Sidentity保FFN；一真点仍3节点路径；S常量保持不等非线性SFS均值保持。
- HPC原c94f/17map/原8源+YAML9及NULL/reference56全冻结；旧2f7eff19ca59cc4586e13ca81a547a18ea7e313d/父56和f395 native f9a2/op1362/0f失败保留。本轮9文件逐字节一致的单亲d585兼容source6282263d805c1741234f97afc981a05aca2ad6e3，proof f82a3f05/实际Git独审24e906ad，恰9A/9blob/clean，无模型修订/主线ff/部署。
- HPC本轮兼容native/op在tick_fd073f88/hpc_compatible_prepare；worker原字节/资源整函数/0-only+六owner+原deadline+三锁/once/reconcile保留，只source/parent/runtime路径声明适配，当前候选图/FP32/autograd/resources均NOT_RUN，不借CRE PASS。
- M219-APF stableID hierarchy-ancestry-path-factor-composition：每真fine取原fine/middle/coarse祖先一次GELU(W3C→3C)，拆u/v/w；fine直接u，上层私有v/w按真fine路径equalmean，coarse非等middle/pointmass。原3LN/rawskip/rawbanks/CSORT/HCG/单inst保持，无learnedscore/gate/新routing。
- APF source bf6c3fafe0f690e16e838e7c0192f09e789389f9/父d585，原04993/19map/9文件字节/61185协议/NULL-reference56保持。上轮35软件核+独立43仅静态，本轮新native4c44cdac/独审8ed1773b与op64f5aafb/独审c63951a5，42+46软件核只工具，不是训练实验。
- APF真实观察准备：一jointmap/GELU/三slice/directfine/两原mean返回原对象/原ID写回/三skip→HCG→单inst。整体factorW原loss聚合有限非零及实际更新是门，9块仅描述、逐call/row/bias零合法；全空真实支持INCONCLUSIVE不重抽。common动态names/shapes/count/hash排3FFN/path_factor保3LN；原resources整函数保持。
- APF/HPC均已保存独立源码及静态工具，当前validation待真实自然TRAIN2/resources；无GPU检查/PASS/收据/训练队列。两个reviewed prepare(0)本轮实际因原CRE登记占用在transport前拒绝，0transport/0active/0native。未来必须freshowner+实际兼容parent+真空GPU0/UUID/三锁，非未来空卡许可。

## Closed Or Failed Directions
- BEC/M215 archive4bd2119b138d4676972019b7462720fa，旧R1唯一True→1 JIT修复/9b失败/94f通过全保留，不加R2。AEF/M216 archivead76de1eebbd43f7be720a8b17fca1cb，旧终态不重复归档/重启；完整日志在0f两证据中。
- CTS/M214 stopped_unknown14/50 best.4890/archivea966d7e40d26454598863ac4a87fc4a9，无endingmarker/根因UNKNOWN不自动恢复。BFC/M213 crashed20/50 step3832/4686 DataLoader scatter overlap/archiveb91b3ba11671451bb28f39dc3cc3f2c7；根因UNKNOWN，epoch19旧ckpt best.4992169439792633，无RNG/sampler/失败输入复现，需专属新恢复计划+人工许可。
- HAP epoch18恢复授权已消费。M206用户暂停+dispatch_hold+resumeFalse保持。PCE2+extra1已尽/RSTR2已尽；禁PCE_R4/RSTR_R3/M201自动恢复，旧RSTR9文件localcommit授权不授额外修订。
- 10旧held（辅助监督/无图数值/PCE/RSTR/M206/BFC）本轮原记录digest均保持，未重读旧授权/ckpt/855目标，无新增人类动作；145条无新候选，只有CRE/HPC/APF三条进展metadata变化。

## Running And Queue
- 当前唯一M217-CRE server4 GPU0原PID118189/runtime d585；上海{shanghai} TRAIN{epoch}/50 step{step}/4686/native best{best}。0ready/0claiming；waiting M206用户暂停不可派发。储备HPC6282/APFbf6两条，尚非已准入训练队列。
- SSH keys/strict hostkey pinned songcl@192.168.1.115，先验dl04-MS-7E06，GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c。runtime /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1；conda project_cluster/server4_conda_4ca73fba.sh，data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints。
- 不用旧IP.137/密码/sudo，不查询/使用GPU1；未知request/PID只exactreconcile，禁盲重启/kill/删锁。主线当前d585，原用户28内容/status/原index/空暂存及18生命周期账本本轮保持。

## Open Questions And Risks
- 历史0f CRE/HPC首M95 control在构造前依赖import失败：CRE sre_compile list callable，HPC Lark Transformer_NonRecursive nochildren，各0loss/backward/step，根因UNKNOWN。旧raw/独审0528056c保留；01b完整CPU两order/CRE实际四臂与新训练通过不证明根因修复、不替HPC/APF过门。无库/stdlib/全局cache改动。
- HPC/APF真自然batch支持/公共初始化pairing、Torch浮点/autograd、效率/泛化/新颖性均待测。原source-only/工具静态结果不签资源或效果；没有新FP32 conservation/Jacobian阈值。若主线未来推进须再显式对同9文件字节做兼容核验，不跨兄弟ff/重标raw。

## Last Tick
- canonical begin一次查进展/既有派发，无新终态；snapshot creation/reserve预算均0，准备上限内只推进已有HPC/APF。
- HPC同9文件字节兼容save6282/parentd585及18项只读Git独审完成；HPC工具元数据兼容、APF独立native/op工具42+46软件核与独审完成，均NOT_RUN原生。两staticrelease只是模板bytecopy外锚，不是执行lease/许可。
- 两实际prepare(0)均拒绝CRE占用/0transport/0active/0native；CRE原PID/source8/YAML/runtime/GPU0步数实增，早期验证如上。无新增候选/修订/准入/队列/启动，不改调度/其他项目/资源。
- 六段报告用report_notes生成，七节memory本轮更新，随后canonical report/finish并核验FINALIZED/contextcommitted/released；此处不预签收尾结果。
'''
        assert len(memory.splitlines())<120
        json.dumps(notes,ensure_ascii=False,indent=2,allow_nan=False);memory.encode('utf8')
        decision=ROOT/'pipeline/decisions'/('20261028-'+observed.astimezone(timezone(timedelta(hours=8))).strftime('%H%M%S')+'_next_batch.md')
        text='# 本轮实验决定\n\n'+'\n'.join('- '+s for s in notes['actions']+notes['decisions'])+'\n\nHPC/APF 的 native TRAIN2/资源结果仍标为 NOT_RUN；已实测且正在训练的 CRE 保持原记录。下一步等待授权 GPU0 真正空闲，不需要重复常规操作授权。\n'
        text.encode('utf8');assert not decision.exists() and not (HERE/'report_notes.json').exists()
        intent={'recorded_at':now,'owner':EXPECTED,
            'before_work_sha256':sha(ROOT/'pipeline/research_work.json'),'live':u.ref(live_path),
            'guards':u.ref(HERE/'current_resource_guard_result.json'),'program':u.ref(__file__),
            'scope':'All work/memory/notes/decision payloads composed and serialized first. Existing CRE observation, existing HPC/APF current resource guards and audit text only; no source/queue/receipt/launch or held-candidate mutation.'}
        guard()
        with (HERE/'final_records_intent.json').open('x',encoding='utf8') as f:
            json.dump(intent,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
        u.atomic(ROOT/'pipeline/research_work.json',work)
        u.atomic(ROOT/'pipeline/codex_memory.md',memory,text=True)
        u.save(HERE/'report_notes.json',notes)
        guard()
        with decision.open('x',encoding='utf8') as f:f.write(text)
        u.primary_protection(b);u.lifecycle_protection(b)
        changed=[c['id'] for c in work['candidates'] if u.digest(c)!=b['candidate_digests'][c['id']]]
        assert set(changed)=={u.CRE,u.HPC,u.APF}
        u.save(HERE/'protected_assets_after.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,
            'primary_head':u.SOURCE,'primary_index_sha256':b['index_sha256'],'original_source28_status_and_empty_staging_preserved':True,
            'lifecycle_18_unchanged':True,'candidate_count':145,'changed_existing_candidates':changed,
            'other_142_candidates_unchanged':True,'new_candidates':0,'model_revisions':0,'new_native_commands':0,'new_launches':0,
            'current_training':u.ref(live_path),'catalogue_refs':catalogue_refs,'report_notes':u.ref(HERE/'report_notes.json'),
            'decision':u.ref(decision),'memory_lines':len(memory.splitlines()),'finish_status':'NOT_YET_CALLED'})
        print(json.dumps({'observed_at_shanghai':shanghai,'epoch':epoch,'step':step,'best':best,
            'new_candidates':0,'new_launches':0,'memory_lines':len(memory.splitlines()),'report_notes':u.ref(HERE/'report_notes.json')},ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
