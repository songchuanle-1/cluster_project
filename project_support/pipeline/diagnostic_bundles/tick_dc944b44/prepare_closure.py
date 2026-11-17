"""Persist due-candidate resource evidence without changing frozen science."""
from datetime import datetime, timedelta, timezone
import json
import os
import shutil
import subprocess
from ops import ROOT, OUT, SKILL, TOKEN, GOAL, IDS, guard, tick, evidence, save, now

owner, _ = guard(180)
resources = tick.load(OUT / 'current_resources_and_training.json')
assert resources['server4']['returncode'] == 0
live = resources['server4']['data']
cards = live['cards']
assert cards['0']['contexts'].startswith('1085297,')
assert not any(cards['0']['locks_available'].values())
assert cards['1']['contexts'] and all(cards['1']['locks_available'].values())
assert len(cards['1']['processes']) == 2
assert resources['server3']['gpu1_occupation'] is None
assert 'Connection timed out' in resources['server3']['observed_stderr']
steps = live['M204_native_steps']
assert len(steps) >= 2 and steps[-1][0] == steps[0][0] == '25'
assert int(steps[-1][1]) > int(steps[0][1])
observed = datetime.fromisoformat(live['observed_at'])
retry = observed + timedelta(hours=1)
assert retry > datetime.now(timezone.utc)
work = tick.load(ROOT / 'pipeline/research_work.json')
before = {row['id']:row for row in work['candidates'] if row['id'] in IDS}
assert len(before) == 2
for row in before.values():
    assert row['stage'] == 'blocked' and row['non_gpu_preparation_completed']
    assert not row['scientific_admission']
    for entry in row['evidence']:
        assert tick.digest(ROOT / entry['path']) == entry['sha256'], entry['path']

analysis = save('analysis.json', {
    'observed_at':now(), 'token':TOKEN, 'snapshot_at':'2026-10-19T18:13:48.142346+00:00',
    'goal_sha256':GOAL, 'candidate_ids':list(IDS),
    'scientific_status':'INCONCLUSIVE; no new CUDA geometry/mask/backward experiment or trained efficacy evidence. Existing frozen CPU/source evidence is reused, not counted again.',
    'actual_observation':{
        'server4_at':live['observed_at'],
        'GPU0':'Same M204 PID1085297,19863MiB/28%,all3projectlocksheld;nativeTrain25/50steps1519to1523/4686,freshlog,no recent traceback.',
        'GPU1':'Two foreign compute contexts,16065MiB/100%;three project locks are available but do not permit sharing an occupied card.',
        'server3':'Actual bounded strict-known-host/key SSH hostname probe timed out before identity confirmation; GPU1 occupation UNKNOWN. It is an unavailable fallback, not an occupied/idle classification.',
        'M204_best':'Preflight monitor approx0.4993 at25/50,no_improve6/10;exact current fullprecision UNKNOWN. Not historical champion or goal reached.'},
    'frozen_next_tests':{
        IDS[0]:'Original4-pair/32expression fixedprefix/finalquery resolution protocol;resume pair0 only under a NEW current-tick execution lease and live resource checks.0actualGPU maskpairs so far.',
        IDS[1]:'Original native FPS/composedhierarchy/identity/inverse-relabel physical co-membership protocol;source-binary correspondence and task effects remain UNKNOWN.0actualGPUgeometryruns so far.'},
    'alternatives_checked':[
        'server4GPU0 remains original M204,not a diagnostic slot;no migration/restart/eviction.',
        'server4GPU1 is authorized but two actual foreign contexts prohibit sharing regardless of available project locks.',
        'server3GPU1 authorization retained;SSH timeout leaves runtime/assets/exclusive availability unverified.',
        'Frozen nonGPU controls/preparation completed previously;unchanged census/CPUunsupportedFPS/fixedanchor tests were not rerun. No evidence-backed independent executable nonGPU test identified in this due-resource check;not a global route-exhaustion claim.'],
    'this_tick_outputs':{'due_primary_resource_reviews':2,'authorized_server4_cards_observed':2,
        'bounded_server3_connection_checks':1,'new_stable_candidates':0,'new_cpu_scientific_tests':0,
        'new_gpu_diagnostic_attempts':0,'native_gpu_geometry_runs':0,'native_mask_pairs':0,
        'native_backwards':0,'new_models':0,'admissions':0,'new_training':0},
    'local_operational_faults':[
        'One malformed PowerShell invocation exited1 without resource data;corrected using guarded subprocess/shlex and a successful current observation.',
        'Direct apply_patch file creation failed;approved CLI apply_patch wrote only this current project bundle. No earlier script/evidence was changed.'],
    'auxiliary_holds':'Four supervisionIDs remain notdue until2026-10-20 04:37:50Shanghai;no scope rereview,priority restoration or repeated permission question.',
    'evidence':[evidence(OUT / 'current_resources_and_training.json')],
    'retry_after':retry.isoformat(), 'stop_reason':'external_resource_blocked',
    'execution_status':'Report and finish still required;no postflight success claimed.'})
blocker = ('At2026-10-20 02:18:40Shanghai server4GPU1 has2foreigncomputecontexts,16065MiB/util100%;one-task/card forbids sharing. '
           'GPU0 remains originalM204 with3locksheld. Bounded server3SSHhostnameprobe timedout;GPU1occupationunknown/unavailable,not provedoccupied.')
for row in work['candidates']:
    if row['id'] not in IDS:
        continue
    row.update(stage='blocked',updated_at=now(),failure_scope='inconclusive',
        blocker_kind='live_external_gpu_occupation',blocker=blocker,
        required_server='server-4',physical_gpu=1,retry_after=retry.isoformat(),
        unblock_condition='Actual authorizedGPU1contextrelease plus fresh UUID/idleness/all3exclusive-lock/runtime/frozenasset checks;server3 fallback only after identity/runtime/assets/exclusivechecks fully recover. Timer or available project locks alone never permits sharing.',
        non_gpu_preparation_completed=True,scientific_admission=False)
    row['evidence'].extend([evidence(OUT / 'current_resources_and_training.json'),evidence(analysis)])
work['design_cycle'] = {'updated_at':now(),'stop_reason':'external_resource_blocked',
    'attempted_ids':list(IDS),'retry_after':retry.isoformat(),
    'evidence':[evidence(analysis),evidence(OUT / 'current_resources_and_training.json')],
    'resume_condition':'Resume SAME frozen resolutionpair0 then native relabelgeometry when authorizedGPU1 is actuallyidle and NEWlease/UUID/runtime/assets/3locks pass;server3 only after recovered strictidentity/connectivity. Preserve M204 and foreignjobs.',
    'scope':'Due resource-evidence check only. Both nativeCUDA routes remain prepared and inconclusive. Not independent_routes_exhausted/no_information_gain/deadline expiry or missingGPU1permission;no filler route or repeated unchanged CPUprobes.'}
guard()
tick.save(ROOT / 'pipeline/research_work.json',work)
shutil.copyfile(ROOT / 'pipeline/codex_memory.md',OUT / 'memory_before.md')

memory = '''# Codex Research Memory
## Goal And Phase
- Currenttick dc944b44bc41467081a86ea8ef7dbfea,begin2026-10-19T18:13:48.142346Z/deadline19:13:48.142346Z(Oct20 02:13/03:13Shanghai),DESIGN. Actualowner01a04987-fdbe-7301-b2f0-f9b6ab60f74c and PipelineDisabled verified. Onebegin;no re-preflight.
- PRIORae419db58cbc4de4a44771efc6019a00 FINALIZED/PASS/contextcommitted;ownedlock+pendingabsent verified00:48:56Oct20. Neverfinish/abort/reuseoldtoken. Oldmemory pendingfinish wording was stale.
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85,25constraints/11bans,target.5100. Primary hierarchicalpoint/inst_featsupdate. Four supervisionIDs retain auxiliarypriorityholds,not scientificrejection. Seed1999/epochs50/max_iters70/scienceunchanged.
- Directhuman server4GPU1authorization already recorded:pipeline/authorizations/server4_gpu1_20261019.json. Authorizedserver4[0,1],server3[1],1task/card,capacity3. No duplicatepermissionrequest,server3GPU0/server6newdispatch/reset/eviction/restart/migration/schedulerchange.
- Pinnedserver4.115/dl04-MS-7E06 GPU0UUID958e741a-e5cf-127e-ffe8-9b984e1f404c,GPU1UUID7f82edb9-f620-8045-caea-a75232265cd1;server3.120/sysu311-MS-7C59 GPU1UUID340de111-e7e4-ed2d-15c9-8ab6a253e4a0. Strictknown-host/keySSH,passwordreferenceunread.
## Champion And Baseline
- HistoricalM95.5020,baseline.4894,target.5100,gap.0080. AvailablefrozenM95epoch16=.5024607181549072 NOTverifiedhistoricalchampionweights.
- CURRENT02:13monitorM204bestapprox.4993,25/50,noimprove6/10,sequence.4921/.4949/.4889/.4854/.4913. Bestunchangedfrom00:11,notnewchampion/target/terminalefficacy. ExactcurrentfullprecisionmetricUNKNOWN.
- CURRENT02:18:40sameM204PID1085297Train25/50steps1519->1523/4686,freshlog,norecentTraceback. CACHED00:22Train21/50 and00:11noimprove2/10 are historical,notcurrent.
- CACHEDM203FLE.4885315597@epoch13,earlystop23/50,priorfullVALdelta-.0139291520/sceneCI[-.0223369116,-.0054631474];notrestarted.
## Active Hypotheses
- coarse-semantic-point-cross-attention/M204CPA-R1 TRAINING underconsumedscopedhumanresume. Q=currentpoint,K=rawpreCTFcoarse,V=refinedcoarse;fine/middle/fusion/query/lossunchanged. Oneconnectionrevision,zeronewparams,no revision2/automaticrestart.
- CPA diagnosis/controls/constraintsUNPASSED,revision1inconclusive;activity/nonlocalsensitivityNOTtaskdeficit. Previous8scene32exprreadoutsmixed. ManualtrainingexceptionNOTscientificadmission. Prior9.769168428GvsM959.762532428G,inferpeak+1.2878%,matchedtrainpeak+.3289%to+.7063%;fulloptimizerpeakUNKNOWN.
- hierarchy-native-batch-minimum-resolution BLOCKEDbyactualexternaloccupation. PriorCPUcensus562/562TRAINscenes,28support<256,min131,maxpoints537406<2500000,0missing/unknown;nativegroups240/9372. Reused,no censusrerun/provedmaskharm.
- SameID original4pairedTRAINcohort/32expr,M95epoch16,fixedprefix/finalquery/nativepositives,cap256/64/8,original1e-6baseline/reaggregation/smallpeercontrols. Oldpair0preCUDAoccupationfailurepreserved. Cumulative0GPUmaskpairs;resumeSAMEpair0withNEWcurrentlease/freshUUID/context/idleness/3locks. Files pipeline/diagnostic_bundles/tick_4e35c1ce/native/ and native_resolution_protocol.json.
- hierarchy-native-superpoint-relabeling-audit BLOCKED,notrejected/notadmitted. Prior4nativeCPUfixedanchorcontrols onscene0000/0001/0002/0003_00 support667/710/2329/406:identity/inverserelabelpass,0/0/0/0assignmentchanges. Centersfixedfirst256physicalrows,NOTnativeFPS;CPUcentroidsNOTprovedbitwiseGPUscattermeans. DoNOTrepeatunchangedCPUcontrols.
- ProvidedCUDA sampling_gpu.cu old=0/idxs[0] sourcewitnessonly. ProjectwrapperSHA0d72921d19cd21e5321e0b7a6292712a83fe1667491fc698a9549177e9fe8b09;installedbinarySHAef0daa5ccf7fe471a5d73528762f209ba6d2dd89a6c3b50c6371eb9e0edebcfe;sourcebinarycorrespondenceUNKNOWN.
- ExactFPSbinaryCPUtestpreviouslyRuntimeError:CPU not supported,CUDAuninitialized;notmodelscientificfailure. FrozenoriginalFPS/composedhierarchy/identity/inverse/labelinvariantco-membershiprunner+geometry+manifest pipeline/diagnostic_bundles/tick_ae419db5/ remainsready;0GPUgeometry/mask/backwardruns. Notuploaded/executedthistick.
## Closed Or Failed Directions
- Allrank/meanmoment/ancestry/padding/prefix/QF/HDS/FLE diagnoses/rejections/bans anddirtyPDC/untrackedBCCA preserved. No renamedrouting/gate/residual/largeQKV/N2attention/tuning/canonicalseed singleoprepair/HDSrevision3/FLErestart/M201recovery.
- Priorbounded8scene/32exprstudiesCOMPLETE,nottrainable:expressiondonor-minus-ownprobabilityerror+.004466350020434506,7positive/1negative,295correlatedqueryrows. Scaleboundaryinteraction-.006994256213229087,2positive/6negative,30/32expr. Not efficacy/populationCI/newmechanism;no unchangedreruns.
- Originalexpressionboolsubtractionfailurepreserved;measurementrevision1casts2original0/1targets only;4correctedpairscontrols0. OriginalscaleFULLSOURCEpermutation2.86102294921875e-6FAILED1e-6onall4;fixedfusionconditionalcontrols0NOTfullsourcePASS. CPUassignment0doesNOToverridefailure.
- PriorCPUfloat32identity3.814697265625e-6/algebra2.4318695068359375e-5FAILED1e-6;float64internal0/4.44e-14butcachedGPUreconstruction7.48e-6FAILED. No thresholdwaiver/kernelrepeat/reopenedfiniteaudits. RelabelauditrecomputesFPS/maps,notoldfixedmembershipFLE/fixedmapmessagepermutation/batchmincount.
## Running And Queue
- CURRENT02:13snapshotactive1/target3,waiting0,candidatebudget2,reserve0/2,prep2,pending6/8=2primaryresourceholds+4auxpriorityholds. ThisTick0newcandidates/models/admissions/queueentries/training/policychanges. CumulativecountsNOTtickprogress/successrate.
- CURRENT02:18:40server4GPU0sameM204PID1085297,19810MiBprocess/card19863MiB/util28%,all3projectlocksheld,verifiednativeprogress. Sameoriginalepoch5resume/optimizer/scheduler/best/patience/fixedschedule;no restart/migration. Originalcheckpointfolder20261019_093003preserved.
- CURRENT02:18:40server4GPU1TWOforeigncontexts2495227/2507786,card16065MiB/util100%;all3projectlocksAVAILABLEbutcontextsnotemptyindependentlyforbidsharing. NoownGPUdiagnosticcontext/heldlock/newexecutionlease. Cached00:22same2contexts15667MiB/97%notcurrent.
- CURRENTthisTickboundedserver3key/strictknownhosthostnameprobe:SSHconnectionTIMEDOUT;toolcode1,rawSSHexitUNKNOWN. GPU1occupationUNKNOWN/notidleoroccupied;no verifiedtargetidentity/runtime/assets/lease. Preflightalso reportsunreachable. No resets/drivers/reboots/foreignjobactions.
- Recordedproductioncommitc31f45994f8d68b78dfe8bb4fef3f9aaefabe86e(prior,notreauditedthistick);no model/configedits. OriginalbackboneSHAa6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f.
## Open Questions And Risks
- NativeFPSphysicalsupport/mask/taskimpact/noise/efficacy/noveltyUNKNOWN;sourcewitness+fixedanchorCPUcontrolareNOTpointfeaturedeficit/admission. BatchminmaskedtaskimpactUNKNOWN. Preserveexactnativeengine/originalstrictcontrols;no handwrittenFPS.
- Bothprimaryresourcefallback2026-10-20 03:18:40Shanghai fromactual02:18:40+1h;timerNOTidleproof/scheduledrunpromise. Fourauxholdsunchangedandnotdueuntil04:37:50Shanghai;notrerevieworrepeatedhumanconfirmation thisTick.
- design_cycleexternal_resource_blocked:actualtwo preparedCUDA testsblockedbyM204GPU0,foreignGPU1,unreachableserver3. Notindependentroutesexhausted/noinformationgain/deadlineexpiry/globalpause/missingGPU1permission. No evidence-backedindependentexecutableCPUtestidentified;no fillervariant.
- Oldcontrollersops.py/study.py/observe.py/closinghelpers hardcodeexpiredtokens. Newtick_dc944b44controlleralsoexpiresafterfinish. Neverreuse;reuseonlyfrozenprotocol/sourcewithfreshguard/currentlease/runtime/assetchecks.
## Last Tick
- tick_dc944b44:onlydue2primaryresourceevidencechecks;fresh2authorizedserver4cardobservations+1boundedserver3connectivityprobe,verifiedsameM204nativeprogress. No newscientificCPU/GPU/mask/backward/trainingexperiment;allpriornegativespreserved.
- Artifacts pipeline/diagnostic_bundles/tick_dc944b44/. One malformedPowerShellSSHinvocationfailedlocallybeforeobservations;correctedstructuredSSHsucceeded. Directapply_patchcreationfailed;approvedCLIapply_patchwroteonlynewcurrentbundle. Neitherfaultwasmodelscientificfailure.
- Priorreport/memory/evidence/goal/scheduler/otherprojectsunchangedexceptsevensectionmemory+currentresearchrecords. Memorybeforebackedup. Resourceevidencehashesandoriginalcandidateevidenceverified.
- Thisprefinishsave:fullsixsectionreport/finish/FINALIZEDreceipt+ownedleaseandpendingabsenceverificationSTILLREQUIRED. DoNOTinferfinalizationfrommemory. Usageonlypartialbegin18:13:48Z->receiptlocalwindow;earlierreads/finalreplyexcluded,cachepartofinput/reasoningpartofoutput,notbill,nopostreleaseprojectwrites.
'''
assert len(memory.splitlines()) < 120
guard()
(ROOT / 'pipeline/codex_memory.md').write_text(memory,encoding='utf-8')

index = ROOT / 'pipeline/decisions/_index.md'
old_index = index.read_bytes()
env = os.environ.copy()
env['TZ'] = 'CST-8'
decision = subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL / 'log_decision.sh'),
    'cluster_project','other','Due native diagnostics remain resource-blocked.',
    'Keep frozen protocols; no sharing, restart or new training.',
    '两项主线候选已到资源复查点：server4GPU0原M204原生25/50步数增长，GPU1两项外部计算实际占用；server3密钥SSH超时，其GPU1占用未知。保留原协议和全部失败，不重复CPU测试，不造新候选、不再次索要已存在GPU1授权。',str(analysis)],
    capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=20)
assert decision.returncode == 0, decision.stderr
assert index.read_bytes().startswith(old_index)
save('decision_record_receipt.json',{'observed_at':now(),'returncode':decision.returncode,
    'stdout':decision.stdout,'stderr':decision.stderr,'existing_index_bytes_preserved':True,'timezone':'Asia/Shanghai'})
notes = save('report_notes.json',{'actions':[
    '本轮快照2026-10-20 02:13:48上海，design；已核对真实所属任务、前台模式及旧调度Disabled，仅执行一次begin。目标0.5100、历史最佳M95为0.5020、差0.0080；GPU1原授权有效，未更改科学或资源规则。',
    '预检监控M204-CPA最佳约0.4993、25/50、连续6/10次未刷新；最佳与前轮相同，未超过M95或目标。02:18:40原PID1085297原生日志Train25/50步数1519至1523/4686持续增长、mtime新鲜且无近期Traceback；不是仅凭登记或PID判断训练。精确当前全精度指标未知，未重启或迁移。',
    '02:18:40上海严格主机身份和授权UUID检查通过：server4GPU0为原M204、19863MiB/28%、三锁占用；GPU1为两项外部计算、16065MiB/100%，三项项目锁虽可用，仍不得共享。server3本轮有界密钥SSH主机查询超时，GPU1占用未知，不当作空闲或占用；未读取密码、抢卡、reset或处置外部进程。',
    '按ID续做hierarchy-native-batch-minimum-resolution和hierarchy-native-superpoint-relabeling-audit的到期资源检查，验证保留证据哈希，并追加本次真实占用证据。前者保持原4对/32表达固定query与严格1e-6控制、从pair0恢复；后者保持原生FPS/组合层级/身份逆置换及物理共成员控制。均未准入，资源计时器不代表可执行。',
    '复用已完成的562场景普查、4场景CPU固定中心控制及CPU不支持原始FPS的旧证据，未重复计算或把它们计作本轮实验。四个辅助监督候选未到复查点，保留原优先级和科学状态；未重新索要授权、恢复M201或制造同类变体。',
    '本轮实际产出为两项到期候选的资源证据更新、两张授权server4卡的实时占用核验、一次server3连接检查及M204原生进度确认；0新增科学CPU/GPU诊断、0mask对、0backward、0新模型/准入/入队/训练。一次本地SSH命令构造失败已保留并修正，未算远端故障或科学失败。',
    '用量窗口仅本轮begin(2026-10-19T18:13:48Z)至finish收据的本地记录，排除此前读取、晚到记录和最终回复；当前具体用量未知，以收据为准。缓存包含在输入、reasoning包含在输出，不重复相加、不视为账单。完整六段复用脚本事实表；本报告保存时finish尚未执行。'
], 'decisions':[
    '科学状态仍为证据不足/等待实际原生CUDA测试，没有新的机制收益或损害结论。严格保留旧full-source置换等数值失败，不放宽阈值、不修改冻结样本/query/目标/seed/schedule/FLOPs，也不把资源复查当新创新。',
    '两项主线的非GPU准备已完成，当前下一项需要原生CUDA；按真实外部占用及server3不可达保留有界资源阻塞，不声称独立路线穷尽、无信息增益或截止已到。未发现有证据支撑的独立可执行非GPU测试，不为填预算制造候选。',
    '实际授权GPU1释放并通过新当前租约、UUID/上下文/空闲、原生资产/runtime与三锁检查后，先续原分辨率pair0，再续原生重标号几何控制。server3仅在身份/连接/原生资产/独占条件完整恢复后使用；M204自然继续，不自动重启/迁移/驱逐，不需要新的GPU1授权。'
]})
print(json.dumps({'analysis':evidence(analysis),'notes':evidence(notes),'resource_retry_after':retry.isoformat(),
    'candidate_ids':list(IDS),'pending_count':6,'new_admissions':0,'finish_still_required':True},ensure_ascii=False,indent=2))
