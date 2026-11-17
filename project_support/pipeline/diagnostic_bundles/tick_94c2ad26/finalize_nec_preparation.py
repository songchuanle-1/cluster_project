"""Register actual NEC preparation/resource check and close this tick's research records."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
import sys,copy,json
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
CID='hierarchy-coupled-node-edge-state-composition'
def main():
 if sys.argv[1:]!=['--execute-root']:print('DEFAULT_NOP');return
 guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  b=u.read(HERE/'protected_assets_before.json');u.protect(b)
  pins={'nec_version_prepare/isolated_source_version.json':'87453f6c78bf6acf061685f7492b2c25723c23d5d6ed5846ffd364f015807f6c','nec_actual_source_version_independent_review.json':'26dbb8d9e26e4fe73593a4b84421fcd17ceaa189f8a78746c9d538e64a6bc4ac','nec_native_prepare/preparation.json':'6c527a90cb53de8e57fce7c4ae1fd7f6148138bd6837197f216487315ab02de0','nec_operational_prepare/preparation.json':'53fe96c2c0430a5330abe5872327bc470a1548775f292c25b52eadce7ab5c5fd','nec_native_and_operational_independent_review.json':'2b237fcff5a7886ccff633ffd719046a98efd49e2169a8ac725e6b92e8b01d3a','nec_root_packet_integration_result.json':'d92e5b2941a529d183df35dd00bfc6f0e82ef5d58df8877b74f52a8441b39bd7','nec_gpu_precondition_observation.json':'6cb7097bb5e6a342c7df49372b8a0c26f6d33804cdaf0165a69896b12f64114e','dual_original_run_observer/original_both_phase_observation.json':'c3be28dc85205abd7b4cf86ab2a628be27d4dda9af4637f18ad6e3aa0e257465'}
  for name,h in pins.items():assert sha(HERE/name)==h
  peer=u.read(HERE/'nec_native_and_operational_independent_review.json');assert peer['material_concerns']==[]
  version=u.read(HERE/'nec_version_prepare/isolated_source_version.json');native=u.read(HERE/'nec_native_prepare/preparation.json');op=u.read(HERE/'nec_operational_prepare/preparation.json')
  assert version['code_commit']==native['code_commit']==op['code_commit']=='6bc36adfe42764aac2209e6600fb3a783e2fa374' and version['parent_commit']==b['head']
  for directory,prep in [(HERE/'nec_native_prepare',native),(HERE/'nec_operational_prepare',op)]:
   for name,h in prep['prepared_file_hashes'].items():assert sha(directory/name)==h
  assert native['draft_execution_disabled'] is op['draft_execution_disabled'] is True and native['operational_ready'] is op['operational_ready'] is False
  gpu=u.read(HERE/'nec_gpu_precondition_observation.json');observed=datetime.fromisoformat(gpu['observation']['observed_at'])
  assert gpu['returncode']==0 and gpu['result']=='blocked' and gpu['idle_gpu_ids']==[] and gpu['busy_gpu_ids']==[0,1] and datetime.now(timezone.utc)-observed<timedelta(minutes=5)
  assert u.read(HERE/'nec_root_packet_integration_result.json')['passed'] is True
  work=u.read(ROOT/'pipeline/research_work.json');assert sha(ROOT/'pipeline/research_work.json')==b['research_work_sha256']
  assert {c['id']:u.digest(c) for c in work['candidates']}==b['candidate_digests']
  c=next(c for c in work['candidates'] if c['id']==CID);assert c['stage']=='implementation' and c['code_commit'] is None and c['source_commit'] is None
  prior=copy.deepcopy(c);refs=[u.ref(HERE/name) for name in pins]
  refs.extend([native['static_validation'],native['source_version_binding'],op['metadata_validation']])
  for e in refs:
   assert sha(ROOT/e['path'])==e['sha256']
   if e not in c['evidence']:c['evidence'].append(e)
  c['source_version_history']=[{'recorded_at':datetime.now(timezone.utc).isoformat(),'prior_source_commit':None,'prior_code_commit':None,'prior_source_parent_commit':None,'original_source_preparation':c['source_preparation'],'saved_isolated_source_version':u.ref(HERE/'nec_version_prepare/isolated_source_version.json'),'prototype_original_NULL_metadata_unchanged':True,'model_revision':False}]
  c.update(stage='validation',code_commit=version['code_commit'],source_commit=version['code_commit'],source_parent_commit=version['parent_commit'],future_version_parent=version['parent_commit'],source_version=u.ref(HERE/'nec_version_prepare/isolated_source_version.json'),source_version_status='EXACT9_COMPATIBLE_ISOLATED_VERSION_SAVED_NOT_PROMOTED',independent_source_version_review=u.ref(HERE/'nec_actual_source_version_independent_review.json'),implementation_status='SOURCE_VERSION_AND_DRAFT_DIAGNOSTIC_SOFTWARE_VERIFIED_NATIVE_NOT_RUN',native_status='NOT_RUN',resource_status='NOT_RUN',Torch_FP32_autograd='NOT_RUN',queued=False,scientific_admission=False)
  c['worker_preparation']={'status':'SOURCE_BOUND_DISABLED_DRAFT_SOFTWARE_REVIEWED_NOT_NATIVE','preparation':u.ref(HERE/'nec_native_prepare/preparation.json'),'draft_execution_disabled':True,'operational_ready':False,'native_backward_executed':False,'resource_profile_executed':False,'native_backward_passed':None,'resources_passed':None,'active_native_manifest_or_execution_lease_created':False,'independent_review':u.ref(HERE/'nec_native_and_operational_independent_review.json')}
  c['execution_adapter']={'status':'SOURCE_BOUND_DISABLED_OPERATIONAL_DRAFT_NOT_EXECUTED','preparation':u.ref(HERE/'nec_operational_prepare/preparation.json'),'native_preparation':u.ref(HERE/'nec_native_prepare/preparation.json'),'release_template':op['release_template'],'release':None,'draft_execution_disabled':True,'operational_ready':False,'remote_adapter_execution_tested':False,'native_execution_tested':False,'active_binding_manifest_lease_created':False,'transport_executed':False,'standard_summaries_created':False,'independent_review':u.ref(HERE/'nec_native_and_operational_independent_review.json')}
  c['implementation_test_history']=[copy.deepcopy(prior.get('implementation_test'))]
  c['implementation_test']={'result':'passed','command':native['static_check_command'],'scope':'48 actual author software checks plus independently reviewed source/native/adapter draft and root default-NOP cross-integration; no native or resource pass.','evidence':[native['static_validation'],u.ref(HERE/'nec_root_packet_integration_result.json'),u.ref(HERE/'nec_native_and_operational_independent_review.json')]}
  c['native_execution_blocker']={'kind':'occupied_authorized_gpus','server':'server-4','observed_at':observed.isoformat(),'busy_gpu_ids':[0,1],'original_tasks':['M226-WFC','M227-LFT'],'evidence':u.ref(HERE/'nec_gpu_precondition_observation.json'),'scope':'Physical resource precondition only; not failed backward, resource budget, human permission or scientific rejection.'}
  c['retry_after']=(observed+timedelta(hours=1)).isoformat()
  c['unblock_condition']='An authorized server4 physical GPU is genuinely idle, original task/uncertain canonical reservations naturally clear, fresh owner/runtime/source/native assets and exclusive locks verify; root reviewed activation and same native protocol then allowed under existing project authorization.'
  c['next_action']='When an authorized card is genuinely idle, preserve frozen drafts and materialize reviewed active copies with fresh actual owner/deadline/source/runtime/UUID and current producer hashes under existing project authorization; no extra human permission. This draft selects1; an idle0 needs only reviewed GPU metadata port, not resource expansion. Run unchanged original paired natural TRAIN2 and original full resources on source6bc only while runtime4457 remains exact; if main changes first save/rebind same9 compatibly, never blindly ff a sibling. Actual PASS plus result independence then admit/queue/dispatch this tick. No request/lease/raw/receipt exists yet; no replay or borrowed result.'
  now=datetime.now(timezone.utc).isoformat();oldattempt=work.get('tick_attempt')
  if oldattempt and oldattempt.get('tick_started_at')!=EXPECTED['generated_at']:work.setdefault('tick_attempt_history',[]).append(oldattempt)
  work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+str(HERE/'check_nec_gpu_precondition.py')+' --execute-root','observation':'Actual pinned hostname/physical0+1 UUIDs and both original PID/start identities verified; NVML has no idle card. NEC native/model/resources not entered, no signal or eviction. Source/version/software progress recorded separately.','evidence':[u.ref(HERE/'nec_gpu_precondition_observation.json')]}
  work['updated_at']=now
  assert len(work['candidates'])==155 and all(u.digest(x)==b['candidate_digests'][x['id']] for x in work['candidates'] if x['id']!=CID)
  u.protect(b);u.atomic(ROOT/'pipeline/research_work.json',work)
  sections={
  'Goal And Phase':[
   '当前owner94c2ad26b7464980b44134a7f42bed27，generated2026-10-31T14:09:05.368671Z/deadline15:09:05.368671Z；真实root thread01a159c5-29ab-7a22-ba7f-e79174757253与foreground target一致，不延租约；收尾以实际receipt为准。',
   'Phase1目标mIoU .5100；冠军M95 .5020/baseline .4894/gap .0080。原YAML/data/pretrain/loss/optimizer/precision/seed1999/50epochs/maxiters70/patience10、10G/原conditional15%/bans不变，Phase2人工。',
   '只用server4物理0/1各1任务；goal0441/SERVERS19b3/closure2993/standing2e89/GPU1grant6529保持，其他服务器新dispatch禁用，Pipeline-cluster_project仍Disabled。'],
  'Champion And Baseline':[
   '冠军不换。旧SFC .49663493037223816@20/epoch30、ELC .5015384554862976@21/epoch31正常早停，archive2816/c437及精确校正018c保持；本轮没有新正式终态。',
   'generic归档stdout舍入/空log路径局限仍在，终态须核完整native日志/远端SHA；原CSV换行失败与binary atomic仅两行修复留档，不改全局skill/调度。旧AOC .500072062/archive b132、FCB stopped_unknown/be337与PES原失败保留。',
   '上轮d94467a9实际FINALIZED/PASS/context_committed/released于2026-10-31T12:57:23.277396Z；不是方法有效或项目目标完成。'],
  'Active Hypotheses':[
   'M226-WFC：无序楔[中心,两端和]共享非线性后一次incidence mean回节点，保原LN/skip/HCG/单inst。原PID2085005/start105948793/source94/GPU0不变；14:13:02→05Z TRAIN[7,222]→229，6次已完native val best .45783278346061707/noimp0，仅早期部分结果。',
   'M227-LFT：真fine祖先路径P/U非线性三角分析→原3packedFFN→逆合成→3层原写回。原PID2685912/start106767833/source4457/GPU1不变；14:13:05→08Z TRAIN[2,4686]不动而VAL[2,121]→126，正常验证，1次已完val best .3451182544231415/noimp0，不冒称TRAIN增长。',
   'LFT原四臂db71/34bc/0625/7bf1/b06c、receiptad0f/一次dispatch0b56与原source5931/兼容4457历史保持；原resources9.781406796G、allocated937816064 vs936763392B、median88.3758245 vs87.1036780ms；无新latency/FP32门，whole新core聚合梯度/真实更新才是训练性门，效力/novelty/pureTRAIN峰未知。',
   'M228-NEC：节点h/边e双持久状态在真forest结构直径2/4轮同步交替更新。原proto7592/协议17ba/sourcepeer8cdc与NULL母包不改；本轮真实保存exact9孤立兼容版6bc(parent4457)，proof8745/独审26db，未ff或同步主线，无模型revision。',
   'NEC诊断draft native6c52/worker c14c/runtime0c27/templateefec 与op53fe已合审2b23；48项软件核dc8d+root默认NOP跨包集成d92e通过。两包DRAFTTrue/10activeNULL/operationalreadyFalse，原YAML/TRAIN2/完整资源协议均未执行；原assembler/checker局部失败原件保留，未改模型/协议。',
   'M229-MIC：真fine祖先路径共享非线性八顶点Möbius混合差分，fine q直接等均值回mid/coarse。原proto346a/协议a507/独审0a67、33源检查与17carrier案例保持；实际code/source/parent仍NULL，仅94历史参考，本轮未推进或训练。'],
  'Closed Or Failed Directions':[
   '10旧holds、PCE2+extra1/RSTR2已尽预算、已消费HAP旧grant保持；M206-CGCA waiting/user_paused/dispatch_hold/noPID，GPU1授权不恢复它或旧FCB。',
   'PES clip_grad_norm根因UNKNOWN及partial .4211保留；旧APF/HPC/CTS/BFC negative/unknown不换名重开，也不借NEC声称已修复。'],
  'Running And Queue':[
   '当前正式运行仍WFC GPU0和LFT GPU1；两原进程身份与源版本保持，14:13 c3be分别TRAIN/VAL真实增长。14:27:29Z全新物理核验6cb7：两卡均被这两个原PID占用，idle[]；没有NEC GPU检查/新进程/驱逐。',
   '155候选：47complete/94rejected/10blocked/2training/1validation(NEC)/1implementation(MIC)。NEC有源与禁用诊断准备但native/resources NOT_RUN，ready_waiting0；M206仍唯一暂停waiting，不能把两原型当待跑任务。',
   'main local/remote仍4457，WFC历史source94不重标签；28用户文件/status/正常index精确SHA、两运行18源文件、38生命周期及其余154候选保持。'],
  'Open Questions And Risks':[
   'WFC .4578/LFT .3451都是早期部分验证且低于冠军，不调参/换seed/重启；NEC/MIC效力/novelty与原生资源均未知。源MAC代理不是10G实测，NEC需要原完整资源口径，个别map/row/column/bias零合法。',
   'NEC现草案需另存受审active副本后才可执行；root激活/新owner/source/runtime/UUID绑定属于已有项目授权，不是新人工审批。当前副本意向GPU1；若先空闲GPU0只能做受审元数据端口，不扩大资源。10NULL不能伪造补签，旧request不能重放。',
   '6bc是4457上的独立9A；当前不提升未native测版本。若未来main先变，先将相同9源码另存真实兼容版并重绑定，不盲ff兄弟版本；冻结母包/负结果/协议保留，工具metadata更换不冒称模型revision或native成功。',
   '所有本地/诊断python -B/dontwrite1，原正式argv不为样式重启。只用key+strictknownhost且hostname先核dl04/.115，未读密码/用旧.137/推断sudo；无调度或全局pipeline变更。'],
  'Last Tick':[
   '本轮begin14:09已查进展/派发已有ready，无终态或故障；快照creation/reserve_budget0，因此只推进已有NEC，MIC/旧holds不动。source6bc保存、48软件核/跨包集成/独审完成，实际资源检查因双卡原任务占用blocked，tick_attempt及证据已绑定NEC。',
   '0新候选/0模型revision/1孤立9A源码保存/0nativearm/0准入/0新正式训练/0正式终态。最新主指标来源14:13，资源来源14:27；报告0–3是begin冻结快照，后状态见动作/决策。',
   '六段report/七段memory先留档，finish/release以真实receipt为准，不在释放后补写。当前无需用户处理；有首个LFT验证值和NEC实质准备进展可NOTIFY，绝不宣称有效。',
   '下一轮先核两原运行/ready；空闲授权卡出现才按当轮owner/runtime做root受审激活/新绑定，执行NEC原YAML匹配自然TRAIN2+原完整resources，通过实际独审后同轮入队/启动；无空槽不重复源检查或造新结论。']}
  memory='# Codex Research Memory\n\n'+'\n\n'.join('## '+h+'\n'+'\n'.join('- '+s for s in rows) for h,rows in sections.items())+'\n'
  assert len(sections)==7 and len(memory.splitlines())<120
  path=ROOT/'pipeline/codex_memory.md';temp=path.with_name(path.name+'.94c2ad26.tmp');assert not temp.exists();guard();temp.write_text(memory,encoding='utf8');guard();temp.replace(path)
  notes={'actions':[
   '实际现场2026-10-31T14:13:02→08Z：原WFC/PID2085005/source94/GPU0 TRAIN7/222→229，6次已完成native val best.45783278346061707；原LFT/PID2685912/source4457/GPU1 TRAIN2/4686不动而VAL2/121→126，1次已完成val best.3451182544231415。两原任务正常推进，不将验证移动冒称训练步数增长；无新正式终态。',
   '按本轮creation/reserve_budget0只推进已有NEC：原7592/协议17ba/9源码字节不改，真实另存4457父上的孤立6bc版；主线不ff/不同步，proof8745与独审26db核9A、用户28/index/两运行18源码及38生命周期保持。',
   'NEC诊断native6c52与op53fe草案完成，48软件核dc8d、root默认NOP跨包集成d92e及独审2b23通过；保原YAML/匹配自然TRAIN2/whole新core聚合梯度更新门、原完整资源函数与unsupported口径。两包DRAFTTrue/10执行NULL/未就绪，不借静态检查或旧结果签native/resources PASS。初assembler/checker失败原件保留，无模型/协议修订。',
   '14:27:29Z再次hostfirst/key/strictknownhost实测物理0/1 UUID、NVML compute成员及原PID/start：两卡均由WFC/LFT占用，idle[]；NEC实际资源前置检查blocked。没有新CUDA模型/原生诊断/租约/原始结果/准入/入队/训练，未暂停或驱逐原任务。',
   'NEC登记validation/source6bc与软件准备证据、native/resource NOT_RUN及明确空槽条件，MIC原code/source/parent NULL和旧10holds/M206暂停保持。155记录中其余154候选、队列/running/CSV/全部原receipt与既有运行保持；报告0–3仍是begin14:09冻结事实。'
  ],'decisions':[
   '冠军仍M95 .5020，目标.5100/gap.0080；WFC.4578/LFT.3451为早期部分验证、均未达冠军，不改变原seed/data/schedule/patience，不宣称新方法有效。',
   '现有项目授权覆盖未来root受审激活和测试，不增加人工确认。下次空闲卡出现才用当轮owner/runtime/source/UUID/三锁新绑定执行NEC原YAML匹配TRAIN2和原资源；通过实际独审当轮准入/入队/派发。当前草案不能重放，若main变则保存相同9字节兼容源后重绑定；不盲ff兄弟版。',
   '本轮没有新训练，真实成果是NEC兼容源与禁用诊断工具准备；actual resource_check blocked有当前证据并归NEC，不把GPU等待当模型失败。原实验继续，无用户待办；report/finish/release是否通过以实际命令与收据为准。'
  ]}
  u.save(HERE/'final_report_notes.json',notes)
  state={'owner':EXPECTED,'recorded_at':now,'candidate_stage_counts':dict(Counter(x['stage'] for x in work['candidates'])),'source_commit':version['code_commit'],'main_HEAD_unchanged':b['head'],'new_candidates':0,'model_revisions':0,'new_native_arms':0,'new_admissions':0,'new_formal_runs':0,'new_formal_terminals':0,'source_isolated_versions_saved':1,'tick_attempt':work['tick_attempt'],'protected_other154_candidates':True,'protected_user28_original18_source_and38_lifecycle':True,'work_sha256':sha(ROOT/'pipeline/research_work.json'),'memory_sha256':sha(path),'notes':u.ref(HERE/'final_report_notes.json'),'bound_artifacts':refs,'foreground_finish':'NOT_YET_RUN'}
  u.save(HERE/'preclosure_actual_state.json',state);u.protect(b)
  print(json.dumps({'status':'NEC_PREPARATION_AND_ACTUAL_RESOURCE_BLOCK_RECORDED_FINISH_PENDING','state':u.ref(HERE/'preclosure_actual_state.json'),'notes':state['notes'],'stage_counts':state['candidate_stage_counts'],'memory_lines':len(memory.splitlines())},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
