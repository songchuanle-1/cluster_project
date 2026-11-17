# Codex Research Memory

## Goal And Phase
- owner01a159c5-29ab-7a22-ba7f-e79174757253实际环境/execution_mode一致。前轮16b87793 FINALIZED/released与headless lock/pending消失已核验。当前86e41faaff0b4fa1965a8b90d7636631 DESIGN，上海10-22 04:12:34快照/原deadline05:12:34（UTC20:12:34.701059/21:12:34.701059）；begin先监控派发，2running/0waiting，无新terminal/operational issue。
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95champion.5020/gap.0080，baseline.4894；Phase1 hierarchy→inst_feats→query/masks主线，辅助supervision不取代主线。seed1999/epochs50/maxiters70/default10G不变，禁止调参/门系/语言路由/大QKV/禁用route/残差系及历史重开，Phase2仍需确认。
- Standing pipeline/authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8授权本项目代码/YAML/真实检查/版本/安全同步/入队训练，不重复确认常规操作；不解除历史修订、禁用项、数据/seed/schedule及资源边界。
- 最新直接人类“gpu1可以使用”覆盖此前GPU0-only对server4GPU1的限制，当前server4[0,1]每卡1任务；新grant pipeline/authorizations/server4_gpu1_reenabled_20261021_gpu1_reenable_152505.json SHA30f17c5bcb66782a255d7eed4bb00277e807bfea4e64a48a499ab749fadd2fa7。server3/server6仍allowed[]/dispatchfalse，不恢复旧fallback。Windows Pipeline-cluster_project仍Disabled，调度/goal/科学门槛未改。

## Champion And Baseline
- M205-MDC native自行earlystop：原日志明确epoch26/no-improve10/best.4872；比M95 .5020低.0148、比baseline .4894低.0022。精确PID3842306消失及GPU0无context实测，canonical可恢复archive已完成，state=done_earlystop/stage=complete；这是该实现负训练结果，不是整条hierarchy机制被证伪。
- M206-CGCA GPU1原full-resume保持：04:13:55 PID732137/starttime21298582/--resume argv/cwd匹配，native15/50 4506→4507、log新鲜.013s；04:12 monitor Best.4899@15/noimprove1/10（序列.4706/.4836/.4878/.4899/.4841）。该指标为在训进度，不判提前收敛或改参数，原恢复best.4751223027706146历史分开。
- M207-HAP GPU0原进程保持：04:13:55 PID979955/starttime21613920/cwd/argv匹配，native7/50 1200→1201、log新鲜.47s；04:12 monitor Best.4603@7/noimprove0/10。完整训练稳定性与效益仍待终态，不依早期验证改机制/选参。
- HAP标准计数9.762944066G vsM95 9.762532428G；同bs1/lang1/warmup20/repeat100/input/原3fvcore文件：median46.254797 vs43.596659ms(+6.097%)，P9064.774761 vs60.729895ms(+6.660%)，参数均157484090。预测peak936769536 vs936763392bytes(+.000656%)；TRAIN同2批peak7426868224 vs7418928128bytes(+.1070%)，非full-run worst-case保证。
- HAP pinv2/index_add等unsupported完整披露，标准计数不是完整算子成本；资源mode无spy，实际计时/显存包含执行。GPU1有M206并行，不能横比旧M205 idle-host绝对延迟。旧M2059.7331723G及M2069.764703308G等原资源证据仍保留。

## Active Hypotheses
- M208-HRC stable hierarchy-bottom-up-refined-token-composition，localcommit9e543af623acd7fa9bd4a3f81ce79c932e98774a（仅8独立model源+1原生YAML）。h0=μ0+F0(LNμ0)，u1=mean_ids1(h0)，h1=u1+F1(LNu1)，u2=mean_ids2(h1)，h2=u2+F2(LNu2)；原3FFN各一次、rawbanks/FPS/IDs/CSORT/HCG/最后inst更新保持。原9hash/static准备本轮保持；native/资源NOT_RUN，stageblocked/resumevalidation/exclusive_gpu_slot，04:13:55两卡原任务实证，retry21:13:55UTC或实际空卡事件。
- HRC持久native准备已冻结到tick_86e41faa/hrc_native_prepare：worker37782c1ae1ea9cb2f7bb77d59c7b8aff926438fbac827106f94d8c8fa396ef01，runtime4737e6f08ebb202cec073819ba95bcb94f78fc93ed1b4d5e214ef69d1f9ef0e4，template ea756a6b95861ac65e3a535e9cfa5743151d965d8aed4876599bdab36b414509。mdc/pce/root独立静态检查无阻断，原resources函数AST相同/9asset精确9e；PREPARED_UNEXECUTED，无active manifest/lease/staging。未来owner需当前context/deadline/whitelist/runtimeHEAD/asset+双idle/3flocks后才可GPU。
- M207-HAP stable hierarchy-affine-coarse-to-fine-prolongation，commitf51823bbddf0f8095a9a5813bf1f8169e3d7edb0，原8独立源+nativeYAML内容不变。3原FFNs后coarse→middle→fine：D=occupied child centers−组均值，A=pinv(D.TD,hermitian=True)@(D.T@原refined child)，新child=更新parent+DA，返回fine/middle、coarse外部保持。新operator0参数、无learned gate/child residual/QKV/seed扫参，原FPS/featurepool/CSORT/HCG/末尾inst_feats路径保持。
- occupied由真实point沿原ids向上传播，排除padding/空ID；几何FP32 detached、特征RHS/detail在autograd。训练首次真实4scene/16expression同两批与M95指纹匹配；HAP losses9.6735115/13.9038401，对照9.5291233/13.9095869，无效果推断。
- native原train.train+原loader两步完成：每步618个observed gradient tensors全部finite，3FFNs均非零weight grad且逐级初末hash改变。新operator两次forward/backward，3输入/2输出及fine/mid非恒定、coarseparent梯度实测非零finite，32次actual G/pinv输入返回全finite、原调用恰1次/default tolerances/hermitianTrue/原函数finally恢复、observer完整。
- HAP历史native材料tick_008137b4/hap_prepare，reviewed worker_v2 SHAffb2e09a53f3e860b398b435674ca0800b9641f5e48391d1af0d3098b8698a73；其中runtime/manifest/execution_lease绑定008137b4/原UTC17:03:27deadline，已过期不得直接运行。原正向实测证据仍只支持其不变source/version历史，不能冒作当前fresh权限。
- HAP收据pipeline/admissions/M207-HAP.json SHA61aded24398cb95d2296c3fc3fffeeb6e2960e6e9646fffc2d18c466ea564c59，四门native/resources/constraints/independence及standing授权真实绑定，效益UNKNOWN。stage=training/training_status=running；首筛保持原数据/pretrain/seed/50epochs/maxiters70，未从trainedM95全模初始化。
- M206-CGCA stable hierarchy-coarse-conditioned-fine-channel-attention，原898ff63a2cf63d3895a9e86c0ee3d1e5b672b335/admission不变、stage=training/running_resumed；coarseGram→fine channel算子0新参数，旧GPU1 PID3873690暂停/GPU0 waiting/最新GPU1恢复历史完整保留。

## Closed Or Failed Directions
- M205-MDC（hierarchy-middle-directional-token-convolution）已complete/done_earlystop .4872@native26/50，保留59013e132241322054f1906e771aa78b81c48da6原准入/launch proof及负结果。精确原run35MB日志经remoteSHA匹配拉至Checkpoints/server_4/exact_m205_20261021_050739；调用canonical finalize_task归档，不kill、不人为增加deathwatch计数、不改阈值。terminal日志不意味着last.pth保存到该epoch，checkpoint留远端。
- 8旧hold保持：4supervision辅助scope、2measurement实现/未定hold（同输入FP32差1.907e-6>1e-6，不是机制反证），PCE默认2+额外1已耗尽/2.861e-6失败与13.86x延迟，RSTR默认2已耗尽/committed R2 mean1.027033878e-6>1e-6。旧passed或独立重算9.536743e-7不清最终RSTR失败，PCE不自动R4/RSTR不R3；RSTR授权9文件localcommit36b59daa不是新修订。M201不自动恢复。
- 最近原生旧hold复核仍tick_f8150790，无新保门修复/授权；本轮tick86e41faa/held_route_boundary_check.json仅有界程序核8旧记录逐项保持，当前human只有heartbeat无新reopen/revision/scope许可。到期不解除失败/scope/修订hold；不重跑旧诊断。旧complete历史SERVERS冻结同SHA60cba26a的tick_899d59f1/SERVERS.before.yaml，不重写原结果或验证器。
- 上轮有界备用审查未形成独立候选；本轮定向核原M95与REAG_CASC/lite_agg/MFP/CCP实际源，形成HRC不同的新依赖图。有限历史核对不代表全历史/文献新颖性或收益；原pair-edge/moment/改M205邻域等未重开，未注册ILA新诊断。
- 首次HAP派发被错误queued候选标签阻止（未sync/启动）；纠正为canonical deployment后同原gate通过。首次额外只读部署YAML比较忽略允许work_dir映射而失败；确认唯一该差别后新proof通过。两个原错误证据保留，无模型修改/重训/门槛放宽/实现修订消耗。

## Running And Queue
- server4 pinned192.168.1.115/dl04-MS-7E06，allowed[0,1]/max1card；GPU0 UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c，GPU1 UUIDGPU-7f82edb9-f620-8045-caea-a75232265cd1。root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，现HEADf51823bb，仅ff9个HAP新增文件；common/M206既有源码未改，未传输本地脏RSTR/旧脚本/未跟踪PCE/BCCA文件。
- 三账保持M205 complete/done_earlystop，M207-HAP running/GPU0/PID979955与M206-CGCA running/GPU1/PID732137，launch_verifiedtrue。04:13:55两卡NVML各仅原context，显存GPU0 19793MiB/GPU1 19801MiB、native步骤递增。HRC仍仅candidate资源hold，训练queue waiting0。
- HAP正式config configs/Quard/ctf_hcg_csort_hap/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap.yaml；新log root/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap_20261022_001959.log。formal launch仅允许work_dir路径适配，所有其他YAML值与control相同；测试/部署8源hash一致，新训练checkpoint是否已保存UNKNOWN。
- M206 log仍root/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca_20261021_232722.log；原fixed resume /data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth SHA2e11ea38ba81b657301a34efc11483455fb1f9eeb83a5f4d52fbc40ffb4669d7，CPU完整optimizer642states5groups/scheduler/meta保留，latest GPU1绑定proof见manual_ops/20261021_gpu1_reenable_152505。
- canonical cluster_resume.py已严格支持server4GPU0/1（116相关离线+独立22专门tests PASS），当前白名单/任务卡号/双hash人类授权proof/CPU完整state/source/checkpoint均须一致，无cold fallback。M206正跑版本仍898ff，不能因root新HEADf518而改写其身份；若将来再resume，旧exactHEAD合同会阻止直接冒用newHEAD，必须重新核精确admitted source，不能冷启动或放松guard。
- server3/server6仍禁用；localHEAD仍9e543af、remoteHEAD沿用f518历史（本轮未sync/切换）。HRC9源/YAML及28个既有脏/未跟踪文件逐字节保持、index空；无reset/clean/stash/force/sudo/密码读取。本轮snapshot capacity2/running2/waiting0/creation2，实际0新candidate/0model修订/0commit/0准入/0queue/0launch。

## Open Questions And Risks
- HRC worker里的actual TRAIN2步、coarse对fine/mid FFN依赖probe与1e-6 mean参考都尚未执行。probe设计用autograd.grad/retain_graph并隔离native hooks，检查.grad对象/version/值、optimizer/scheduler和CPU/CUDA RNG不变；失败应留实证，不把静态当native PASS。smoke峰值含probe/observer开销，不称纯TRAIN内存；原bs1/warm20/repeat100 predict资源模式无probe，纯TRAIN峰值UNKNOWN仅支持项，不加新准入门。
- HRC只有新信息流预期，参数增量0依据构造不变、真实资源未知。每batch仅排除padding，内部empty-ID child槽原等权mean保留，FFN bias可传播父层；重复池化可能丢细节/重复尺度。下一步必须原生解析精确HRC模块（resolver有默认fallback风险）+实际TRAIN两步finite loss/backward/新parent梯度+同M95原口径FLOPs/计时/内存，不能拿静态检查替代准入。原native worker需fresh token/deadline/assets/slot/locks，旧lease不得重放。
- HAP实测max|Gplus|1308527.125，max GGplus幂等误差.114782333；finite/native gate不证明条件良好、精确投影、完整期稳定或准确率收益。正规方程平方条件数/defaultFP32cutoff风险保留，禁止为了PASS加ridge/改精度/调阈值；无预注册门不事后捏造失败阈值。诊断matrix_rank0/1/2/3是额外API，不是backend pinv保留秩。
- rank(D)<=min(3,nchild−1)，单child/零D parent-only；≤4仿射独立时detail=Hchild−mean，不能说每组独特几何过滤。组token均值parent不等于pointmass守恒，不套用RSTR声称；可能抹高阶语义/伤小目标。细/中FFN常数bias梯度可0，已按非恒定weight/path观测。
- 保留M205负训练结果，HAP与M206均待正式验证。无新验证挑参/换seed、无历史重开或额外数据/标注授权。下一轮先实际监控两卡/终态，按新快照决定储备；旧tick lease/stage不可重放。

## Last Tick
- 本轮tick_86e41faa已先begin监控/派发；04:13:55 strict known-host/pinned hostname/physicalUUID/NVML/原PID/starttime/argv/cwd/native日志实证，GPU0 HAP7/50 1200→1201、GPU1 CGCA15/50 4506→4507，两卡原运行保持，无新终态/失败/需要人处理项。
- 继续已有HRC，完成持久native worker/runtime/template与原8源+YAML拷贝准备；没有新生产模型代码或Git版本。new_variant及mdc/pce审查后root实跑validate_static.py/AST/11诊断hash/无顶层torch/原resourcesAST/无activelease检查通过；这是工具准备，native/backward/资源效益NOT_RUN。
- 当前tick_attempt绑定generated_at2026-10-21T20:12:34.701059Z及HRC fresh resource_check/blocked真实证据；HRC追加当前worker准备和资源证据，1既有candidate准备推进，0新candidate/0修订/0commit/0准入/0queue/0launch/0terminal，8旧hold完整不动。next_batch决策20261022-042252留档，不制造全局冷却或等待审批。
- 下步真实授权空卡出现后，root新建当前guard/manifest/lease/stage并核资产、执行双target实际两步和原资源配对；通过才准入与派发。保持quiet（在训正常进度与工具准备不构成用户需立即知道的变化）。当前86e41faa收尾以实际report/finish和receipt为准，不预写PASS；须核FINALIZED/released与headless锁/pending消失，释放后不写项目。
