# Codex Research Memory

## Goal And Phase
- 最新接管f86d1cfaf966476db888f6ba553b74d1；实际owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-25T20:07:28.056644+00:00/原deadline2026-10-25T21:07:28.056644+00:00不延长。前6bdb FINALIZED/released且lock/pending消失后begin；本轮report/finish以实际receipt为准，不预签。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020/gap.0080，baseline.4894。Phase1不同层级分工→inst_feats→query/masks，supervision辅助，Phase2需人工确认。
- seed1999/epochs50/max_iters70/原YAML/data/pretrain/optimizer/precision不变；原同口径10G、bs1/lang1/warm20/repeat100 median/P90/fullunsupported，峰值显存+15%需≥+.003mIoU。禁止调参、gate/cag/cfe/layerscale、语言路由、大QKV/N²attention、重复inst注入、旧rejected改名、无图改变微调。
- standing pipeline/authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖普通实现/测试/相关版本/安全同步/准入训练，不授旧hold重开/额外修订/受保护恢复/扩大资源/改调度。
- 最新人类资源“server4 GPU1也可以用了”：pipeline/authorizations/server4_gpu1_20261025.json SHA90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8；SERVERS d5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2允许server4 physical[0,1]/每卡1，其他allowed[]。M206暂停保持；Pipeline-cluster_project Disabled。

## Champion And Baseline
- M95仍.5020；M205-MDC26/.4872、M207-HAP授权epoch18恢复后31/.5002、M208-HRC31/.4901、M209-PSBR23/.4969、M210-PSNC31/.5001、M211-BTC31/.4914均自然earlystop且未超M95。不调参重跑或整体否定hierarchy。
- BTC在前336已canonical archive_id73e3038e744b4f6a9bffb68a7b43e8f8，原source00e2b18c6b8d568a64edb496e6979d766440883c/receipt93756329…/launch保持；42038211B原log本远SHA2b4032d0b705ae7f5e8ebdba81f14d5ed7eb55da491b4b9fec2ba78342aba38c。当前snapshot new_terminal仅识别前轮归档，不是本轮新完成，未重复archive。
- HAP原epoch19 DataLoader AttributeError根因UNKNOWN，epoch18恢复授权已消费；原crash/snapshot/prior_runs保留。既有负结果/恢复/版本/归档细节见前336 memory及其证据，不重写或再启动。

## Active Hypotheses
- M213-BFC正式training，tested/admitted/primary/runtime48fc302c3c02ffef0b241be3593c386b6b65a72e/parent11a811618179ab1ddc0cee299194667413b7fdb9；receipt812454a819702e8f4d53080c1b479617d605f2175bf44a3422905688253ca01c。只替middle同父true-supported几何token，bit-up/down配对共享2C→2C/GELU同步双输出。fine/coarse/LN/cfskip/rawmeans/FPS/IDs/CSORT/HCG/单inst原件保持，非可逆/无损/新颖/收益结论。
- BFC前336实际4nativearms terminal/rc0；两原TRAIN loss9.5372838974/13.9084777832，共同843张量/156958522参数/hash04231c23…，原2batch配对；64n3多stage/56nonpower/四W quadrant原loss非零有限grad+每步slice更新。逐call/row/half零合法，singleton/empty/pad NOT_EXERCISED。实际审b8fa/43af/419f及4reconcile/status历史保持，不拿旧诊断lease再用。
- BFC真资源9.775377484G vsM959.762532428G，参数157221178（−262912）；同GPU0 median42.218151968 vs42.311575031ms（−.2208%），P9062.910521450 vs60.952819872ms（+3.2118%更慢），预测allocated−.1121%，observer-smoke+.00214%，15%条件未触发。fullunsupported保持，pureTRAIN峰值/新颖性/准确率未知。
- 前336仅已测BFC9A ff-only primary/safe runtime同步至48fc；首dispatch normalized UUID-map KeyError发生在0intent/transport，新受审raw-map执行copy才一次canonical Popen，实际result9e453fb4/最终审069833d3…；本轮不重放、不推进公共源或修改BCR8/YAML/原进程。保护28/index/账实际核保持。
- M212-BCR tested/admitted scientific source11a811618179ab1ddc0cee299194667413b7fdb9/receiptb8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac，公共runtime48fc仅BFC9 additions；原strict-exclusive双向scan/own-L-R/独立8源/映射YAML77e不变。前7526真TRAIN2/资源/准入/launch沿用，不代签CTS/BEC。
- M214-CTS validation，隔离source4e80006047d5cb3dcdfb9c1102e02c33f354a07d/唯一parent48fc，worktree pipeline/isolated_versions/cts_336ca5d7；前336源证明6b666a8c8e9d0f5bed8422fa02e6e2ea17192b1114c6eda5ecf28affb409c2d0/独审5f3eb45e…保持。原bfab八model+原YAML9A仍冻结原code/parent null，不回填。
- CTS同父几何cycle同步old own/±3^r，经共享3C→C/原GELU，最小3^k>=n轮；重复minus私有0，n1W[x,0,0]，无支持/pad delta0，nC状态保留。原LN/cfskip/finecoarse/rawmean/FPS/IDs/CSORT/HCG/单inst保持。dense3tap dilated circular Conv1D家族整体图替代，非新覆盖/单因素因果/新颖/重开MDC。
- 前6b CTS版本绑定operational packet tick_6bdbcf77/cts_operational_prepare/preparation.json SHA51cbc658fcf5877a0b46776e361adb99d36d4551841aacdf7559ac6d46c937d6；nativeaab40a87/worker原03329/独审0fc1425f/61真mock+69ASThash+7真CLI拒绝。新copy绑定4e8与期望live48fc，原ff7 DRAFTTrue/code-parent-null及失败元数据保持；全部runtime函数AST/原资源口径不变，无原地启用旧包。
- 前6b root单flag CTSanchor新copy310ed9显式exact0fc审后，实际只静态release eaa3 bytecopy+CTS历史/外锚；actualguard a9946e21核当前owner/context/rawUUID/版本/原deadline，prepare0/1精确registeredbusy拒绝，14非法入口+deadline拒绝，0transport/process/network/Torch/active。原8source/YAML/primary28/index/13账保持；独审另附。该结果不是NVML idle/原生两步/资源PASS。
- CTS未来沿原7036协议，在fresh真实空卡绑定后做M95/CTS固定TRAIN2+原资源；须3distinct/multiround/r>=1与三W input块每step原loss有限非零grad+实际update。缺覆盖INCONCLUSIVE，不换样本/seed/precision/阈值；内部mix call/row合法零，whole-helper input/output沿03329既有非零后验。native/resource/efficacy均未测，无M214receipt/queue/训练。
- 既有M215-BEC implementation，私有8model+原YAML字节冻结，code/source/futureparent均null，不造CTS旁支Git。双跨层joint child+parent→2C/GELU各split u/v，v按true child等权上行；原coarse LN/FFN组合后，两2C→C/GELU向middle/fine回传，原三cfskip/HCG/一次inst回写。rawmeans/FPS/IDs/CSORT与六原model文件逐字保持，coarse空/unsupported bias mask0。
- BEC当前真实stdlib生产AST plan133cases、forward provenance42cases、14拒绝/10643assertions；不是Torch/GELU数值/autograd/原数据/10G。有限CCP/REAG_CASC/HRC/lite_agg源近邻审及最终实现独审留档，不称一般新颖/attention/新覆盖/单因素收益，不恢复M206。
- BEC源码推断新4Linear787968、替代2FFN1051136、净−263168；fine/middle denseMAC各6C² vs8C²，coarse原8C²，linear metadata grouping；全口径FLOPs/CPU开销/时延/显存均未知。未来实际派生共同参数集合，不照抄843；核2U双split、4maps及原coarse loss路径grad/update，当前不入队。

- 本轮f86d CTS只读四臂结果checker已冻结并独审：pipeline/diagnostic_bundles/tick_f86d1cfa/cts_execution_review_prepare/preparation.json SHA82da6073da4044c7f666ca70519b3b3ee796e3ad536698180a581823d51e9beb；只本地软件正确性/缺失拒绝测试，actual_native_results_reviewed=false。当前catalog freshguard37a81144…核20:07原owner/context/deadline与两registeredbusy、0transport/active，不是原生资源PASS。
- 本轮f86d BEC禁用/无版本native工具冻结并独审：pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_prepare/preparation.json SHA322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff；复用原M95 setup/TRAIN2/criterion/optimizer/原resources整函数AST，只读观测原production split/mean/coarse/down/单inst路径。原2d06/6555不改，source/parent/10active null、DRAFTTrue；实际native/resources/原common/batch配对未知，不能原地填旧包或用软件fixture代签。

## Closed Or Failed Directions
- 本轮旧9 parked不due，未再读655旧证据正文或旧grant正文、checkpoint body；不改旧scope、失败、修订上限或恢复状态。前336有界声明/授权目录无新动作证据8f5a970b…沿用，不能当新授权。
- 四supervision保持辅助；PCE默认2+额外1已尽/2.861e-6/13.86x，RSTR默认2已尽/R2mean1.027033878e-6>1e-6；禁PCE_R4/RSTR_R3/M201自动恢复。旧RSTR9文件localcommit授权不授额外修订，全部负证据保持。

## Running And Queue
- 采集2026-10-26T04:09:46.692380+08:00上海：BFC原PID219369/start56265957 GPU0 Train6/50 4352→4360/4686；BCR原PID1215422/start51717921 GPU1 Train19/50 2731→2737/4686。两原TRAIN增长/唯一argv/cwd/fd1/8源/YAML77e/UUID核实，proofa04cf150…/独审eec37a37…。本轮preflight实时指标UNKNOWN，不用cursor或前轮best代签当前best。
- 当前2running/0ready，2准备储备CTS+源级BEC；M206-CGCA waiting但paused/dispatch_hold/resume_authorizedfalse/noPID，不计ready、不恢复迁卡；历史meta24/best.4952535927295685/noimprove7与checkpointSHAe9b42b26…保持，未读body。
- pinned songcl@192.168.1.115 / dl04-MS-7E06，GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c、GPU1 GPU-7f82edb9-f620-8045-caea-a75232265cd1；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster/runtime server4_conda_4ca73fba.sh，data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints。keys/strict hostkey/先hostname，不用旧IP/密码/sudo；python -B/PYTHONDONTWRITEBYTECODE=1。
- 任何新GPU计算均需fresh实际owner/deadline/资源UUID/idle/assets/三锁；旧lease/context空不是未来许可。原训练未知claim/request/PID只读reconcile，不盲重启/kill/删锁。BFC启动三flock未覆盖整个训练，未知如实保持。

## Open Questions And Risks
- 目标差距.0080不变；BFC/BCR最终收益未知。BEC/CTS仅准备与软件正确性，尚无两步native backward、同输入/common配对、原口径资源或准确率，新颖性未证。
- BFC P90+3.2118%/BCR原GPU1 median+2.55%、P90+9%更慢，不夸称全面效率或跨GPU因果；预测/含observer smoke不等于pureTRAIN峰值。fullbuffers/RNG/FP32/offdiagonal与未行使零边界尚未测。
- CTS新catalog可复用但当前无activebinding；只在原版本/原协议/fresh空卡检验。BEC还需兼容当时实际tested main源版本与native observer，不从旧null推断已测或造旁支假定可ff。

## Last Tick
- 本轮f86d snapshot2running/0ready、candidate_budget2、reserve_target/count2、creation/reserve0，due仅CTS与BEC，旧9不due。begin先查/尝试已有合格队列，M206paused不是ready；无新终态或运行故障。
- root有界两原native观察BFC6:4352→4360、BCR19:2731→2737，current CTS37a8实际localguard/2busy/14invalid/deadline全部正确且无transport；23项独审eec37a37…通过，未再次preflight或反复poll GPU。
- 两分工推进既有候选：CTS四原真实结果语义checker与本地软件测试/独审；BEC原2d06对应disabled/unversioned native observer/manifest/template/本地软件测试/独审。不是新模型候选或真实TRAIN/resource实验，未改原freeze或放松门槛。
- 0新候选/0准入/0queue/0启动/0训练终态；保护公共HEAD48fc/index空/历史28status+bytes/10运行归档账，四个允许候选仅更新准备/观察证据，141IDs集合保持，M206与旧9保持。
- 完整证据tick_f86d1cfa；真实implementation tick_attempt、七段memory和Chinese notes后canonical六段report/finish，核实际FINALIZED/released及lock/pending消失，释放后不回写。当前无新增用户确认，后续原生仍需自然空卡和fresh绑定。
