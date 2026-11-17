# Codex Research Memory

## Goal And Phase
- 最新接管e245536aa26d4da0bf5db80eede47358，actual target/thread01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-26T05:37:01.862189+00:00/实际deadline2026-10-26T06:37:01.862189+00:00。因人类GPU1撤回先合法finish45eb、manual资源0后新begin；本次操作stop仍05:52:30，不用新lease延时。finish以实际receipt为准。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020/gap.0080，baseline.4894。Phase1不同层级分工→inst_feats→query/masks，supervision辅助，Phase2需人工确认。
- seed1999/epochs50/max_iters70/原YAML/data/pretrain/optimizer/precision不变；原同口径10G、bs1/lang1/warm20/repeat100 median/P90/fullunsupported，峰值显存+15%需≥+.003mIoU。禁止调参、gate/cag/cfe/layerscale、语言路由、大QKV/N²attention、重复inst注入、旧rejected改名、无图改变微调。
- standing pipeline/authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖普通实现/测试/相关版本/安全同步/准入训练，不授旧hold重开/额外修订/受保护恢复/扩大资源/改调度。
- 最新直接人类不用gpu1已应用：SERVERS SHA2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1仅server4physical[0]/max1；authorizations/server4_gpu0_only_20261026.json SHA94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09。旧GPU1 grant仅历史合法依据，不再授权未来GPU1计算；M206暂停/其他allowed[]/调度Disabled保持。

## Champion And Baseline
- M95仍.5020；M205-MDC26/.4872、M207-HAP授权epoch18恢复后31/.5002、M208-HRC31/.4901、M209-PSBR23/.4969、M210-PSNC31/.5001、M211-BTC31/.4914均自然earlystop且未超M95。不调参重跑或整体否定hierarchy。
- BTC在前336已canonical archive_id73e3038e744b4f6a9bffb68a7b43e8f8，原source00e2b18c6b8d568a64edb496e6979d766440883c/receipt93756329…/launch保持；42038211B原log本远SHA2b4032d0b705ae7f5e8ebdba81f14d5ed7eb55da491b4b9fec2ba78342aba38c。前6bdb snapshot仅识别前336归档；本轮无新终态，不重复archive。
- HAP原epoch19 DataLoader AttributeError根因UNKNOWN，epoch18恢复授权已消费；原crash/snapshot/prior_runs保留。既有负结果/恢复/版本/归档细节见前336 memory及其证据，不重写或再启动。

## Active Hypotheses
- M213-BFC原run在TRAIN20/50 step3832/4686共享DataLoader scatter overlap RuntimeError中断，canonical crashed archiveb91b3ba11671451bb28f39dc3cc3f2c7。科学source48fc/原receipt812454/launch/log均保留，非BFC机制否定；原日志max.499为3dp。CPU核last.pth SHA24b3424f… epoch19/optimizer+scheduler/best.4992169439792633/noimprove4；完整1151tensor finite，640optstate/5group/maxstep89034。RNG/sampler/失败输入未复现，不能称续3833；原native恢复仍需具体兼容source计划及BFC专属人类授权，不借其他grant，不自动恢复。
- BFC前336实际4nativearms terminal/rc0；两原TRAIN loss9.5372838974/13.9084777832，共同843张量/156958522参数/hash04231c23…，原2batch配对；64n3多stage/56nonpower/四W quadrant原loss非零有限grad+每步slice更新。逐call/row/half零合法，singleton/empty/pad NOT_EXERCISED。实际审b8fa/43af/419f及4reconcile/status历史保持，不拿旧诊断lease再用。
- BFC真资源9.775377484G vsM959.762532428G，参数157221178（−262912）；同GPU0 median42.218151968 vs42.311575031ms（−.2208%），P9062.910521450 vs60.952819872ms（+3.2118%更慢），预测allocated−.1121%，observer-smoke+.00214%，15%条件未触发。fullunsupported保持，pureTRAIN峰值/新颖性/准确率未知。
- 前336仅已测BFC9A ff-only primary/safe runtime同步至48fc；首dispatch normalized UUID-map KeyError发生在0intent/transport，新受审raw-map执行copy才一次canonical Popen，实际result9e453fb4/最终审069833d3…；本轮不重放、不推进公共源或修改BCR8/YAML/原进程。保护28/index/账实际核保持。
- M212-BCR原run native earlystop27/patience10/best.4995，canonical archive5d060afca23d43deb4ae63525c00ff3d，未超M95.5020；原scientific11a/receiptb853/public48fc下8源/YAML/launch保持，无重启。
- M214-CTS已技术准入、FIFO waiting GPU0，精确source4e80006047d5cb3dcdfb9c1102e02c33f354a07d/单父48fc与原9A/YAML。receipt pipeline/admissions/M214-CTS.json SHA5416d5e…；当前无PID/无launch，实际GPU0占10743MiB，等待真空闲。历史45eb GPU0四真臂/a33c/5d2f保持原owner/版本，只current部署门更新，不重标或重跑历史。
- CTS同父几何cycle同步old own/±3^r，经共享3C→C/原GELU，最小3^k>=n轮；重复minus私有0，n1W[x,0,0]，无支持/pad delta0，nC状态保留。原LN/cfskip/finecoarse/rawmean/FPS/IDs/CSORT/HCG/单inst保持。dense3tap dilated circular Conv1D家族整体图替代，非新覆盖/单因素因果/新颖/重开MDC。
- 前6b CTS版本绑定operational packet tick_6bdbcf77/cts_operational_prepare/preparation.json SHA51cbc658fcf5877a0b46776e361adb99d36d4551841aacdf7559ac6d46c937d6；nativeaab40a87/worker原03329/独审0fc1425f/61真mock+69ASThash+7真CLI拒绝。新copy绑定4e8与期望live48fc，原ff7 DRAFTTrue/code-parent-null及失败元数据保持；全部runtime函数AST/原资源口径不变，无原地启用旧包。
- 前6b root单flag CTSanchor新copy310ed9显式exact0fc审后，实际只静态release eaa3 bytecopy+CTS历史/外锚；actualguard a9946e21核当前owner/context/rawUUID/版本/原deadline，prepare0/1精确registeredbusy拒绝，14非法入口+deadline拒绝，0transport/process/network/Torch/active。原8source/YAML/primary28/index/13账保持；独审另附。该结果不是NVML idle/原生两步/资源PASS。
- CTS未来沿原7036协议，在fresh真实空卡绑定后做M95/CTS固定TRAIN2+原资源；须3distinct/multiround/r>=1与三W input块每step原loss有限非零grad+实际update。缺覆盖INCONCLUSIVE，不换样本/seed/precision/阈值；内部mix call/row合法零，whole-helper input/output沿03329既有非零后验。native/resource/efficacy均未测，无M214receipt/queue/训练。
- M215-BEC现validation，实际隔离source9b6782f44ca7f2c8ac35baea01dfd070314b5701/单父48fc302c3c02ffef0b241be3593c386b6b65a72e，9blob精确等于原2d06；primary/runtime仍48fc。它与pendingCTS4e8为兄弟，不假定相互ff；原2d06及native322c的null版本声明保持，不回填。双跨层joint child+parent→2C/GELU各split u/v，v按true child等权上行；原coarse LN/FFN组合后，两2C→C/GELU向middle/fine回传，原三cfskip/HCG/一次inst回写。rawmeans/FPS/IDs/CSORT与六原model文件逐字保持，coarse空/unsupported bias mask0。
- BEC当前真实stdlib生产AST plan133cases、forward provenance42cases、14拒绝/10643assertions；不是Torch/GELU数值/autograd/原数据/10G。有限CCP/REAG_CASC/HRC/lite_agg源近邻审及最终实现独审留档，不称一般新颖/attention/新覆盖/单因素收益，不恢复M206。
- BEC源码推断新4Linear787968、替代2FFN1051136、净−263168；fine/middle denseMAC各6C² vs8C²，coarse原8C²，linear metadata grouping；全口径FLOPs/CPU开销/时延/显存均未知。未来实际派生共同参数集合，不照抄843；核2U双split、4maps及原coarse loss路径grad/update，当前不入队。

- 前f86d CTS只读四臂结果checker已冻结并独审：pipeline/diagnostic_bundles/tick_f86d1cfa/cts_execution_review_prepare/preparation.json SHA82da6073da4044c7f666ca70519b3b3ee796e3ad536698180a581823d51e9beb；只本地软件正确性/缺失拒绝测试，actual_native_results_reviewed=false。当前catalog freshguard37a81144…核20:07原owner/context/deadline与两registeredbusy、0transport/active，不是原生资源PASS。
- 前f86d BEC禁用/无版本native工具冻结并独审：pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_prepare/preparation.json SHA322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff；复用原M95 setup/TRAIN2/criterion/optimizer/原resources整函数AST，只读观测原production split/mean/coarse/down/单inst路径。原2d06/6555不改，source/parent/10active null、DRAFTTrue；实际native/resources/原common/batch配对未知，不能原地填旧包或用软件fixture代签。

- 前b5dc实际BEC隔离保存证据pipeline/diagnostic_bundles/tick_b5dc39b4/bec_version_execute/isolated_source_version.json SHAe2f3439ead898c3f8acdc8d54d929720515aa5783650850ae2c8d20666c30f44，独审cb7ec9d8…确认32项/实际Git父tree/blob/clean与全部保护。仅新本地9A子提交，无主线ff/部署/native/queue；source母本2d06及旧native322c23文件全部原字节，native_execution_code_commit仍null。

- 前521 BEC新版本绑定op420022/原生pre8e2d（source9b67、parent/live48fc，worker7e及6555原字节）已61mock/71ASThash/7CLI拒绝并独审c8ee1830。root只静态release b551字节copy与新外锚，旧322c全23文件/null/DRAFTTrue及原history保留；新10active仍null，无native执行绑定。
- 前521 BEC实际localguard24c8719a…验证current owner/context/rawUUID/version/原deadline和新catalog，2卡registeredbusy beforetransport、14invalid/deadline、0process/network/Torch/active；实际anchor独审另附。新四原结果checkerpipeline/diagnostic_bundles/tick_521a6f59/bec_execution_review_prepare/preparation.json SHA5f739a385ffb8032b31b95e170f9380bbd3962df5b04fc2b923eb5d3af34956f及独审已具备，5module/12block/common实际名/原资源门不改，软件fixture不代签原生。

## Closed Or Failed Directions
- 本轮旧9到期，仅一次有界metadata复核pipeline/diagnostic_bundles/tick_509e9191/held_boundary_check.json SHA6b87e37d8d7dc31f13540774023a524cfd18db642b556ba458fa191bedc257a7；旧8canonical记录/声明path-hash字符串和授权目录metadata及M206暂停语义无新动作，未读或重探655正文/旧grant正文/checkpoint body，不重开路线/增加修订。
- 四supervision保持辅助；PCE默认2+额外1已尽/2.861e-6/13.86x，RSTR默认2已尽/R2mean1.027033878e-6>1e-6；禁PCE_R4/RSTR_R3/M201自动恢复。旧RSTR9文件localcommit授权不授额外修订，全部负证据保持。

## Running And Queue
- 采集2026-10-26T13:47:46.634601+08:00：selected GPU0 UUID958e，NVML10743MiB/util1/context3381194:10694MiB，归属用途未知、未探/proc/发信号。当前canonical一次派发0Popen，CTS仍waiting/noPID；未sync或launch。没有查询/使用GPU1。BFC原20轮crash、BCR27/.4995早停已归档，当前CTS效果未知。
- 当前0running、1ready CTS waiting GPU0资源；另M206waiting但paused/dispatch_hold/resume_authorizedfalse不计ready。BEC R1隔离026c child4e8/CPU兼容修复已准备，实际R1 native/resource未跑；原BFC checkpoint19保留待具体恢复计划/人类授权。GPU1禁止。
- pinned songcl@192.168.1.115 / dl04-MS-7E06，GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c、GPU1 GPU-7f82edb9-f620-8045-caea-a75232265cd1；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster/runtime server4_conda_4ca73fba.sh，data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints。keys/strict hostkey/先hostname，不用旧IP/密码/sudo；python -B/PYTHONDONTWRITEBYTECODE=1。
- 任何新GPU计算均需fresh实际owner/deadline/资源UUID/idle/assets/三锁；旧lease/context空不是未来许可。原训练未知claim/request/PID只读reconcile，不盲重启/kill/删锁。BFC启动三flock未覆盖整个训练，未知如实保持。

- 历史b5dc/521曾见未知PID1565126额外占卡且最小归属读取PermissionError；历史f15/509两次NVML未列该PID，不等于证明其退出/归属。本轮新0-only只核被授权GPU0，不读或计算GPU1，不重复身份探查/发信号。

## Open Questions And Risks
- 目标差距.0080不变；BFC/BCR最终收益未知。BEC/CTS仅准备与软件正确性，尚无两步native backward、同输入/common配对、原口径资源或准确率，新颖性未证。
- BFC P90+3.2118%/BCR原GPU1 median+2.55%、P90+9%更慢，不夸称全面效率或跨GPU因果；预测/含observer smoke不等于pureTRAIN峰值。fullbuffers/RNG/FP32/offdiagonal与未行使零边界尚未测。
- CTS新catalog可复用但当前无activebinding；只在原版本/原协议/fresh空卡检验。BEC已实存9b678/parent48fc，前521对应版本native/operational静态包和四结果checker已完成并受审外锚；若tested main改变必须另建兼容版本并按该版本真实检查，不从旧null推断已测或假定兄弟可ff。

## Last Tick
- 旧45eb四真臂及两原terminal已完整report/finish/FINALIZED/released；新用户不用gpu1后manual授权94075与SERVERS2583实际仅[0]，本轮e245新snapshot容量1。TEST_OWNER45eb/旧raw不改，CURRENT_OWNER e245/current0部署分开，原05:52:30操作stop保留。
- 复用同源4e8、当时合法GPU0真实2TRAIN+资源/a33c/独审5d2f，当前owner下只exact9A ff48fc→4e8，28status+bytes/index空保持；生成真实标准摘要/技术收据M214、canonical admission+budget/FIFO/一次_process_queue。其selectedGPU0 inventory10743MiB忙，仅查询/0Popen/0sync/0launch，仍waiting无PID，不是原生进度通过。
- CTS仅server4GPU0等待资源，原数据/seed1999/epochs50/maxiters70/YAML保持，训练效果未知。1准入/1queue/0新训练启动。随后wrapper duplicate result writer FileExistsError已据原result/transport/只读NVML核定known no-launch，不重跑helper；没有GPU1查询或任务。
- BEC原9b两smoke已成功但resource JIT bool index_fill失败；R1已注册/CPU精确兼容/单True→1+隔离026c(父4e8)独立保存，不旧raw重标，新native/资源仍NOT_RUN，后续仅GPU0空槽。BFC原last19完整CPU元信息/失败保留，根因/输入未复现，未自动resume；M206暂停、BCR终态不动。
- 0新候选/141IDs；当轮只CTS准入部署及BEC next_action更新，原终态账/admission/28用户文件保护。原新建准备预算不强凑候选，只有GPU0且CTS已占用，不为填buffer重跑旧hold/655/旧测试。
- 六段报告与七段memory留档后核实际FINALIZED/released和lock/pending消失；释放后不回写。后续监测只报告新结果/故障/必要用户动作。
