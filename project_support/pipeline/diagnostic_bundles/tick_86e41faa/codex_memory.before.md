# Codex Research Memory

## Goal And Phase
- owner01a159c5-29ab-7a22-ba7f-e79174757253实际环境/execution_mode一致。前轮008137b4 FINALIZED/lease released及headless lock/pending消失已核验。当前16b87793a9414372a17cfa776ccdd8c9 DESIGN，上海10-22 02:03:15快照/原deadline03:03:15（UTC18:03:15.148972/19:03:15.148972）；begin先监控派发，2running/0waiting，无新terminal。
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95champion.5020/gap.0080，baseline.4894；Phase1 hierarchy→inst_feats→query/masks主线，辅助supervision不取代主线。seed1999/epochs50/maxiters70/default10G不变，禁止调参/门系/语言路由/大QKV/禁用route/残差系及历史重开，Phase2仍需确认。
- Standing pipeline/authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8授权本项目代码/YAML/真实检查/版本/安全同步/入队训练，不重复确认常规操作；不解除历史修订、禁用项、数据/seed/schedule及资源边界。
- 最新直接人类“gpu1可以使用”覆盖此前GPU0-only对server4GPU1的限制，当前server4[0,1]每卡1任务；新grant pipeline/authorizations/server4_gpu1_reenabled_20261021_gpu1_reenable_152505.json SHA30f17c5bcb66782a255d7eed4bb00277e807bfea4e64a48a499ab749fadd2fa7。server3/server6仍allowed[]/dispatchfalse，不恢复旧fallback。Windows Pipeline-cluster_project仍Disabled，调度/goal/科学门槛未改。

## Champion And Baseline
- M205-MDC native自行earlystop：原日志明确epoch26/no-improve10/best.4872；比M95 .5020低.0148、比baseline .4894低.0022。精确PID3842306消失及GPU0无context实测，canonical可恢复archive已完成，state=done_earlystop/stage=complete；这是该实现负训练结果，不是整条hierarchy机制被证伪。
- M206-CGCA GPU1原full-resume进程保持：02:15:16 PID732137/starttime21298582/--resume argv/cwd匹配，native13/50 609→610，原log新鲜.18s；本轮monitor02:03 Best.4836@12，稍后原生新验证仅打印3位mIOU .488，精确新best未额外读取。恢复历史best.4751223027706146与新验证分开，不判提前收敛。
- M207-HAP GPU0原进程保持：02:15:16 PID979955/starttime21613920/cwd/argv匹配，native4/50 422→423，原log新鲜.41s；新验证原生日志仅打印3位mIOU .406，精确best未额外读取。完整训练稳定性与效益仍UNKNOWN，不依据早期验证改机制/选参。
- HAP标准计数9.762944066G vsM95 9.762532428G；同bs1/lang1/warmup20/repeat100/input/原3fvcore文件：median46.254797 vs43.596659ms(+6.097%)，P9064.774761 vs60.729895ms(+6.660%)，参数均157484090。预测peak936769536 vs936763392bytes(+.000656%)；TRAIN同2批peak7426868224 vs7418928128bytes(+.1070%)，非full-run worst-case保证。
- HAP pinv2/index_add等unsupported完整披露，标准计数不是完整算子成本；资源mode无spy，实际计时/显存包含执行。GPU1有M206并行，不能横比旧M205 idle-host绝对延迟。旧M2059.7331723G及M2069.764703308G等原资源证据仍保留。

## Active Hypotheses
- 新M208-HRC stable hierarchy-bottom-up-refined-token-composition，localcommit9e543af623acd7fa9bd4a3f81ce79c932e98774a（仅8独立model源+1原生YAML）。h0=μ0+F0(LNμ0)，h1=mean_ids1(h0)+F1(LN mean_ids1(h0))，h2同理由refined h1组成；原3FFN各一次，原rawbanks/FPS/IDs/CSORT/HCG/最后inst_feats注入保持。静态9hash/AST/compile/YAML独立和有限历史核对通过；native/反传/资源NOT_RUN，stageblocked/resumevalidation/独占卡资源hold，02:15:16两卡原任务实证，retry19:15:16UTC或真实空卡事件。
- M207-HAP stable hierarchy-affine-coarse-to-fine-prolongation，commitf51823bbddf0f8095a9a5813bf1f8169e3d7edb0，原8独立源+nativeYAML内容不变。3原FFNs后coarse→middle→fine：D=occupied child centers−组均值，A=pinv(D.TD,hermitian=True)@(D.T@原refined child)，新child=更新parent+DA，返回fine/middle、coarse外部保持。新operator0参数、无learned gate/child residual/QKV/seed扫参，原FPS/featurepool/CSORT/HCG/末尾inst_feats路径保持。
- occupied由真实point沿原ids向上传播，排除padding/空ID；几何FP32 detached、特征RHS/detail在autograd。训练首次真实4scene/16expression同两批与M95指纹匹配；HAP losses9.6735115/13.9038401，对照9.5291233/13.9095869，无效果推断。
- native原train.train+原loader两步完成：每步618个observed gradient tensors全部finite，3FFNs均非零weight grad且逐级初末hash改变。新operator两次forward/backward，3输入/2输出及fine/mid非恒定、coarseparent梯度实测非零finite，32次actual G/pinv输入返回全finite、原调用恰1次/default tolerances/hermitianTrue/原函数finally恢复、observer完整。
- 当前fresh材料tick_008137b4/hap_prepare，reviewed worker_v2 SHAffb2e09a53f3e860b398b435674ca0800b9641f5e48391d1af0d3098b8698a73逐字节未改；native_runtime/manifest/execution_lease绑定本轮token/原deadline/物理GPU0 UUID958e741a/3flocks/双空闲检查，核验后才importtorch。独立mdc_review/pce_audit均静态及实测只读复核，无技术门阻断。
- HAP收据pipeline/admissions/M207-HAP.json SHA61aded24398cb95d2296c3fc3fffeeb6e2960e6e9646fffc2d18c466ea564c59，四门native/resources/constraints/independence及standing授权真实绑定，效益UNKNOWN。stage=training/training_status=running；首筛保持原数据/pretrain/seed/50epochs/maxiters70，未从trainedM95全模初始化。
- M206-CGCA stable hierarchy-coarse-conditioned-fine-channel-attention，原898ff63a2cf63d3895a9e86c0ee3d1e5b672b335/admission不变、stage=training/running_resumed；coarseGram→fine channel算子0新参数，旧GPU1 PID3873690暂停/GPU0 waiting/最新GPU1恢复历史完整保留。

## Closed Or Failed Directions
- M205-MDC（hierarchy-middle-directional-token-convolution）已complete/done_earlystop .4872@native26/50，保留59013e132241322054f1906e771aa78b81c48da6原准入/launch proof及负结果。精确原run35MB日志经remoteSHA匹配拉至Checkpoints/server_4/exact_m205_20261021_050739；调用canonical finalize_task归档，不kill、不人为增加deathwatch计数、不改阈值。terminal日志不意味着last.pth保存到该epoch，checkpoint留远端。
- 8旧hold保持：4supervision辅助scope、2measurement实现/未定hold（同输入FP32差1.907e-6>1e-6，不是机制反证），PCE默认2+额外1已耗尽/2.861e-6失败与13.86x延迟，RSTR默认2已耗尽/committed R2 mean1.027033878e-6>1e-6。旧passed或独立重算9.536743e-7不清最终RSTR失败，PCE不自动R4/RSTR不R3；RSTR授权9文件localcommit36b59daa不是新修订。M201不自动恢复。
- 最近有界旧hold复核tick_f8150790/due_hold_readonly_review.json，无指定新授权wake或保门修复；本轮资源开放不解除科学/scope/修订hold。旧complete历史SERVERS引用冻结到同SHA60cba26a的tick_899d59f1/SERVERS.before.yaml，不重写原结果或验证器。
- 上轮有界备用审查未形成独立候选；本轮定向核原M95与REAG_CASC/lite_agg/MFP/CCP实际源，形成HRC不同的新依赖图。有限历史核对不代表全历史/文献新颖性或收益；原pair-edge/moment/改M205邻域等未重开，未注册ILA新诊断。
- 首次HAP派发被错误queued候选标签阻止（未sync/启动）；纠正为canonical deployment后同原gate通过。首次额外只读部署YAML比较忽略允许work_dir映射而失败；确认唯一该差别后新proof通过。两个原错误证据保留，无模型修改/重训/门槛放宽/实现修订消耗。

## Running And Queue
- server4 pinned192.168.1.115/dl04-MS-7E06，allowed[0,1]/max1card；GPU0 UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c，GPU1 UUIDGPU-7f82edb9-f620-8045-caea-a75232265cd1。root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，现HEADf51823bb，仅ff9个HAP新增文件；common/M206既有源码未改，未传输本地脏RSTR/旧脚本/未跟踪PCE/BCCA文件。
- 三账保持M205 complete/done_earlystop，M207-HAP running/GPU0/PID979955与M206-CGCA running/GPU1/PID732137，launch_verifiedtrue。02:15:16两卡NVML各仅原context，显存GPU0 19791MiB/GPU1 19801MiB；native步骤递增。M208仅候选resource hold，未入训练queue，waiting仍0。
- HAP正式config configs/Quard/ctf_hcg_csort_hap/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap.yaml；新log root/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap_20261022_001959.log。formal launch仅允许work_dir路径适配，所有其他YAML值与control相同；测试/部署8源hash一致，新训练checkpoint是否已保存UNKNOWN。
- M206 log仍root/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca_20261021_232722.log；原fixed resume /data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth SHA2e11ea38ba81b657301a34efc11483455fb1f9eeb83a5f4d52fbc40ffb4669d7，CPU完整optimizer642states5groups/scheduler/meta保留，latest GPU1绑定proof见manual_ops/20261021_gpu1_reenable_152505。
- canonical cluster_resume.py已严格支持server4GPU0/1（116相关离线+独立22专门tests PASS），当前白名单/任务卡号/双hash人类授权proof/CPU完整state/source/checkpoint均须一致，无cold fallback。M206正跑版本仍898ff，不能因root新HEADf518而改写其身份；若将来再resume，旧exactHEAD合同会阻止直接冒用newHEAD，必须重新核精确admitted source，不能冷启动或放松guard。
- server3/server6仍禁用；localHEAD新增HRC9文件到9e543af623acd7fa9bd4a3f81ce79c932e98774a，remoteHEAD仍f518（本轮未sync）。28个既有脏/未跟踪文件逐字节保持、git index为空，无reset/clean/stash/force/sudo/密码读取。本轮snapshot capacity2/running2/waiting0/reserve_budget2/creation2，实际1新准备/0准入/0queue/0launch。

## Open Questions And Risks
- HRC只有新信息流预期，参数增量0依据构造不变、真实资源未知。每batch仅排除padding，内部empty-ID child槽原等权mean保留，FFN bias可传播父层；重复池化可能丢细节/重复尺度。下一步必须原生解析精确HRC模块（resolver有默认fallback风险）+实际TRAIN两步finite loss/backward/新parent梯度+同M95原口径FLOPs/计时/内存，不能拿静态检查替代准入。原native worker需fresh token/deadline/assets/slot/locks，旧lease不得重放。
- HAP实测max|Gplus|1308527.125，max GGplus幂等误差.114782333；finite/native gate不证明条件良好、精确投影、完整期稳定或准确率收益。正规方程平方条件数/defaultFP32cutoff风险保留，禁止为了PASS加ridge/改精度/调阈值；无预注册门不事后捏造失败阈值。诊断matrix_rank0/1/2/3是额外API，不是backend pinv保留秩。
- rank(D)<=min(3,nchild−1)，单child/零D parent-only；≤4仿射独立时detail=Hchild−mean，不能说每组独特几何过滤。组token均值parent不等于pointmass守恒，不套用RSTR声称；可能抹高阶语义/伤小目标。细/中FFN常数bias梯度可0，已按非恒定weight/path观测。
- 保留M205负训练结果，HAP与M206均待正式验证。无新验证挑参/换seed、无历史重开或额外数据/标注授权。下一轮先实际监控两卡/终态，按新快照决定储备；旧tick lease/stage不可重放。

## Last Tick
- 本轮tick_16b87793留档：初始及02:15:16两次strict known-host/pinned hostname/physicalUUID/NVML/原PID/starttime/argv/cwd/native日志只读核验；两卡原运行保持，无终态/故障。最新native HAP4/50、CGCA13/50，早期验证仅3位打印不能冒充精确best。
- 实现M208-HRC独立9文件并完成agent+root两套静态源/YAML核验；本地精确commit9e543af，保护28个既有脏/未跟踪文件，未sync/占GPU/入队。准备证据hrc_prepare/{preparation,static_validation,independent_review,version,native_resource_block}.json及implementation.md完整冻结。
- tick_attempt绑定当前generated_at和HRC真实resource_check/blocked证据（两张当前授权卡已有原native任务，max1/card）；1新候选resource hold、0准入/0训练队列/0新启动/0实现修订。不是模型失败/全局停研/旧hold解锁；next_batch决策20261022-021649已记录。
- 仍需在真实授权空卡时对精确HRC版本做原生两步/依赖梯度/资源；通过才收据、入队和尝试派发，已有standing授权可复用。当前前台16b87793收尾以实际report/finish及receipt为准，不预写PASS；须核FINALIZED/released和headless锁/pending消失，释放后不写项目。
